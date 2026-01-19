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
  loadOrchResultLinesV1,
  loadOrchResultSeenSetV1,
  markOrchResultSeenV1,
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
    resumeEscalatedStrategy?: import("../rebalance/types").ResumeStrategyV1; // PR219
    resumeEscalationCodes?: string[]; // PR219
    resumeMarketRegime?: import("../rebalance/types").MarketRegimeV1; // PR220
    resumeMarketRegimeCodes?: string[]; // PR220
    resumeMatrixStrategy?: import("../rebalance/types").ResumeStrategyV1; // PR220
    resumeMatrixCodes?: string[]; // PR220
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
 * PR217: Derive orchestrator policy hooks v1 (label-only)
 *
 * Purpose:
 *   Derive execution timing/condition hints from resume context.
 *   Outputs are "constraints/intentions" NOT schedules.
 *   Actual scheduling is orchestrator responsibility.
 *
 * Inputs:
 *   - resumeStrategy (PR213)
 *   - resumeDelayClass (PR215)
 *   - resumeDelayOffsetLabel (PR215)
 *   - originStopCause (PR209)
 *   - policyStatus / unlockStatus (existing labels)
 *
 * Outputs (all label-only):
 *   - orch_policy_class: "NONE" | "DELAY_WINDOW" | "RETRY_LIMIT" | "MARKET_GUARD" | "UNKNOWN"
 *   - orch_not_before: "NB_0S" | "NB_30S" | "NB_2M" | "NB_5M" | "NB_15M" | "NB_1H" | "UNKNOWN"
 *   - orch_deadline: "DL_1M" | "DL_5M" | "DL_15M" | "DL_1H" | "DL_6H" | "DL_24H" | "NONE" | "UNKNOWN"
 *   - orch_retry_limit: "RETRY_0" | "RETRY_1" | "RETRY_3" | "RETRY_5" | "RETRY_10" | "UNKNOWN"
 *   - orch_market_guard: "GUARD_NONE" | "GUARD_ORACLE_OK" | "GUARD_GATE_PASS" | "GUARD_LIQUID_OK" | "UNKNOWN"
 *   - orch_hint_codes: pipe-joined, dedup/sort/truncate(8)
 *
 * Fixed Mapping Rules (v1):
 *   delayClass → orch_policy_class + orch_not_before:
 *     IMMEDIATE → "NONE" + "NB_0S"
 *     BACKOFF_SHORT → "DELAY_WINDOW" + "NB_2M"
 *     BACKOFF_LONG → "DELAY_WINDOW" + "NB_15M"
 *     MANUAL → "DELAY_WINDOW" + "NB_1H"
 *
 *   originStopCause → orch_retry_limit + orch_market_guard:
 *     TIMEOUT → "RETRY_3" + "GUARD_ORACLE_OK"
 *     GATE → "RETRY_5" + "GUARD_GATE_PASS"
 *     POLICY → "RETRY_0" + "GUARD_NONE"
 *     PHASE → "RETRY_3" + "GUARD_GATE_PASS"
 *     NONE → "RETRY_3" + "GUARD_ORACLE_OK"
 *
 *   deadline: v1 = "DL_1H" (simple default, refinement in v2+)
 *
 * IMPORTANT: Never throws, always returns hooks decision
 */
function deriveOrchPolicyHooksV1(args: {
  resumeStrategy?: import("../rebalance/types").ResumeStrategyV1;
  resumeDelayClass?: import("../rebalance/types").ResumeDelayClassV1;
  resumeDelayOffsetLabel?: import("../rebalance/types").ResumeDelayOffsetLabelV1;
  originStopCause?: import("../rebalance/types").StopCause;
}): import("../orchestrator/interface").OrchPolicyHooksV1 {
  try {
    const { resumeDelayClass, resumeDelayOffsetLabel, originStopCause } = args;
    const codes: string[] = [];

    // Derive orch_policy_class and orch_not_before from delayClass
    let policyClass: import("../orchestrator/interface").OrchPolicyClassV1 = "DELAY_WINDOW";
    let notBefore: import("../orchestrator/interface").OrchNotBeforeV1 = "NB_2M";

    if (resumeDelayClass === "IMMEDIATE") {
      policyClass = "NONE";
      notBefore = "NB_0S";
      codes.push("HINT_DELAY_IMMEDIATE");
    } else if (resumeDelayClass === "BACKOFF_SHORT") {
      policyClass = "DELAY_WINDOW";
      notBefore = "NB_2M";
      codes.push("HINT_DELAY_BACKOFF_SHORT");
    } else if (resumeDelayClass === "BACKOFF_LONG") {
      policyClass = "DELAY_WINDOW";
      notBefore = "NB_15M";
      codes.push("HINT_DELAY_BACKOFF_LONG");
    } else if (resumeDelayClass === "MANUAL") {
      policyClass = "DELAY_WINDOW";
      notBefore = "NB_1H";
      codes.push("HINT_DELAY_MANUAL");
    } else {
      // Unknown/undefined → safe default
      policyClass = "DELAY_WINDOW";
      notBefore = "NB_2M";
      codes.push("HINT_DELAY_UNKNOWN");
    }

    // Derive orch_retry_limit and orch_market_guard from originStopCause
    let retryLimit: import("../orchestrator/interface").OrchRetryLimitV1 = "RETRY_3";
    let marketGuard: import("../orchestrator/interface").OrchMarketGuardV1 = "GUARD_ORACLE_OK";

    if (originStopCause === "TIMEOUT") {
      retryLimit = "RETRY_3";
      marketGuard = "GUARD_ORACLE_OK";
      codes.push("HINT_FROM_TIMEOUT");
      codes.push("HINT_RETRY_LIMIT_3");
      codes.push("HINT_GUARD_ORACLE_OK");
    } else if (originStopCause === "GATE") {
      retryLimit = "RETRY_5";
      marketGuard = "GUARD_GATE_PASS";
      codes.push("HINT_FROM_GATE");
      codes.push("HINT_RETRY_LIMIT_5");
      codes.push("HINT_GUARD_GATE_PASS");
    } else if (originStopCause === "POLICY") {
      retryLimit = "RETRY_0";
      marketGuard = "GUARD_NONE";
      codes.push("HINT_FROM_POLICY");
      codes.push("HINT_RETRY_LIMIT_0");
      codes.push("HINT_GUARD_NONE");
    } else if (originStopCause === "PHASE") {
      retryLimit = "RETRY_3";
      marketGuard = "GUARD_GATE_PASS";
      codes.push("HINT_FROM_PHASE");
      codes.push("HINT_RETRY_LIMIT_3");
      codes.push("HINT_GUARD_GATE_PASS");
    } else {
      // NONE or unknown → safe default
      retryLimit = "RETRY_3";
      marketGuard = "GUARD_ORACLE_OK";
      codes.push("HINT_FROM_UNKNOWN");
      codes.push("HINT_RETRY_LIMIT_3");
      codes.push("HINT_GUARD_ORACLE_OK");
    }

    // Deadline: v1 = simple default (refinement in v2+)
    const deadline: import("../orchestrator/interface").OrchDeadlineV1 = "DL_1H";
    codes.push("HINT_DEADLINE_1H");

    // Process hint codes: dedup, sort, truncate to 8
    const uniqueCodes = Array.from(new Set(codes)).sort();
    const truncated = uniqueCodes.slice(0, 8);
    if (uniqueCodes.length > 8) {
      truncated.push("REASONS_TRUNCATED");
    }
    const hintCodesJoined = truncated.join("|");
    const hintCodesStatus: "PRESENT" | "EMPTY" = truncated.length > 0 ? "PRESENT" : "EMPTY";

    return {
      orch_policy_class: policyClass,
      orch_not_before: notBefore,
      orch_deadline: deadline,
      orch_retry_limit: retryLimit,
      orch_market_guard: marketGuard,
      orch_hint_codes_status: hintCodesStatus,
      orch_hint_codes: hintCodesJoined,
    };
  } catch {
    // Defensive: Never throw, return safe default
    return {
      orch_policy_class: "UNKNOWN",
      orch_not_before: "UNKNOWN",
      orch_deadline: "UNKNOWN",
      orch_retry_limit: "UNKNOWN",
      orch_market_guard: "UNKNOWN",
      orch_hint_codes_status: "EMPTY",
      orch_hint_codes: "",
    };
  }
}

