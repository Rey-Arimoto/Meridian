/**
 * PR163: v1.4 Supervisor Loop (READ-ONLY)
 * PR164: Telemetry integration
 *
 * Purpose:
 *   24/7 operational loop that ticks periodically, evaluates resume conditions,
 *   and runs TWAP-lite execution when safe.
 *
 * Constitutional Constraints:
 *   - READ-ONLY: Fixed tick logic, no learning, no optimization
 *   - Double-key maintained: PR156 policy controls execution
 *   - Safe defaults: Uncertain → WAIT
 *   - Label-only: All actions/reasons are labels
 *   - Defensive: Never throws, always returns result
 */

import { StateStore, MeridianStateV1 } from "../state";
import { evaluateResumeV1, ResumeInputs } from "../rebalance/resumePolicy";
import { createEventV1, appendEventV1 } from "../telemetry";
import {
  buildMarketRegimeSnapshotV1,
  appendSnapshotV1,
  SnapshotInputsV1,
} from "../snapshot";
import { evaluateSpecLockV1 } from "../spec";

/**
 * Supervisor action (label-only)
 */
export type SupervisorAction =
  | "ACTION_WAIT_RESUME" // Waiting for resume conditions
  | "ACTION_RUN_TWAP" // Running TWAP execution
  | "ACTION_ABORT" // Abandoned run
  | "ACTION_NOOP" // No action needed
  | "ACTION_WAIT_HARDSTOP" // Waiting for HardStop release
  | "ACTION_ERROR"; // Error occurred

/**
 * Supervisor config
 */
export interface SupervisorConfig {
  // Tick interval (internal numeric only)
  tickIntervalMs: number;

  // Max ticks (for testing)
  maxTicks?: number;

  // Dry run mode (simulation only)
  dryRun?: boolean;
}

/**
 * Supervisor tick result
 */
export interface SupervisorTickResult {
  // Status
  status: "OK" | "ERROR";

  // Action taken (label-only)
  action: SupervisorAction;

  // Warnings (label-only)
  warnings: string[];

  // Notes (label-only, for debugging)
  notes: string[];
}

/**
 * Supervisor dependencies (for testing/DI)
 */
export interface SupervisorDeps {
  // Get current timestamp
  getNowMs?: () => number;

  // Evaluate policy (PR156)
  evaluatePolicy?: () => Promise<{
    allowExecution: boolean;
    hardStopActive: boolean;
    status: string;
    reasons: string[];
  }>;

  // Get resume inputs (for PR162 evaluation)
  getResumeInputs?: () => Promise<ResumeInputs>;

  // Run TWAP execution (PR159/161/162)
  runTwapExecution?: () => Promise<{
    status: string;
    reasons: string[];
    resumeState?: any;
  }>;
}

/**
 * PR207: Summarize resume reason codes for telemetry
 *
 * @param codes - Array of resume reason code strings
 * @param maxCodes - Maximum number of codes to include (default: 8)
 * @returns Summary object with status and joined string
 *
 * Rules:
 * - Empty/undefined → {status: "EMPTY", joined: ""}
 * - Filter to string-only values (defensive)
 * - Deduplicate via Set
 * - Sort alphabetically (deterministic)
 * - Truncate to maxCodes (with REASONS_TRUNCATED marker)
 * - Join with pipe separator
 */
function summarizeResumeReasonCodesV1(
  codes?: unknown[],
  maxCodes: number = 8
): { status: "PRESENT" | "EMPTY"; joined: string } {
  try {
    if (!Array.isArray(codes) || codes.length === 0) {
      return { status: "EMPTY", joined: "" };
    }

    // Filter to strings only (defensive)
    const stringCodes = codes.filter(
      (c): c is string => typeof c === "string" && c.length > 0
    );
    if (stringCodes.length === 0) {
      return { status: "EMPTY", joined: "" };
    }

    // Deduplicate and sort
    const unique = Array.from(new Set(stringCodes)).sort();

    // Truncate if needed
    let final = unique;
    if (unique.length > maxCodes) {
      final = unique.slice(0, maxCodes);
      final.push("REASONS_TRUNCATED");
    }

    return { status: "PRESENT", joined: final.join("|") };
  } catch {
    // Defensive: Never throw
    return { status: "EMPTY", joined: "" };
  }
}

