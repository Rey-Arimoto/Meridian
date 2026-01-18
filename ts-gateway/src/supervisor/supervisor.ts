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
import {
  buildOrchestrationInstructionV1,
  appendOrchQueueV1,
  loadOrchAckSetV1,
} from "../orchestrator/interface";

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
    runId?: string;
  }>;

  // PR215: Set resume fields on runPlan before execution
  setRunPlanResumeFields?: (fields: {
    resumeId?: string;
    previousRunId?: string;
    resumeStopReason?: string;
    resumeStrategy?: import("../rebalance/types").ResumeStrategyV1;
    resumeStrategyCodes?: string[];
    resumeStrategyEnforcedExecutionMode?: import("../rebalance/types").ExecutionMode;
    resumeStrategyEnforcedCodes?: string[];
    resumeDelayClassV1?: import("../rebalance/types").ResumeDelayClassV1;
    resumeDelayOffsetLabelV1?: import("../rebalance/types").ResumeDelayOffsetLabelV1;
    resumeDelayReasonCodesV1?: string[];
  }) => void;
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
 * PR208: Generate resume ID for resume re-execution traceability
 *
 * @returns Resume ID in format RESUME_{timestamp}_{random}
 */
function generateResumeIdV1(): string {
  const ts = Date.now();
  const rand = Math.floor(Math.random() * 100000);
  return `RESUME_${ts}_${rand}`;
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
 * PR213: Summarize resume strategy reason codes (label-only)
 *
 * @param codes - Array of strategy reason codes
 * @returns Summary object with status and joined string
 *
 * Purpose:
 *   Create deterministic, fixed-length summary of strategy codes for telemetry.
 *   Same pattern as summarizeResumeReasonCodesV1.
 *
 * Rules:
 *   - Empty/undefined → {status: "EMPTY", joined: ""}
 *   - Filter to string-only values (defensive)
 *   - Deduplicate via Set
 *   - Sort alphabetically (deterministic ordering)
 *   - Take first 8 items
 *   - If truncated, append "REASONS_TRUNCATED"
 *   - Join with "|" separator
 *
 * IMPORTANT: Never throws, always returns summary
 */
function summarizeStrategyCodesV1(codes: string[] | undefined): {
  status: "PRESENT" | "EMPTY";
  joined: string;
} {
  try {
    if (!codes || codes.length === 0) {
      return { status: "EMPTY", joined: "" };
    }

    // Defensive: filter to string-only, dedupe, sort
    const filtered = codes.filter((c) => typeof c === "string" && c.length > 0);
    if (filtered.length === 0) {
      return { status: "EMPTY", joined: "" };
    }

    const deduped = Array.from(new Set(filtered));
    const sorted = deduped.sort();

    const maxCodes = 8;
    const truncated = sorted.length > maxCodes;
    const taken = sorted.slice(0, maxCodes);

    if (truncated) {
      taken.push("REASONS_TRUNCATED");
    }

    return {
      status: "PRESENT",
      joined: taken.join("|"),
    };
  } catch {
    // Defensive: Never throw
    return { status: "EMPTY", joined: "" };
  }
}

/**
 * PR213: Derive resume strategy from origin context (Autonomous Recovery Strategy v1)
 *
 * @param resumeDecision - Resume decision from evaluateResumeV1
 * @param resumeState - Resume state (contains origin context from PR209)
 * @returns Strategy and reason codes
 *
 * Purpose:
 *   Determine HOW to retry execution based on WHY it stopped.
 *   Safe defaults: dangerous scenarios → SIM_ONLY or WAIT.
 *
 * Constitutional:
 *   - READ-ONLY: Fixed mapping rules, no learning/optimization
 *   - Safe defaults: GATE/PHASE → SIM_ONLY, POLICY → WAIT
 *   - Label-only: All outputs are strings
 *   - Deterministic: Same inputs → same outputs
 *
 * Strategy derivation rules (v1):
 *   1. If resume decision ≠ RESUMABLE → follow decision
 *      - WAIT → WAIT_FOR_RECOVERY
 *      - ABANDON → ABANDON
 *   2. If RESUMABLE → inspect origin stop cause:
 *      - TIMEOUT → RETRY_IMMEDIATE (safe to retry)
 *      - GATE → RETRY_SAFE_SIM_ONLY (may still be blocked)
 *      - PHASE → RETRY_SAFE_SIM_ONLY (market risk may persist)
 *      - POLICY → WAIT_FOR_UNLOCK (hardstop/env key)
 *      - NONE/unknown → RETRY_SAFE_SIM_ONLY (safe default)
 *
 * IMPORTANT: Never throws, always returns strategy
 */
function deriveResumeStrategyV1(
  resumeDecision: { status: string; reasons: string[] },
  resumeState: any
): {
  strategy: import("../rebalance/types").ResumeStrategyV1;
  codes: string[];
} {
  try {
    const codes: string[] = [];

    // Rule 1: Non-RESUMABLE decisions
    if (resumeDecision.status === "WAIT") {
      codes.push("STRAT_DECISION_WAIT");
      return { strategy: "WAIT_FOR_RECOVERY", codes };
    }

    if (resumeDecision.status === "ABANDON") {
      codes.push("STRAT_DECISION_ABANDON");
      return { strategy: "ABANDON", codes };
    }

    if (resumeDecision.status !== "RESUMABLE") {
      // UNKNOWN or unexpected status → safe default
      codes.push("STRAT_DECISION_UNKNOWN");
      return { strategy: "WAIT_FOR_RECOVERY", codes };
    }

    // Rule 2: RESUMABLE → inspect origin context (PR209 fields)
    const originStopCause = resumeState?.originStopCause || "NONE";
    const originRunReasonCodes = resumeState?.originRunReasonCodes || [];

    // Helper: check if reason codes contain prefix
    const hasReasonPrefix = (prefix: string): boolean => {
      return originRunReasonCodes.some((code: string) =>
        typeof code === "string" && code.includes(prefix)
      );
    };

    // TIMEOUT → safe to retry immediately
    if (originStopCause === "TIMEOUT") {
      codes.push("STRAT_FROM_TIMEOUT");
      return { strategy: "RETRY_IMMEDIATE", codes };
    }

    // GATE → retry in SIM_ONLY (gate may still block)
    if (originStopCause === "GATE" || hasReasonPrefix("RUN_GATE_")) {
      codes.push("STRAT_FROM_GATE");
      codes.push("STRAT_EXEC_MODE_SIM_ONLY");
      return { strategy: "RETRY_SAFE_SIM_ONLY", codes };
    }

    // PHASE → retry in SIM_ONLY (market risk may persist)
    if (
      originStopCause === "PHASE" ||
      hasReasonPrefix("RUN_PHASE_") ||
      hasReasonPrefix("PHASE_TXN_")
    ) {
      codes.push("STRAT_FROM_PHASE_RISK");
      codes.push("STRAT_EXEC_MODE_SIM_ONLY");
      return { strategy: "RETRY_SAFE_SIM_ONLY", codes };
    }

    // POLICY → wait for unlock (hardstop/env key)
    if (originStopCause === "POLICY" || hasReasonPrefix("RUN_POLICY_")) {
      codes.push("STRAT_FROM_POLICY");
      codes.push("STRAT_WAIT_FOR_UNLOCK");
      return { strategy: "WAIT_FOR_UNLOCK", codes };
    }

    // NONE/unknown → safe default (SIM_ONLY)
    codes.push("STRAT_FROM_UNKNOWN");
    codes.push("STRAT_EXEC_MODE_SIM_ONLY");
    return { strategy: "RETRY_SAFE_SIM_ONLY", codes };
  } catch {
    // Defensive: Never throw, return safe default
    return {
      strategy: "WAIT_FOR_RECOVERY",
      codes: ["STRAT_ERROR"],
    };
  }
}

/**
 * PR214: Derive execution mode override from resume strategy (Enforcement v1)
 *
 * @param resumeStrategy - Resume strategy from PR213
 * @param currentDesiredMode - Current/desired execution mode (optional)
 * @returns Enforced execution mode and reason codes
 *
 * Purpose:
 *   Enforce strategy-driven execution control. Strategy determines safe mode
 *   for resumed execution based on stop cause and risk assessment.
 *
 * Constitutional:
 *   - READ-ONLY: Fixed mapping rules, no learning
 *   - Safety-first: NEVER allow LIVE execution (v1.4 constraint)
 *   - Safe defaults: Cap at DRY_RUN, prefer SIM_ONLY for risky scenarios
 *   - Label-only: All codes are strings
 *   - Deterministic: Same inputs → same outputs
 *
 * Enforcement rules (v1):
 *   1. RETRY_SAFE_SIM_ONLY → enforcedMode = "SIM_ONLY"
 *   2. WAIT_FOR_UNLOCK → enforcedMode = "SIM_ONLY"
 *   3. WAIT_FOR_RECOVERY → enforcedMode = "SIM_ONLY"
 *   4. RETRY_IMMEDIATE → cap at DRY_RUN (never escalate to LIVE)
 *      - If currentDesiredMode = "LIVE" → enforcedMode = "DRY_RUN" (capped)
 *      - If currentDesiredMode = "DRY_RUN" → enforcedMode = "DRY_RUN" (keep)
 *      - Else → enforcedMode = "SIM_ONLY" (safe default)
 *   5. ABANDON → enforcedMode = "SIM_ONLY" (shouldn't re-exec)
 *   6. Unknown → enforcedMode = "SIM_ONLY" (safe default)
 *
 * IMPORTANT: Never throws, always returns enforcement decision
 */
function deriveExecutionModeOverrideFromStrategyV1(
  resumeStrategy: import("../rebalance/types").ResumeStrategyV1,
  currentDesiredMode?: import("../rebalance/types").ExecutionMode
): {
  enforcedMode: import("../rebalance/types").ExecutionMode;
  enforcedCodes: string[];
} {
  try {
    const codes: string[] = [];

    // Rule 1-3: Safe retry strategies → SIM_ONLY
    if (
      resumeStrategy === "RETRY_SAFE_SIM_ONLY" ||
      resumeStrategy === "WAIT_FOR_UNLOCK" ||
      resumeStrategy === "WAIT_FOR_RECOVERY"
    ) {
      codes.push("STRAT_ENFORCE_EXEC_MODE_SIM_ONLY");
      return { enforcedMode: "SIM_ONLY", enforcedCodes: codes };
    }

    // Rule 4: RETRY_IMMEDIATE → cap at DRY_RUN (never allow LIVE)
    if (resumeStrategy === "RETRY_IMMEDIATE") {
      if (currentDesiredMode === "LIVE") {
        // Cap LIVE down to DRY_RUN (v1.4 safety constraint)
        codes.push("STRAT_ENFORCE_CAPPED_FROM_LIVE");
        codes.push("STRAT_ENFORCE_EXEC_MODE_DRY_RUN");
        return { enforcedMode: "DRY_RUN", enforcedCodes: codes };
      } else if (currentDesiredMode === "DRY_RUN") {
        // Keep DRY_RUN (no override needed)
        codes.push("STRAT_ENFORCE_NO_OVERRIDE");
        return { enforcedMode: "DRY_RUN", enforcedCodes: codes };
      } else {
        // Default to SIM_ONLY (safe)
        codes.push("STRAT_ENFORCE_EXEC_MODE_SIM_ONLY");
        return { enforcedMode: "SIM_ONLY", enforcedCodes: codes };
      }
    }

    // Rule 5-6: ABANDON or unknown → SIM_ONLY (safe default)
    codes.push("STRAT_ENFORCE_EXEC_MODE_SIM_ONLY");
    return { enforcedMode: "SIM_ONLY", enforcedCodes: codes };
  } catch {
    // Defensive: Never throw, return safe default
    return {
      enforcedMode: "SIM_ONLY",
      enforcedCodes: ["STRAT_ENFORCE_ERROR"],
    };
  }
}

/**
 * PR215: Derive resume re-execution timing from strategy (Timing Control v1)
 *
 * @param resumeStrategy - Resume strategy from PR213
 * @param originStopCause - Origin stop cause from PR209
 * @returns Timing decision with delay class, offset label, and reason codes
 *
 * Purpose:
 *   Determine WHEN to re-execute based on WHY it stopped.
 *   Provides explainable delay/backoff without numeric timestamps.
 *
 * Constitutional:
 *   - READ-ONLY: Fixed delay mapping, no learning
 *   - Label-only: No numeric milliseconds/timestamps
 *   - Deterministic: Same inputs → same outputs
 *   - Scheduler-less v1: Decision only, no actual scheduling
 *
 * Timing mapping rules (v1):
 *   1. TIMEOUT / RETRY_IMMEDIATE → IMMEDIATE + DELAY_0S
 *   2. GATE / PHASE / RETRY_SAFE_SIM_ONLY → BACKOFF_SHORT + DELAY_2M
 *   3. POLICY / WAIT_FOR_UNLOCK → MANUAL + DELAY_1H
 *   4. WAIT_FOR_RECOVERY → BACKOFF_LONG + DELAY_15M
 *   5. ABANDON → MANUAL + DELAY_1H
 *   6. Unknown → BACKOFF_SHORT + DELAY_2M (safe default)
 *
 * IMPORTANT: Never throws, always returns timing decision
 */
function deriveResumeReexecTimingV1(args: {
  resumeStrategy?: import("../rebalance/types").ResumeStrategyV1;
  originStopCause?: import("../rebalance/types").StopCause;
}): {
  delayClass: import("../rebalance/types").ResumeDelayClassV1;
  delayOffsetLabel: import("../rebalance/types").ResumeDelayOffsetLabelV1;
  timingReasonCodes: string[];
} {
  try {
    const { resumeStrategy, originStopCause } = args;
    const codes: string[] = [];

    // Rule 1: TIMEOUT or RETRY_IMMEDIATE → execute immediately
    if (originStopCause === "TIMEOUT" || resumeStrategy === "RETRY_IMMEDIATE") {
      if (originStopCause === "TIMEOUT") {
        codes.push("TIMING_FROM_TIMEOUT");
      }
      codes.push("TIMING_IMMEDIATE");
      codes.push("TIMING_DELAY_0S");
      return {
        delayClass: "IMMEDIATE",
        delayOffsetLabel: "DELAY_0S",
        timingReasonCodes: codes,
      };
    }

    // Rule 2: GATE/PHASE or RETRY_SAFE_SIM_ONLY → short backoff
    if (
      originStopCause === "GATE" ||
      originStopCause === "PHASE" ||
      resumeStrategy === "RETRY_SAFE_SIM_ONLY"
    ) {
      if (originStopCause === "GATE") {
        codes.push("TIMING_FROM_GATE");
      }
      if (originStopCause === "PHASE") {
        codes.push("TIMING_FROM_PHASE");
      }
      codes.push("TIMING_BACKOFF_SHORT");
      codes.push("TIMING_DELAY_2M");
      return {
        delayClass: "BACKOFF_SHORT",
        delayOffsetLabel: "DELAY_2M",
        timingReasonCodes: codes,
      };
    }

    // Rule 3: POLICY or WAIT_FOR_UNLOCK → manual intervention
    if (originStopCause === "POLICY" || resumeStrategy === "WAIT_FOR_UNLOCK") {
      if (originStopCause === "POLICY") {
        codes.push("TIMING_FROM_POLICY");
      }
      codes.push("TIMING_MANUAL");
      codes.push("TIMING_DELAY_1H");
      return {
        delayClass: "MANUAL",
        delayOffsetLabel: "DELAY_1H",
        timingReasonCodes: codes,
      };
    }

    // Rule 4: WAIT_FOR_RECOVERY → long backoff
    if (resumeStrategy === "WAIT_FOR_RECOVERY") {
      codes.push("TIMING_FROM_RECOVERY");
      codes.push("TIMING_BACKOFF_LONG");
      codes.push("TIMING_DELAY_15M");
      return {
        delayClass: "BACKOFF_LONG",
        delayOffsetLabel: "DELAY_15M",
        timingReasonCodes: codes,
      };
    }

    // Rule 5: ABANDON → manual (no re-exec)
    if (resumeStrategy === "ABANDON") {
      codes.push("TIMING_MANUAL");
      codes.push("TIMING_DELAY_1H");
      return {
        delayClass: "MANUAL",
        delayOffsetLabel: "DELAY_1H",
        timingReasonCodes: codes,
      };
    }

    // Rule 6: Unknown → safe default (short backoff)
    codes.push("TIMING_UNKNOWN");
    codes.push("TIMING_BACKOFF_SHORT");
    codes.push("TIMING_DELAY_2M");
    return {
      delayClass: "BACKOFF_SHORT",
      delayOffsetLabel: "DELAY_2M",
      timingReasonCodes: codes,
    };
  } catch {
    // Defensive: Never throw, return safe default
    return {
      delayClass: "BACKOFF_SHORT",
      delayOffsetLabel: "DELAY_2M",
      timingReasonCodes: ["TIMING_ERROR"],
    };
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

    // PR216: Load orchestration ACK set (for idempotency)
    const orchAckSet = loadOrchAckSetV1();
    if (orchAckSet.size > 0) {
      notes.push(`NOTE_ORCH_ACK_LOADED_COUNT_${orchAckSet.size}`);
      // Emit ORCH_ACK for each ACKed resume_id (v1: simple approach)
      // Note: In production, may want to track "last seen" to avoid re-emitting
      for (const resumeId of orchAckSet) {
        await appendEventV1(
          createEventV1("ORCH_ACK", "INFO", {
            resume_id: resumeId,
            ack_status: "ACKED",
          })
        ).catch(() => {}); // Defensive: Don't fail on telemetry error
      }
    }

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

      // PR208: Resume re-execution traceability
      let resumeId: string | undefined;
      let previousRunId: string | undefined;
      let stopReason: string | undefined;
      let resumeStatus: string | undefined;

      // PR213: Resume strategy derivation (declare outside for wider scope)
      let resumeStrategy: import("../rebalance/types").ResumeStrategyV1 | undefined;
      let resumeStrategyCodes: string[] | undefined;
      let strategySummary: { status: "PRESENT" | "EMPTY"; joined: string } = {
        status: "EMPTY",
        joined: "",
      };

      // PR214: Enforcement variables (declare outside for wider scope)
      let enforcedExecutionMode: import("../rebalance/types").ExecutionMode | undefined;
      let enforcedCodes: string[] | undefined;
      let enforcedSummary: { status: "PRESENT" | "EMPTY"; joined: string } = {
        status: "EMPTY",
        joined: "",
      };

      // PR215: Timing variables (declare outside for wider scope)
      let resumeDelayClass: import("../rebalance/types").ResumeDelayClassV1 | undefined;
      let resumeDelayOffsetLabel: import("../rebalance/types").ResumeDelayOffsetLabelV1 | undefined;
      let resumeTimingReasonCodes: string[] | undefined;
      let timingSummary: { status: "PRESENT" | "EMPTY"; joined: string } = {
        status: "EMPTY",
        joined: "",
      };

      if (state.resumeState) {
        resumeId = generateResumeIdV1();
        // Extract previous run ID if available (assume lastRun has runId)
        previousRunId = (state.lastRun as any)?.runId || "UNKNOWN";
        stopReason = state.resumeState.stopReason;
        resumeStatus = "RESUMABLE"; // If we're here, resume decision was RESUMABLE

        // PR213: Derive resume strategy from origin context
        // Need to access resumeDecision from earlier scope
        // Since we're here, we know resumeDecision.status was RESUMABLE
        const strategyDerived = deriveResumeStrategyV1(
          { status: "RESUMABLE", reasons: [] },
          state.resumeState
        );
        resumeStrategy = strategyDerived.strategy;
        resumeStrategyCodes = strategyDerived.codes;

        strategySummary = summarizeStrategyCodesV1(resumeStrategyCodes);

        // PR214: Derive execution mode enforcement from strategy
        const enforcement = deriveExecutionModeOverrideFromStrategyV1(
          resumeStrategy,
          undefined // No current desired mode available in minimal supervisor
        );
        enforcedExecutionMode = enforcement.enforcedMode;
        enforcedCodes = enforcement.enforcedCodes;
        enforcedSummary = summarizeStrategyCodesV1(enforcedCodes);

        // PR215: Derive timing control from strategy
        const timing = deriveResumeReexecTimingV1({
          resumeStrategy,
          originStopCause: state.resumeState.originStopCause,
        });
        resumeDelayClass = timing.delayClass;
        resumeDelayOffsetLabel = timing.delayOffsetLabel;
        resumeTimingReasonCodes = timing.timingReasonCodes;
        timingSummary = summarizeStrategyCodesV1(resumeTimingReasonCodes);

        // PR213/PR214/PR215: Set resume fields on runPlan before execution
        if (deps?.setRunPlanResumeFields) {
          deps.setRunPlanResumeFields({
            resumeId,
            previousRunId,
            resumeStopReason: stopReason,
            resumeStrategy,
            resumeStrategyCodes,
            resumeStrategyEnforcedExecutionMode: enforcedExecutionMode,
            resumeStrategyEnforcedCodes: enforcedCodes,
            resumeDelayClassV1: resumeDelayClass,
            resumeDelayOffsetLabelV1: resumeDelayOffsetLabel,
            resumeDelayReasonCodesV1: resumeTimingReasonCodes,
          });
        }

        // PR208: Emit RESUME_REEXEC_ATTEMPT before runner call
        // PR213: Add resume strategy labels
        // PR214: Add enforcement labels
        // PR215: Add timing labels
        await appendEventV1(
          createEventV1("RESUME_REEXEC_ATTEMPT", "INFO", {
            resume_id: resumeId,
            previous_run_id: previousRunId,
            stop_reason: stopReason,
            resume_status: resumeStatus,
            resume_strategy: resumeStrategy, // PR213
            resume_strategy_codes_status: strategySummary.status, // PR213
            resume_strategy_codes: strategySummary.joined, // PR213
            resume_enforced_execution_mode: enforcedExecutionMode, // PR214
            resume_enforced_codes_status: enforcedSummary.status, // PR214
            resume_enforced_codes: enforcedSummary.joined, // PR214
            resume_delay_class: resumeDelayClass, // PR215
            resume_delay_offset_label: resumeDelayOffsetLabel, // PR215
            resume_timing_codes_status: timingSummary.status, // PR215
            resume_timing_codes: timingSummary.joined, // PR215
          })
        ).catch(() => {}); // Defensive: Don't fail on telemetry error
      }

      let runResult: {
        status: string;
        reasons: string[];
        resumeState?: any;
        runId?: string; // PR208: Track next_run_id
      };

      // PR215: Decision gating - if delayClass is not IMMEDIATE, defer execution
      if (resumeDelayClass && resumeDelayClass !== "IMMEDIATE") {
        // Emit RESUME_REEXEC_DEFERRED event
        if (resumeId) {
          await appendEventV1(
            createEventV1("RESUME_REEXEC_DEFERRED", "INFO", {
              resume_id: resumeId,
              previous_run_id: previousRunId || "UNKNOWN",
              stop_reason: stopReason || "UNKNOWN",
              resume_strategy: resumeStrategy || "UNKNOWN",
              resume_delay_class: resumeDelayClass,
              resume_delay_offset_label: resumeDelayOffsetLabel || "UNKNOWN",
              resume_timing_codes_status: timingSummary.status,
              resume_timing_codes: timingSummary.joined,
              deferred_reason: "DEFERRED_BY_TIMING_CLASS",
            })
          ).catch(() => {}); // Defensive: Don't fail on telemetry error

          // PR216: Build orchestration instruction and enqueue (idempotent)
          // Only enqueue if not already ACKed
          if (!orchAckSet.has(resumeId)) {
            const orchInstruction = buildOrchestrationInstructionV1({
              resumeId,
              previousRunId: previousRunId || "UNKNOWN",
              stopReason: stopReason || "UNKNOWN",
              resumeStatus: resumeStatus || "UNKNOWN",
              resumeStrategy,
              enforcedExecutionMode,
              delayClassV1: resumeDelayClass,
              delayOffsetV1: resumeDelayOffsetLabel,
              hintCodes: [
                ...(resumeStrategyCodes || []),
                ...(enforcedCodes || []),
                ...(resumeTimingReasonCodes || []),
              ],
            });

            // PR216: Emit ORCH_ENQUEUE event
            await appendEventV1(
              createEventV1("ORCH_ENQUEUE", "INFO", {
                instruction_version: orchInstruction.instruction_version,
                resume_id: orchInstruction.resume_id,
                previous_run_id: orchInstruction.previous_run_id,
                stop_reason: orchInstruction.stop_reason,
                resume_strategy: orchInstruction.resume_strategy || "UNKNOWN",
                enforced_execution_mode: orchInstruction.enforced_execution_mode || "UNKNOWN",
                delay_class_v1: orchInstruction.delay_class_v1 || "UNKNOWN",
                delay_offset_v1: orchInstruction.delay_offset_v1 || "UNKNOWN",
                orch_action: orchInstruction.orch_action,
                orch_hint_codes_status: orchInstruction.orch_hint_codes_status,
                orch_hint_codes: orchInstruction.orch_hint_codes,
              })
            ).catch(() => {}); // Defensive: Don't fail on telemetry error

            // PR216: Write to orchestration queue file
            await appendOrchQueueV1(orchInstruction);
          } else {
            notes.push("NOTE_ORCH_ENQUEUE_SKIPPED_ALREADY_ACKED");
          }
        }

        // Set runResult to indicate deferred status
        runResult = {
          status: "DEFERRED",
          reasons: ["REASON_RESUME_DEFERRED_BY_TIMING", ...(resumeTimingReasonCodes || [])],
        };
      } else {
        // PR215: delayClass is IMMEDIATE (or not set), proceed with normal execution
        try {
          if (deps?.runTwapExecution) {
            runResult = await deps.runTwapExecution();
          } else {
            // Default: no-op (for minimal implementation)
            runResult = {
              status: "COMPLETED",
              reasons: ["REASON_NO_RUNNER_PROVIDED"],
            };
          }

          // PR208: Emit RESUME_REEXEC_RESULT after successful runner call
          // PR213: Add resume strategy labels
          // PR214: Add enforcement labels
          // PR215: Add timing labels
          if (resumeId) {
            await appendEventV1(
              createEventV1("RESUME_REEXEC_RESULT", "INFO", {
                resume_id: resumeId,
                previous_run_id: previousRunId || "UNKNOWN",
                next_run_id: runResult.runId || "UNKNOWN",
                stop_reason: stopReason || "UNKNOWN",
                resume_status: resumeStatus || "UNKNOWN",
                execution_status: runResult.status,
                resume_strategy: resumeStrategy || "UNKNOWN", // PR213
                resume_strategy_codes_status: strategySummary.status, // PR213
                resume_strategy_codes: strategySummary.joined, // PR213
                resume_enforced_execution_mode: enforcedExecutionMode || "UNKNOWN", // PR214
                resume_enforced_codes_status: enforcedSummary.status, // PR214
                resume_enforced_codes: enforcedSummary.joined, // PR214
                resume_delay_class: resumeDelayClass || "UNKNOWN", // PR215
                resume_delay_offset_label: resumeDelayOffsetLabel || "UNKNOWN", // PR215
                resume_timing_codes_status: timingSummary.status, // PR215
                resume_timing_codes: timingSummary.joined, // PR215
              })
            ).catch(() => {}); // Defensive: Don't fail on telemetry error
          }
        } catch (error) {
          // PR208: Emit RESUME_REEXEC_RESULT on error
          // PR213: Add resume strategy labels
          // PR214: Add enforcement labels
          // PR215: Add timing labels
          if (resumeId) {
            await appendEventV1(
              createEventV1("RESUME_REEXEC_RESULT", "ERROR", {
                resume_id: resumeId,
                previous_run_id: previousRunId || "UNKNOWN",
                next_run_id: "ERROR",
                stop_reason: stopReason || "UNKNOWN",
                resume_status: resumeStatus || "UNKNOWN",
                execution_status: "ERROR",
                resume_strategy: resumeStrategy || "UNKNOWN", // PR213
                resume_strategy_codes_status: strategySummary.status, // PR213
                resume_strategy_codes: strategySummary.joined, // PR213
                resume_enforced_execution_mode: enforcedExecutionMode || "UNKNOWN", // PR214
                resume_enforced_codes_status: enforcedSummary.status, // PR214
                resume_enforced_codes: enforcedSummary.joined, // PR214
                resume_delay_class: resumeDelayClass || "UNKNOWN", // PR215
                resume_delay_offset_label: resumeDelayOffsetLabel || "UNKNOWN", // PR215
                resume_timing_codes_status: timingSummary.status, // PR215
                resume_timing_codes: timingSummary.joined, // PR215
              }, ["ERROR_RUNNER_EXCEPTION"])
            ).catch(() => {}); // Defensive: Don't fail on telemetry error
          }

          // Re-throw to maintain existing error handling
          throw error;
        }
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