/**
 * PR219: Derive resume strategy escalation from orchestrator feedback v1
 *
 * @param args - Escalation inputs
 * @returns Escalated strategy and reason codes
 *
 * Purpose:
 *   Use PR218 orchestrator feedback (orchLastStatus / orchLastOutcomeCodes)
 *   to deterministically escalate/de-escalate the next resume strategy.
 *
 * Constitutional:
 *   - READ-ONLY: Rule-based, no learning
 *   - Label-only: No numeric durations/counters
 *   - Safety-first: Never escalate to LIVE
 *   - Defensive: Never throws, handles unknown inputs gracefully
 *   - Deterministic: Same inputs → same outputs (sorted codes)
 *
 * Rules (v1):
 *   - SKIPPED_POLICY → WAIT_FOR_UNLOCK (policy says no)
 *   - SKIPPED_WINDOW → WAIT_FOR_RECOVERY (window not satisfied)
 *   - FAILED_MARKET → WAIT_FOR_RECOVERY (market says unsafe)
 *   - FAILED_NETWORK → RETRY_SAFE_SIM_ONLY (de-risk)
 *   - SUCCEEDED → RETRY_IMMEDIATE (success → immediate)
 *   - Unknown/missing → no change (keep baseStrategy)
 */
function deriveResumeEscalationV1(args: {
  originStopCause?: import("../rebalance/types").StopCause;
  baseStrategy: import("../rebalance/types").ResumeStrategyV1;
  orchLastStatus?: string; // Label-only defensive
  orchLastOutcomeCodes?: unknown[]; // Defensive
  consecutiveSuccesses?: number; // PR225: Consecutive success counter (internal only)
}): { strategy: import("../rebalance/types").ResumeStrategyV1; codes: string[] } {
  try {
    const { baseStrategy, orchLastStatus, orchLastOutcomeCodes } = args;
    const codes: string[] = [];

    // Always include marker code
    codes.push("STRAT_ESC_APPLIED_V1");

    // Defensive: Normalize outcome codes to string array
    const normalizedOutcomeCodes: string[] = [];
    if (Array.isArray(orchLastOutcomeCodes)) {
      for (const code of orchLastOutcomeCodes) {
        if (typeof code === "string") {
          normalizedOutcomeCodes.push(code);
        }
      }
    }

    // Helper: check if outcome codes contain prefix
    const hasOutcomePrefix = (prefix: string): boolean => {
      return normalizedOutcomeCodes.some((code) => code.includes(prefix));
    };

    // Rule A: SKIPPED_POLICY → WAIT_FOR_UNLOCK
    if (
      orchLastStatus === "SKIPPED_POLICY" ||
      hasOutcomePrefix("ORCH_POLICY_")
    ) {
      codes.push("STRAT_ESC_FROM_ORCH_STATUS_SKIPPED_POLICY");
      codes.push("STRAT_ESC_TO_WAIT_FOR_UNLOCK");
      return { strategy: "WAIT_FOR_UNLOCK", codes: codes.sort() };
    }

    // Rule B: SKIPPED_WINDOW → WAIT_FOR_RECOVERY
    if (
      orchLastStatus === "SKIPPED_WINDOW" ||
      hasOutcomePrefix("ORCH_NOT_BEFORE_ACTIVE") ||
      hasOutcomePrefix("ORCH_DEADLINE_EXCEEDED")
    ) {
      codes.push("STRAT_ESC_FROM_ORCH_STATUS_SKIPPED_WINDOW");
      codes.push("STRAT_ESC_TO_WAIT_FOR_RECOVERY");
      return { strategy: "WAIT_FOR_RECOVERY", codes: codes.sort() };
    }

    // Rule C: FAILED_MARKET → WAIT_FOR_RECOVERY
    if (orchLastStatus === "FAILED_MARKET") {
      codes.push("STRAT_ESC_FROM_ORCH_STATUS_FAILED_MARKET");
      codes.push("STRAT_ESC_TO_WAIT_FOR_RECOVERY");
      return { strategy: "WAIT_FOR_RECOVERY", codes: codes.sort() };
    }

    // Rule D: FAILED_NETWORK → RETRY_SAFE_SIM_ONLY (de-risk)
    if (orchLastStatus === "FAILED_NETWORK") {
      codes.push("STRAT_ESC_FROM_ORCH_STATUS_FAILED_NETWORK");
      codes.push("STRAT_ESC_TO_RETRY_SAFE_SIM_ONLY");
      return { strategy: "RETRY_SAFE_SIM_ONLY", codes: codes.sort() };
    }

    // Rule E: SUCCEEDED → RETRY_IMMEDIATE (with PR225 consecutive success gating)
    if (orchLastStatus === "SUCCEEDED") {
      // PR225: Use the updated success count from supervisor (already incremented)
      const successCount = args.consecutiveSuccesses || 0;

      // PR225: Require 2 consecutive successes before escalating to IMMEDIATE
      if (successCount >= 2) {
        codes.push("STRAT_ESC_FROM_ORCH_STATUS_SUCCEEDED");
        codes.push("STRAT_ESC_TO_RETRY_IMMEDIATE");
        codes.push("STRAT_ESC_CONSECUTIVE_SUCCESS_GATE_PASS");
        return { strategy: "RETRY_IMMEDIATE", codes: codes.sort() };
      } else {
        // First success, wait for confirmation (keep baseStrategy)
        codes.push("STRAT_ESC_FROM_ORCH_STATUS_SUCCEEDED");
        codes.push("STRAT_ESC_CONSECUTIVE_SUCCESS_GATE_WAIT");
        return { strategy: baseStrategy, codes: codes.sort() };
      }
    }

    // Rule F: No orch feedback or unknown status → keep baseStrategy
    if (!orchLastStatus || orchLastStatus === "UNKNOWN") {
      codes.push("STRAT_ESC_NO_CHANGE_NO_ORCH_FEEDBACK");
      return { strategy: baseStrategy, codes: codes.sort() };
    }

    // Other statuses (DISPATCHED, FAILED_UNKNOWN, etc.) → keep baseStrategy
    codes.push("STRAT_ESC_NO_CHANGE_ORCH_STATUS_" + orchLastStatus);
    return { strategy: baseStrategy, codes: codes.sort() };
  } catch {
    // Defensive: Never throw, return safe default (keep baseStrategy)
    return {
      strategy: args.baseStrategy || "WAIT_FOR_RECOVERY",
      codes: ["STRAT_ESC_ERROR"],
    };
  }
}