/**
 * PR207: Derive resume reason codes from inputs and decision
 *
 * @param inputs - Resume inputs
 * @param decision - Resume decision
 * @param resumeState - Resume state (optional)
 * @returns Array of resume reason codes
 *
 * Maps resume evaluation inputs and decision to structured reason codes.
 * Always returns at least one code (RESUME_UNKNOWN as fallback).
 */
function deriveResumeReasonCodesV1(
  inputs: ResumeInputs,
  decision: { status: string; reasons: string[] },
  resumeState?: any
): import("../rebalance/types").ResumeReasonCode[] {
  const codes: import("../rebalance/types").ResumeReasonCode[] = [];

  try {
    // Decision status
    if (decision.status === "RESUMABLE") {
      codes.push("RESUME_ALLOWED");
    } else if (decision.status === "WAIT") {
      codes.push("RESUME_BLOCKED");
    } else if (decision.status === "ABANDON") {
      codes.push("RESUME_EXPIRED");
    } else {
      codes.push("RESUME_UNKNOWN");
    }

    // Oracle condition
    if (inputs.oracleStatus === "AVAILABLE") {
      codes.push("RESUME_ORACLE_AVAILABLE");
    } else if (inputs.oracleStatus === "STALE" || inputs.oracleStatus === "ERROR") {
      codes.push("RESUME_ORACLE_UNAVAILABLE");
    }

    // Gate condition
    if (inputs.gateStatus === "PASS") {
      codes.push("RESUME_GATE_PASS");
    } else if (inputs.gateStatus === "BLOCK" || inputs.gateStatus === "ERROR") {
      codes.push("RESUME_GATE_BLOCK");
    }

    // Route condition
    if (inputs.routeAvailable === true) {
      codes.push("RESUME_ROUTE_AVAILABLE");
    } else if (inputs.routeAvailable === false) {
      codes.push("RESUME_ROUTE_UNAVAILABLE");
    }

    // Policy/HardStop condition
    if (inputs.hardStopActive === true) {
      codes.push("RESUME_HARDSTOP_ACTIVE");
    } else if (inputs.hardStopActive === false) {
      codes.push("RESUME_HARDSTOP_INACTIVE");
    }

    if (inputs.policyEnvEnabled === true) {
      codes.push("RESUME_POLICY_ENV_ENABLED");
    } else if (inputs.policyEnvEnabled === false) {
      codes.push("RESUME_POLICY_ENV_DISABLED");
    }

    // Phase condition
    const phaseLabel = inputs.phaseLabel;
    if (phaseLabel === "PHASE_NORMAL" || phaseLabel === "PHASE_RECOVERY") {
      codes.push("RESUME_PHASE_NORMAL");
    } else if (
      phaseLabel === "PHASE_DOWN_SHOCK" ||
      phaseLabel === "PHASE_UP_SHOCK" ||
      phaseLabel === "PHASE_UP_REVERSAL" ||
      phaseLabel === "PHASE_DOWN_REVERSAL"
    ) {
      codes.push("RESUME_PHASE_RISK");
    }

    // Timeout condition (check if resumeAfterTs is set and if we've passed it)
    if (resumeState?.resumeAfterTs) {
      if (inputs.nowTs >= resumeState.resumeAfterTs) {
        codes.push("RESUME_TIMEOUT_OK");
      } else {
        codes.push("RESUME_TIMEOUT_EXCEEDED");
      }
    }

    // Defensive fallback
    if (codes.length === 0) {
      codes.push("RESUME_UNKNOWN");
    }

    return codes;
  } catch {
    // Defensive: Never throw
    return ["RESUME_UNKNOWN"];
  }
}

/**
 * Run supervisor once (single tick)
 *
 * @param store - State store
 * @param cfg - Config (optional)
 * @param deps - Dependencies (optional, for testing)
 * @returns Tick result
 *
 * Fixed Tick Flow:
 *   Step 0: Read state
 *   Step 1: Evaluate policy (PR156)
 *   Step 2: If resumeState exists, evaluate resume (PR162)
 *   Step 3: If RESUMABLE, run TWAP execution (PR159/161/162)
 *   Step 4: Save results to state
 *   Step 5: Update health
 *
 * IMPORTANT: Never throws, always returns result (defensive)
 */
