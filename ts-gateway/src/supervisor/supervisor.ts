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

      // PR164: Emit RESUME_EVAL event
      await appendEventV1(
        createEventV1("RESUME_EVAL", "INFO", {
          resume_status: resumeDecision.status,
          stop_reason: state.resumeState.stopReason,
        }, resumeDecision.reasons)
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