/**
 * PR220: Summarize market regime codes (label-only)
 *
 * @param codes - Array of regime codes
 * @param maxCodes - Maximum codes to include (default: 8)
 * @returns Summary object with status and joined string
 *
 * Constitutional:
 *   - Defensive: Handles undefined/non-string values
 *   - Deterministic: Dedup via Set, sort alphabetically
 *   - Label-only: No numeric values, all strings
 */
function summarizeMarketRegimeCodesV1(
  codes?: unknown[],
  maxCodes = 8
): { status: "PRESENT" | "EMPTY"; joined: string } {
  try {
    if (!codes || codes.length === 0) {
      return { status: "EMPTY", joined: "" };
    }

    // Filter to strings only (defensive)
    const stringCodes: string[] = [];
    for (const code of codes) {
      if (typeof code === "string") {
        stringCodes.push(code);
      }
    }

    if (stringCodes.length === 0) {
      return { status: "EMPTY", joined: "" };
    }

    // Dedup via Set, sort alphabetically (deterministic)
    const uniqueCodes = Array.from(new Set(stringCodes)).sort();

    // Truncate to maxCodes
    const truncated = uniqueCodes.slice(0, maxCodes);
    if (uniqueCodes.length > maxCodes) {
      truncated.push("REASONS_TRUNCATED");
    }

    // Join with pipe separator
    const joined = truncated.join("|");

    return { status: "PRESENT", joined };
  } catch {
    // Defensive: Never throw
    return { status: "EMPTY", joined: "" };
  }
}

/**
 * PR220: Derive market regime from signals v1
 *
 * @param signals - Label-only market signals
 * @returns Regime classification and reason codes
 *
 * Purpose:
 *   Classify market conditions to inform strategy/timing decisions.
 *   Enables regime-aware recovery without numeric calculations.
 *
 * Constitutional:
 *   - READ-ONLY: Derived from signals, no learning
 *   - Label-only: No BPS/prices/numeric thresholds
 *   - Deterministic: Same signals → same regime
 *   - Defensive: Handles missing/unknown signals gracefully
 *   - Safety-first: Uncertain signals → conservative regimes
 *
 * Rules (v1, hierarchical precedence):
 *   1. Oracle issues → REGIME_ORACLE_UNCERTAIN
 *   2. Liquidity issues → REGIME_ILLIQUID
 *   3. Volatility signals → REGIME_VOLATILE
 *   4. Network issues → REGIME_NETWORK_UNSTABLE
 *   5. Insufficient signals → REGIME_UNKNOWN
 *   6. Otherwise → REGIME_NORMAL
 */
function deriveMarketRegimeV1(
  signals: import("../rebalance/types").MarketRegimeSignalsV1
): { regime: import("../rebalance/types").MarketRegimeV1; codes: string[] } {
  try {
    const codes: string[] = [];

    // Rule 1: Oracle issues (highest priority - affects all pricing)
    if (
      signals.oracle_status === "ORACLE_UNAVAILABLE" ||
      signals.oracle_status === "ORACLE_STALE"
    ) {
      codes.push("REGIME_BY_ORACLE_UNCERTAIN");
      return { regime: "REGIME_ORACLE_UNCERTAIN", codes: codes.sort() };
    }

    // Rule 2: Liquidity issues (depth or quote unavailable)
    if (
      signals.gate_depth_status === "DEPTH_THIN" ||
      signals.gate_depth_status === "DEPTH_UNAVAILABLE" ||
      signals.quote_status === "QUOTE_UNAVAILABLE" ||
      signals.quote_status === "QUOTE_STALE"
    ) {
      codes.push("REGIME_BY_LIQUIDITY_THIN");
      return { regime: "REGIME_ILLIQUID", codes: codes.sort() };
    }

    // Rule 3: Volatility (phase shock or gate block)
    if (
      signals.phase_label === "PHASE_DOWN_SHOCK" ||
      signals.phase_label === "PHASE_UP_REVERSAL" ||
      signals.gate_status === "BLOCK"
    ) {
      codes.push("REGIME_BY_VOLATILITY");
      return { regime: "REGIME_VOLATILE", codes: codes.sort() };
    }

    // Rule 4: Network issues
    if (
      signals.network_status === "NET_DEGRADED" ||
      signals.network_status === "NET_FAIL"
    ) {
      codes.push("REGIME_BY_NETWORK");
      return { regime: "REGIME_NETWORK_UNSTABLE", codes: codes.sort() };
    }

    // Rule 5: Check if we have sufficient signals to classify as NORMAL
    // Just check for presence, not specific values (defensive)
    const hasOracleSignal = signals.oracle_status !== undefined;
    const hasGateSignal = signals.gate_status !== undefined;
    const hasNetworkSignal = signals.network_status !== undefined;

    if (!hasOracleSignal && !hasGateSignal && !hasNetworkSignal) {
      codes.push("REGIME_BY_UNKNOWN");
      return { regime: "REGIME_UNKNOWN", codes: codes.sort() };
    }

    // Rule 6: Normal conditions (all signals nominal or at least no red flags)
    codes.push("REGIME_BY_NORMAL");
    return { regime: "REGIME_NORMAL", codes: codes.sort() };
  } catch {
    // Defensive: Never throw, return safe default
    return { regime: "REGIME_UNKNOWN", codes: ["REGIME_ERROR"] };
  }
}

/**
 * PR224: Confirm regime change with hysteresis (2-tick confirmation)
 *
 * @param instantRegime - Instant regime from current signals
 * @param priorRegime - Last confirmed regime (from previous tick)
 * @param regimeHistory - Last N instant regimes (circular buffer)
 * @returns Confirmed regime and hysteresis codes
 *
 * Purpose:
 *   Prevent regime oscillation from transient signal flaps.
 *   Require regime to be stable for 2 consecutive ticks before changing.
 *
 * Constitutional:
 *   - READ-ONLY: Fixed hysteresis rules, no learning
 *   - Label-only: All codes are strings
 *   - Deterministic: Same history → same output
 *   - Defensive: Never throws, handles undefined gracefully
 *
 * Rules:
 *   1. No prior OR no change → use instant regime (NO_CHANGE)
 *   2. Regime changed:
 *      - If last instant regime in history equals current instant → CONFIRMED change
 *      - Else → HOLD prior regime (wait for confirmation)
 */