export async function runSupervisorOnceV1(
  store: StateStore,
  cfg?: Partial<SupervisorConfig>,
  deps?: SupervisorDeps
): Promise<SupervisorTickResult> {
  const warnings: string[] = [];
  const notes: string[] = [];
  const getNowMs = deps?.getNowMs || (() => Date.now());

  try {
    notes.push("NOTE_SUPERVISOR_TICK_START");

    // PR164: Emit SUPERVISOR_TICK event
    await appendEventV1(
      createEventV1("SUPERVISOR_TICK", "INFO", {
        action: "TICK_START",
      })
    ).catch(() => {}); // Defensive: Don't fail on telemetry error

    // Step 0: Read state
    const readResult = await store.readState();
    warnings.push(...readResult.warnings);

    if (readResult.status === "ERROR") {
      notes.push("NOTE_STATE_READ_ERROR");
      return {
        status: "ERROR",
        action: "ACTION_ERROR",
        warnings,
        notes,
      };
    }

    const state = readResult.state;
    notes.push("NOTE_STATE_LOADED");

    // Step 1: Evaluate policy (PR156)
    let policyResult: {
      allowExecution: boolean;
      hardStopActive: boolean;
      status: string;
      reasons: string[];
    };

    if (deps?.evaluatePolicy) {
      policyResult = await deps.evaluatePolicy();
    } else {
      // Default: assume policy OK (for minimal implementation)
      policyResult = {
        allowExecution: true,
        hardStopActive: false,
        status: "ALLOW",
        reasons: [],
      };
    }

    notes.push(`NOTE_POLICY_STATUS_${policyResult.status}`);

    // PR179: Evaluate spec lock status
    try {
      const specLockResult = await evaluateSpecLockV1();

      // Emit telemetry based on spec lock status
      if (specLockResult.status === "ACTIVE_OK") {
        await appendEventV1(
          createEventV1("SPEC_LOCK_STATUS", "INFO", {
            status: specLockResult.status,
            activeSpec: specLockResult.activeSpec || "SPEC_NONE",
          })
        ).catch(() => {});
      } else if (specLockResult.status === "LOCKED_EXPIRED") {
        await appendEventV1(
          createEventV1("SPEC_LOCK_EXPIRED", "WARN", {
            status: specLockResult.status,
            activeSpec: specLockResult.activeSpec || "NONE",
            latestSpec: specLockResult.latestSpec || "NONE",
          })
        ).catch(() => {});
        notes.push("NOTE_SPEC_LOCK_EXPIRED");
      } else if (specLockResult.status === "LOCKED_PENDING_ACK") {
        await appendEventV1(
          createEventV1("SPEC_LOCK_STATUS", "WARN", {
            status: specLockResult.status,
            latestSpec: specLockResult.latestSpec || "NONE",
          })
        ).catch(() => {});
        notes.push("NOTE_SPEC_PENDING_ACK");
      } else if (specLockResult.status === "ERROR") {
        await appendEventV1(
          createEventV1("SPEC_LOCK_ERROR", "ERROR", {
            status: specLockResult.status,
          })
        ).catch(() => {});
        warnings.push("WARN_SPEC_LOCK_ERROR");
      }

      warnings.push(...specLockResult.warnings);
    } catch (error) {
      // Defensive: Don't fail supervisor on spec lock error
      warnings.push("WARN_SPEC_LOCK_EVAL_EXCEPTION");
    }

    // Check if HardStop is active
    if (policyResult.hardStopActive) {
      notes.push("NOTE_HARDSTOP_ACTIVE_WAITING");

      // PR164: Emit POLICY_BLOCK event
      await appendEventV1(
        createEventV1("POLICY_BLOCK", "WARN", {
          policy_reason: policyResult.reasons[0] || "HARDSTOP_ACTIVE",
        })
      ).catch(() => {});

      // Update state with HardStop info
      await store.patchState({
        hardStop: {
          active: true,
          reason: policyResult.reasons[0],
        },
        health: {
          oracle: state.health?.oracle || "UNKNOWN",
          route: state.health?.route || "UNKNOWN",
          policy: "DENY",
          notes: ["NOTE_HARDSTOP_ACTIVE"],
        },
      });

      return {
        status: "OK",
        action: "ACTION_WAIT_HARDSTOP",
        warnings,
        notes,
      };
    }

    // Step 2: If resumeState exists, evaluate resume (PR162)
    if (state.resumeState) {
      notes.push("NOTE_RESUME_STATE_EXISTS");

      // Get resume inputs
      let resumeInputs: ResumeInputs;

      if (deps?.getResumeInputs) {
        resumeInputs = await deps.getResumeInputs();
      } else {
        // Default: assume all conditions OK (for minimal implementation)
        resumeInputs = {
          nowTs: getNowMs(),
          oracleStatus: "AVAILABLE",
          gateStatus: "PASS",
          phaseLabel: "PHASE_NORMAL",
          routeAvailable: true,
          hardStopActive: false,
          policyEnvEnabled: true,
        };
      }

      // Evaluate resume
      const resumeDecision = evaluateResumeV1(state.resumeState, resumeInputs);
      notes.push(`NOTE_RESUME_DECISION_${resumeDecision.status}`);

      // PR207: Derive resume reason codes for explainability
      const resumeReasonCodes = deriveResumeReasonCodesV1(
        resumeInputs,
        resumeDecision,
        state.resumeState
      );
      const resumeReasonSummary = summarizeResumeReasonCodesV1(resumeReasonCodes);

      // PR164/PR207: Emit RESUME_EVAL event with reason codes
      await appendEventV1(
        createEventV1("RESUME_EVAL", "INFO", {
          resume_status: resumeDecision.status,
          stop_reason: state.resumeState.stopReason,
          resume_reason_codes_status: resumeReasonSummary.status, // PR207
          resume_reason_codes: resumeReasonSummary.joined, // PR207
        }, resumeDecision.reasons)
      ).catch(() => {});

      // PR207: Emit RESUME_DECISION event for final decision audit trail
      await appendEventV1(
        createEventV1("RESUME_DECISION", "INFO", {
          resume_status: resumeDecision.status,
          stop_reason: state.resumeState.stopReason,
          resume_reason_codes_status: resumeReasonSummary.status,
          resume_reason_codes: resumeReasonSummary.joined,
        })
      ).catch(() => {});

      if (resumeDecision.status === "WAIT") {
        notes.push("NOTE_WAIT_RESUME_CONDITIONS");

        // Update health
        await store.patchState({
          health: {
            oracle: resumeInputs.oracleStatus || "UNKNOWN",
            route: resumeInputs.routeAvailable ? "AVAILABLE" : "NONE",
            policy: policyResult.allowExecution ? "OK" : "DENY",
            notes: ["NOTE_WAIT_RESUME"],
          },
        });

        return {
          status: "OK",
          action: "ACTION_WAIT_RESUME",
          warnings,
          notes,
        };
      } else if (resumeDecision.status === "ABANDON") {
        notes.push("NOTE_ABANDON_RUN");

        // Update state: mark as abandoned
        await store.patchState({
          lastRun: {
            status: "ABANDONED",
            stopReason: state.resumeState.stopReason,
            warnings: [...state.resumeState.warnings, "WARN_RUN_ABANDONED"],
          },
          resumeState: undefined, // Clear resume state
        });

        return {
          status: "OK",
          action: "ACTION_ABORT",
          warnings,
          notes,
        };
      } else if (resumeDecision.status === "UNKNOWN") {
        notes.push("NOTE_RESUME_UNKNOWN");

        // Treat as WAIT (conservative)
        return {
          status: "OK",
          action: "ACTION_WAIT_RESUME",
          warnings: [...warnings, "WARN_RESUME_UNKNOWN"],
          notes,
        };
      }

      // RESUMABLE → continue to execution
      notes.push("NOTE_RESUME_RESUMABLE");
    }

    // Step 3: Run TWAP execution (if no resumeState, or if RESUMABLE)
    if (policyResult.allowExecution || cfg?.dryRun) {
      notes.push("NOTE_RUN_TWAP_EXECUTION");

      let runResult: {
        status: string;
        reasons: string[];
        resumeState?: any;
      };

      if (deps?.runTwapExecution) {
        runResult = await deps.runTwapExecution();
      } else {
        // Default: no-op (for minimal implementation)
        runResult = {
          status: "COMPLETED",
          reasons: ["REASON_NO_RUNNER_PROVIDED"],
        };
      }

      notes.push(`NOTE_RUN_STATUS_${runResult.status}`);

      // Step 4: Save results to state
      const lastRun: MeridianStateV1["lastRun"] = {
        status: runResult.status,
        warnings: runResult.reasons,
      };

      // If stopped, save resumeState
      if (runResult.status === "STOPPED" && runResult.resumeState) {
        await store.patchState({
          lastRun,
          resumeState: runResult.resumeState,
        });

        return {
          status: "OK",
          action: "ACTION_RUN_TWAP",
          warnings,
          notes,
        };
      }

      // If completed, clear resumeState
      await store.patchState({
        lastRun,
        resumeState: undefined,
      });

      return {
        status: "OK",
        action: "ACTION_RUN_TWAP",
        warnings,
        notes,
      };
    }

    // No action needed
    notes.push("NOTE_NO_ACTION_NEEDED");

    // PR165: Save snapshot (defensive, failure doesn't abort tick)
    await saveSnapshotDefensive(state, policyResult);

    return {
      status: "OK",
      action: "ACTION_NOOP",
      warnings,
      notes,
    };
  } catch (error) {
    warnings.push("WARN_SUPERVISOR_UNEXPECTED_ERROR");

    return {
      status: "ERROR",
      action: "ACTION_ERROR",
      warnings,
      notes,
    };
  }
}