function confirmRegimeChangeV1(
  instantRegime: import("../rebalance/types").MarketRegimeV1,
  priorRegime: import("../rebalance/types").MarketRegimeV1 | undefined,
  regimeHistory: import("../rebalance/types").MarketRegimeV1[] | undefined
): { regime: import("../rebalance/types").MarketRegimeV1; codes: string[] } {
  try {
    const codes: string[] = [];

    // Rule 1: First read or no change → use instant regime
    if (!priorRegime || instantRegime === priorRegime) {
      codes.push("REGIME_HYSTERESIS_NO_CHANGE");
      return { regime: instantRegime, codes };
    }

    // Rule 2: Regime changed - check if confirmed by history
    // Defensive: Check if regimeHistory has entries
    if (!regimeHistory || regimeHistory.length === 0) {
      // No history, treat as first change (tentative, hold prior)
      codes.push("REGIME_HYSTERESIS_HOLD");
      return { regime: priorRegime, codes };
    }

    const lastInstantRegime = regimeHistory[regimeHistory.length - 1];

    if (lastInstantRegime === instantRegime) {
      // 2 consecutive ticks with same new regime → confirmed change
      codes.push("REGIME_HYSTERESIS_CONFIRMED");
      return { regime: instantRegime, codes };
    } else {
      // Tentative change, wait for confirmation (hold prior)
      codes.push("REGIME_HYSTERESIS_HOLD");
      return { regime: priorRegime, codes };
    }
  } catch {
    // Defensive: Never throw, return safe default (use instant regime)
    return { regime: instantRegime, codes: ["REGIME_HYSTERESIS_ERROR"] };
  }
}

/**
 * PR220: Derive resume strategy from regime × escalation matrix v1
 *
 * @param args - Matrix inputs
 * @returns Final strategy after regime overlay and reason codes
 *
 * Purpose:
 *   Apply regime-aware overlays to escalated strategy for safer autonomous recovery.
 *   Ensures strategy selection respects market conditions.
 *
 * Constitutional:
 *   - READ-ONLY: Fixed overlay rules, no learning
 *   - Label-only: No numeric values
 *   - Safety-first: Regimes force conservative overlays
 *   - Defensive: Handles missing inputs gracefully
 *   - Deterministic: Same inputs → same outputs (codes sorted)
 *
 * Matrix Rules (v1, regime overlays applied after escalation):
 *   1. REGIME_ORACLE_UNCERTAIN / REGIME_ILLIQUID → Force WAIT_FOR_RECOVERY
 *   2. REGIME_VOLATILE → Force RETRY_SAFE_SIM_ONLY
 *   3. REGIME_NETWORK_UNSTABLE → De-risk RETRY_IMMEDIATE to RETRY_SAFE_SIM_ONLY
 *   4. REGIME_NORMAL → Keep baseStrategy
 *   5. REGIME_UNKNOWN → Safe default (de-risk RETRY_IMMEDIATE)
 *
 * Note: baseStrategy comes from PR219 escalation output
 */
function deriveResumeStrategyFromMatrixV1(args: {
  baseStrategy: import("../rebalance/types").ResumeStrategyV1;
  originStopCause?: import("../rebalance/types").StopCause;
  regime?: import("../rebalance/types").MarketRegimeV1;
  orchLastStatus?: string;
}): { strategy: import("../rebalance/types").ResumeStrategyV1; codes: string[] } {
  try {
    const { baseStrategy, regime } = args;
    const codes: string[] = [];

    // Always include marker code
    codes.push("MATRIX_APPLIED_V1");

    // Rule 1: Oracle uncertain or illiquid → Force WAIT_FOR_RECOVERY
    if (regime === "REGIME_ORACLE_UNCERTAIN" || regime === "REGIME_ILLIQUID") {
      codes.push("MATRIX_FORCE_WAIT_RECOVERY");
      return { strategy: "WAIT_FOR_RECOVERY", codes: codes.sort() };
    }

    // Rule 2: Volatile → Force RETRY_SAFE_SIM_ONLY
    if (regime === "REGIME_VOLATILE") {
      codes.push("MATRIX_FORCE_SIM_ONLY_VOLATILE");
      return { strategy: "RETRY_SAFE_SIM_ONLY", codes: codes.sort() };
    }

    // Rule 3: Network unstable → De-risk RETRY_IMMEDIATE
    if (regime === "REGIME_NETWORK_UNSTABLE") {
      if (baseStrategy === "RETRY_IMMEDIATE") {
        codes.push("MATRIX_DERISK_NETWORK");
        return { strategy: "RETRY_SAFE_SIM_ONLY", codes: codes.sort() };
      } else {
        codes.push("MATRIX_KEEP_BASE_NETWORK");
        return { strategy: baseStrategy, codes: codes.sort() };
      }
    }

    // Rule 4: Normal → Keep baseStrategy
    if (regime === "REGIME_NORMAL") {
      codes.push("MATRIX_KEEP_BASE");
      return { strategy: baseStrategy, codes: codes.sort() };
    }

    // Rule 5: Unknown → Safe default (de-risk RETRY_IMMEDIATE)
    if (!regime || regime === "REGIME_UNKNOWN") {
      if (baseStrategy === "RETRY_IMMEDIATE") {
        codes.push("MATRIX_SAFE_DEFAULT_UNKNOWN");
        return { strategy: "RETRY_SAFE_SIM_ONLY", codes: codes.sort() };
      } else {
        codes.push("MATRIX_KEEP_BASE_UNKNOWN");
        return { strategy: baseStrategy, codes: codes.sort() };
      }
    }

    // Default: Keep baseStrategy (defensive fallback)
    codes.push("MATRIX_KEEP_BASE_FALLBACK");
    return { strategy: baseStrategy, codes: codes.sort() };
  } catch {
    // Defensive: Never throw, return safe default
    return {
      strategy: args.baseStrategy || "WAIT_FOR_RECOVERY",
      codes: ["MATRIX_ERROR"],
    };
  }
}

/**
 * PR226: Detect strategy/regime oscillation (telemetry only)
 *
 * @param args - Oscillation detection inputs
 * @returns Warnings and codes (does NOT change decisions)
 *
 * Purpose:
 *   Emit warning telemetry if strategy/regime changes >10 times/hour.
 *   Helps operators detect flapping signals or policy issues.
 *
 * Constitutional:
 *   - READ-ONLY: Detection only, no intervention
 *   - Label-only: Counts converted to classes (not emitted as raw numbers)
 *   - Defensive: Never throws, handles undefined
 *   - Deterministic: Same inputs → same outputs
 *
 * Logic:
 *   - Track changes within 1-hour rolling window
 *   - Threshold: >10 changes/hour triggers warning
 *   - Reset counter if >1h since last change
 */
function detectOscillationV1(args: {
  resumeState: import("../rebalance/types").ResumeState;
  currentStrategy: import("../rebalance/types").ResumeStrategyV1;
  currentRegime: import("../rebalance/types").MarketRegimeV1;
  nowMs: number;
}): { warnings: string[]; codes: string[] } {
  try {
    const { resumeState, currentStrategy, currentRegime, nowMs } = args;
    const warnings: string[] = [];
    const codes: string[] = [];

    const HOUR_MS = 60 * 60 * 1000;
    const OSCILLATION_THRESHOLD = 10;

    // Strategy oscillation check
    if (
      resumeState.lastObservedStrategy &&
      resumeState.lastObservedStrategy !== currentStrategy
    ) {
      // Strategy changed
      const timeSinceLastChange = resumeState.lastStrategyChangeTs
        ? nowMs - resumeState.lastStrategyChangeTs
        : HOUR_MS + 1;

      if (timeSinceLastChange > HOUR_MS) {
        // Reset counter (new hour window)
        resumeState.strategyChangeCount = 1;
      } else {
        // Increment counter
        resumeState.strategyChangeCount = (resumeState.strategyChangeCount || 0) + 1;

        if (resumeState.strategyChangeCount > OSCILLATION_THRESHOLD) {
          warnings.push("WARN_STRATEGY_OSCILLATION_DETECTED");
          codes.push("OSC_STRATEGY_OVER_THRESHOLD");
        }
      }

      resumeState.lastStrategyChangeTs = nowMs;
    }

    // Regime oscillation check
    if (resumeState.lastObservedRegime && resumeState.lastObservedRegime !== currentRegime) {
      // Regime changed
      const timeSinceLastChange = resumeState.lastRegimeChangeTs
        ? nowMs - resumeState.lastRegimeChangeTs
        : HOUR_MS + 1;

      if (timeSinceLastChange > HOUR_MS) {
        // Reset counter (new hour window)
        resumeState.regimeChangeCount = 1;
      } else {
        // Increment counter
        resumeState.regimeChangeCount = (resumeState.regimeChangeCount || 0) + 1;

        if (resumeState.regimeChangeCount > OSCILLATION_THRESHOLD) {
          warnings.push("WARN_REGIME_OSCILLATION_DETECTED");
          codes.push("OSC_REGIME_OVER_THRESHOLD");
        }
      }

      resumeState.lastRegimeChangeTs = nowMs;
    }

    // Always update last observed values (defensive)
    resumeState.lastObservedStrategy = currentStrategy;
    resumeState.lastObservedRegime = currentRegime;

    return { warnings, codes };
  } catch {
    // Defensive: Never throw, return empty
    return { warnings: [], codes: ["OSC_DETECTION_ERROR"] };
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

    // PR218: Load orchestration results (feedback loop)
    const orchResults = loadOrchResultLinesV1(200); // Last 200 results
    const orchResultSeenSet = loadOrchResultSeenSetV1();
    if (orchResults.length > 0) {
      notes.push(`NOTE_ORCH_RESULT_LOADED_COUNT_${orchResults.length}`);

      for (const result of orchResults) {
        // Skip if already seen (idempotency)
        if (orchResultSeenSet.has(result.result_id)) {
          continue;
        }

        // Mark as seen
        await markOrchResultSeenV1(result.result_id);

        // Process outcome codes: dedup, sort, truncate to 8
        let outcomeSummary: { status: "PRESENT" | "EMPTY"; joined: string } = {
          status: "EMPTY",
          joined: "",
        };
        if (result.outcome_codes && result.outcome_codes.length > 0) {
          const uniqueCodes = Array.from(new Set(result.outcome_codes)).sort();
          const truncated = uniqueCodes.slice(0, 8);
          if (uniqueCodes.length > 8) {
            truncated.push("REASONS_TRUNCATED");
          }
          outcomeSummary = {
            status: "PRESENT",
            joined: truncated.join("|"),
          };
        }

        // Process hint codes: dedup, sort, truncate to 8
        let hintSummary: { status: "PRESENT" | "EMPTY"; joined: string } = {
          status: "EMPTY",
          joined: "",
        };
        if (result.hint_codes && result.hint_codes.length > 0) {
          const uniqueCodes = Array.from(new Set(result.hint_codes)).sort();
          const truncated = uniqueCodes.slice(0, 8);
          if (uniqueCodes.length > 8) {
            truncated.push("REASONS_TRUNCATED");
          }
          hintSummary = {
            status: "PRESENT",
            joined: truncated.join("|"),
          };
        }

        // Emit ORCH_RESULT telemetry event
        await appendEventV1(
          createEventV1("ORCH_RESULT", "INFO", {
            resume_id: result.resume_id,
            orch_result_id: result.result_id,
            orch_result_status: result.status,
            orch_outcome_codes_status: outcomeSummary.status,
            orch_outcome_codes: outcomeSummary.joined,
            orch_hint_codes_status: hintSummary.status,
            orch_hint_codes: hintSummary.joined,
          })
        ).catch(() => {}); // Defensive: Don't fail on telemetry error

        // Update resumeState if this result is for the current resume_id
        if (
          state.resumeState &&
          state.resumeState.status === "STOPPED" &&
          result.resume_id === (state.lastRun as any)?.resumeId
        ) {
          // Update orchestrator feedback fields
          state.resumeState.orchLastStatus = result.status;
          state.resumeState.orchLastOutcomeCodes = result.outcome_codes || [];
          state.resumeState.orchLastResultId = result.result_id;

          // PR221: Track when orchestrator feedback was received (staleness guard)
          state.resumeState.orchLastStatusTs = getNowMs();

          // Persist updated state (defensive: don't fail tick on error)
          await store.patchState({ resumeState: state.resumeState }).catch(() => {});
        }
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

      // PR219: Escalation variables (declare outside for wider scope)
      let baseStrategy: import("../rebalance/types").ResumeStrategyV1 | undefined;
      let escalatedStrategy: import("../rebalance/types").ResumeStrategyV1 | undefined;
      let escalationCodes: string[] | undefined;
      let escalationSummary: { status: "PRESENT" | "EMPTY"; joined: string } = {
        status: "EMPTY",
        joined: "",
      };

      // PR220: Market regime / matrix variables (declare outside for wider scope)
      let marketRegime: import("../rebalance/types").MarketRegimeV1 | undefined;
      let marketRegimeCodes: string[] | undefined;
      let regimeSummary: { status: "PRESENT" | "EMPTY"; joined: string } = {
        status: "EMPTY",
        joined: "",
      };
      let matrixStrategy: import("../rebalance/types").ResumeStrategyV1 | undefined;
      let matrixCodes: string[] | undefined;
      let matrixSummary: { status: "PRESENT" | "EMPTY"; joined: string } = {
        status: "EMPTY",
        joined: "",
      };

      // PR221: Orch feedback freshness variables (declare outside for wider scope)
      let orchFeedbackFreshness: "FRESH" | "STALE" | "NONE" = "NONE";
      let orchFeedbackAge: "AGE_FRESH" | "AGE_STALE" | "AGE_NONE" = "AGE_NONE";

      // PR224: Regime hysteresis variables (declare outside for wider scope)
      let regimeHysteresisClass: string = "H_UNKNOWN"; // H0_NO_CHANGE, H1_CONFIRMED, H2_HOLD

      // PR225: Consecutive success variables (declare outside for wider scope)
      let successStreakClass: string = "S_UNKNOWN"; // S0, S1, S2_PLUS
      let successGateStatus: string = "GATE_UNKNOWN"; // PASS, WAIT

      // PR226: Oscillation detection variables (declare outside for wider scope)
      let oscillationStatus: string = "OSC_NONE"; // NONE, WARN_STRATEGY, WARN_REGIME, WARN_BOTH
      let oscillationCodes: string[] = [];

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
        baseStrategy = strategyDerived.strategy;
        resumeStrategyCodes = strategyDerived.codes;

        // PR221: Derive orchestrator feedback freshness (staleness guard)
        const nowMs = getNowMs();
        const ORCH_FEEDBACK_STALE_THRESHOLD_MS = 15 * 60 * 1000; // 15 minutes
        let effectiveOrchLastStatus: string | undefined = state.resumeState.orchLastStatus;

        if (state.resumeState.orchLastStatus && state.resumeState.orchLastStatusTs) {
          const ageMs = nowMs - state.resumeState.orchLastStatusTs;
          if (ageMs > ORCH_FEEDBACK_STALE_THRESHOLD_MS) {
            orchFeedbackFreshness = "STALE";
            orchFeedbackAge = "AGE_STALE";
            effectiveOrchLastStatus = undefined; // Ignore stale feedback
            warnings.push("WARN_ORCH_FEEDBACK_STALE");
          } else {
            orchFeedbackFreshness = "FRESH";
            orchFeedbackAge = "AGE_FRESH";
          }
        } else if (state.resumeState.orchLastStatus) {
          // Have status but no timestamp (backward compatibility)
          orchFeedbackFreshness = "FRESH"; // Assume fresh if no timestamp
          orchFeedbackAge = "AGE_FRESH";
        } else {
          orchFeedbackFreshness = "NONE";
          orchFeedbackAge = "AGE_NONE";
        }

        // PR225: Update consecutive success counter for gating
        let consecutiveSuccesses = state.resumeState.consecutiveSuccesses || 0;
        const lastOrchEffectiveStatus = state.resumeState.lastOrchEffectiveStatus;

        // Reset counter if effective status changed (deterministic reset)
        if (effectiveOrchLastStatus !== lastOrchEffectiveStatus) {
          if (effectiveOrchLastStatus === "SUCCEEDED") {
            consecutiveSuccesses = 1; // First success
          } else {
            consecutiveSuccesses = 0; // Non-success resets counter
          }
        } else if (effectiveOrchLastStatus === "SUCCEEDED") {
          consecutiveSuccesses += 1; // Increment on consecutive success
        }

        // Update resumeState with current values (for next tick)
        state.resumeState.consecutiveSuccesses = consecutiveSuccesses;
        state.resumeState.lastOrchEffectiveStatus = effectiveOrchLastStatus;

        // PR219: Derive escalated strategy from orchestrator feedback
        // PR221: Use effectiveOrchLastStatus (filters out stale feedback)
        // PR225: Pass consecutiveSuccesses for gating
        const escalation = deriveResumeEscalationV1({
          originStopCause: state.resumeState.originStopCause,
          baseStrategy,
          orchLastStatus: effectiveOrchLastStatus, // PR221: May be undefined if stale
          orchLastOutcomeCodes: state.resumeState.orchLastOutcomeCodes,
          consecutiveSuccesses, // PR225: For consecutive success gating
        });
        escalatedStrategy = escalation.strategy;
        escalationCodes = escalation.codes;

        // PR220: Derive market regime from signals (v1 pragmatic: use existing fields)
        // PR223: Use CURRENT signals from deps if available (not stale resumeState)
        const regimeSignals: import("../rebalance/types").MarketRegimeSignalsV1 = {};
        const regimeSignalsCodes: string[] = [];

        // PR223: Populate signals from current deps.getResumeInputs if available (fresh data)
        if (deps?.getResumeInputs) {
          try {
            const resumeInputs = await deps.getResumeInputs();

            // Map resume inputs to regime signals
            if (resumeInputs.oracleStatus) {
              if (resumeInputs.oracleStatus === "AVAILABLE") {
                regimeSignals.oracle_status = "ORACLE_OK";
              } else if (resumeInputs.oracleStatus === "STALE") {
                regimeSignals.oracle_status = "ORACLE_STALE";
              } else {
                // UNAVAILABLE, ERROR, or unknown → ORACLE_UNAVAILABLE
                regimeSignals.oracle_status = "ORACLE_UNAVAILABLE";
              }
              regimeSignalsCodes.push("REGIME_SIGNAL_ORACLE_PRESENT");
            } else {
              regimeSignalsCodes.push("REGIME_SIGNAL_ORACLE_MISSING");
            }

            if (resumeInputs.gateStatus) {
              // Filter to valid regime signal gate_status values
              if (resumeInputs.gateStatus === "PASS" || resumeInputs.gateStatus === "BLOCK") {
                regimeSignals.gate_status = resumeInputs.gateStatus;
              } else {
                regimeSignals.gate_status = "UNKNOWN";
              }
              regimeSignalsCodes.push("REGIME_SIGNAL_GATE_PRESENT");
            } else {
              regimeSignalsCodes.push("REGIME_SIGNAL_GATE_MISSING");
            }

            if (resumeInputs.phaseLabel) {
              regimeSignals.phase_label = resumeInputs.phaseLabel;
              regimeSignalsCodes.push("REGIME_SIGNAL_PHASE_PRESENT");
            } else {
              regimeSignalsCodes.push("REGIME_SIGNAL_PHASE_MISSING");
            }

            // Note: network_status, gate_depth_status, quote_status not available from resumeInputs v1
            regimeSignalsCodes.push("REGIME_SIGNAL_NETWORK_MISSING");
            regimeSignalsCodes.push("REGIME_SIGNAL_DEPTH_MISSING");
            regimeSignalsCodes.push("REGIME_SIGNAL_QUOTE_MISSING");

            regimeSignalsCodes.push("REGIME_SIGNALS_FROM_DEPS_FRESH");
          } catch (error) {
            // Fallback to stale signals if deps fails
            warnings.push("WARN_REGIME_SIGNALS_DEPS_ERROR");
            regimeSignals.phase_label = state.resumeState.lastPhaseLabel;
            regimeSignalsCodes.push("REGIME_SIGNALS_FROM_RESUMESTATE_STALE");
          }
        } else {
          // Fallback: use stale signals from resumeState (backward compatibility)
          regimeSignals.phase_label = state.resumeState.lastPhaseLabel;
          regimeSignalsCodes.push("REGIME_SIGNALS_FROM_RESUMESTATE_STALE");
          warnings.push("WARN_REGIME_SIGNALS_STALE");
        }

        // Derive regime from signals
        const regime = deriveMarketRegimeV1(regimeSignals);
        const instantRegime = regime.regime; // Instant regime from signals
        marketRegimeCodes = [...regime.codes, ...regimeSignalsCodes];

        // PR224: Apply regime hysteresis (2-tick confirmation)
        const priorRegime = state.resumeState.priorRegime;
        const regimeHistory = state.resumeState.regimeHistory || [];

        const hysteresis = confirmRegimeChangeV1(instantRegime, priorRegime, regimeHistory);
        marketRegime = hysteresis.regime; // Confirmed regime (may differ from instant)
        marketRegimeCodes.push(...hysteresis.codes); // Add hysteresis codes

        // Update circular buffer: append instant regime, keep last 3
        const updatedHistory = [...regimeHistory, instantRegime].slice(-3);
        state.resumeState.regimeHistory = updatedHistory;
        state.resumeState.priorRegime = marketRegime; // Persist confirmed regime

        // Persist regime in ResumeState (for next tick / telemetry)
        state.resumeState.marketRegime = marketRegime;
        state.resumeState.marketRegimeCodes = marketRegimeCodes;

        // PR220: Apply regime × escalation matrix overlay
        const matrix = deriveResumeStrategyFromMatrixV1({
          baseStrategy: escalatedStrategy, // Input is escalated strategy from PR219
          originStopCause: state.resumeState.originStopCause,
          regime: marketRegime,
          orchLastStatus: state.resumeState.orchLastStatus,
        });
        matrixStrategy = matrix.strategy;
        matrixCodes = matrix.codes;

        // Use matrix strategy as final resumeStrategy for subsequent steps
        resumeStrategy = matrixStrategy;

        // PR226: Detect oscillation (warning-only)
        const oscillation = detectOscillationV1({
          resumeState: state.resumeState,
          currentStrategy: resumeStrategy,
          currentRegime: marketRegime,
          nowMs: getNowMs(),
        });
        warnings.push(...oscillation.warnings); // Add oscillation warnings (if any)
        oscillationCodes = oscillation.codes;

        // PR224: Derive hysteresis class label (label-only, no raw numbers)
        if (hysteresis.codes.includes("REGIME_HYSTERESIS_NO_CHANGE")) {
          regimeHysteresisClass = "H0_NO_CHANGE";
        } else if (hysteresis.codes.includes("REGIME_HYSTERESIS_CONFIRMED")) {
          regimeHysteresisClass = "H1_CONFIRMED";
        } else if (hysteresis.codes.includes("REGIME_HYSTERESIS_HOLD")) {
          regimeHysteresisClass = "H2_HOLD";
        } else {
          regimeHysteresisClass = "H_ERROR";
        }

        // PR225: Derive success streak class label (label-only, no raw numbers)
        const successCount = state.resumeState.consecutiveSuccesses || 0;
        if (successCount === 0) {
          successStreakClass = "S0";
        } else if (successCount === 1) {
          successStreakClass = "S1";
        } else {
          successStreakClass = "S2_PLUS";
        }

        // PR225: Derive success gate status from escalation codes
        if (escalationCodes.includes("STRAT_ESC_CONSECUTIVE_SUCCESS_GATE_PASS")) {
          successGateStatus = "GATE_PASS";
        } else if (escalationCodes.includes("STRAT_ESC_CONSECUTIVE_SUCCESS_GATE_WAIT")) {
          successGateStatus = "GATE_WAIT";
        } else {
          successGateStatus = "GATE_NA"; // Not applicable (no gating logic applied)
        }

        // PR226: Derive oscillation status label
        const hasStrategyOsc = oscillation.warnings.some((w) =>
          w.includes("STRATEGY_OSCILLATION")
        );
        const hasRegimeOsc = oscillation.warnings.some((w) =>
          w.includes("REGIME_OSCILLATION")
        );

        if (hasStrategyOsc && hasRegimeOsc) {
          oscillationStatus = "OSC_WARN_BOTH";
        } else if (hasStrategyOsc) {
          oscillationStatus = "OSC_WARN_STRATEGY";
        } else if (hasRegimeOsc) {
          oscillationStatus = "OSC_WARN_REGIME";
        } else {
          oscillationStatus = "OSC_NONE";
        }

        strategySummary = summarizeStrategyCodesV1(resumeStrategyCodes);
        escalationSummary = summarizeStrategyCodesV1(escalationCodes);
        regimeSummary = summarizeMarketRegimeCodesV1(marketRegimeCodes);
        matrixSummary = summarizeStrategyCodesV1(matrixCodes);

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

        // PR213/PR214/PR215/PR219/PR220: Set resume fields on runPlan before execution
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
            resumeEscalatedStrategy: escalatedStrategy, // PR219
            resumeEscalationCodes: escalationCodes, // PR219
            resumeMarketRegime: marketRegime, // PR220
            resumeMarketRegimeCodes: marketRegimeCodes, // PR220
            resumeMatrixStrategy: matrixStrategy, // PR220
            resumeMatrixCodes: matrixCodes, // PR220
          });
        }

        // PR208: Emit RESUME_REEXEC_ATTEMPT before runner call
        // PR213: Add resume strategy labels
        // PR214: Add enforcement labels
        // PR215: Add timing labels
        // PR219: Add escalation labels
        // PR220: Add regime/matrix labels
        // PR221: Add orch feedback freshness labels
        // PR224: Add regime hysteresis labels
        // PR225: Add consecutive success gating labels
        // PR226: Add oscillation detection labels
        await appendEventV1(
          createEventV1("RESUME_REEXEC_ATTEMPT", "INFO", {
            resume_id: resumeId,
            previous_run_id: previousRunId,
            stop_reason: stopReason,
            resume_status: resumeStatus,
            resume_base_strategy: baseStrategy, // PR219
            resume_strategy: resumeStrategy, // PR213 (now matrix in PR220)
            resume_escalated_strategy: escalatedStrategy, // PR219
            resume_strategy_codes_status: strategySummary.status, // PR213
            resume_strategy_codes: strategySummary.joined, // PR213
            resume_escalation_codes_status: escalationSummary.status, // PR219
            resume_escalation_codes: escalationSummary.joined, // PR219
            orch_last_status: state.resumeState.orchLastStatus || "NONE", // PR219 (causality)
            orch_feedback_freshness: orchFeedbackFreshness, // PR221
            orch_feedback_age: orchFeedbackAge, // PR221
            resume_market_regime: marketRegime || "REGIME_UNKNOWN", // PR220
            resume_market_regime_codes_status: regimeSummary.status, // PR220
            resume_market_regime_codes: regimeSummary.joined, // PR220
            resume_matrix_strategy: matrixStrategy || "UNKNOWN", // PR220
            resume_matrix_codes_status: matrixSummary.status, // PR220
            resume_matrix_codes: matrixSummary.joined, // PR220
            resume_enforced_execution_mode: enforcedExecutionMode, // PR214
            resume_enforced_codes_status: enforcedSummary.status, // PR214
            resume_enforced_codes: enforcedSummary.joined, // PR214
            resume_delay_class: resumeDelayClass, // PR215
            resume_delay_offset_label: resumeDelayOffsetLabel, // PR215
            resume_timing_codes_status: timingSummary.status, // PR215
            resume_timing_codes: timingSummary.joined, // PR215
            resume_regime_hysteresis: regimeHysteresisClass, // PR224
            resume_success_streak_status: successStreakClass, // PR225
            resume_success_gate: successGateStatus, // PR225
            resume_oscillation_status: oscillationStatus, // PR226
            resume_oscillation_codes: oscillationCodes.join("|") || "NONE", // PR226
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
        // PR222: Check deferral limits before deferring
        const MAX_DEFERRAL_COUNT = 50;
        const MAX_DEFERRAL_AGE_MS = 24 * 60 * 60 * 1000; // 24 hours

        const deferralCount = (state.resumeState?.deferralCount || 0) + 1;
        const firstDeferredAtTs = state.resumeState?.firstDeferredAtTs || getNowMs();
        const deferralAgeMs = getNowMs() - firstDeferredAtTs;

        // Derive label-only age class
        let deferralAgeClass: "AGE_FRESH" | "AGE_MODERATE" | "AGE_OLD" | "AGE_EXPIRED" = "AGE_FRESH";
        if (deferralAgeMs >= MAX_DEFERRAL_AGE_MS) {
          deferralAgeClass = "AGE_EXPIRED";
        } else if (deferralAgeMs >= 12 * 60 * 60 * 1000) { // 12 hours
          deferralAgeClass = "AGE_OLD";
        } else if (deferralAgeMs >= 1 * 60 * 60 * 1000) { // 1 hour
          deferralAgeClass = "AGE_MODERATE";
        }

        // Derive label-only count class
        let deferralCountClass: "COUNT_LOW" | "COUNT_MEDIUM" | "COUNT_HIGH" | "COUNT_EXCEEDED" = "COUNT_LOW";
        if (deferralCount >= MAX_DEFERRAL_COUNT) {
          deferralCountClass = "COUNT_EXCEEDED";
        } else if (deferralCount >= 30) {
          deferralCountClass = "COUNT_HIGH";
        } else if (deferralCount >= 10) {
          deferralCountClass = "COUNT_MEDIUM";
        }

        // PR222: Check if deferral limits exceeded
        if (deferralCount >= MAX_DEFERRAL_COUNT || deferralAgeMs >= MAX_DEFERRAL_AGE_MS) {
          // Abandon resume (exceeded deferral limits)
          warnings.push("WARN_RESUME_ABANDONED_MAX_DEFERRALS");
          notes.push("NOTE_DEFERRAL_LIMIT_EXCEEDED");

          // Emit RESUME_REEXEC_ABANDONED event
          await appendEventV1(
            createEventV1("RESUME_REEXEC_ABANDONED", "WARN", {
              resume_id: resumeId || "UNKNOWN",
              previous_run_id: previousRunId || "UNKNOWN",
              stop_reason: stopReason || "UNKNOWN",
              abandon_reason: "ABANDON_MAX_DEFERRALS",
              deferral_count: String(deferralCount), // String to keep label-only
              deferral_count_class: deferralCountClass,
              deferral_age_class: deferralAgeClass,
              resume_strategy: resumeStrategy || "UNKNOWN",
              resume_delay_class: resumeDelayClass || "UNKNOWN",
            })
          ).catch(() => {}); // Defensive: Don't fail on telemetry error

          // Update state: mark as abandoned
          await store.patchState({
            lastRun: {
              status: "ABANDONED",
              stopReason: state.resumeState?.stopReason || "UNKNOWN",
              warnings: [...(state.resumeState?.warnings || []), "WARN_RUN_ABANDONED_MAX_DEFERRALS"],
            },
            resumeState: undefined, // Clear resume state
          });

          return {
            status: "OK",
            action: "ACTION_ABORT",
            warnings,
            notes,
          };
        }

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
              deferral_count: String(deferralCount), // PR222
              deferral_count_class: deferralCountClass, // PR222
              deferral_age_class: deferralAgeClass, // PR222
            })
          ).catch(() => {}); // Defensive: Don't fail on telemetry error

          // PR222: Update resumeState with deferral tracking
          if (state.resumeState) {
            state.resumeState.deferralCount = deferralCount;
            state.resumeState.firstDeferredAtTs = firstDeferredAtTs;
            await store.patchState({ resumeState: state.resumeState }).catch(() => {});
          }

          // PR216: Build orchestration instruction and enqueue (idempotent)
          // PR217: Derive policy hooks for orchestrator
          // Only enqueue if not already ACKed
          if (!orchAckSet.has(resumeId)) {
            // PR217: Derive orchestrator policy hooks
            const policyHooks = deriveOrchPolicyHooksV1({
              resumeStrategy,
              resumeDelayClass,
              resumeDelayOffsetLabel,
              originStopCause: state.resumeState?.originStopCause,
            });

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
              policyHooks, // PR217: Pass policy hooks
            });

            // PR216/PR217: Emit ORCH_ENQUEUE event
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
                // PR217: Policy hooks labels
                orch_policy_class: orchInstruction.orch_policy_class || "UNKNOWN",
                orch_not_before: orchInstruction.orch_not_before || "UNKNOWN",
                orch_deadline: orchInstruction.orch_deadline || "UNKNOWN",
                orch_retry_limit: orchInstruction.orch_retry_limit || "UNKNOWN",
                orch_market_guard: orchInstruction.orch_market_guard || "UNKNOWN",
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
          // PR219: Add escalation labels
          // PR220: Add regime/matrix labels
          // PR221: Add orch feedback freshness labels
          if (resumeId) {
            await appendEventV1(
              createEventV1("RESUME_REEXEC_RESULT", "INFO", {
                resume_id: resumeId,
                previous_run_id: previousRunId || "UNKNOWN",
                next_run_id: runResult.runId || "UNKNOWN",
                stop_reason: stopReason || "UNKNOWN",
                resume_status: resumeStatus || "UNKNOWN",
                execution_status: runResult.status,
                resume_base_strategy: baseStrategy || "UNKNOWN", // PR219
                resume_strategy: resumeStrategy || "UNKNOWN", // PR213 (now matrix in PR220)
                resume_escalated_strategy: escalatedStrategy || "UNKNOWN", // PR219
                resume_strategy_codes_status: strategySummary.status, // PR213
                resume_strategy_codes: strategySummary.joined, // PR213
                resume_escalation_codes_status: escalationSummary.status, // PR219
                resume_escalation_codes: escalationSummary.joined, // PR219
                orch_last_status: state.resumeState?.orchLastStatus || "NONE", // PR219 (causality)
                orch_feedback_freshness: orchFeedbackFreshness, // PR221
                orch_feedback_age: orchFeedbackAge, // PR221
                resume_market_regime: marketRegime || "REGIME_UNKNOWN", // PR220
                resume_market_regime_codes_status: regimeSummary.status, // PR220
                resume_market_regime_codes: regimeSummary.joined, // PR220
                resume_matrix_strategy: matrixStrategy || "UNKNOWN", // PR220
                resume_matrix_codes_status: matrixSummary.status, // PR220
                resume_matrix_codes: matrixSummary.joined, // PR220
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
          // PR219: Add escalation labels
          // PR220: Add regime/matrix labels
          // PR221: Add orch feedback freshness labels
          if (resumeId) {
            await appendEventV1(
              createEventV1("RESUME_REEXEC_RESULT", "ERROR", {
                resume_id: resumeId,
                previous_run_id: previousRunId || "UNKNOWN",
                next_run_id: "ERROR",
                stop_reason: stopReason || "UNKNOWN",
                resume_status: resumeStatus || "UNKNOWN",
                execution_status: "ERROR",
                resume_base_strategy: baseStrategy || "UNKNOWN", // PR219
                resume_strategy: resumeStrategy || "UNKNOWN", // PR213 (now matrix in PR220)
                resume_escalated_strategy: escalatedStrategy || "UNKNOWN", // PR219
                resume_strategy_codes_status: strategySummary.status, // PR213
                resume_strategy_codes: strategySummary.joined, // PR213
                resume_escalation_codes_status: escalationSummary.status, // PR219
                resume_escalation_codes: escalationSummary.joined, // PR219
                orch_last_status: state.resumeState?.orchLastStatus || "NONE", // PR219 (causality)
                orch_feedback_freshness: orchFeedbackFreshness, // PR221
                orch_feedback_age: orchFeedbackAge, // PR221
                resume_market_regime: marketRegime || "REGIME_UNKNOWN", // PR220
                resume_market_regime_codes_status: regimeSummary.status, // PR220
                resume_market_regime_codes: regimeSummary.joined, // PR220
                resume_matrix_strategy: matrixStrategy || "UNKNOWN", // PR220
                resume_matrix_codes_status: matrixSummary.status, // PR220
                resume_matrix_codes: matrixSummary.joined, // PR220
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