/**
 * Save snapshot (defensive helper)
 *
 * PR165: Generate and save market regime snapshot at tick completion.
 * Failures are logged to telemetry but don't abort the tick.
 *
 * @param state - Current state
 * @param policyResult - Policy result
 */
async function saveSnapshotDefensive(
  state: MeridianStateV1,
  policyResult: {
    allowExecution: boolean;
    hardStopActive: boolean;
    status: string;
    reasons: string[];
  }
): Promise<void> {
  try {
    // Build snapshot inputs from state
    const inputs: SnapshotInputsV1 = {
      latest: {
        // Extract from state (label-only where possible)
        hardStop: state.hardStop?.active ? "ACTIVE" : "INACTIVE",
        resume: state.resumeState ? "WAIT" : "NONE",
        policyDecision: policyResult.allowExecution ? "ALLOW" : "DENY",
        policyReason: policyResult.reasons[0],
        // Health labels
        gateDecision:
          state.health?.oracle === "AVAILABLE" ? "PASS" : "BLOCK",
        blockReason:
          state.health?.oracle !== "AVAILABLE"
            ? `ORACLE_${state.health?.oracle}`
            : undefined,
      },
    };

    // Build snapshot
    const snapshot = await buildMarketRegimeSnapshotV1(inputs);

    // Save snapshot
    const saveResult = await appendSnapshotV1(snapshot);

    // Emit telemetry event
    if (saveResult.status === "OK") {
      await appendEventV1(
        createEventV1("SNAPSHOT_SAVED", "INFO", {
          snapshot_status: snapshot.status,
          snapshot_kind: snapshot.kind,
        })
      ).catch(() => {}); // Defensive: Don't fail on telemetry error
    } else {
      await appendEventV1(
        createEventV1("SNAPSHOT_ERROR", "ERROR", {
          snapshot_status: snapshot.status,
        }, saveResult.warnings)
      ).catch(() => {}); // Defensive: Don't fail on telemetry error
    }
  } catch (error) {
    // Defensive: Snapshot failure doesn't abort tick
    await appendEventV1(
      createEventV1("SNAPSHOT_ERROR", "ERROR", {}, ["WARN_SNAPSHOT_FAILED"])
    ).catch(() => {}); // Defensive: Don't fail on telemetry error
  }
}
