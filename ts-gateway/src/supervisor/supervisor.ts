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
    // PR228: Observability pack (passthrough to runner)
    resumeRegimeInstant?: import("../rebalance/types").MarketRegimeV1;
    resumeRegimeConfirmed?: import("../rebalance/types").MarketRegimeV1;
    resumeRegimeHysteresisAction?: string;
    resumeRegimeHysteresisCodes?: string[];
    resumeConsecutiveSuccessesClass?: string;
    resumeSuccessGate?: string;
    resumeSuccessGateCodes?: string[];
    resumeOscWindowStatus?: string;
    resumeOscChangeLevelStrategy?: string;
    resumeOscChangeLevelRegime?: string;
    resumeOscBasisCodes?: string[];
    // PR229: Recovery Budgeting (label-only budget status)
    resumeBudgetAttemptStatus?: string;
    resumeBudgetImmediateRateStatus?: string;
    resumeBudgetFailedMarketRateStatus?: string;
    resumeBudgetOscCooldownStatus?: string;
    resumeBudgetAction?: string;
    resumeBudgetCodes?: string[];
    // PR230a: Signal trust & consensus layer (Article XI passthrough)
    resumeSignalConsensus?: import("../rebalance/types").SignalConsensusV1;
    resumeSignalConsensusCodesStatus?: string;
    resumeSignalConsensusCodes?: string;
    resumeSignalOracleTrust?: import("../rebalance/types").SignalTrustV1;
    resumeSignalDexTrust?: import("../rebalance/types").SignalTrustV1;
    resumeSignalRpcTrust?: import("../rebalance/types").SignalTrustV1;
    resumeSignalCrosscheckStatus?: import("../rebalance/types").QuoteCrossCheckStatusV1;
    // PR230b: Consensus → execution hard cap (NEVER LIVE)
    resumeSignalEnforcedExecutionMode?: import("../rebalance/types").ExecutionMode;
    resumeSignalEnforcedCodes?: string[];
    resumeSignalExecCapStatus?: import("../rebalance/types").SignalExecCapStatusV1;
    // PR231: Invariant Checks v1 (Final defensive layer)
    resumeInvariantStatus?: import("../rebalance/types").InvariantStatusV1;
    resumeInvariantFailedGroup?: import("../rebalance/types").InvariantGroupV1;
    resumeInvariantCodes?: string[];
    // PR232: Economic Safety Invariants v1 (LIVE capital safety)
    resumeEconomicInvariantStatus?: import("../rebalance/types").EconomicInvariantStatusV1;
    resumeEconomicInvariantFailedGroup?: import("../rebalance/types").EconomicInvariantGroupV1;
    resumeEconomicInvariantCodes?: string[];
    resumeEconomicActionOverride?: import("../rebalance/types").EconomicActionOverrideV1;
    // PR233: Economic Risk Constraints Layer v1 (Article XII)
    resumeEconLiquidityCondition?: import("../rebalance/types").LiquidityConditionV1;
    resumeEconSlippageRisk?: import("../rebalance/types").SlippageRiskV1;
    resumeEconExposureStatus?: import("../rebalance/types").ExposureStatusV1;
    resumeEconDrawdownStatus?: import("../rebalance/types").DrawdownStatusV1;
    resumeEconConstraintClass?: import("../rebalance/types").EconConstraintClassV1;
    resumeEconConstraintAction?: import("../rebalance/types").EconConstraintActionV1;
    resumeEconConstraintCodes?: string[];
    resumeEconConstraintCodesStatus?: string;
    // PR233a: Economic Risk Observability Pack v1 (telemetry-only)
    resumeEconRiskSeverity?: string;
    resumeEconRiskCooldownStatus?: string;
    resumeEconRiskWindowStatus?: string;
    // PR233b: Economic Execution Shaping v1 (Article XII-b)
    resumeEconExecSizeCap?: import("../rebalance/types").EconomicExecSizeCapV1;
    resumeEconExecFreqCap?: import("../rebalance/types").EconomicExecFreqCapV1;
    resumeEconCapitalCap?: import("../rebalance/types").EconomicCapitalCapV1;
    resumeEconExecShapeStatus?: import("../rebalance/types").EconomicExecShapeStatusV1;
    resumeEconExecShapeCodes?: string[];
    // PR234: Capital-at-Risk Envelope v1 (Article XIII)
    resumeCapitalRiskWindowStatus?: import("../rebalance/types").CapitalRiskWindowStatusV1;
    resumeCapitalRiskUsageLevel?: import("../rebalance/types").CapitalRiskUsageLevelV1;
    resumeCapitalRiskAction?: import("../rebalance/types").CapitalRiskActionV1;
    resumeCapitalRiskCodes?: string[];
    resumeCapitalRiskCodesStatus?: string;
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
 * PR228: Classify oscillation change count into label-only class
 *
 * @param count - Internal change count (never emitted as raw number)
 * @returns Label class: CHG_LOW|CHG_MEDIUM|CHG_HIGH|CHG_EXCEEDED|CHG_UNKNOWN
 *
 * Constitutional:
 *   - Label-only: Never emit raw count
 *   - Deterministic: Same count → same class
 *   - Defensive: Handles undefined
 */
function classifyOscillationChangeLevelV1(count: number | undefined): string {
  try {
    if (count === undefined || count === null) {
      return "CHG_UNKNOWN";
    }

    if (count >= 11) {
      return "CHG_EXCEEDED"; // Over threshold (>10)
    } else if (count >= 7) {
      return "CHG_HIGH"; // 7-10
    } else if (count >= 3) {
      return "CHG_MEDIUM"; // 3-6
    } else {
      return "CHG_LOW"; // 0-2
    }
  } catch {
    return "CHG_UNKNOWN";
  }
}

/**
 * PR228: Determine oscillation window status (fresh vs reset)
 *
 * @param lastChangeTs - Timestamp of last change (ms)
 * @param nowMs - Current timestamp (ms)
 * @returns WINDOW_FRESH | WINDOW_RESET | WINDOW_UNKNOWN
 *
 * Constitutional:
 *   - Label-only: No numeric timestamps emitted
 *   - Deterministic: Same inputs → same output
 */
function classifyOscillationWindowStatusV1(
  lastChangeTs: number | undefined,
  nowMs: number
): string {
  try {
    if (!lastChangeTs) {
      return "WINDOW_UNKNOWN";
    }

    const HOUR_MS = 60 * 60 * 1000;
    const ageMs = nowMs - lastChangeTs;

    if (ageMs > HOUR_MS) {
      return "WINDOW_RESET"; // Outside 1-hour window, will reset on next change
    } else {
      return "WINDOW_FRESH"; // Within 1-hour window
    }
  } catch {
    return "WINDOW_UNKNOWN";
  }
}

/**
 * PR228: Summarize code array into status + joined string
 *
 * @param codes - Array of code strings
 * @returns {status: PRESENT|EMPTY, joined: pipe-separated string}
 *
 * Constitutional:
 *   - Defensive: Never throws
 *   - Deterministic: Dedup, sort, truncate(8)
 */
function summarizeCodeArrayV1(
  codes: string[] | undefined
): { status: "PRESENT" | "EMPTY"; joined: string } {
  try {
    if (!codes || codes.length === 0) {
      return { status: "EMPTY", joined: "" };
    }

    // Defensive: filter non-strings
    const validCodes = codes.filter((c) => typeof c === "string" && c.length > 0);

    if (validCodes.length === 0) {
      return { status: "EMPTY", joined: "" };
    }

    // Dedup + sort
    const uniqueCodes = Array.from(new Set(validCodes)).sort();

    // Truncate to 8
    const truncated =
      uniqueCodes.length > 8
        ? [...uniqueCodes.slice(0, 8), "REASONS_TRUNCATED"]
        : uniqueCodes;

    return { status: "PRESENT", joined: truncated.join("|") };
  } catch {
    return { status: "EMPTY", joined: "" };
  }
}

/**
 * PR229: Derive Recovery Budget Decision v1 (暴走防止)
 *
 * Purpose:
 *   Enforce budget rules to prevent autonomous recovery from running away.
 *   Rules (in priority order):
 *     1. Attempt limit: >=10 attempts → ABANDON
 *     2. Oscillation cooldown: CHG_EXCEEDED → DEFER BACKOFF_LONG
 *     3. FAILED_MARKET cap: >=2/hour → DEFER MANUAL
 *     4. IMMEDIATE rate limit: >=3/hour → DEFER BACKOFF_LONG
 *
 * Constitutional:
 *   - READ-ONLY: Fixed rules, no learning
 *   - Label-only: Budget status classes (B0/B1/B2, R0/R1/R2, etc.)
 *   - Deterministic: Same inputs → same decision
 *   - Defensive: Never throws, handles malformed state
 *
 * @param args - Budget decision inputs
 * @returns Budget decision with action, codes, and status labels
 */
function deriveRecoveryBudgetDecisionV1(args: {
  desiredDelayClass: string;
  desiredDelayOffsetLabel: string;
  orchEffectiveStatus?: string;
  oscChangeLevelStrategy: string;
  oscChangeLevelRegime: string;
  resumeState: any;
  nowMs: number;
}): {
  action: "ALLOW" | "DEFER" | "ABANDON";
  overrideDelayClass?: string;
  overrideDelayOffsetLabel?: string;
  codes: string[];
  budgetAttemptStatus: string;
  budgetImmediateRateStatus: string;
  budgetFailedMarketRateStatus: string;
  budgetOscCooldownStatus: string;
} {
  const codes: string[] = [];

  try {
    // Constants (constitutional READ-ONLY)
    const MAX_RECOVERY_ATTEMPTS = 10;
    const MAX_IMMEDIATE_PER_1H = 3;
    const FAILED_MARKET_PER_1H_MAX = 2;
    const HOUR_MS = 60 * 60 * 1000;

    // Extract budget tracking fields (defensive)
    const attemptCount = args.resumeState?.recoveryAttemptCount ?? 0;
    const windowAnchorTs = args.resumeState?.recoveryWindowAnchorTs ?? 0;
    const immediateCountInWindow = args.resumeState?.recoveryImmediateCountInWindow ?? 0;
    const failedMarketCountInWindow = args.resumeState?.recoveryFailedMarketCountInWindow ?? 0;

    // Classify attempt budget status
    let budgetAttemptStatus = "B_UNKNOWN";
    if (attemptCount >= MAX_RECOVERY_ATTEMPTS) {
      budgetAttemptStatus = "B2_LIMIT_EXCEEDED";
    } else if (attemptCount >= MAX_RECOVERY_ATTEMPTS - 2) {
      budgetAttemptStatus = "B1_NEAR_LIMIT";
    } else {
      budgetAttemptStatus = "B0_OK";
    }

    // Classify IMMEDIATE rate status (within window)
    let budgetImmediateRateStatus = "R_UNKNOWN";
    const windowAge = windowAnchorTs > 0 ? args.nowMs - windowAnchorTs : HOUR_MS + 1;
    const windowActive = windowAge <= HOUR_MS;

    if (windowActive) {
      if (immediateCountInWindow >= MAX_IMMEDIATE_PER_1H) {
        budgetImmediateRateStatus = "R2_LIMIT_EXCEEDED";
      } else if (immediateCountInWindow >= MAX_IMMEDIATE_PER_1H - 1) {
        budgetImmediateRateStatus = "R1_NEAR_LIMIT";
      } else {
        budgetImmediateRateStatus = "R0_OK";
      }
    } else {
      budgetImmediateRateStatus = "R0_OK"; // Window expired, reset counts
    }

    // Classify FAILED_MARKET rate status (within window)
    let budgetFailedMarketRateStatus = "F_UNKNOWN";
    if (windowActive) {
      if (failedMarketCountInWindow >= FAILED_MARKET_PER_1H_MAX) {
        budgetFailedMarketRateStatus = "F2_LIMIT_EXCEEDED";
      } else if (failedMarketCountInWindow >= FAILED_MARKET_PER_1H_MAX - 1) {
        budgetFailedMarketRateStatus = "F1_NEAR_LIMIT";
      } else {
        budgetFailedMarketRateStatus = "F0_OK";
      }
    } else {
      budgetFailedMarketRateStatus = "F0_OK"; // Window expired
    }

    // Classify oscillation cooldown status
    let budgetOscCooldownStatus = "C_UNKNOWN";
    if (args.oscChangeLevelStrategy === "CHG_EXCEEDED" || args.oscChangeLevelRegime === "CHG_EXCEEDED") {
      budgetOscCooldownStatus = "C1_COOLDOWN_ACTIVE";
    } else {
      budgetOscCooldownStatus = "C0_OK";
    }

    // Rule 1: Attempt limit (>=10 → ABANDON)
    if (attemptCount >= MAX_RECOVERY_ATTEMPTS) {
      codes.push("BUDGET_ABANDON_ATTEMPT_LIMIT_EXCEEDED");
      codes.push(`BUDGET_ATTEMPT_COUNT_${attemptCount}`);
      return {
        action: "ABANDON",
        codes,
        budgetAttemptStatus,
        budgetImmediateRateStatus,
        budgetFailedMarketRateStatus,
        budgetOscCooldownStatus,
      };
    }

    // Rule 2: Oscillation cooldown (CHG_EXCEEDED → DEFER BACKOFF_LONG)
    if (budgetOscCooldownStatus === "C1_COOLDOWN_ACTIVE") {
      codes.push("BUDGET_DEFER_OSC_COOLDOWN");
      codes.push(`BUDGET_OSC_STRATEGY_${args.oscChangeLevelStrategy}`);
      codes.push(`BUDGET_OSC_REGIME_${args.oscChangeLevelRegime}`);
      return {
        action: "DEFER",
        overrideDelayClass: "BACKOFF_LONG",
        overrideDelayOffsetLabel: "DELAY_15M",
        codes,
        budgetAttemptStatus,
        budgetImmediateRateStatus,
        budgetFailedMarketRateStatus,
        budgetOscCooldownStatus,
      };
    }

    // Rule 3: FAILED_MARKET cap (>=2/hour → DEFER MANUAL)
    if (budgetFailedMarketRateStatus === "F2_LIMIT_EXCEEDED") {
      codes.push("BUDGET_DEFER_FAILED_MARKET_CAP");
      codes.push(`BUDGET_FAILED_MARKET_COUNT_${failedMarketCountInWindow}`);
      return {
        action: "DEFER",
        overrideDelayClass: "MANUAL",
        overrideDelayOffsetLabel: "DELAY_1H",
        codes,
        budgetAttemptStatus,
        budgetImmediateRateStatus,
        budgetFailedMarketRateStatus,
        budgetOscCooldownStatus,
      };
    }

    // Rule 4: IMMEDIATE rate limit (>=3/hour → DEFER BACKOFF_LONG)
    if (
      budgetImmediateRateStatus === "R2_LIMIT_EXCEEDED" &&
      args.desiredDelayClass === "IMMEDIATE"
    ) {
      codes.push("BUDGET_DEFER_IMMEDIATE_RATE_LIMIT");
      codes.push(`BUDGET_IMMEDIATE_COUNT_${immediateCountInWindow}`);
      return {
        action: "DEFER",
        overrideDelayClass: "BACKOFF_LONG",
        overrideDelayOffsetLabel: "DELAY_15M",
        codes,
        budgetAttemptStatus,
        budgetImmediateRateStatus,
        budgetFailedMarketRateStatus,
        budgetOscCooldownStatus,
      };
    }

    // All budget checks passed → ALLOW
    codes.push("BUDGET_ALLOW_ALL_OK");
    if (budgetAttemptStatus === "B1_NEAR_LIMIT") {
      codes.push("BUDGET_WARN_ATTEMPT_NEAR_LIMIT");
    }
    if (budgetImmediateRateStatus === "R1_NEAR_LIMIT") {
      codes.push("BUDGET_WARN_IMMEDIATE_NEAR_LIMIT");
    }
    if (budgetFailedMarketRateStatus === "F1_NEAR_LIMIT") {
      codes.push("BUDGET_WARN_FAILED_MARKET_NEAR_LIMIT");
    }

    return {
      action: "ALLOW",
      codes,
      budgetAttemptStatus,
      budgetImmediateRateStatus,
      budgetFailedMarketRateStatus,
      budgetOscCooldownStatus,
    };
  } catch (err) {
    // Defensive: Budget evaluation error → DEFER MANUAL (safe default)
    codes.push("BUDGET_ERROR_EVALUATION_FAILED");
    codes.push(`BUDGET_ERROR_${String(err).substring(0, 50)}`);
    return {
      action: "DEFER",
      overrideDelayClass: "MANUAL",
      overrideDelayOffsetLabel: "DELAY_1H",
      codes,
      budgetAttemptStatus: "B_UNKNOWN",
      budgetImmediateRateStatus: "R_UNKNOWN",
      budgetFailedMarketRateStatus: "F_UNKNOWN",
      budgetOscCooldownStatus: "C_UNKNOWN",
    };
  }
}

/**
 * PR230: Derive Signal Trust & Consensus Layer v1 (Article XI)
 *
 * Purpose:
 *   Multi-source signal verification to prevent single-source market truth risks.
 *   Converts raw signals (oracle/dex/rpc) into per-source trust + consensus.
 *
 * Constitutional:
 *   - READ-ONLY: Fixed trust mapping rules, no learning
 *   - Label-only: No numeric prices/timestamps/diffs
 *   - Safety-first: Disagreement/missing → degrade, never upgrade
 *   - Deterministic: Same inputs → same outputs
 *   - Defensive: Never throws, fallback to CONSENSUS_UNTRUSTED
 *
 * Rules:
 *   1. Per-signal trust mapping (oracle, dex, rpc)
 *   2. Cross-check status (oracle vs dex comparison)
 *   3. Consensus status (multi-source truth confidence)
 *   4. Explainability codes (dedup/sort/truncate to 8)
 *
 * @param args - Signal status inputs (all label-only)
 * @returns SignalTruthV1 (trust + consensus + codes)
 */
function deriveSignalTrustLayerV1(args: {
  oracleStatus?: import("../rebalance/types").OracleStatusV1;
  dexStatus?: import("../rebalance/types").DexPriceStatusV1;
  rpcHealth?: import("../rebalance/types").RpcHealthStatusV1;
  quoteCrossCheck?: import("../rebalance/types").QuoteCrossCheckStatusV1 | { status: import("../rebalance/types").QuoteCrossCheckStatusV1; sources?: string[] };
}): import("../rebalance/types").SignalTruthV1 {
  try {
    const codes: string[] = [];

    // Rule 1: Per-signal trust mapping
    let oracle_trust: import("../rebalance/types").SignalTrustV1 = "UNKNOWN";
    if (args.oracleStatus === "ORACLE_OK") {
      oracle_trust = "TRUSTED";
      codes.push("TRUST_ORACLE_TRUSTED");
    } else if (args.oracleStatus === "ORACLE_STALE") {
      oracle_trust = "DEGRADED";
      codes.push("TRUST_ORACLE_DEGRADED");
    } else if (args.oracleStatus === "ORACLE_MISSING" || args.oracleStatus === "ORACLE_ERROR") {
      oracle_trust = "UNTRUSTED";
      codes.push("TRUST_ORACLE_UNTRUSTED");
    } else {
      oracle_trust = "UNKNOWN";
      codes.push("TRUST_ORACLE_UNKNOWN");
    }

    let dex_trust: import("../rebalance/types").SignalTrustV1 = "UNKNOWN";
    if (args.dexStatus === "DEX_OK") {
      dex_trust = "TRUSTED";
      codes.push("TRUST_DEX_TRUSTED");
    } else if (args.dexStatus === "DEX_STALE") {
      dex_trust = "DEGRADED";
      codes.push("TRUST_DEX_DEGRADED");
    } else if (args.dexStatus === "DEX_MISSING" || args.dexStatus === "DEX_ERROR") {
      dex_trust = "UNTRUSTED";
      codes.push("TRUST_DEX_UNTRUSTED");
    } else {
      dex_trust = "UNKNOWN";
      codes.push("TRUST_DEX_UNKNOWN");
    }

    let rpc_trust: import("../rebalance/types").SignalTrustV1 = "UNKNOWN";
    if (args.rpcHealth === "RPC_OK") {
      rpc_trust = "TRUSTED";
      codes.push("TRUST_RPC_TRUSTED");
    } else if (args.rpcHealth === "RPC_DEGRADED") {
      rpc_trust = "DEGRADED";
      codes.push("TRUST_RPC_DEGRADED");
    } else if (args.rpcHealth === "RPC_DOWN") {
      rpc_trust = "UNTRUSTED";
      codes.push("TRUST_RPC_UNTRUSTED");
    } else {
      rpc_trust = "UNKNOWN";
      codes.push("TRUST_RPC_UNKNOWN");
    }

    // Rule 2: Cross-check status (oracle vs dex comparison)
    let crosscheck_status: import("../rebalance/types").QuoteCrossCheckStatusV1 = "XCHK_UNKNOWN";
    if (args.quoteCrossCheck) {
      // Explicit cross-check provided (handle both string and object forms)
      if (typeof args.quoteCrossCheck === "string") {
        crosscheck_status = args.quoteCrossCheck;
      } else {
        crosscheck_status = args.quoteCrossCheck.status || "XCHK_UNKNOWN";
      }
      codes.push(`XCHK_${crosscheck_status.replace("XCHK_", "")}`);
    } else {
      // Derive minimal cross-check from trust levels
      if (oracle_trust === "TRUSTED" && dex_trust === "TRUSTED") {
        crosscheck_status = "XCHK_OK";
        codes.push("XCHK_OK");
      } else if (
        (oracle_trust === "TRUSTED" || oracle_trust === "DEGRADED") &&
        (dex_trust === "TRUSTED" || dex_trust === "DEGRADED") &&
        !(oracle_trust === "TRUSTED" && dex_trust === "TRUSTED")
      ) {
        crosscheck_status = "XCHK_INSUFFICIENT";
        codes.push("XCHK_INSUFFICIENT");
      } else {
        crosscheck_status = "XCHK_UNKNOWN";
        codes.push("XCHK_UNKNOWN");
      }
    }

    // Rule 3: Consensus status (Article XI - multi-source truth confidence)
    // Use string comparison to avoid type narrowing issues
    let consensus: import("../rebalance/types").SignalConsensusV1 = "CONSENSUS_UNTRUSTED";

    const oracleTrustStr = String(oracle_trust);
    const dexTrustStr = String(dex_trust);
    const rpcTrustStr = String(rpc_trust);
    const xchkStr = String(crosscheck_status);

    // Safety-first priority order:
    // 1. Any UNTRUSTED → CONSENSUS_UNTRUSTED
    if (oracleTrustStr === "UNTRUSTED" || dexTrustStr === "UNTRUSTED" || rpcTrustStr === "UNTRUSTED") {
      consensus = "CONSENSUS_UNTRUSTED";
      codes.push("CONSENSUS_UNTRUSTED");
      codes.push("CONSENSUS_REASON_SOURCE_UNTRUSTED");
    }
    // 2. Both oracle+dex UNKNOWN → CONSENSUS_UNTRUSTED (signal starvation)
    else if (oracleTrustStr === "UNKNOWN" && dexTrustStr === "UNKNOWN") {
      consensus = "CONSENSUS_UNTRUSTED";
      codes.push("CONSENSUS_UNTRUSTED");
      codes.push("CONSENSUS_REASON_SIGNAL_STARVATION");
    }
    // 3. Cross-check DIVERGED → CONSENSUS_UNTRUSTED
    else if (xchkStr === "XCHK_DIVERGED") {
      consensus = "CONSENSUS_UNTRUSTED";
      codes.push("CONSENSUS_UNTRUSTED");
      codes.push("CONSENSUS_REASON_XCHK_DIVERGED");
    }
    // 4. Any DEGRADED → CONSENSUS_DEGRADED (but none UNTRUSTED)
    else if (oracleTrustStr === "DEGRADED" || dexTrustStr === "DEGRADED" || rpcTrustStr === "DEGRADED") {
      consensus = "CONSENSUS_DEGRADED";
      codes.push("CONSENSUS_DEGRADED");
      codes.push("CONSENSUS_REASON_SOURCE_DEGRADED");
    }
    // 5. Mixed TRUSTED/DEGRADED → CONSENSUS_WEAK
    else if (
      ((oracleTrustStr === "TRUSTED" && dexTrustStr === "DEGRADED") ||
        (oracleTrustStr === "DEGRADED" && dexTrustStr === "TRUSTED")) &&
      rpcTrustStr !== "UNTRUSTED"
    ) {
      consensus = "CONSENSUS_WEAK";
      codes.push("CONSENSUS_WEAK");
      codes.push("CONSENSUS_REASON_MIXED_TRUST");
    }
    // 6. All trusted + cross-check OK → CONSENSUS_STRONG
    else if (
      oracleTrustStr === "TRUSTED" &&
      dexTrustStr === "TRUSTED" &&
      (rpcTrustStr === "TRUSTED" || rpcTrustStr === "DEGRADED") &&
      xchkStr === "XCHK_OK"
    ) {
      consensus = "CONSENSUS_STRONG";
      codes.push("CONSENSUS_STRONG");
      codes.push("CONSENSUS_REASON_ALL_TRUSTED");
    }
    // 7. Fallback → CONSENSUS_UNTRUSTED (safety default)
    else {
      consensus = "CONSENSUS_UNTRUSTED";
      codes.push("CONSENSUS_UNTRUSTED");
      codes.push("CONSENSUS_REASON_FALLBACK");
    }

    codes.push("TRUST_LAYER_APPLIED_V1");

    // Dedup + sort + truncate codes
    const uniqueCodes = Array.from(new Set(codes)).sort();
    const truncatedCodes = uniqueCodes.length > 8 ? [...uniqueCodes.slice(0, 8), "CODES_TRUNCATED"] : uniqueCodes;

    return {
      oracle_trust,
      dex_trust,
      rpc_trust,
      crosscheck_status,
      consensus,
      truth_codes: truncatedCodes,
    };
  } catch (err) {
    // Defensive: On error, return UNTRUSTED consensus (safety-first)
    return {
      oracle_trust: "UNKNOWN",
      dex_trust: "UNKNOWN",
      rpc_trust: "UNKNOWN",
      crosscheck_status: "XCHK_UNKNOWN",
      consensus: "CONSENSUS_UNTRUSTED",
      truth_codes: ["TRUST_LAYER_DEFENSIVE_FALLBACK", `ERROR_${String(err).substring(0, 30)}`],
    };
  }
}

/**
 * PR230b: Derive execution mode override from signal consensus (NEVER LIVE)
 *
 * Purpose:
 *   Enforce a structural safety invariant: if signal consensus is not STRONG,
 *   execution must be capped to SIM_ONLY (never LIVE).
 *
 * Constitutional:
 *   - READ-ONLY: Fixed consensus → cap mapping
 *   - Safety-first: Non-STRONG consensus → SIM_ONLY
 *   - Label-only: No numeric values
 *   - Deterministic: Same consensus → same cap
 *   - Defensive: Errors → SIM_ONLY + CAP_ERROR
 *
 * @param args.signalConsensus - Signal consensus status from PR230
 * @returns Enforcement result with enforcedMode, capStatus, codes
 */
function deriveExecutionModeOverrideFromSignalConsensusV1(args: {
  signalConsensus: import("../rebalance/types").SignalConsensusV1 | undefined;
}): {
  enforcedMode?: import("../rebalance/types").ExecutionMode;
  capStatus: import("../rebalance/types").SignalExecCapStatusV1;
  codes: string[];
} {
  try {
    const { signalConsensus } = args;
    const codes: string[] = [];

    // Defensive: undefined consensus → UNTRUSTED (safety-first)
    if (!signalConsensus) {
      codes.push("SIGCAP_APPLIED_V1");
      codes.push("SIGCAP_ERROR_NO_CONSENSUS");
      codes.push("SIGCAP_EXEC_MODE_SIM_ONLY");
      return {
        enforcedMode: "SIM_ONLY",
        capStatus: "CAP_ERROR",
        codes: Array.from(new Set(codes)).sort(),
      };
    }

    // Rule 1: STRONG consensus → no cap
    if (signalConsensus === "CONSENSUS_STRONG") {
      codes.push("SIGCAP_NONE_CONSENSUS_STRONG");
      return {
        enforcedMode: undefined, // No override
        capStatus: "CAP_NONE",
        codes: Array.from(new Set(codes)).sort(),
      };
    }

    // Rule 2: Non-STRONG consensus → SIM_ONLY (NEVER LIVE)
    codes.push("SIGCAP_APPLIED_V1");
    codes.push(`SIGCAP_FROM_CONSENSUS_${signalConsensus}`);
    codes.push("SIGCAP_EXEC_MODE_SIM_ONLY");

    return {
      enforcedMode: "SIM_ONLY",
      capStatus: "CAP_SIM_ONLY",
      codes: Array.from(new Set(codes)).sort(),
    };
  } catch (err) {
    // Defensive: On error, enforce SIM_ONLY
    return {
      enforcedMode: "SIM_ONLY",
      capStatus: "CAP_ERROR",
      codes: ["SIGCAP_ERROR_FALLBACK_SIM_ONLY", `ERROR_${String(err).substring(0, 30)}`].sort(),
    };
  }
}

/**
 * PR230b: Combine enforced execution modes (PR214 + PR230b)
 *
 * Purpose:
 *   Compose strategy enforcement (PR214) with signal enforcement (PR230b)
 *   using min-safety precedence.
 *
 * Constitutional:
 *   - Safety-first: SIM_ONLY wins over DRY_RUN wins over LIVE
 *   - Deterministic: Same inputs → same output
 *   - Defensive: Never throws
 *
 * Precedence (most restrictive wins):
 *   1. SIM_ONLY (either source)
 *   2. DRY_RUN (either source)
 *   3. undefined (no override)
 *
 * @param strategyEnforced - Execution mode from PR214 strategy enforcement
 * @param signalEnforced - Execution mode from PR230b signal consensus cap
 * @returns Combined enforced execution mode (most restrictive)
 */
function combineEnforcedExecutionModesV1(
  strategyEnforced: import("../rebalance/types").ExecutionMode | undefined,
  signalEnforced: import("../rebalance/types").ExecutionMode | undefined
): import("../rebalance/types").ExecutionMode | undefined {
  try {
    // Rule 1: If either enforces SIM_ONLY → SIM_ONLY
    if (strategyEnforced === "SIM_ONLY" || signalEnforced === "SIM_ONLY") {
      return "SIM_ONLY";
    }

    // Rule 2: If either enforces DRY_RUN → DRY_RUN
    if (strategyEnforced === "DRY_RUN" || signalEnforced === "DRY_RUN") {
      return "DRY_RUN";
    }

    // Rule 3: Neither enforces anything → undefined (no override)
    return undefined;
  } catch (err) {
    // Defensive: On error, return most restrictive
    return "SIM_ONLY";
  }
}

/**
 * PR231: Derive invariant checks (final defensive layer)
 *
 * Purpose:
 *   Validate critical invariants before execution to ensure structural
 *   safety guarantees haven't been violated by bugs or configuration errors.
 *
 * Constitutional:
 *   - READ-ONLY: Pure rule-based checks, no learning
 *   - Label-only: No numeric values
 *   - Deterministic: Same inputs → same result
 *   - Defensive: Errors → INV_FAIL
 *   - Safety-first: Violations abort execution
 *
 * Invariant Groups:
 *   I1 (G1_EXEC): NEVER LIVE - finalEnforcedMode must not be LIVE
 *   I2 (G2_SIGNAL): Non-STRONG consensus requires SIM_ONLY enforcement
 *   I3 (G3_REGIME): Non-STRONG consensus requires REGIME_ORACLE_UNCERTAIN
 *   I4 (G4_BUDGET): Budget ABANDON/DEFER must prevent execution
 *
 * @param args - Invariant check inputs
 * @returns { status, failedGroup, codes }
 */
function deriveInvariantChecksV1(args: {
  finalEnforcedExecutionMode?: import("../rebalance/types").ExecutionMode;
  resumeSignalConsensus?: import("../rebalance/types").SignalConsensusV1;
  resumeRegimeConfirmed?: import("../rebalance/types").MarketRegimeV1;
  resumeBudgetAction?: string;
}): {
  status: import("../rebalance/types").InvariantStatusV1;
  failedGroup: import("../rebalance/types").InvariantGroupV1;
  codes: string[];
} {
  try {
    const {
      finalEnforcedExecutionMode,
      resumeSignalConsensus,
      resumeRegimeConfirmed,
      resumeBudgetAction,
    } = args;

    const codes: string[] = [];
    let status: import("../rebalance/types").InvariantStatusV1 = "INV_PASS";
    let failedGroup: import("../rebalance/types").InvariantGroupV1 = "G0_NONE";

    // I1: NEVER LIVE invariant (highest priority)
    if (finalEnforcedExecutionMode === "LIVE") {
      status = "INV_FAIL";
      failedGroup = "G1_EXEC";
      codes.push("INV_FAIL_LIVE_EXECUTION_MODE");
      codes.push("INV_GROUP_G1_EXEC");
      // Return immediately - this is critical
      return {
        status,
        failedGroup,
        codes: Array.from(new Set(codes)).sort().slice(0, 8),
      };
    }

    // I2: Non-STRONG consensus requires SIM_ONLY enforcement
    if (
      resumeSignalConsensus &&
      resumeSignalConsensus !== "CONSENSUS_STRONG" &&
      finalEnforcedExecutionMode !== "SIM_ONLY"
    ) {
      status = "INV_FAIL";
      failedGroup = "G2_SIGNAL";
      codes.push("INV_FAIL_SIGCAP_NOT_APPLIED_NON_STRONG");
      codes.push("INV_EXPECTED_SIM_ONLY");
      codes.push("INV_GROUP_G2_SIGNAL");
      codes.push(`INV_CONSENSUS_${resumeSignalConsensus}`);
      codes.push(`INV_ACTUAL_MODE_${finalEnforcedExecutionMode || "NONE"}`);
      // Return immediately - this is critical
      return {
        status,
        failedGroup,
        codes: Array.from(new Set(codes)).sort().slice(0, 8),
      };
    }

    // I3: Non-STRONG consensus requires REGIME_ORACLE_UNCERTAIN
    if (
      resumeSignalConsensus &&
      resumeSignalConsensus !== "CONSENSUS_STRONG" &&
      resumeRegimeConfirmed &&
      resumeRegimeConfirmed !== "REGIME_ORACLE_UNCERTAIN"
    ) {
      status = "INV_FAIL";
      failedGroup = "G3_REGIME";
      codes.push("INV_FAIL_REGIME_NOT_GATED_NON_STRONG");
      codes.push("INV_EXPECTED_REGIME_ORACLE_UNCERTAIN");
      codes.push("INV_GROUP_G3_REGIME");
      codes.push(`INV_CONSENSUS_${resumeSignalConsensus}`);
      codes.push(`INV_ACTUAL_REGIME_${resumeRegimeConfirmed}`);
      // Return immediately - this is critical
      return {
        status,
        failedGroup,
        codes: Array.from(new Set(codes)).sort().slice(0, 8),
      };
    }

    // I4: Budget decision consistency
    if (resumeBudgetAction) {
      if (resumeBudgetAction === "ABANDON") {
        // If budget says ABANDON, we shouldn't be here (supervisor should have aborted earlier)
        status = "INV_FAIL";
        failedGroup = "G4_BUDGET";
        codes.push("INV_FAIL_BUDGET_ABANDON_BUT_RUN");
        codes.push("INV_GROUP_G4_BUDGET");
        return {
          status,
          failedGroup,
          codes: Array.from(new Set(codes)).sort().slice(0, 8),
        };
      }

      if (resumeBudgetAction === "DEFER") {
        // If budget says DEFER, we shouldn't be attempting RUN
        status = "INV_FAIL";
        failedGroup = "G4_BUDGET";
        codes.push("INV_FAIL_BUDGET_DEFER_BUT_RUN");
        codes.push("INV_GROUP_G4_BUDGET");
        return {
          status,
          failedGroup,
          codes: Array.from(new Set(codes)).sort().slice(0, 8),
        };
      }
    }

    // All checks passed
    codes.push("INV_ALL_CHECKS_PASSED");
    return {
      status: "INV_PASS",
      failedGroup: "G0_NONE",
      codes: Array.from(new Set(codes)).sort().slice(0, 8),
    };
  } catch (err) {
    // Defensive: On error, fail the invariant check
    return {
      status: "INV_FAIL",
      failedGroup: "G9_UNKNOWN",
      codes: ["INV_ERROR_DEFENSIVE_FAIL", `ERROR_${String(err).substring(0, 30)}`].sort(),
    };
  }
}

/**
 * PR232: Economic Safety Invariants v1 (LIVE Capital Safety)
 *
 * @param args - Economic invariant check inputs
 * @returns { status, failedGroup, actionOverride, codes }
 *
 * Purpose:
 *   Final "last mile" economic safety layer to prevent capital loss under:
 *   - Large LIVE operations
 *   - Unstable external dependencies (oracle/policy/orchestrator/rpc failures)
 *   - Adversarial markets (flash crash, oracle manipulation, network partition)
 *
 * Constitutional:
 *   - READ-ONLY: No state modification
 *   - Label-only: All inputs and outputs are categorical labels
 *   - Deterministic: Same inputs → same outputs
 *   - Safety-first: Unknown inputs → EINV_FAIL with appropriate action
 *   - Defensive: Never throws
 *
 * Decision precedence (highest first):
 *   E0) Non-execution action → PASS (not applicable)
 *   E1) Budget ABANDON/DEFER → PASS (skip economic checks)
 *   E2) Market integrity failures → FAIL + ABORT/DEFER_MANUAL
 *   E3) Liquidity inadequate → FAIL + DEFER_MANUAL/ABORT
 *   E4) Slippage extreme → FAIL + ABORT/DEFER_BACKOFF_LONG
 *   E5) Crash risk → FAIL + ABORT/DEFER_BACKOFF_LONG
 *   E6) Exposure/concentration → FAIL + ABORT/DEFER_MANUAL
 *   E7) All checks passed → PASS
 */
function deriveEconomicInvariantsV1(args: {
  // Execution intent
  resumeActionIntent?: string; // ACTION_RUN_TWAP | ACTION_WAIT_* | ACTION_ABORT
  budgetAction?: string; // ALLOW | DEFER | ABANDON
  executionModeFinal?: import("../rebalance/types").ExecutionMode; // LIVE | SIM_ONLY | DRY_RUN | NONE

  // Market integrity signals (from PR230)
  rpcHealth?: string; // RPC_OK | RPC_DEGRADED | RPC_DOWN | RPC_UNKNOWN
  quoteCrosscheckStatus?: string; // XCHK_OK | XCHK_DIVERGED | XCHK_INSUFFICIENT | XCHK_UNKNOWN

  // Liquidity signals (label-only, from deps or upstream transform)
  liqDepthClass?: string; // DEPTH_NONE | DEPTH_THIN | DEPTH_OK | DEPTH_DEEP | DEPTH_UNKNOWN
  orderSizeClass?: string; // SIZE_TINY | SIZE_SMALL | SIZE_MEDIUM | SIZE_LARGE | SIZE_HUGE | SIZE_UNKNOWN
  liqMatchStatus?: string; // LIQ_OK | LIQ_MARGINAL | LIQ_INADEQUATE | LIQ_UNKNOWN

  // Slippage signals (label-only)
  slippageRiskClass?: string; // SLIP_LOW | SLIP_MEDIUM | SLIP_HIGH | SLIP_EXTREME | SLIP_UNKNOWN

  // Crash risk signals (label-only)
  crashRiskClass?: string; // CRASH_NONE | CRASH_ELEVATED | CRASH_FLASH | CRASH_UNKNOWN

  // Exposure signals (label-only, stateful if available)
  exposureClass?: string; // EXP_LOW | EXP_MEDIUM | EXP_HIGH | EXP_CRITICAL | EXP_UNKNOWN
  concentrationClass?: string; // CONC_OK | CONC_HIGH | CONC_CRITICAL | CONC_UNKNOWN
}): {
  status: import("../rebalance/types").EconomicInvariantStatusV1;
  failedGroup: import("../rebalance/types").EconomicInvariantGroupV1;
  actionOverride: import("../rebalance/types").EconomicActionOverrideV1;
  codes: string[];
} {
  try {
    const {
      resumeActionIntent,
      budgetAction,
      executionModeFinal,
      rpcHealth,
      quoteCrosscheckStatus,
      liqDepthClass,
      orderSizeClass,
      liqMatchStatus,
      slippageRiskClass,
      crashRiskClass,
      exposureClass,
      concentrationClass,
    } = args;

    const codes: string[] = [];
    let status: import("../rebalance/types").EconomicInvariantStatusV1 = "EINV_PASS";
    let failedGroup: import("../rebalance/types").EconomicInvariantGroupV1 = "EG0_NONE";
    let actionOverride: import("../rebalance/types").EconomicActionOverrideV1 = "NONE";

    // E0: Non-execution action → PASS (not applicable)
    if (resumeActionIntent && !resumeActionIntent.includes("RUN")) {
      codes.push("EINV_NOT_APPLICABLE_NON_EXEC_ACTION");
      return { status: "EINV_PASS", failedGroup: "EG0_NONE", actionOverride: "NONE", codes };
    }

    // E1: Budget ABANDON/DEFER → PASS (skip economic checks, budget wins)
    if (budgetAction === "ABANDON") {
      codes.push("EINV_SKIPPED_BUDGET_ABANDON");
      return { status: "EINV_PASS", failedGroup: "EG0_NONE", actionOverride: "NONE", codes };
    }
    if (budgetAction === "DEFER") {
      codes.push("EINV_SKIPPED_BUDGET_DEFER");
      return { status: "EINV_PASS", failedGroup: "EG0_NONE", actionOverride: "NONE", codes };
    }

    // E2: Market integrity failures (EG5_INTEGRITY) → ABORT or DEFER_MANUAL
    if (rpcHealth === "RPC_DOWN") {
      status = "EINV_FAIL";
      failedGroup = "EG5_INTEGRITY";
      actionOverride = "ABORT";
      codes.push("EINV_FAIL_V1", "EINV_INTEGRITY_RPC_DOWN");
      return { status, failedGroup, actionOverride, codes: Array.from(new Set(codes)).sort().slice(0, 8) };
    }

    if (quoteCrosscheckStatus === "XCHK_DIVERGED") {
      status = "EINV_FAIL";
      failedGroup = "EG5_INTEGRITY";
      actionOverride = "ABORT";
      codes.push("EINV_FAIL_V1", "EINV_INTEGRITY_XCHK_DIVERGED");
      return { status, failedGroup, actionOverride, codes: Array.from(new Set(codes)).sort().slice(0, 8) };
    }

    // E2b: Degraded integrity (RPC_DEGRADED, XCHK_INSUFFICIENT) → only fail if LIVE execution
    // Rationale: PR230b already enforces SIM_ONLY for degraded consensus, so if we reach here
    // with executionModeFinal=SIM_ONLY or DRY_RUN, earlier layers are working correctly.
    // Only fail if attempting LIVE execution with degraded integrity (defense in depth).
    if ((rpcHealth === "RPC_DEGRADED" || quoteCrosscheckStatus === "XCHK_INSUFFICIENT") && executionModeFinal === "LIVE") {
      status = "EINV_FAIL";
      failedGroup = "EG5_INTEGRITY";
      actionOverride = "DEFER_MANUAL";
      codes.push("EINV_FAIL_V1", "EINV_INTEGRITY_DEGRADED_NEVER_LIVE");
      if (rpcHealth === "RPC_DEGRADED") codes.push("EINV_INTEGRITY_RPC_DEGRADED");
      if (quoteCrosscheckStatus === "XCHK_INSUFFICIENT") codes.push("EINV_INTEGRITY_XCHK_INSUFFICIENT");
      return { status, failedGroup, actionOverride, codes: Array.from(new Set(codes)).sort().slice(0, 8) };
    }

    // E3: Liquidity adequacy (EG1_LIQUIDITY) → DEFER_MANUAL or ABORT
    // Note: For v1, undefined inputs (missing data) are treated as "not evaluated" and pass through
    // Only explicit UNKNOWN or failure states cause safety failures
    if (liqMatchStatus === "LIQ_INADEQUATE") {
      status = "EINV_FAIL";
      failedGroup = "EG1_LIQUIDITY";
      actionOverride = "DEFER_MANUAL";
      codes.push("EINV_FAIL_V1", "EINV_LIQ_INADEQUATE");
      return { status, failedGroup, actionOverride, codes: Array.from(new Set(codes)).sort().slice(0, 8) };
    }

    if (liqDepthClass === "DEPTH_THIN" && (orderSizeClass === "SIZE_LARGE" || orderSizeClass === "SIZE_HUGE")) {
      status = "EINV_FAIL";
      failedGroup = "EG1_LIQUIDITY";
      actionOverride = "DEFER_MANUAL";
      codes.push("EINV_FAIL_V1", "EINV_LIQ_THIN_FOR_SIZE");
      return { status, failedGroup, actionOverride, codes: Array.from(new Set(codes)).sort().slice(0, 8) };
    }

    if (liqDepthClass === "DEPTH_NONE") {
      status = "EINV_FAIL";
      failedGroup = "EG1_LIQUIDITY";
      actionOverride = "ABORT";
      codes.push("EINV_FAIL_V1", "EINV_LIQ_DEPTH_NONE");
      return { status, failedGroup, actionOverride, codes: Array.from(new Set(codes)).sort().slice(0, 8) };
    }

    // E4: Slippage / impact (EG2_SLIPPAGE) → DEFER_BACKOFF_LONG or ABORT
    if (slippageRiskClass === "SLIP_EXTREME") {
      status = "EINV_FAIL";
      failedGroup = "EG2_SLIPPAGE";
      actionOverride = "ABORT";
      codes.push("EINV_FAIL_V1", "EINV_SLIP_EXTREME");
      return { status, failedGroup, actionOverride, codes: Array.from(new Set(codes)).sort().slice(0, 8) };
    }

    if (slippageRiskClass === "SLIP_HIGH") {
      status = "EINV_FAIL";
      failedGroup = "EG2_SLIPPAGE";
      actionOverride = "DEFER_BACKOFF_LONG";
      codes.push("EINV_FAIL_V1", "EINV_SLIP_HIGH");
      return { status, failedGroup, actionOverride, codes: Array.from(new Set(codes)).sort().slice(0, 8) };
    }

    // E5: Crash risk (EG3_CRASH) → ABORT or DEFER_BACKOFF_LONG
    if (crashRiskClass === "CRASH_FLASH") {
      status = "EINV_FAIL";
      failedGroup = "EG3_CRASH";
      actionOverride = "ABORT";
      codes.push("EINV_FAIL_V1", "EINV_CRASH_FLASH");
      return { status, failedGroup, actionOverride, codes: Array.from(new Set(codes)).sort().slice(0, 8) };
    }

    if (crashRiskClass === "CRASH_ELEVATED" && executionModeFinal === "LIVE") {
      status = "EINV_FAIL";
      failedGroup = "EG3_CRASH";
      actionOverride = "ABORT";
      codes.push("EINV_FAIL_V1", "EINV_CRASH_ELEVATED_NEVER_LIVE");
      return { status, failedGroup, actionOverride, codes: Array.from(new Set(codes)).sort().slice(0, 8) };
    }

    // E6: Exposure / concentration (EG4_EXPOSURE) → DEFER_MANUAL or ABORT
    if (exposureClass === "EXP_CRITICAL") {
      status = "EINV_FAIL";
      failedGroup = "EG4_EXPOSURE";
      actionOverride = "ABORT";
      codes.push("EINV_FAIL_V1", "EINV_EXP_CRITICAL");
      return { status, failedGroup, actionOverride, codes: Array.from(new Set(codes)).sort().slice(0, 8) };
    }

    if (concentrationClass === "CONC_CRITICAL") {
      status = "EINV_FAIL";
      failedGroup = "EG4_EXPOSURE";
      actionOverride = "ABORT";
      codes.push("EINV_FAIL_V1", "EINV_CONC_CRITICAL");
      return { status, failedGroup, actionOverride, codes: Array.from(new Set(codes)).sort().slice(0, 8) };
    }

    if (exposureClass === "EXP_HIGH" || concentrationClass === "CONC_HIGH") {
      status = "EINV_FAIL";
      failedGroup = "EG4_EXPOSURE";
      actionOverride = "DEFER_MANUAL";
      codes.push("EINV_FAIL_V1", "EINV_EXP_OR_CONC_HIGH");
      return { status, failedGroup, actionOverride, codes: Array.from(new Set(codes)).sort().slice(0, 8) };
    }

    // E7: All checks passed
    codes.push("EINV_PASS_V1");
    return {
      status: "EINV_PASS",
      failedGroup: "EG0_NONE",
      actionOverride: "NONE",
      codes: Array.from(new Set(codes)).sort().slice(0, 8),
    };
  } catch (err) {
    // Defensive: On error, fail the economic invariant check
    return {
      status: "EINV_FAIL",
      failedGroup: "EG9_UNKNOWN",
      actionOverride: "ABORT",
      codes: ["EINV_ERROR_DEFENSIVE_FAIL", `ERROR_${String(err).substring(0, 30)}`].sort(),
    };
  }
}

/**
 * PR233: Economic Risk Constraints Layer v1 (Article XII - LIVE Capital Safety)
 *
 * Purpose:
 *   Active economic constraint layer that can DEFER/ABANDON execution based on
 *   risk envelope conditions (liquidity, slippage, exposure, drawdown).
 *   Complements signal trust layer (PR230) and economic invariants (PR232).
 *
 * Constitutional:
 *   - READ-ONLY: Fixed rules, no learning
 *   - Label-only: No numeric risk values in telemetry
 *   - Deterministic: Same inputs → same outputs
 *   - Defensive: Never throws, fails closed
 *   - Safety-first: Conservative defaults for missing inputs
 *
 * Decision Precedence (highest first):
 *   R0) Defensive baseline: missing inputs → conservative for LIVE
 *   R1) NEVER block SIM_ONLY solely due to liquidity/slippage
 *   R2) LIVE execution fragility: LIQ_VACUUM, SLIP_EXTREME, volatile regimes
 *   R3) Rate/cooldown: prevent repeated risky attempts
 *   R4) Exposure hard cap: applies even to SIM_ONLY
 *   R5) Drawdown protection: circuit breaker for equity losses
 *
 * @param args - Economic constraint inputs
 * @returns { econClass, action, codes, nextStatePatch }
 */
function deriveEconomicRiskConstraintsV1(args: {
  finalDesiredExecutionMode?: import("../rebalance/types").ExecutionMode;
  finalEnforcedExecutionMode?: import("../rebalance/types").ExecutionMode;
  signalConsensus?: import("../rebalance/types").SignalConsensusV1;
  marketRegimeConfirmed?: import("../rebalance/types").MarketRegimeV1;
  budgetDecision?: { action: string };
  inputs: {
    liquidity?: import("../rebalance/types").LiquidityConditionV1;
    slippageRisk?: import("../rebalance/types").SlippageRiskV1;
    exposure?: import("../rebalance/types").ExposureStatusV1;
    drawdown?: import("../rebalance/types").DrawdownStatusV1;
  };
  state?: import("../rebalance/types").ResumeState;
  nowMs: number;
}): {
  econClass: import("../rebalance/types").EconConstraintClassV1;
  action: import("../rebalance/types").EconConstraintActionV1;
  codes: string[];
  nextStatePatch?: Partial<import("../rebalance/types").ResumeState>;
} {
  try {
    const codes: string[] = [];

    let econClass: import("../rebalance/types").EconConstraintClassV1 = "E0_OK";
    let action: import("../rebalance/types").EconConstraintActionV1 = "ECON_ALLOW";

    const {
      finalDesiredExecutionMode,
      finalEnforcedExecutionMode,
      marketRegimeConfirmed,
      inputs,
      state,
      nowMs,
    } = args;

    const { liquidity, slippageRisk, exposure, drawdown } = inputs;

    // Determine if this is a LIVE execution attempt
    // isLiveAttempt = trying to execute LIVE AND not already capped to SIM_ONLY/DRY_RUN
    // If no enforcement (undefined), default to allowing LIVE (conservative: check constraints)
    const effectiveMode = finalEnforcedExecutionMode || finalDesiredExecutionMode || "LIVE";
    const isLiveAttempt = (effectiveMode === "LIVE");
    const isSimOnlyEnforced = (finalEnforcedExecutionMode === "SIM_ONLY");

    // State patch for internal tracking
    const nextStatePatch: Partial<import("../rebalance/types").ResumeState> = {};

    // R0: Defensive baseline - missing inputs handled per rule context

    // R5: Drawdown protection (highest priority - affects all modes)
    if (drawdown === "DD_CRITICAL") {
      econClass = "E3_FORBIDDEN";
      action = "ECON_ABANDON";
      codes.push("ECON_ABANDON_V1", "ECON_R5_DRAWDOWN_EMERGENCY");
      nextStatePatch.econConstraintLastAction = action;
      return {
        econClass,
        action,
        codes: Array.from(new Set(codes)).sort().slice(0, 8),
        nextStatePatch,
      };
    }

    if (drawdown === "DD_WARNING" && isLiveAttempt) {
      econClass = "E2_RISKY";
      action = "ECON_DEFER";
      codes.push("ECON_DD_WARNING_DEFER_LIVE");
      nextStatePatch.econConstraintLastAction = action;
      nextStatePatch.econConstraintCooldownUntilTs = nowMs + 15 * 60 * 1000; // 15min cooldown
      return {
        econClass,
        action,
        codes: Array.from(new Set(codes)).sort().slice(0, 8),
        nextStatePatch,
      };
    }

    // R4: Exposure hard cap (applies even to SIM_ONLY)
    if (exposure === "EXP_EXCESSIVE") {
      econClass = "E3_FORBIDDEN";
      action = "ECON_ABANDON";
      codes.push("ECON_ABANDON_V1", "ECON_R4_EXPOSURE_HARD_CAP");
      nextStatePatch.econConstraintLastAction = action;
      return {
        econClass,
        action,
        codes: Array.from(new Set(codes)).sort().slice(0, 8),
        nextStatePatch,
      };
    }

    if (exposure === "EXP_LARGE") {
      const volatileRegimes: string[] = ["REGIME_VOLATILE", "REGIME_FLASH_CRASH", "REGIME_ORACLE_UNCERTAIN"];
      if (marketRegimeConfirmed && volatileRegimes.includes(marketRegimeConfirmed)) {
        econClass = "E2_RISKY";
        action = "ECON_DEFER";
        codes.push("ECON_EXPOSURE_LARGE_VOLATILE_DEFER");
        nextStatePatch.econConstraintLastAction = action;
        nextStatePatch.econConstraintCooldownUntilTs = nowMs + 15 * 60 * 1000;
        return {
          econClass,
          action,
          codes: Array.from(new Set(codes)).sort().slice(0, 8),
          nextStatePatch,
        };
      }
    }

    // R3: Check cooldown (if last action was DEFER and within cooldown window)
    const cooldownActive = state?.econConstraintCooldownUntilTs && state.econConstraintCooldownUntilTs > nowMs;
    if (cooldownActive) {
      econClass = "E1_CONSERVATIVE";
      action = "ECON_DEFER";
      codes.push("ECON_DEFER_V1", "ECON_R3_COOLDOWN_ACTIVE");
      nextStatePatch.econConstraintLastAction = action;
      // Keep cooldown timestamp as-is
      return {
        econClass,
        action,
        codes: Array.from(new Set(codes)).sort().slice(0, 8),
        nextStatePatch,
      };
    }

    // R1: NEVER block SIM_ONLY solely due to liquidity/slippage
    // If SIM_ONLY enforced and no exposure/drawdown issues, allow
    if (isSimOnlyEnforced) {
      codes.push("ECON_ALLOW_V1");

      // Detect if bypassing liquidity or slippage issues
      if (liquidity === "LIQ_VACUUM" || liquidity === "LIQ_THIN") {
        codes.push("ECON_R1_SIM_ONLY_LIQUIDITY_BYPASS");
        econClass = liquidity === "LIQ_VACUUM" ? "E1_CONSERVATIVE" : econClass;
      }
      if (slippageRisk === "SLIP_EXTREME" || slippageRisk === "SLIP_HIGH") {
        codes.push("ECON_R1_SIM_ONLY_SLIPPAGE_BYPASS");
        econClass = slippageRisk === "SLIP_EXTREME" ? "E2_RISKY" : econClass;
      }

      nextStatePatch.econConstraintLastAction = action; // ECON_ALLOW
      return {
        econClass,
        action: "ECON_ALLOW",
        codes: Array.from(new Set(codes)).sort().slice(0, 8),
        nextStatePatch,
      };
    }

    // R2: LIVE execution fragility checks
    if (isLiveAttempt) {
      // Liquidity vacuum
      if (liquidity === "LIQ_VACUUM") {
        econClass = "E3_FORBIDDEN";
        action = "ECON_DEFER"; // Could escalate to ABANDON if repeated
        codes.push("ECON_LIVE_BLOCK_LIQ_VACUUM");
        nextStatePatch.econConstraintLastAction = action;
        nextStatePatch.econConstraintCooldownUntilTs = nowMs + 15 * 60 * 1000;
        return {
          econClass,
          action,
          codes: Array.from(new Set(codes)).sort().slice(0, 8),
          nextStatePatch,
        };
      }

      // Slippage extreme
      if (slippageRisk === "SLIP_EXTREME") {
        econClass = "E3_FORBIDDEN";
        action = "ECON_DEFER";
        codes.push("ECON_LIVE_BLOCK_SLIP_EXTREME");
        nextStatePatch.econConstraintLastAction = action;
        nextStatePatch.econConstraintCooldownUntilTs = nowMs + 15 * 60 * 1000;
        return {
          econClass,
          action,
          codes: Array.from(new Set(codes)).sort().slice(0, 8),
          nextStatePatch,
        };
      }

      // Volatile/fragile regimes
      const fragileRegimes: string[] = ["REGIME_VOLATILE", "REGIME_FLASH_CRASH", "REGIME_ORACLE_UNCERTAIN", "CRASH", "VOLATILE", "EXTREME"];
      if (marketRegimeConfirmed && fragileRegimes.includes(marketRegimeConfirmed)) {
        econClass = "E2_RISKY";
        action = "ECON_DEFER";
        codes.push("ECON_DEFER_V1", "ECON_R2_LIVE_FRAGILE_REGIME");
        nextStatePatch.econConstraintLastAction = action;
        nextStatePatch.econConstraintCooldownUntilTs = nowMs + 15 * 60 * 1000;
        return {
          econClass,
          action,
          codes: Array.from(new Set(codes)).sort().slice(0, 8),
          nextStatePatch,
        };
      }

      // Liquidity thin (warning level)
      if (liquidity === "LIQ_THIN") {
        econClass = "E1_CONSERVATIVE";
        codes.push("ECON_LIVE_LIQ_THIN_CAUTION");
        // Allow but flag
      }

      // Slippage high (warning level)
      if (slippageRisk === "SLIP_HIGH") {
        econClass = "E1_CONSERVATIVE";
        codes.push("ECON_LIVE_SLIP_HIGH_CAUTION");
        // Allow but flag
      }
    }

    // R0: Defensive handling for unknown inputs with LIVE attempt
    if (isLiveAttempt) {
      if (liquidity === "LIQ_UNKNOWN" || slippageRisk === "SLIP_UNKNOWN" ||
          exposure === "EXP_UNKNOWN" || drawdown === "DD_UNKNOWN") {
        econClass = "E1_CONSERVATIVE";
        action = "ECON_DEFER";
        codes.push("ECON_DEFER_V1", "ECON_R0_DEFENSIVE_UNKNOWN");
        nextStatePatch.econConstraintLastAction = action;
        nextStatePatch.econConstraintCooldownUntilTs = nowMs + 15 * 60 * 1000;
        return {
          econClass,
          action,
          codes: Array.from(new Set(codes)).sort().slice(0, 8),
          nextStatePatch,
        };
      }
    }

    // All checks passed - add final codes
    if (econClass === "E0_OK") {
      codes.push("ECON_OK");
    }
    codes.push("ECON_ALLOW_V1");

    nextStatePatch.econConstraintLastAction = action;

    return {
      econClass,
      action,
      codes: Array.from(new Set(codes)).sort().slice(0, 8),
      nextStatePatch,
    };
  } catch (err) {
    // Defensive: On error, defer with error class
    return {
      econClass: "E9_ERROR",
      action: "ECON_DEFER",
      codes: ["ECON_ERROR_DEFENSIVE_DEFER", `ERROR_${String(err).substring(0, 30)}`].sort(),
    };
  }
}

/**
 * PR233b: Economic Risk → Execution Shaping Layer v1 (Article XII-b)
 *
 * Purpose:
 *   Map PR233 economic constraint decisions to execution control hints
 *   (size/frequency/capital caps) for runner-side execution shaping.
 *
 * Constitutional:
 *   - READ-ONLY: Fixed rules, no learning
 *   - Label-only: No numeric amounts
 *   - Deterministic: Same inputs → same outputs
 *   - Defensive: Never throws, fails to most restrictive
 *   - Does NOT override PR233 decision (ALLOW/DEFER/ABANDON)
 *
 * Decision Precedence:
 *   R0) Defensive baseline: missing inputs → most restrictive
 *   R1) SIM_ONLY bypass: don't overconstrain simulations
 *   R2) ABANDON/DEFER interplay: map to caps
 *   R3) Severity shaping: SEV_HIGH/CRITICAL → specific caps
 *   R4) Deterministic codes: dedup/sort/truncate
 *
 * @param args - Shaping inputs (econDecision, severity, executionMode)
 * @returns { sizeCap, freqCap, capitalCap, shapeStatus, codes }
 */
function deriveEconomicExecutionShapingV1(args: {
  econDecision?: import("../rebalance/types").EconConstraintActionV1;
  econSeverity?: string; // SEV_LOW | SEV_MEDIUM | SEV_HIGH | SEV_CRITICAL
  executionMode?: import("../rebalance/types").ExecutionMode;
  timingClass?: import("../rebalance/types").ResumeDelayClassV1;
}): {
  sizeCap: import("../rebalance/types").EconomicExecSizeCapV1;
  freqCap: import("../rebalance/types").EconomicExecFreqCapV1;
  capitalCap: import("../rebalance/types").EconomicCapitalCapV1;
  shapeStatus: import("../rebalance/types").EconomicExecShapeStatusV1;
  codes: string[];
} {
  try {
    const codes: string[] = [];

    let sizeCap: import("../rebalance/types").EconomicExecSizeCapV1 = "SIZE_NONE";
    let freqCap: import("../rebalance/types").EconomicExecFreqCapV1 = "FREQ_NONE";
    let capitalCap: import("../rebalance/types").EconomicCapitalCapV1 = "CAPITAL_NONE";
    let shapeStatus: import("../rebalance/types").EconomicExecShapeStatusV1 = "SHAPE_NONE";

    const { econDecision, econSeverity, executionMode, timingClass } = args;

    // R0: Defensive baseline - missing inputs → most restrictive
    if (!econDecision || !econSeverity) {
      sizeCap = "SIZE_ZERO";
      freqCap = "FREQ_COOLDOWN";
      capitalCap = "CAPITAL_MINIMAL";
      shapeStatus = "SHAPE_ERROR";
      codes.push("ECONSHAPE_ERROR_MISSING_INPUTS");
      return {
        sizeCap,
        freqCap,
        capitalCap,
        shapeStatus,
        codes: Array.from(new Set(codes)).sort().slice(0, 8),
      };
    }

    // R1: SIM_ONLY bypass - don't overconstrain simulations
    if (executionMode === "SIM_ONLY") {
      sizeCap = "SIZE_NONE";
      freqCap = "FREQ_NONE";
      capitalCap = "CAPITAL_NONE";
      shapeStatus = "SHAPE_NONE";
      codes.push("ECONSHAPE_BYPASS_SIM_ONLY");
      return {
        sizeCap,
        freqCap,
        capitalCap,
        shapeStatus,
        codes: Array.from(new Set(codes)).sort().slice(0, 8),
      };
    }

    // R2: ABANDON/DEFER interplay
    if (econDecision === "ECON_ABANDON") {
      sizeCap = "SIZE_ZERO";
      freqCap = "FREQ_COOLDOWN";
      capitalCap = "CAPITAL_MINIMAL";
      shapeStatus = "SHAPE_APPLIED";
      codes.push("ECONSHAPE_FROM_ECON_ABANDON");
      return {
        sizeCap,
        freqCap,
        capitalCap,
        shapeStatus,
        codes: Array.from(new Set(codes)).sort().slice(0, 8),
      };
    }

    if (econDecision === "ECON_DEFER") {
      sizeCap = "SIZE_SMALL";
      freqCap = "FREQ_COOLDOWN";
      capitalCap = "CAPITAL_LOW";
      shapeStatus = "SHAPE_APPLIED";
      codes.push("ECONSHAPE_FROM_ECON_DEFER");
      return {
        sizeCap,
        freqCap,
        capitalCap,
        shapeStatus,
        codes: Array.from(new Set(codes)).sort().slice(0, 8),
      };
    }

    // R3: Severity shaping (applies when econDecision is ALLOW and executionMode != SIM_ONLY)
    if (econSeverity === "SEV_CRITICAL") {
      sizeCap = "SIZE_ZERO";
      freqCap = "FREQ_COOLDOWN";
      capitalCap = "CAPITAL_MINIMAL";
      shapeStatus = "SHAPE_APPLIED";
      codes.push("ECONSHAPE_FROM_SEV_CRITICAL");
      return {
        sizeCap,
        freqCap,
        capitalCap,
        shapeStatus,
        codes: Array.from(new Set(codes)).sort().slice(0, 8),
      };
    }

    if (econSeverity === "SEV_HIGH") {
      sizeCap = "SIZE_SMALL";
      freqCap = "FREQ_SLOW";
      capitalCap = "CAPITAL_LOW";
      shapeStatus = "SHAPE_APPLIED";
      codes.push("ECONSHAPE_FROM_SEV_HIGH");
      return {
        sizeCap,
        freqCap,
        capitalCap,
        shapeStatus,
        codes: Array.from(new Set(codes)).sort().slice(0, 8),
      };
    }

    // Else (SEV_LOW / SEV_MEDIUM) - no shaping needed
    codes.push("ECONSHAPE_NONE_SEV_OK");
    shapeStatus = "SHAPE_NONE";

    return {
      sizeCap,
      freqCap,
      capitalCap,
      shapeStatus,
      codes: Array.from(new Set(codes)).sort().slice(0, 8),
    };
  } catch (err) {
    // Defensive: On error, return most restrictive caps
    return {
      sizeCap: "SIZE_ZERO",
      freqCap: "FREQ_COOLDOWN",
      capitalCap: "CAPITAL_MINIMAL",
      shapeStatus: "SHAPE_ERROR",
      codes: ["ECONSHAPE_ERROR_DEFENSIVE", `ERROR_${String(err).substring(0, 30)}`].sort(),
    };
  }
}

/**
 * PR234: Capital-at-Risk Envelope v1 (Article XIII)
 *
 * Purpose:
 *   Prevent runaway scenarios from cumulative risk events within a rolling time window.
 *   This is a "physical guardrail" that tracks execution attempts that could expose capital.
 *
 * Constitutional:
 *   - READ-ONLY: Fixed rules, no learning
 *   - Label-only: No raw event counts in telemetry
 *   - Deterministic: Same state/inputs → same outputs
 *   - Defensive: Never throws, fails to CAR_DEFER on error
 *   - Backward compatible: All new fields optional
 *
 * Rule Precedence:
 *   R0) Defensive baseline: Missing/corrupt state → CAR_DEFER
 *   R1) Window reset: 1h rolling window (anchor tracking)
 *   R2) Risk event accumulation: Count events that could expose capital (with SIM_ONLY bypass)
 *   R3) Usage level classification: Convert internal count to label (LOW/MEDIUM/HIGH/EXHAUSTED)
 *   R4) Action mapping: LOW/MEDIUM→ALLOW, HIGH→DEFER, EXHAUSTED→ABORT
 *   R5) Precedence: Budget/Econ ABANDON/DEFER take priority (observation only)
 *
 * @param args - Envelope inputs (labels + internal counters)
 * @returns { windowStatus, usageLevel, action, codes, statePatch }
 */
function deriveCapitalRiskEnvelopeV1(args: {
  nowMs: number;
  resumeState?: import("../rebalance/types").ResumeState;
  finalEnforcedExecutionMode?: import("../rebalance/types").ExecutionMode;
  econDecision?: import("../rebalance/types").EconConstraintActionV1;
  econSeverity?: string; // SEV_LOW | SEV_MEDIUM | SEV_HIGH | SEV_CRITICAL
  execShapeStatus?: import("../rebalance/types").EconomicExecShapeStatusV1;
  execSizeCap?: import("../rebalance/types").EconomicExecSizeCapV1;
  budgetAction?: string; // ALLOW | DEFER | ABANDON
}): {
  windowStatus: import("../rebalance/types").CapitalRiskWindowStatusV1;
  usageLevel: import("../rebalance/types").CapitalRiskUsageLevelV1;
  action: import("../rebalance/types").CapitalRiskActionV1;
  codes: string[];
  statePatch: Partial<import("../rebalance/types").ResumeState>;
} {
  try {
    const codes: string[] = [];
    const statePatch: Partial<import("../rebalance/types").ResumeState> = {};

    const {
      nowMs,
      resumeState,
      finalEnforcedExecutionMode,
      econDecision,
      econSeverity,
      execShapeStatus,
      execSizeCap,
      budgetAction,
    } = args;

    let windowStatus: import("../rebalance/types").CapitalRiskWindowStatusV1 = "WIN_FRESH";
    let usageLevel: import("../rebalance/types").CapitalRiskUsageLevelV1 = "RISK_LOW";
    let action: import("../rebalance/types").CapitalRiskActionV1 = "CAR_ALLOW";

    // R0: Defensive baseline
    if (!resumeState) {
      codes.push("CAR_DEFENSIVE_DEFER_V1");
      codes.push("CAR_ERROR_NO_RESUME_STATE");
      return {
        windowStatus: "WIN_FRESH",
        usageLevel: "RISK_LOW",
        action: "CAR_DEFER",
        codes: Array.from(new Set(codes)).sort().slice(0, 8),
        statePatch: {},
      };
    }

    // R1: Window reset (1h rolling)
    const WINDOW_MS = 60 * 60 * 1000; // 1 hour
    let anchor = resumeState.capitalRiskWindowAnchorTs;
    let eventCount = resumeState.capitalRiskEventsInWindow || 0;

    if (!anchor) {
      // Initialize window
      anchor = nowMs;
      eventCount = 0;
      windowStatus = "WIN_FRESH";
      codes.push("CAR_WINDOW_INIT");
      statePatch.capitalRiskWindowAnchorTs = anchor;
      statePatch.capitalRiskEventsInWindow = eventCount;
    } else if (nowMs - anchor > WINDOW_MS) {
      // Window expired, reset
      anchor = nowMs;
      eventCount = 0;
      windowStatus = "WIN_EXPIRED";
      codes.push("CAR_WINDOW_RESET");
      statePatch.capitalRiskWindowAnchorTs = anchor;
      statePatch.capitalRiskEventsInWindow = eventCount;
    } else {
      // Window active
      windowStatus = "WIN_ACTIVE";
      codes.push("CAR_WINDOW_ACTIVE");
    }

    // R2: Risk event accumulation (with SIM_ONLY bypass)
    // A risk event is any attempt that could expose capital:
    // A) Not SIM_ONLY enforced (DRY_RUN or LIVE possible)
    // B) High/Critical severity (even if SIM_ONLY, signals severe risk)
    // C) Size cap applied (indicates shaping needed)
    // D) Shape status = APPLIED
    let riskEventTriggered = false;

    // Condition A: Not SIM_ONLY
    const notSimOnly = finalEnforcedExecutionMode !== "SIM_ONLY";
    if (notSimOnly) {
      riskEventTriggered = true;
      codes.push("CAR_EVENT_TRIGGER_NOT_SIM_ONLY");
    }

    // Condition B: High/Critical severity
    if (econSeverity === "SEV_HIGH" || econSeverity === "SEV_CRITICAL") {
      riskEventTriggered = true;
      codes.push("CAR_EVENT_TRIGGER_HIGH_SEVERITY");
    }

    // Condition C: Size cap applied
    if (execSizeCap && execSizeCap !== "SIZE_NONE") {
      riskEventTriggered = true;
      codes.push("CAR_EVENT_TRIGGER_SIZE_CAP");
    }

    // Condition D: Shape applied
    if (execShapeStatus === "SHAPE_APPLIED") {
      riskEventTriggered = true;
      codes.push("CAR_EVENT_TRIGGER_SHAPE_APPLIED");
    }

    // SIM_ONLY bypass note
    if (finalEnforcedExecutionMode === "SIM_ONLY" && !riskEventTriggered) {
      codes.push("CAR_EVENT_SKIP_SIM_ONLY");
    }

    // Increment counter if risk event triggered
    if (riskEventTriggered) {
      eventCount++;
      codes.push("CAR_EVENT_INC");
      statePatch.capitalRiskEventsInWindow = eventCount;
    } else {
      codes.push("CAR_EVENT_SKIP");
    }

    // R3: Usage level classification (label-only)
    if (eventCount >= 9) {
      usageLevel = "RISK_EXHAUSTED";
      codes.push("CAR_LEVEL_EXHAUSTED");
    } else if (eventCount >= 6) {
      usageLevel = "RISK_HIGH";
      codes.push("CAR_LEVEL_HIGH");
    } else if (eventCount >= 3) {
      usageLevel = "RISK_MEDIUM";
      codes.push("CAR_LEVEL_MEDIUM");
    } else {
      usageLevel = "RISK_LOW";
      codes.push("CAR_LEVEL_LOW");
    }

    // Update last level in state
    statePatch.capitalRiskLevelLast = usageLevel;

    // R4: Action mapping
    if (usageLevel === "RISK_EXHAUSTED") {
      action = "CAR_ABORT";
      codes.push("CAR_ACTION_ABORT");
    } else if (usageLevel === "RISK_HIGH") {
      action = "CAR_DEFER";
      codes.push("CAR_ACTION_DEFER_BACKOFF_LONG");
    } else {
      action = "CAR_ALLOW";
      codes.push("CAR_ACTION_ALLOW");
    }

    // R5: Precedence with Budget/Econ (observation only when they block)
    if (budgetAction === "ABANDON") {
      action = "CAR_ABORT";
      codes.push("CAR_BYPASS_BY_BUDGET_ABANDON");
    } else if (budgetAction === "DEFER") {
      // If PR234 wants ABORT but Budget is DEFER, keep DEFER (don't escalate)
      if (action !== "CAR_ABORT") {
        action = "CAR_DEFER";
      }
      codes.push("CAR_BYPASS_BY_BUDGET_DEFER");
    }

    if (econDecision === "ECON_ABANDON") {
      action = "CAR_ABORT";
      codes.push("CAR_BYPASS_BY_ECON_ABANDON");
    } else if (econDecision === "ECON_DEFER") {
      // PR234 can escalate DEFER→ABORT if EXHAUSTED, but not relax
      if (action !== "CAR_ABORT") {
        action = "CAR_DEFER";
      }
      codes.push("CAR_BYPASS_BY_ECON_DEFER");
    }

    return {
      windowStatus,
      usageLevel,
      action,
      codes: Array.from(new Set(codes)).sort().slice(0, 8),
      statePatch,
    };
  } catch (err) {
    // Defensive: On error, defer
    return {
      windowStatus: "WIN_FRESH",
      usageLevel: "RISK_LOW",
      action: "CAR_DEFER",
      codes: ["CAR_DEFENSIVE_DEFER_V1", `CAR_ERROR_${String(err).substring(0, 30)}`].sort(),
      statePatch: {},
    };
  }
}

/**
 * PR235: Adversarial Incident Quarantine v1 (Article XIV - Adversarial Market Isolation)
 *
 * @param args - Quarantine detection inputs
 * @returns Quarantine status, incident classification, action, codes, and state patch
 *
 * Purpose:
 *   Detect adversarial market conditions (flash crash, oracle manipulation, network partition,
 *   signal starvation) and quarantine LIVE execution during hostile states.
 *
 * Constitutional:
 *   - READ-ONLY: Never modifies execution directly
 *   - Deterministic: Always produces same output for same inputs
 *   - Defensive: Fail-safe to QA_DEFER on errors
 *   - Backward compatible: All outputs are labels/codes
 *   - Telemetry parity: State tracking + RunPlan passthrough
 *
 * Detection inputs:
 *   - signalConsensus: CONSENSUS_STRONG | WEAK | DEGRADED | UNTRUSTED
 *   - crosscheckStatus: XCHK_OK | DIVERGED | INSUFFICIENT | UNKNOWN
 *   - rpcHealth: TRUSTED | DEGRADED | UNTRUSTED | UNKNOWN (mapped from signalRpcTrust)
 *   - marketRegime: STABLE | VOLATILE | CRASH
 *   - oscStatus: OSC_NONE | OSC_WARN | OSC_CRITICAL (from PR228)
 *   - capriskUsageLevel: RISK_LOW | RISK_MEDIUM | RISK_HIGH | RISK_EXHAUSTED (from PR234)
 *   - econSeverity: SEV_LOW | SEV_MEDIUM | SEV_HIGH | SEV_CRITICAL (from PR233a)
 *
 * Rules:
 *   R0: Defensive baseline - missing inputs → QA_DEFER
 *   R1: SIM_ONLY bypass - no quarantine for simulations
 *   R2: Incident detection - classify type & severity
 *   R3: Quarantine activation - activate if SEV2_HIGH+ detected
 *   R4: Exit condition selection - based on severity:
 *       - SEV3_CRITICAL → EXIT_MANUAL_ONLY
 *       - SEV2_HIGH → EXIT_CONSENSUS_STRONG_2TICKS or EXIT_COOLDOWN_EXPIRED (60min)
 *   R5: Action mapping - QA_ABORT if Q1_ACTIVE, else QA_ALLOW
 */
function deriveAdversarialQuarantineV1(args: {
  nowMs: number;
  resumeState?: import("../rebalance/types").ResumeState;
  executionMode?: import("../rebalance/types").ExecutionMode;
  signalConsensus?: import("../rebalance/types").SignalConsensusV1;
  crosscheckStatus?: import("../rebalance/types").QuoteCrossCheckStatusV1;
  rpcHealth?: import("../rebalance/types").SignalTrustV1; // Mapped from signalRpcTrust
  marketRegime?: import("../rebalance/types").MarketRegimeV1;
  oscStatus?: string; // OSC_NONE | OSC_WARN | OSC_CRITICAL
  capriskUsageLevel?: import("../rebalance/types").CapitalRiskUsageLevelV1;
  econSeverity?: string; // SEV_LOW | SEV_MEDIUM | SEV_HIGH | SEV_CRITICAL
}): {
  quarantineStatus: import("../rebalance/types").QuarantineStatusV1;
  incidentType: import("../rebalance/types").IncidentTypeV1;
  severity: import("../rebalance/types").IncidentSeverityV1;
  exitCondition: import("../rebalance/types").QuarantineExitConditionV1;
  action: import("../rebalance/types").QuarantineActionV1;
  codes: string[];
  statePatch: Partial<import("../rebalance/types").ResumeState>;
} {
  try {
    const codes: string[] = [];
    const statePatch: Partial<import("../rebalance/types").ResumeState> = {};

    const {
      nowMs,
      resumeState,
      executionMode,
      signalConsensus,
      crosscheckStatus,
      rpcHealth,
      marketRegime,
      oscStatus,
      capriskUsageLevel,
      econSeverity,
    } = args;

    let quarantineStatus: import("../rebalance/types").QuarantineStatusV1 = "Q0_NONE";
    let incidentType: import("../rebalance/types").IncidentTypeV1 = "INC_NONE";
    let severity: import("../rebalance/types").IncidentSeverityV1 = "SEV0_NONE";
    let exitCondition: import("../rebalance/types").QuarantineExitConditionV1 = "EXIT_NONE";
    let action: import("../rebalance/types").QuarantineActionV1 = "QA_ALLOW";

    // R0: Defensive baseline
    if (!resumeState) {
      codes.push("Q_DEFENSIVE_DEFER");
      codes.push("Q_ERROR_NO_RESUME_STATE");
      return {
        quarantineStatus: "Q0_NONE",
        incidentType: "INC_NONE",
        severity: "SEV0_NONE",
        exitCondition: "EXIT_NONE",
        action: "QA_DEFER",
        codes: Array.from(new Set(codes)).sort().slice(0, 8),
        statePatch: {},
      };
    }

    // R1: SIM_ONLY bypass
    if (executionMode === "SIM_ONLY") {
      codes.push("Q_BYPASS_SIM_ONLY");
      return {
        quarantineStatus: "Q0_NONE",
        incidentType: "INC_NONE",
        severity: "SEV0_NONE",
        exitCondition: "EXIT_NONE",
        action: "QA_ALLOW",
        codes: Array.from(new Set(codes)).sort().slice(0, 8),
        statePatch: {},
      };
    }

    // R2: Incident detection (classify type & severity)
    // Check for flash crash (regime=ILLIQUID + crosscheck diverged/insufficient)
    if (marketRegime === "REGIME_ILLIQUID" && (crosscheckStatus === "XCHK_DIVERGED" || crosscheckStatus === "XCHK_INSUFFICIENT")) {
      incidentType = "INC_FLASH_CRASH";
      severity = "SEV3_CRITICAL";
      codes.push("Q_DETECT_FLASH_CRASH");
    }
    // Check for oracle manipulation (crosscheck diverged + consensus untrusted/degraded)
    else if (
      crosscheckStatus === "XCHK_DIVERGED" &&
      (signalConsensus === "CONSENSUS_UNTRUSTED" || signalConsensus === "CONSENSUS_DEGRADED")
    ) {
      incidentType = "INC_ORACLE_MANIPULATION";
      severity = "SEV2_HIGH";
      codes.push("Q_DETECT_ORACLE_MANIPULATION");
    }
    // Check for network partition (rpcHealth untrusted + consensus untrusted/degraded)
    else if (
      rpcHealth === "UNTRUSTED" &&
      (signalConsensus === "CONSENSUS_UNTRUSTED" || signalConsensus === "CONSENSUS_DEGRADED")
    ) {
      incidentType = "INC_NETWORK_PARTITION";
      severity = "SEV2_HIGH";
      codes.push("Q_DETECT_NETWORK_PARTITION");
    }
    // Check for signal starvation (consensus untrusted + crosscheck insufficient)
    else if (signalConsensus === "CONSENSUS_UNTRUSTED" && crosscheckStatus === "XCHK_INSUFFICIENT") {
      incidentType = "INC_SIGNAL_STARVATION";
      severity = "SEV2_HIGH";
      codes.push("Q_DETECT_SIGNAL_STARVATION");
    }
    // Check for suspect conditions (any single degraded signal)
    else if (
      signalConsensus === "CONSENSUS_WEAK" ||
      crosscheckStatus === "XCHK_DIVERGED" ||
      rpcHealth === "DEGRADED" ||
      marketRegime === "REGIME_VOLATILE" ||
      oscStatus === "OSC_WARN" ||
      capriskUsageLevel === "RISK_HIGH" ||
      econSeverity === "SEV_HIGH"
    ) {
      incidentType = "INC_UNKNOWN";
      severity = "SEV1_SUSPECT";
      codes.push("Q_DETECT_SUSPECT");
    } else {
      // No incident detected
      incidentType = "INC_NONE";
      severity = "SEV0_NONE";
      codes.push("Q_NO_INCIDENT");
    }

    // R3: Quarantine activation (activate if SEV2_HIGH+ detected)
    // Check if already in quarantine
    const activeQuarantineTs = resumeState.quarantineActiveSinceTs;
    const existingIncident = resumeState.quarantineIncidentType;
    const existingSeverity = resumeState.quarantineSeverity;
    const existingExitCondition = resumeState.quarantineExitCondition;

    if (activeQuarantineTs && existingSeverity && (existingSeverity === "SEV2_HIGH" || existingSeverity === "SEV3_CRITICAL")) {
      // Already in active quarantine
      quarantineStatus = "Q1_ACTIVE";
      incidentType = existingIncident || incidentType;
      severity = existingSeverity;
      exitCondition = existingExitCondition || "EXIT_MANUAL_ONLY";
      codes.push("Q_ACTIVE_EXISTING");

      // R4: Check exit conditions
      if (exitCondition === "EXIT_MANUAL_ONLY") {
        codes.push("Q_EXIT_MANUAL_ONLY");
        // No automatic exit, must wait for manual intervention
      } else if (exitCondition === "EXIT_CONSENSUS_STRONG_2TICKS") {
        // Check if we have 2 consecutive ticks of strong consensus
        const consecutiveCount = resumeState.quarantineConsecutiveStrongConsensus || 0;
        if (signalConsensus === "CONSENSUS_STRONG") {
          const newCount = consecutiveCount + 1;
          statePatch.quarantineConsecutiveStrongConsensus = newCount;
          codes.push(`Q_EXIT_CONSENSUS_TICK_${newCount}`);
          if (newCount >= 2) {
            // Exit quarantine
            quarantineStatus = "Q2_EXPIRED";
            statePatch.quarantineActiveSinceTs = undefined;
            statePatch.quarantineIncidentType = undefined;
            statePatch.quarantineSeverity = undefined;
            statePatch.quarantineExitCondition = undefined;
            statePatch.quarantineConsecutiveStrongConsensus = undefined;
            codes.push("Q_EXIT_CONSENSUS_STRONG_2TICKS");
          }
        } else {
          // Reset counter if consensus not strong
          statePatch.quarantineConsecutiveStrongConsensus = 0;
          codes.push("Q_EXIT_CONSENSUS_RESET");
        }
      } else if (exitCondition === "EXIT_COOLDOWN_EXPIRED") {
        // Check if 60min cooldown has passed
        const COOLDOWN_MS = 60 * 60 * 1000; // 60 minutes
        if (nowMs - activeQuarantineTs > COOLDOWN_MS) {
          // Exit quarantine
          quarantineStatus = "Q2_EXPIRED";
          statePatch.quarantineActiveSinceTs = undefined;
          statePatch.quarantineIncidentType = undefined;
          statePatch.quarantineSeverity = undefined;
          statePatch.quarantineExitCondition = undefined;
          statePatch.quarantineConsecutiveStrongConsensus = undefined;
          codes.push("Q_EXIT_COOLDOWN_EXPIRED");
        } else {
          codes.push("Q_EXIT_COOLDOWN_ACTIVE");
        }
      }
    } else if (severity === "SEV2_HIGH" || severity === "SEV3_CRITICAL") {
      // New quarantine activation
      quarantineStatus = "Q1_ACTIVE";
      statePatch.quarantineActiveSinceTs = nowMs;
      statePatch.quarantineIncidentType = incidentType;
      statePatch.quarantineSeverity = severity;
      statePatch.quarantineConsecutiveStrongConsensus = 0;
      codes.push("Q_ACTIVATE_NEW");

      // R4: Exit condition selection based on severity
      if (severity === "SEV3_CRITICAL") {
        exitCondition = "EXIT_MANUAL_ONLY";
        codes.push("Q_EXIT_COND_MANUAL_ONLY");
      } else if (severity === "SEV2_HIGH") {
        // Choose between consensus or cooldown exit
        // Prefer consensus exit if signals are available, otherwise cooldown
        if (signalConsensus && signalConsensus !== "CONSENSUS_UNTRUSTED") {
          exitCondition = "EXIT_CONSENSUS_STRONG_2TICKS";
          codes.push("Q_EXIT_COND_CONSENSUS_2TICKS");
        } else {
          exitCondition = "EXIT_COOLDOWN_EXPIRED";
          codes.push("Q_EXIT_COND_COOLDOWN_60MIN");
        }
      }
      statePatch.quarantineExitCondition = exitCondition;
    } else {
      // No quarantine (SEV0_NONE or SEV1_SUSPECT)
      quarantineStatus = "Q0_NONE";
      codes.push("Q_NO_QUARANTINE");
    }

    // R5: Action mapping
    if (quarantineStatus === "Q1_ACTIVE") {
      action = "QA_ABORT";
      codes.push("Q_ACTION_ABORT");
    } else if (quarantineStatus === "Q2_EXPIRED") {
      action = "QA_DEFER";
      codes.push("Q_ACTION_DEFER_COOLDOWN");
    } else {
      action = "QA_ALLOW";
      codes.push("Q_ACTION_ALLOW");
    }

    return {
      quarantineStatus,
      incidentType,
      severity,
      exitCondition,
      action,
      codes: Array.from(new Set(codes)).sort().slice(0, 8),
      statePatch,
    };
  } catch (err) {
    // Defensive: On error, defer
    return {
      quarantineStatus: "Q9_ERROR",
      incidentType: "INC_UNKNOWN",
      severity: "SEV0_NONE",
      exitCondition: "EXIT_NONE",
      action: "QA_DEFER",
      codes: ["Q_DEFENSIVE_DEFER", `Q_ERROR_${String(err).substring(0, 30)}`].sort(),
      statePatch: {},
    };
  }
}

/**
 * PR236: Recovery Governance Layer v1 (Article XV - Recovery Permission Control)
 *
 * @param args - Governance inputs from prior layers
 * @returns Permission state, gate action, timing overrides, state patch, codes
 *
 * Purpose:
 *   Control when recovery (resume re-execution) is permitted after major stops.
 *   Implements recovery permission state machine: AUTO_ALLOWED → COOLDOWN_ONLY → MANUAL_ONLY → PERMANENT_HALT.
 *
 * Constitutional:
 *   - READ-ONLY: Never modifies execution directly
 *   - Deterministic: Same inputs → same outputs
 *   - Defensive: Fail-safe to COOLDOWN_ONLY + RG_DEFER on errors
 *   - Backward compatible: All outputs are labels/codes
 *   - Safety-first: Major stops require manual intervention or cooldown
 *
 * Rules:
 *   R0: Defensive baseline - missing context → COOLDOWN_ONLY + RG_DEFER
 *   R1: PERMANENT_HALT triggers - invariant fail, quarantine SEV3
 *   R2: MANUAL_ONLY triggers - CAR exhausted, econ abandon
 *   R3: COOLDOWN_ONLY triggers - quarantine SEV2, budget abandon
 *   R4: AUTO_ALLOWED default - normal operation
 *   R5: Operator overrides - manual hold/release (v1 optional)
 *   R6: Cooldown enforcement - enforce cooldown timing
 *   R7: Manual hold max age - anti-deadlock (>24h → PERMANENT_HALT)
 */
function deriveRecoveryGovernanceV1(args: {
  nowMs: number;
  resumeState?: import("../rebalance/types").ResumeState;
  // Inputs from prior layers (already computed in tick)
  quarantineStatus?: import("../rebalance/types").QuarantineStatusV1;
  quarantineSeverity?: import("../rebalance/types").IncidentSeverityV1;
  quarantineAction?: import("../rebalance/types").QuarantineActionV1;
  capitalRiskAction?: import("../rebalance/types").CapitalRiskActionV1;
  capitalRiskUsageLevel?: import("../rebalance/types").CapitalRiskUsageLevelV1;
  econAction?: import("../rebalance/types").EconConstraintActionV1;
  budgetAction?: string; // ALLOW | DEFER | ABANDON
  invariantStatus?: import("../rebalance/types").InvariantStatusV1;
  // Operator overrides (v1 optional)
  operatorOverride?: {
    manualHoldActive?: boolean;
    manualReleaseActive?: boolean;
  };
}): {
  permission: import("../rebalance/types").RecoveryPermissionV1;
  action: import("../rebalance/types").RecoveryGateActionV1;
  reason: import("../rebalance/types").RecoveryGateReasonV1;
  cooldownClass: "CD_NONE" | "CD_SHORT" | "CD_LONG" | "CD_ACTIVE";
  ageClass: "AGE_NONE" | "AGE_FRESH" | "AGE_MODERATE" | "AGE_OLD" | "AGE_EXPIRED";
  codes: string[];
  statePatch: Partial<import("../rebalance/types").ResumeState>;
} {
  try {
    const codes: string[] = [];
    const statePatch: Partial<import("../rebalance/types").ResumeState> = {};

    const {
      nowMs,
      resumeState,
      quarantineStatus,
      quarantineSeverity,
      quarantineAction,
      capitalRiskAction,
      capitalRiskUsageLevel,
      econAction,
      budgetAction,
      invariantStatus,
      operatorOverride,
    } = args;

    let permission: import("../rebalance/types").RecoveryPermissionV1 = "AUTO_ALLOWED";
    let action: import("../rebalance/types").RecoveryGateActionV1 = "RG_ALLOW";
    let reason: import("../rebalance/types").RecoveryGateReasonV1 = "BY_NONE";
    let cooldownClass: "CD_NONE" | "CD_SHORT" | "CD_LONG" | "CD_ACTIVE" = "CD_NONE";
    let ageClass: "AGE_NONE" | "AGE_FRESH" | "AGE_MODERATE" | "AGE_OLD" | "AGE_EXPIRED" = "AGE_NONE";

    // R0: Defensive baseline
    if (!resumeState) {
      permission = "COOLDOWN_ONLY";
      action = "RG_DEFER";
      reason = "BY_NONE";
      cooldownClass = "CD_LONG";
      codes.push("GOV_R0_DEFENSIVE_DEFAULT");
      return {
        permission,
        action,
        reason,
        cooldownClass,
        ageClass,
        codes: Array.from(new Set(codes)).sort().slice(0, 8),
        statePatch: {},
      };
    }

    // R1: PERMANENT_HALT triggers (fatal)
    if (invariantStatus === "INV_FAIL") {
      permission = "PERMANENT_HALT";
      action = "RG_ABORT";
      reason = "BY_INVARIANT_FAIL";
      codes.push("GOV_R1_HALT_INVARIANT_FAIL");
      statePatch.recoveryPermission = permission;
      statePatch.recoveryPermissionReason = reason;
      statePatch.recoveryPermissionSinceTs = nowMs;
      statePatch.recoveryGateLastAction = action;
      return {
        permission,
        action,
        reason,
        cooldownClass,
        ageClass,
        codes: Array.from(new Set(codes)).sort().slice(0, 8),
        statePatch,
      };
    }

    if (quarantineSeverity === "SEV3_CRITICAL" && quarantineStatus === "Q1_ACTIVE") {
      permission = "PERMANENT_HALT";
      action = "RG_ABORT";
      reason = "BY_QUARANTINE_SEV3";
      codes.push("GOV_R1_HALT_QUAR_SEV3");
      statePatch.recoveryPermission = permission;
      statePatch.recoveryPermissionReason = reason;
      statePatch.recoveryPermissionSinceTs = nowMs;
      statePatch.recoveryGateLastAction = action;
      return {
        permission,
        action,
        reason,
        cooldownClass,
        ageClass,
        codes: Array.from(new Set(codes)).sort().slice(0, 8),
        statePatch,
      };
    }

    // R2: MANUAL_ONLY triggers (major)
    if (capitalRiskAction === "CAR_ABORT" || capitalRiskUsageLevel === "RISK_EXHAUSTED") {
      permission = "MANUAL_ONLY";
      action = "RG_ABORT";
      reason = "BY_CAR_EXHAUSTED";
      codes.push("GOV_R2_MANUAL_CAR_EXHAUSTED");
      statePatch.recoveryPermission = permission;
      statePatch.recoveryPermissionReason = reason;
      statePatch.recoveryPermissionSinceTs = resumeState.recoveryPermissionSinceTs || nowMs;
      statePatch.recoveryGateLastAction = action;
      return {
        permission,
        action,
        reason,
        cooldownClass,
        ageClass,
        codes: Array.from(new Set(codes)).sort().slice(0, 8),
        statePatch,
      };
    }

    if (econAction === "ECON_ABANDON") {
      permission = "MANUAL_ONLY";
      action = "RG_ABORT";
      reason = "BY_ECON_ABANDON";
      codes.push("GOV_R2_MANUAL_ECON_ABANDON");
      statePatch.recoveryPermission = permission;
      statePatch.recoveryPermissionReason = reason;
      statePatch.recoveryPermissionSinceTs = resumeState.recoveryPermissionSinceTs || nowMs;
      statePatch.recoveryGateLastAction = action;
      return {
        permission,
        action,
        reason,
        cooldownClass,
        ageClass,
        codes: Array.from(new Set(codes)).sort().slice(0, 8),
        statePatch,
      };
    }

    // R3: COOLDOWN_ONLY triggers (high but recoverable)
    if (
      (quarantineStatus === "Q1_ACTIVE" && quarantineSeverity === "SEV2_HIGH") ||
      quarantineAction === "QA_ABORT"
    ) {
      permission = "COOLDOWN_ONLY";
      action = "RG_DEFER";
      reason = "BY_QUARANTINE_SEV2";
      cooldownClass = "CD_LONG";
      codes.push("GOV_R3_COOLDOWN_QUAR_SEV2");

      // R6: Cooldown enforcement (60min)
      const COOLDOWN_MS = 60 * 60 * 1000; // 60 minutes
      const cooldownUntil = resumeState.recoveryCooldownUntilTs;
      if (!cooldownUntil || nowMs >= cooldownUntil) {
        // Set new cooldown
        statePatch.recoveryCooldownUntilTs = nowMs + COOLDOWN_MS;
        cooldownClass = "CD_ACTIVE";
        codes.push("GOV_R6_COOLDOWN_SET_LONG");
      } else {
        // Cooldown still active
        cooldownClass = "CD_ACTIVE";
        codes.push("GOV_R6_COOLDOWN_ACTIVE");
      }

      statePatch.recoveryPermission = permission;
      statePatch.recoveryPermissionReason = reason;
      statePatch.recoveryPermissionSinceTs = resumeState.recoveryPermissionSinceTs || nowMs;
      statePatch.recoveryGateLastAction = action;
      return {
        permission,
        action,
        reason,
        cooldownClass,
        ageClass,
        codes: Array.from(new Set(codes)).sort().slice(0, 8),
        statePatch,
      };
    }

    if (budgetAction === "ABANDON") {
      permission = "MANUAL_ONLY";
      action = "RG_ABORT";
      reason = "BY_BUDGET_ABANDON";
      codes.push("GOV_R3_MANUAL_BUDGET_ABANDON");
      statePatch.recoveryPermission = permission;
      statePatch.recoveryPermissionReason = reason;
      statePatch.recoveryPermissionSinceTs = resumeState.recoveryPermissionSinceTs || nowMs;
      statePatch.recoveryGateLastAction = action;
      return {
        permission,
        action,
        reason,
        cooldownClass,
        ageClass,
        codes: Array.from(new Set(codes)).sort().slice(0, 8),
        statePatch,
      };
    }

    // R5: Operator overrides (v1 optional)
    if (operatorOverride?.manualHoldActive && resumeState.recoveryPermission !== "PERMANENT_HALT") {
      permission = "MANUAL_ONLY";
      action = "RG_ABORT";
      reason = "BY_OPERATOR_MANUAL_HOLD";
      codes.push("GOV_R5_OPERATOR_HOLD");
      statePatch.recoveryPermission = permission;
      statePatch.recoveryPermissionReason = reason;
      statePatch.recoveryPermissionSinceTs = resumeState.recoveryPermissionSinceTs || nowMs;
      statePatch.recoveryGateLastAction = action;
      return {
        permission,
        action,
        reason,
        cooldownClass,
        ageClass,
        codes: Array.from(new Set(codes)).sort().slice(0, 8),
        statePatch,
      };
    }

    if (operatorOverride?.manualReleaseActive && resumeState.recoveryPermission === "MANUAL_ONLY") {
      permission = "COOLDOWN_ONLY";
      action = "RG_DEFER";
      reason = "BY_OPERATOR_MANUAL_RELEASE";
      cooldownClass = "CD_LONG";
      codes.push("GOV_R5_OPERATOR_RELEASE");

      // Set cooldown on release
      const COOLDOWN_MS = 60 * 60 * 1000; // 60 minutes
      statePatch.recoveryCooldownUntilTs = nowMs + COOLDOWN_MS;
      statePatch.recoveryPermission = permission;
      statePatch.recoveryPermissionReason = reason;
      statePatch.recoveryPermissionSinceTs = nowMs;
      statePatch.recoveryGateLastAction = action;
      return {
        permission,
        action,
        reason,
        cooldownClass,
        ageClass,
        codes: Array.from(new Set(codes)).sort().slice(0, 8),
        statePatch,
      };
    }

    // R7: Manual hold max age (anti-deadlock)
    if (resumeState.recoveryPermission === "MANUAL_ONLY" && resumeState.recoveryPermissionSinceTs) {
      const MAX_AGE_MS = 24 * 60 * 60 * 1000; // 24 hours
      const age = nowMs - resumeState.recoveryPermissionSinceTs;
      if (age > MAX_AGE_MS) {
        permission = "PERMANENT_HALT";
        action = "RG_ABORT";
        reason = resumeState.recoveryPermissionReason || "BY_NONE";
        codes.push("GOV_R7_ESCALATE_MANUAL_TOO_OLD");
        statePatch.recoveryPermission = permission;
        statePatch.recoveryPermissionSinceTs = nowMs;
        statePatch.recoveryGateLastAction = action;
        return {
          permission,
          action,
          reason,
          cooldownClass,
          ageClass: "AGE_EXPIRED",
          codes: Array.from(new Set(codes)).sort().slice(0, 8),
          statePatch,
        };
      } else if (age > 12 * 60 * 60 * 1000) {
        ageClass = "AGE_OLD";
      } else if (age > 6 * 60 * 60 * 1000) {
        ageClass = "AGE_MODERATE";
      } else {
        ageClass = "AGE_FRESH";
      }
    }

    // R4: AUTO_ALLOWED default (normal operation)
    permission = "AUTO_ALLOWED";
    action = "RG_ALLOW";
    reason = "BY_NONE";
    codes.push("GOV_R4_AUTO_ALLOWED");

    return {
      permission,
      action,
      reason,
      cooldownClass,
      ageClass,
      codes: Array.from(new Set(codes)).sort().slice(0, 8),
      statePatch,
    };
  } catch (err) {
    // Defensive: On error, defer with cooldown
    return {
      permission: "COOLDOWN_ONLY",
      action: "RG_DEFER",
      reason: "BY_NONE",
      cooldownClass: "CD_LONG",
      ageClass: "AGE_NONE",
      codes: ["GOV_R0_DEFENSIVE_DEFAULT", `GOV_ERROR_${String(err).substring(0, 30)}`].sort(),
      statePatch: {},
    };
  }
}

/**
 * PR237: Learning Freeze & Drift Firewall v1 (Article XVI - Prevent Learning from Disequilibrium)
 *
 * @param args - Freeze inputs from all prior governance layers
 * @returns Freeze status, reason, exit condition, action, stable tick count, codes
 *
 * Purpose:
 *   Prevent adaptive/learning components from updating during hostile/degraded/abnormal states.
 *   Implements a fail-closed firewall: if conditions are unstable → FREEZE_ON.
 *
 * Constitutional:
 *   - READ-ONLY: Never modifies execution directly
 *   - Deterministic: Same inputs → same outputs
 *   - Defensive: Fail-closed to FREEZE_ON + FREEZE_ERROR on errors
 *   - Backward compatible: All outputs are labels/codes
 *   - Safety-first: Freeze prevents learning from contaminated signals
 *
 * Rules:
 *   R0: Defensive baseline - missing context/errors → FREEZE_ON + FREEZE_ERROR
 *   R1: Activation triggers (priority order) - any trigger → FREEZE_ON
 *       INV_FAIL > QUAR_ACTIVE > RISK_EXHAUSTED > GOV_NOT_AUTO > SIGNAL_NOT_STRONG > ECON_SEV_HIGH > RISK_HIGH > OSC_WARN
 *   R2: Hold behavior - if any trigger present, maintain FREEZE_ON
 *   R3: Exit protocol - requires 2 stable ticks (no triggers) or manual release
 */
function deriveLearningFreezeFirewallV1(args: {
  // Inputs (label-level)
  signalConsensus?: import("../rebalance/types").SignalConsensusV1;
  quarantineStatus?: import("../rebalance/types").QuarantineStatusV1;
  quarantineSeverity?: import("../rebalance/types").IncidentSeverityV1;
  governancePermission?: import("../rebalance/types").RecoveryPermissionV1;
  econSeverity?: string; // SEV_LOW | SEV_MEDIUM | SEV_HIGH | SEV_CRITICAL
  capitalRiskLevel?: import("../rebalance/types").CapitalRiskUsageLevelV1;
  oscillationStatus?: "OSC_NONE" | "OSC_WARN_STRATEGY" | "OSC_WARN_REGIME" | "OSC_WARN_BOTH";
  invariantStatus?: "INV_PASS" | "INV_FAIL";

  // State
  priorFreezeStatus?: import("../rebalance/types").LearningFreezeStatusV1;
  stableTickCount?: number;
  nowMs: number;

  // Optional operator override signals (v1 optional, future-proof)
  manualRelease?: boolean;
}): {
  freezeStatus: import("../rebalance/types").LearningFreezeStatusV1;
  reason: import("../rebalance/types").LearningFreezeReasonV1;
  exit: import("../rebalance/types").LearningFreezeExitV1;
  action: "FREEZE_APPLY" | "FREEZE_HOLD" | "FREEZE_RELEASE";
  stableTickCountNext: number;
  codes: string[];
} {
  try {
    const codes: string[] = [];

    const {
      signalConsensus,
      quarantineStatus,
      quarantineSeverity,
      governancePermission,
      econSeverity,
      capitalRiskLevel,
      oscillationStatus,
      invariantStatus,
      priorFreezeStatus,
      stableTickCount = 0,
      nowMs,
      manualRelease,
    } = args;

    let freezeStatus: import("../rebalance/types").LearningFreezeStatusV1 = "FREEZE_OFF";
    let reason: import("../rebalance/types").LearningFreezeReasonV1 = "LFR_NONE";
    let exit: import("../rebalance/types").LearningFreezeExitV1 = "LFX_NONE";
    let action: "FREEZE_APPLY" | "FREEZE_HOLD" | "FREEZE_RELEASE" = "FREEZE_RELEASE";
    let stableTickCountNext = 0;

    // R1: Activation triggers (priority order - most severe wins)
    let triggerPresent = false;

    // Check triggers in priority order (highest to lowest)
    if (invariantStatus === "INV_FAIL") {
      freezeStatus = "FREEZE_ON";
      reason = "LFR_INVARIANT_FAIL";
      triggerPresent = true;
      codes.push("FREEZE_R1_TRIGGER_INV_FAIL");
    } else if (quarantineStatus === "Q1_ACTIVE") {
      freezeStatus = "FREEZE_ON";
      reason = "LFR_QUARANTINE_ACTIVE";
      triggerPresent = true;
      codes.push("FREEZE_R1_TRIGGER_QUAR_ACTIVE");
    } else if (capitalRiskLevel === "RISK_EXHAUSTED") {
      freezeStatus = "FREEZE_ON";
      reason = "LFR_CAPITAL_RISK_HIGH";
      triggerPresent = true;
      codes.push("FREEZE_R1_TRIGGER_RISK_EXHAUSTED");
    } else if (governancePermission && governancePermission !== "AUTO_ALLOWED") {
      freezeStatus = "FREEZE_ON";
      reason = "LFR_GOV_NOT_AUTO";
      triggerPresent = true;
      codes.push("FREEZE_R1_TRIGGER_GOV_NOT_AUTO");
    } else if (signalConsensus && signalConsensus !== "CONSENSUS_STRONG") {
      freezeStatus = "FREEZE_ON";
      reason = "LFR_SIGNAL_NOT_STRONG";
      triggerPresent = true;
      codes.push("FREEZE_R1_TRIGGER_SIGNAL_WEAK");
    } else if (econSeverity && (econSeverity === "SEV_HIGH" || econSeverity === "SEV_CRITICAL")) {
      freezeStatus = "FREEZE_ON";
      reason = "LFR_ECON_SEV_HIGH";
      triggerPresent = true;
      codes.push("FREEZE_R1_TRIGGER_ECON_SEV_HIGH");
    } else if (capitalRiskLevel === "RISK_HIGH") {
      freezeStatus = "FREEZE_ON";
      reason = "LFR_CAPITAL_RISK_HIGH";
      triggerPresent = true;
      codes.push("FREEZE_R1_TRIGGER_RISK_HIGH");
    } else if (oscillationStatus && oscillationStatus !== "OSC_NONE") {
      freezeStatus = "FREEZE_ON";
      reason = "LFR_OSC_WARN";
      triggerPresent = true;
      codes.push("FREEZE_R1_TRIGGER_OSC_WARN");
    }

    // R2: Hold behavior
    if (triggerPresent) {
      freezeStatus = "FREEZE_ON";
      action = priorFreezeStatus === "FREEZE_ON" ? "FREEZE_HOLD" : "FREEZE_APPLY";
      exit = "LFX_NONE";
      stableTickCountNext = 0; // Reset stable tick counter
      codes.push("FREEZE_R2_HOLD");

      return {
        freezeStatus,
        reason,
        exit,
        action,
        stableTickCountNext,
        codes: Array.from(new Set(codes)).sort().slice(0, 8),
      };
    }

    // R3: Exit protocol (no triggers present)
    if (priorFreezeStatus === "FREEZE_ON") {
      // Manual release override
      if (manualRelease) {
        freezeStatus = "FREEZE_OFF";
        reason = "LFR_NONE";
        exit = "LFX_MANUAL_RELEASE";
        action = "FREEZE_RELEASE";
        stableTickCountNext = 0;
        codes.push("FREEZE_R3_EXIT_MANUAL");

        return {
          freezeStatus,
          reason,
          exit,
          action,
          stableTickCountNext,
          codes: Array.from(new Set(codes)).sort().slice(0, 8),
        };
      }

      // Require 2 stable ticks
      stableTickCountNext = Math.min(2, stableTickCount + 1);

      if (stableTickCountNext < 2) {
        // Not enough stable ticks yet, keep freeze ON
        freezeStatus = "FREEZE_ON";
        reason = priorFreezeStatus === "FREEZE_ON" ? reason : "LFR_NONE"; // Keep prior reason
        exit = "LFX_AUTO_STABLE_2TICK";
        action = "FREEZE_HOLD";
        codes.push("FREEZE_R3_STABLE_TICK_" + stableTickCountNext);

        return {
          freezeStatus,
          reason,
          exit,
          action,
          stableTickCountNext,
          codes: Array.from(new Set(codes)).sort().slice(0, 8),
        };
      } else {
        // 2 stable ticks reached, release freeze
        freezeStatus = "FREEZE_OFF";
        reason = "LFR_NONE";
        exit = "LFX_AUTO_STABLE_2TICK";
        action = "FREEZE_RELEASE";
        stableTickCountNext = 0;
        codes.push("FREEZE_R3_EXIT_AUTO_STABLE");

        return {
          freezeStatus,
          reason,
          exit,
          action,
          stableTickCountNext,
          codes: Array.from(new Set(codes)).sort().slice(0, 8),
        };
      }
    }

    // Default: no freeze, no prior freeze, no triggers
    freezeStatus = "FREEZE_OFF";
    reason = "LFR_NONE";
    exit = "LFX_NONE";
    action = "FREEZE_RELEASE";
    stableTickCountNext = 0;
    codes.push("FREEZE_R0_OFF");

    return {
      freezeStatus,
      reason,
      exit,
      action,
      stableTickCountNext,
      codes: Array.from(new Set(codes)).sort().slice(0, 8),
    };
  } catch (err) {
    // R0: Defensive: On error, freeze ON (fail-closed)
    return {
      freezeStatus: "FREEZE_ERROR",
      reason: "LFR_DEFENSIVE_ERROR",
      exit: "LFX_NONE",
      action: "FREEZE_APPLY",
      stableTickCountNext: 0,
      codes: ["FREEZE_ERROR_FALLBACK_ON", `FREEZE_ERR_${String(err).substring(0, 30)}`].sort().slice(0, 8),
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

      // PR230a: Signal trust & consensus layer variables (declare outside for wider scope)
      let signalTruth: import("../rebalance/types").SignalTruthV1 | undefined;
      let truthCodesSummary: { status: "PRESENT" | "EMPTY"; joined: string } = { status: "EMPTY", joined: "" };
      let resumeInputs: any; // Declare at wider scope for PR233 access

      // PR230b: Signal consensus execution cap variables (declare outside for wider scope)
      let signalEnforcedMode: import("../rebalance/types").ExecutionMode | undefined;
      let signalCapStatus: import("../rebalance/types").SignalExecCapStatusV1 = "CAP_NONE";
      let signalCapCodesSummary: { status: "PRESENT" | "EMPTY"; joined: string } = { status: "EMPTY", joined: "" };

      // PR231: Invariant check variables (declare outside for wider scope)
      let invariantStatus: import("../rebalance/types").InvariantStatusV1 = "INV_PASS";
      let invariantFailedGroup: import("../rebalance/types").InvariantGroupV1 | undefined;
      let invariantCodesSummary: { status: "PRESENT" | "EMPTY"; joined: string } = { status: "EMPTY", joined: "" };

      // PR232: Economic invariant check variables (declare outside for wider scope)
      let economicInvariantStatus: import("../rebalance/types").EconomicInvariantStatusV1 = "EINV_PASS";
      let economicInvariantFailedGroup: import("../rebalance/types").EconomicInvariantGroupV1 | undefined;
      let economicActionOverride: import("../rebalance/types").EconomicActionOverrideV1 = "NONE";
      let economicInvariantCodesSummary: { status: "PRESENT" | "EMPTY"; joined: string } = { status: "EMPTY", joined: "" };

      // PR233: Economic constraint variables (declare outside for wider scope)
      let econConstraintClass: import("../rebalance/types").EconConstraintClassV1 = "E0_OK";
      let econConstraintAction: import("../rebalance/types").EconConstraintActionV1 = "ECON_ALLOW";
      let econConstraintCodesSummary: { status: "PRESENT" | "EMPTY"; joined: string } = { status: "EMPTY", joined: "" };
      let econLiquidityCondition: import("../rebalance/types").LiquidityConditionV1 | undefined;
      let econSlippageRisk: import("../rebalance/types").SlippageRiskV1 | undefined;
      let econExposureStatus: import("../rebalance/types").ExposureStatusV1 | undefined;
      let econDrawdownStatus: import("../rebalance/types").DrawdownStatusV1 | undefined;

      // PR233a: Economic risk observability variables (label-only telemetry)
      let econRiskSeverity: string = "SEV_LOW";
      let econRiskCooldownStatus: string = "CD0_OK";
      let econRiskWindowStatus: string = "WINDOW_UNKNOWN";

      // PR233b: Economic execution shaping variables (label-only execution control)
      let econSizeCap: import("../rebalance/types").EconomicExecSizeCapV1 = "SIZE_NONE";
      let econFreqCap: import("../rebalance/types").EconomicExecFreqCapV1 = "FREQ_NONE";
      let econCapitalCap: import("../rebalance/types").EconomicCapitalCapV1 = "CAPITAL_NONE";
      let econShapeStatus: import("../rebalance/types").EconomicExecShapeStatusV1 = "SHAPE_NONE";
      let econShapeCodesSummary: { status: "PRESENT" | "EMPTY"; joined: string } = { status: "EMPTY", joined: "" };

      // PR234: Capital-at-Risk Envelope variables (label-only cumulative risk tracking)
      let capitalRiskWindowStatus: import("../rebalance/types").CapitalRiskWindowStatusV1 = "WIN_FRESH";
      let capitalRiskUsageLevel: import("../rebalance/types").CapitalRiskUsageLevelV1 = "RISK_LOW";
      let capitalRiskAction: import("../rebalance/types").CapitalRiskActionV1 = "CAR_ALLOW";
      let capitalRiskCodesSummary: { status: "PRESENT" | "EMPTY"; joined: string } = { status: "EMPTY", joined: "" };

      // PR235: Adversarial Incident Quarantine variables (label-only hostile market isolation)
      let quarantineStatus: import("../rebalance/types").QuarantineStatusV1 = "Q0_NONE";
      let quarantineIncidentType: import("../rebalance/types").IncidentTypeV1 = "INC_NONE";
      let quarantineSeverity: import("../rebalance/types").IncidentSeverityV1 = "SEV0_NONE";
      let quarantineExitCondition: import("../rebalance/types").QuarantineExitConditionV1 = "EXIT_NONE";
      let quarantineAction: import("../rebalance/types").QuarantineActionV1 = "QA_ALLOW";
      let quarantineCodesSummary: { status: "PRESENT" | "EMPTY"; joined: string } = { status: "EMPTY", joined: "" };

      // PR236: Recovery Governance Layer variables (label-only recovery permission control)
      let recoveryPermission: import("../rebalance/types").RecoveryPermissionV1 = "AUTO_ALLOWED";
      let recoveryGateAction: import("../rebalance/types").RecoveryGateActionV1 = "RG_ALLOW";
      let recoveryGateReason: import("../rebalance/types").RecoveryGateReasonV1 = "BY_NONE";
      let recoveryCooldownClass: "CD_NONE" | "CD_SHORT" | "CD_LONG" | "CD_ACTIVE" = "CD_NONE";
      let recoveryAgeClass: "AGE_NONE" | "AGE_FRESH" | "AGE_MODERATE" | "AGE_OLD" | "AGE_EXPIRED" = "AGE_NONE";
      let recoveryGateCodesSummary: { status: "PRESENT" | "EMPTY"; joined: string } = { status: "EMPTY", joined: "" };

      // PR237: Learning Freeze & Drift Firewall variables (label-only adaptive freeze control)
      let learningFreezeStatus: import("../rebalance/types").LearningFreezeStatusV1 = "FREEZE_OFF";
      let learningFreezeReason: import("../rebalance/types").LearningFreezeReasonV1 = "LFR_NONE";
      let learningFreezeExit: import("../rebalance/types").LearningFreezeExitV1 = "LFX_NONE";
      let learningFreezeAction: "FREEZE_APPLY" | "FREEZE_HOLD" | "FREEZE_RELEASE" = "FREEZE_RELEASE";
      let learningFreezeCodesSummary: { status: "PRESENT" | "EMPTY"; joined: string } = { status: "EMPTY", joined: "" };

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
            resumeInputs = await deps.getResumeInputs();

            // PR230a: Derive trust layer from fresh signals
            signalTruth = deriveSignalTrustLayerV1({
              oracleStatus: (resumeInputs as any).oracleStatus === "AVAILABLE" ? "ORACLE_OK" :
                           (resumeInputs as any).oracleStatus === "STALE" ? "ORACLE_STALE" :
                           (resumeInputs as any).oracleStatus === "UNAVAILABLE" ? "ORACLE_MISSING" : "ORACLE_UNKNOWN",
              dexStatus: (resumeInputs as any).dexStatus || "DEX_UNKNOWN",
              rpcHealth: (resumeInputs as any).rpcHealth || "RPC_UNKNOWN",
              quoteCrossCheck: (resumeInputs as any).quoteCrossCheck,
            });
            truthCodesSummary = summarizeCodeArrayV1(signalTruth.truth_codes);

            // Persist to ResumeState (defensive, optional)
            if (state.resumeState) {
              state.resumeState.lastSignalConsensus = signalTruth.consensus;
              state.resumeState.lastSignalConsensusCodes = signalTruth.truth_codes;
              state.resumeState.lastSignalTrustOracle = signalTruth.oracle_trust;
              state.resumeState.lastSignalTrustDex = signalTruth.dex_trust;
              state.resumeState.lastSignalTrustRpc = signalTruth.rpc_trust;
            }

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
        let instantRegime = regime.regime; // Instant regime from signals
        marketRegimeCodes = [...regime.codes, ...regimeSignalsCodes];

        // PR230a: Regime gating (Article XI safety-first)
        // If signal consensus is not STRONG, force conservative regime
        if (signalTruth && signalTruth.consensus !== "CONSENSUS_STRONG") {
          instantRegime = "REGIME_ORACLE_UNCERTAIN";
          marketRegimeCodes.push("REGIME_GATED_BY_SIGNAL_CONSENSUS");
          marketRegimeCodes.push(`REGIME_GATED_CONSENSUS_${signalTruth.consensus}`);
        }

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

        // PR228: Regime Hysteresis observability (instant vs confirmed)
        const regimeInstant = instantRegime; // From deriveMarketRegimeV1 (before hysteresis)
        const regimeConfirmed = marketRegime; // From confirmRegimeChangeV1 (after hysteresis)
        const regimeHysteresisAction = regimeHysteresisClass; // Already computed above
        const regimeHysteresisCodes = hysteresis.codes; // From confirmRegimeChangeV1
        const regimeHysteresisCodesSummary = summarizeCodeArrayV1(regimeHysteresisCodes);

        // PR228: Consecutive Success Gate observability (class + gate + codes)
        const consecutiveSuccessesClass = successStreakClass; // Already computed above (S0/S1/S2_PLUS)
        const successGate = successGateStatus; // Already computed above (GATE_WAIT/PASS/NA)

        // Derive success gate codes from escalation codes
        const successGateCodes: string[] = [];
        if (escalationCodes.includes("STRAT_ESC_CONSECUTIVE_SUCCESS_GATE_PASS")) {
          successGateCodes.push("STRAT_ESC_CONSEC_GATE_PASS");
        }
        if (escalationCodes.includes("STRAT_ESC_CONSECUTIVE_SUCCESS_GATE_WAIT")) {
          successGateCodes.push("STRAT_ESC_CONSEC_GATE_WAIT");
        }
        if (escalationCodes.includes("STRAT_ESC_FROM_ORCH_STATUS_SUCCEEDED")) {
          successGateCodes.push("STRAT_ESC_CONSEC_SUCCESS_S" + (successCount >= 2 ? "2_PLUS" : successCount));
        }
        if (successGateCodes.length === 0) {
          successGateCodes.push("STRAT_ESC_CONSEC_GATE_NA");
        }
        const successGateCodesSummary = summarizeCodeArrayV1(successGateCodes);

        // PR228: Oscillation basis observability (window + change levels + codes)
        const nowMsForOsc = getNowMs();
        const oscWindowStatus = classifyOscillationWindowStatusV1(
          state.resumeState.lastStrategyChangeTs || state.resumeState.lastRegimeChangeTs,
          nowMsForOsc
        );
        const oscChangeLevelStrategy = classifyOscillationChangeLevelV1(
          state.resumeState.strategyChangeCount
        );
        const oscChangeLevelRegime = classifyOscillationChangeLevelV1(
          state.resumeState.regimeChangeCount
        );

        // Collect oscillation basis codes
        const oscBasisCodes: string[] = [...oscillationCodes];
        if (oscWindowStatus === "WINDOW_RESET") {
          oscBasisCodes.push("OSC_WINDOW_RESET");
        } else if (oscWindowStatus === "WINDOW_FRESH") {
          oscBasisCodes.push("OSC_WINDOW_FRESH");
        }
        if (oscChangeLevelStrategy === "CHG_EXCEEDED") {
          oscBasisCodes.push("OSC_STRATEGY_LEVEL_EXCEEDED");
        }
        if (oscChangeLevelRegime === "CHG_EXCEEDED") {
          oscBasisCodes.push("OSC_REGIME_LEVEL_EXCEEDED");
        }
        const oscBasisCodesSummary = summarizeCodeArrayV1(oscBasisCodes);

        strategySummary = summarizeStrategyCodesV1(resumeStrategyCodes);
        escalationSummary = summarizeStrategyCodesV1(escalationCodes);
        regimeSummary = summarizeMarketRegimeCodesV1(marketRegimeCodes);
        matrixSummary = summarizeStrategyCodesV1(matrixCodes);

        // PR214: Derive execution mode enforcement from strategy
        const enforcement = deriveExecutionModeOverrideFromStrategyV1(
          resumeStrategy,
          undefined // No current desired mode available in minimal supervisor
        );
        const strategyEnforcedMode = enforcement.enforcedMode;
        const strategyEnforcedCodes = enforcement.enforcedCodes;

        // PR230b: Derive execution mode cap from signal consensus (NEVER LIVE)
        const signalCap = deriveExecutionModeOverrideFromSignalConsensusV1({
          signalConsensus: signalTruth?.consensus,
        });
        signalEnforcedMode = signalCap.enforcedMode;
        signalCapStatus = signalCap.capStatus;
        const signalCapCodes = signalCap.codes;
        signalCapCodesSummary = summarizeCodeArrayV1(signalCapCodes);

        // PR230b: Combine PR214 + PR230b enforcement (min-safety precedence)
        enforcedExecutionMode = combineEnforcedExecutionModesV1(
          strategyEnforcedMode,
          signalEnforcedMode
        );

        // PR230b: Merge enforcement codes (strategy + signal cap)
        enforcedCodes = Array.from(
          new Set([...strategyEnforcedCodes, ...signalCapCodes])
        )
          .sort()
          .slice(0, 8); // Dedup/sort/truncate
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

        // PR229: Recovery Budgeting (暴走防止) - check budget limits AFTER timing decision
        const budgetDecision = deriveRecoveryBudgetDecisionV1({
          desiredDelayClass: resumeDelayClass,
          desiredDelayOffsetLabel: resumeDelayOffsetLabel,
          orchEffectiveStatus: state.resumeState.orchLastStatus,
          oscChangeLevelStrategy,
          oscChangeLevelRegime,
          resumeState: state.resumeState,
          nowMs: getNowMs(),
        });

        // PR229: Budget status labels (label-only, for telemetry)
        const budgetAttemptStatus = budgetDecision.budgetAttemptStatus;
        const budgetImmediateRateStatus = budgetDecision.budgetImmediateRateStatus;
        const budgetFailedMarketRateStatus = budgetDecision.budgetFailedMarketRateStatus;
        const budgetOscCooldownStatus = budgetDecision.budgetOscCooldownStatus;
        const budgetAction = budgetDecision.action; // ALLOW | DEFER | ABANDON
        const budgetCodes = budgetDecision.codes;
        const budgetCodesSummary = summarizeCodeArrayV1(budgetCodes);

        // PR229: Apply budget override if needed
        if (budgetDecision.overrideDelayClass) {
          resumeDelayClass = budgetDecision.overrideDelayClass as import("../rebalance/types").ResumeDelayClassV1;
          resumeDelayOffsetLabel = (budgetDecision.overrideDelayOffsetLabel || resumeDelayOffsetLabel) as import("../rebalance/types").ResumeDelayOffsetLabelV1;
          resumeTimingReasonCodes = [
            ...resumeTimingReasonCodes,
            "TIMING_OVERRIDDEN_BY_BUDGET",
            ...budgetCodes,
          ];
          timingSummary = summarizeStrategyCodesV1(resumeTimingReasonCodes);
        }

        // PR229: Budget ABANDON handling (暴走防止) - check before emission
        if (budgetAction === "ABANDON") {
          // Abandon resume (budget limit exceeded)
          warnings.push("WARN_RESUME_ABANDONED_BUDGET_LIMIT");
          notes.push("NOTE_BUDGET_LIMIT_EXCEEDED");

          // Emit RESUME_REEXEC_ABANDONED event
          await appendEventV1(
            createEventV1("RESUME_REEXEC_ABANDONED", "WARN", {
              resume_id: resumeId || "UNKNOWN",
              previous_run_id: previousRunId || "UNKNOWN",
              abandon_reason: "BUDGET_LIMIT_EXCEEDED",
              budget_attempt_status: budgetAttemptStatus,
              budget_codes: budgetCodes.join("|") || "NONE",
            })
          ).catch(() => {});

          // Return ACTION_ABORT (skip runner call, clear resume state)
          return {
            status: "OK",
            action: "ACTION_ABORT",
            warnings,
            notes,
          };
        }

        // PR233: Economic Risk Constraints v1 (Article XII - LIVE capital safety)
        // PR233: Get economic risk inputs from resumeInputs
        econLiquidityCondition = (resumeInputs as any).liquidity || undefined;
        econSlippageRisk = (resumeInputs as any).slippageRisk || undefined;
        econExposureStatus = (resumeInputs as any).exposure || undefined;
        econDrawdownStatus = (resumeInputs as any).drawdown || undefined;

        const econConstraintResult = deriveEconomicRiskConstraintsV1({
          finalDesiredExecutionMode: undefined, // No desired mode available in minimal supervisor
          finalEnforcedExecutionMode: enforcedExecutionMode,
          signalConsensus: signalTruth?.consensus,
          marketRegimeConfirmed: (resumeInputs as any).marketRegimeConfirmed || regimeConfirmed,
          budgetDecision: { action: budgetAction },
          inputs: {
            liquidity: econLiquidityCondition,
            slippageRisk: econSlippageRisk,
            exposure: econExposureStatus,
            drawdown: econDrawdownStatus,
          },
          state: state.resumeState,
          nowMs: getNowMs(),
        });

        econConstraintClass = econConstraintResult.econClass;
        econConstraintAction = econConstraintResult.action;
        const econConstraintCodes = econConstraintResult.codes;
        econConstraintCodesSummary = summarizeCodeArrayV1(econConstraintCodes);

        // PR233a: Derive observability fields (telemetry-only, label-only)
        // Map econClass to severity
        if (econConstraintClass === "E0_OK") {
          econRiskSeverity = "SEV_LOW";
        } else if (econConstraintClass === "E1_CONSERVATIVE") {
          econRiskSeverity = "SEV_MEDIUM";
        } else if (econConstraintClass === "E2_RISKY") {
          econRiskSeverity = "SEV_HIGH";
        } else if (econConstraintClass === "E3_FORBIDDEN" || econConstraintClass === "E9_ERROR") {
          econRiskSeverity = "SEV_CRITICAL";
        }

        // Derive cooldown status from state
        if (state.resumeState?.econConstraintCooldownUntilTs && state.resumeState.econConstraintCooldownUntilTs > nowMs) {
          econRiskCooldownStatus = "CD1_ACTIVE";
        } else {
          econRiskCooldownStatus = "CD0_OK";
        }

        // Derive window status (simple v1: fresh if recent action, reset if old)
        if (state.resumeState?.econConstraintWindowAnchorTs) {
          const HOUR_MS = 60 * 60 * 1000;
          const windowAge = nowMs - state.resumeState.econConstraintWindowAnchorTs;
          if (windowAge < HOUR_MS) {
            econRiskWindowStatus = "WINDOW_FRESH";
          } else {
            econRiskWindowStatus = "WINDOW_RESET";
          }
        } else {
          econRiskWindowStatus = "WINDOW_UNKNOWN";
        }

        // PR233: Apply state patch if provided
        if (econConstraintResult.nextStatePatch && state.resumeState) {
          Object.assign(state.resumeState, econConstraintResult.nextStatePatch);
        }

        // PR233b: Economic Execution Shaping v1 (Article XII-b)
        const econShapeResult = deriveEconomicExecutionShapingV1({
          econDecision: econConstraintAction,
          econSeverity: econRiskSeverity,
          executionMode: enforcedExecutionMode,
          timingClass: resumeDelayClass,
        });

        econSizeCap = econShapeResult.sizeCap;
        econFreqCap = econShapeResult.freqCap;
        econCapitalCap = econShapeResult.capitalCap;
        econShapeStatus = econShapeResult.shapeStatus;
        econShapeCodesSummary = summarizeCodeArrayV1(econShapeResult.codes);

        // PR234: Capital-at-Risk Envelope v1 (Article XIII)
        const capitalRiskResult = deriveCapitalRiskEnvelopeV1({
          nowMs: getNowMs(),
          resumeState: state.resumeState,
          finalEnforcedExecutionMode: enforcedExecutionMode,
          econDecision: econConstraintAction,
          econSeverity: econRiskSeverity,
          execShapeStatus: econShapeStatus,
          execSizeCap: econSizeCap,
          budgetAction: budgetAction,
        });

        capitalRiskWindowStatus = capitalRiskResult.windowStatus;
        capitalRiskUsageLevel = capitalRiskResult.usageLevel;
        capitalRiskAction = capitalRiskResult.action;
        capitalRiskCodesSummary = summarizeCodeArrayV1(capitalRiskResult.codes);

        // PR234: Apply state patch if provided
        if (capitalRiskResult.statePatch && state.resumeState) {
          Object.assign(state.resumeState, capitalRiskResult.statePatch);
        }

        // PR234: Handle CAR_DEFER action
        if (capitalRiskAction === "CAR_DEFER") {
          warnings.push("WARN_RESUME_DEFERRED_CAPITAL_RISK");
          notes.push("NOTE_CAPITAL_RISK_HIGH");

          // Override timing to BACKOFF_LONG
          resumeDelayClass = "BACKOFF_LONG";
          resumeDelayOffsetLabel = "DELAY_1H"; // Defensive backoff (capital risk high)
          resumeTimingReasonCodes.push("TIMING_OVERRIDDEN_BY_CAPITAL_RISK");
          timingSummary = summarizeStrategyCodesV1(resumeTimingReasonCodes);

          // Emit RESUME_REEXEC_DEFERRED event
          await appendEventV1(
            createEventV1("RESUME_REEXEC_DEFERRED", "WARN", {
              resume_id: resumeId || "UNKNOWN",
              previous_run_id: previousRunId || "UNKNOWN",
              defer_reason: "CAPITAL_RISK_ENVELOPE_HIGH",
              // PR234: Capital risk labels
              resume_caprisk_window_status: capitalRiskWindowStatus,
              resume_caprisk_usage_level: capitalRiskUsageLevel,
              resume_caprisk_action: capitalRiskAction,
              resume_caprisk_codes_status: capitalRiskCodesSummary.status,
              resume_caprisk_codes: capitalRiskCodesSummary.joined,
            })
          ).catch(() => {});

          // Return ACTION_ABORT (skip runner call, keep resume state for next attempt)
          return {
            status: "OK",
            action: "ACTION_ABORT",
            warnings,
            notes,
          };
        }

        // PR234: Handle CAR_ABORT action
        if (capitalRiskAction === "CAR_ABORT") {
          warnings.push("WARN_RESUME_ABANDONED_CAPITAL_RISK");
          notes.push("NOTE_CAPITAL_RISK_EXHAUSTED");

          // Emit RESUME_REEXEC_ABANDONED event
          await appendEventV1(
            createEventV1("RESUME_REEXEC_ABANDONED", "ERROR", {
              resume_id: resumeId || "UNKNOWN",
              previous_run_id: previousRunId || "UNKNOWN",
              abandon_reason: "CAPITAL_RISK_ENVELOPE_EXHAUSTED",
              // PR234: Capital risk labels
              resume_caprisk_window_status: capitalRiskWindowStatus,
              resume_caprisk_usage_level: capitalRiskUsageLevel,
              resume_caprisk_action: capitalRiskAction,
              resume_caprisk_codes_status: capitalRiskCodesSummary.status,
              resume_caprisk_codes: capitalRiskCodesSummary.joined,
            })
          ).catch(() => {});

          // Return ACTION_ABORT (skip runner call, clear resume state)
          return {
            status: "OK",
            action: "ACTION_ABORT",
            warnings,
            notes,
          };
        }

        // PR233: Handle ECON_ABANDON action
        if (econConstraintAction === "ECON_ABANDON") {
          warnings.push("WARN_RESUME_ABANDONED_ECON_CONSTRAINT");
          notes.push(`NOTE_ECON_CONSTRAINT_${econConstraintClass}`);

          // Emit RESUME_REEXEC_ABANDONED event
          await appendEventV1(
            createEventV1("RESUME_REEXEC_ABANDONED", "WARN", {
              resume_id: resumeId || "UNKNOWN",
              previous_run_id: previousRunId || "UNKNOWN",
              abandon_reason: "ECONOMIC_CONSTRAINT_VIOLATION",
              // PR233: Economic Risk Constraints v1
              resume_econ_constraint_class: econConstraintClass,
              resume_econ_constraint_action: econConstraintAction,
              resume_econ_codes_status: econConstraintCodesSummary.status,
              resume_econ_codes: econConstraintCodesSummary.joined,
              // PR233a: Economic risk observability labels
              resume_econ_severity: econRiskSeverity,
              resume_econ_liquidity_class: econLiquidityCondition || "LIQ_UNKNOWN",
              resume_econ_slippage_class: econSlippageRisk || "SLIP_UNKNOWN",
              resume_econ_exposure_class: econExposureStatus || "EXP_UNKNOWN",
              resume_econ_drawdown_class: econDrawdownStatus || "DD_UNKNOWN",
              resume_econ_cooldown_status: econRiskCooldownStatus,
              resume_econ_window_status: econRiskWindowStatus,
              // PR233b: Economic execution shaping labels
              resume_econ_exec_size_cap: econSizeCap,
              resume_econ_exec_freq_cap: econFreqCap,
              resume_econ_capital_cap: econCapitalCap,
              resume_econ_exec_shape_status: econShapeStatus,
              resume_econ_exec_shape_codes_status: econShapeCodesSummary.status,
              resume_econ_exec_shape_codes: econShapeCodesSummary.joined,
            })
          ).catch(() => {});

          // Return ACTION_ABORT (skip runner call, clear resume state)
          return {
            status: "OK",
            action: "ACTION_ABORT",
            warnings,
            notes,
          };
        }

        // PR233: Handle ECON_DEFER action
        if (econConstraintAction === "ECON_DEFER") {
          warnings.push("WARN_RESUME_DEFERRED_ECON_CONSTRAINT");
          notes.push(`NOTE_ECON_CONSTRAINT_${econConstraintClass}`);

          // Emit RESUME_REEXEC_DEFERRED event
          await appendEventV1(
            createEventV1("RESUME_REEXEC_DEFERRED", "WARN", {
              resume_id: resumeId || "UNKNOWN",
              previous_run_id: previousRunId || "UNKNOWN",
              defer_reason: "ECONOMIC_CONSTRAINT_VIOLATION",
              // PR233: Economic Risk Constraints v1
              resume_econ_constraint_class: econConstraintClass,
              resume_econ_constraint_action: econConstraintAction,
              resume_econ_codes_status: econConstraintCodesSummary.status,
              resume_econ_codes: econConstraintCodesSummary.joined,
              // PR233a: Economic risk observability labels
              resume_econ_severity: econRiskSeverity,
              resume_econ_liquidity_class: econLiquidityCondition || "LIQ_UNKNOWN",
              resume_econ_slippage_class: econSlippageRisk || "SLIP_UNKNOWN",
              resume_econ_exposure_class: econExposureStatus || "EXP_UNKNOWN",
              resume_econ_drawdown_class: econDrawdownStatus || "DD_UNKNOWN",
              resume_econ_cooldown_status: econRiskCooldownStatus,
              resume_econ_window_status: econRiskWindowStatus,
              // PR233b: Economic execution shaping labels
              resume_econ_exec_size_cap: econSizeCap,
              resume_econ_exec_freq_cap: econFreqCap,
              resume_econ_capital_cap: econCapitalCap,
              resume_econ_exec_shape_status: econShapeStatus,
              resume_econ_exec_shape_codes_status: econShapeCodesSummary.status,
              resume_econ_exec_shape_codes: econShapeCodesSummary.joined,
            })
          ).catch(() => {});

          // Return ACTION_ABORT (skip runner call, keep resume state for next attempt)
          return {
            status: "OK",
            action: "ACTION_ABORT",
            warnings,
            notes,
          };
        }

        // PR235: Adversarial Incident Quarantine v1 (Article XIV)
        const quarantineResult = deriveAdversarialQuarantineV1({
          nowMs: getNowMs(),
          resumeState: state.resumeState,
          executionMode: enforcedExecutionMode,
          signalConsensus: signalTruth?.consensus,
          crosscheckStatus: signalTruth?.crosscheckStatus,
          rpcHealth: signalTruth?.rpcTrust, // Mapped from signalRpcTrust
          marketRegime: regimeConfirmed, // Use confirmed regime (after hysteresis)
          oscStatus: oscillationStatus, // From PR228
          capriskUsageLevel: capitalRiskUsageLevel, // From PR234
          econSeverity: econRiskSeverity, // From PR233a
        });

        quarantineStatus = quarantineResult.quarantineStatus;
        quarantineIncidentType = quarantineResult.incidentType;
        quarantineSeverity = quarantineResult.severity;
        quarantineExitCondition = quarantineResult.exitCondition;
        quarantineAction = quarantineResult.action;
        quarantineCodesSummary = summarizeCodeArrayV1(quarantineResult.codes);

        // PR235: Apply state patch if provided
        if (quarantineResult.statePatch && state.resumeState) {
          Object.assign(state.resumeState, quarantineResult.statePatch);
        }

        // PR235: Handle QA_ABORT action (quarantine active)
        if (quarantineAction === "QA_ABORT") {
          warnings.push("WARN_RESUME_ABORTED_QUARANTINE");
          notes.push(`NOTE_QUARANTINE_${quarantineSeverity}_${quarantineIncidentType}`);

          // Emit RESUME_REEXEC_ABORTED event
          await appendEventV1(
            createEventV1("RESUME_REEXEC_ABORTED", "ERROR", {
              resume_id: resumeId || "UNKNOWN",
              previous_run_id: previousRunId || "UNKNOWN",
              abort_reason: "ADVERSARIAL_INCIDENT_QUARANTINE",
              // PR235: Quarantine labels
              resume_quarantine_status: quarantineStatus,
              resume_quarantine_incident_type: quarantineIncidentType,
              resume_quarantine_severity: quarantineSeverity,
              resume_quarantine_exit_condition: quarantineExitCondition,
              resume_quarantine_action: quarantineAction,
              resume_quarantine_codes_status: quarantineCodesSummary.status,
              resume_quarantine_codes: quarantineCodesSummary.joined,
            })
          ).catch(() => {});

          // Return ACTION_ABORT (skip runner call, keep resume state for next quarantine check)
          return {
            status: "OK",
            action: "ACTION_ABORT",
            warnings,
            notes,
          };
        }

        // PR235: Handle QA_DEFER action (quarantine expired, cooldown)
        if (quarantineAction === "QA_DEFER") {
          warnings.push("WARN_RESUME_DEFERRED_QUARANTINE_COOLDOWN");
          notes.push("NOTE_QUARANTINE_COOLDOWN_ACTIVE");

          // Override timing to BACKOFF_LONG
          resumeDelayClass = "BACKOFF_LONG";
          resumeDelayOffsetLabel = "DELAY_1H"; // Defensive backoff (post-quarantine cooldown)
          resumeTimingReasonCodes.push("TIMING_OVERRIDDEN_BY_QUARANTINE");
          timingSummary = summarizeStrategyCodesV1(resumeTimingReasonCodes);

          // Emit RESUME_REEXEC_DEFERRED event
          await appendEventV1(
            createEventV1("RESUME_REEXEC_DEFERRED", "WARN", {
              resume_id: resumeId || "UNKNOWN",
              previous_run_id: previousRunId || "UNKNOWN",
              defer_reason: "QUARANTINE_COOLDOWN",
              // PR235: Quarantine labels
              resume_quarantine_status: quarantineStatus,
              resume_quarantine_incident_type: quarantineIncidentType,
              resume_quarantine_severity: quarantineSeverity,
              resume_quarantine_exit_condition: quarantineExitCondition,
              resume_quarantine_action: quarantineAction,
              resume_quarantine_codes_status: quarantineCodesSummary.status,
              resume_quarantine_codes: quarantineCodesSummary.joined,
            })
          ).catch(() => {});

          // Return ACTION_ABORT (skip runner call, keep resume state for next attempt)
          return {
            status: "OK",
            action: "ACTION_ABORT",
            warnings,
            notes,
          };
        }

        // PR231: Invariant Checks v1 (Final defensive layer)
        const invariantResult = deriveInvariantChecksV1({
          finalEnforcedExecutionMode: enforcedExecutionMode,
          resumeSignalConsensus: signalTruth?.consensus,
          resumeRegimeConfirmed: regimeConfirmed,
          resumeBudgetAction: budgetAction,
        });

        invariantStatus = invariantResult.status;
        invariantFailedGroup = invariantResult.failedGroup;
        const invariantCodes = invariantResult.codes;
        invariantCodesSummary = summarizeCodeArrayV1(invariantCodes);

        // PR231: Abort on invariant failure
        if (invariantStatus === "INV_FAIL") {
          warnings.push("WARN_RESUME_ABORTED_INVARIANT_VIOLATION");
          notes.push(`NOTE_INVARIANT_VIOLATION_${invariantFailedGroup}`);

          // Emit RESUME_REEXEC_ABORTED event
          await appendEventV1(
            createEventV1("RESUME_REEXEC_ABORTED", "ERROR", {
              resume_id: resumeId || "UNKNOWN",
              previous_run_id: previousRunId || "UNKNOWN",
              abort_reason: "INVARIANT_VIOLATION",
              invariant_status: invariantStatus,
              invariant_failed_group: invariantFailedGroup || "UNKNOWN",
              invariant_codes: invariantCodes.join("|") || "NONE",
            })
          ).catch(() => {});

          // Return ACTION_ABORT (skip runner call, clear resume state)
          return {
            status: "OK",
            action: "ACTION_ABORT",
            warnings,
            notes,
          };
        }

        // PR232: Economic Safety Invariants v1 (LIVE capital safety)
        // Note: For v1, economic risk classes (liquidity, slippage, etc.) default to safe values.
        // These can be extended in future PRs with actual market data transforms.
        const economicResult = deriveEconomicInvariantsV1({
          resumeActionIntent: "ACTION_RUN_TWAP", // In resume flow, we're attempting execution
          budgetAction,
          executionModeFinal: enforcedExecutionMode,
          // Market integrity signals (from PR230)
          quoteCrosscheckStatus: signalTruth?.crosscheck_status,
          // Economic risk classes (v1: undefined → not evaluated, passes through)
          // Future PRs can add real transforms from market data
          // For v1, all undefined (missing data) → EINV_PASS (not enough data to evaluate)
          liqDepthClass: undefined,
          orderSizeClass: undefined,
          liqMatchStatus: undefined,
          slippageRiskClass: undefined,
          crashRiskClass: undefined,
          exposureClass: undefined,
          concentrationClass: undefined,
        });

        economicInvariantStatus = economicResult.status;
        economicInvariantFailedGroup = economicResult.failedGroup;
        economicActionOverride = economicResult.actionOverride;
        const economicInvariantCodes = economicResult.codes;
        economicInvariantCodesSummary = summarizeCodeArrayV1(economicInvariantCodes);

        // PR232: Apply action override on economic invariant failure
        if (economicInvariantStatus === "EINV_FAIL") {
          if (economicActionOverride === "ABORT") {
            warnings.push("WARN_RESUME_ABORTED_ECONOMIC_VIOLATION");
            notes.push(`NOTE_ECONOMIC_VIOLATION_${economicInvariantFailedGroup}`);

            // Emit RESUME_REEXEC_ABORTED event
            await appendEventV1(
              createEventV1("RESUME_REEXEC_ABORTED", "ERROR", {
                resume_id: resumeId || "UNKNOWN",
                previous_run_id: previousRunId || "UNKNOWN",
                abort_reason: "ECONOMIC_INVARIANT_VIOLATION",
                einv_status: economicInvariantStatus,
                einv_failed_group: economicInvariantFailedGroup || "UNKNOWN",
                einv_action_override: economicActionOverride,
                einv_codes: economicInvariantCodes.join("|") || "NONE",
              })
            ).catch(() => {});

            // Return ACTION_ABORT (skip runner call, clear resume state)
            return {
              status: "OK",
              action: "ACTION_ABORT",
              warnings,
              notes,
            };
          } else if (economicActionOverride === "DEFER_MANUAL" || economicActionOverride === "DEFER_BACKOFF_LONG") {
            // For DEFER overrides, we could map to delay classes
            // For v1, treat as ABORT for simplicity (manual intervention required)
            warnings.push("WARN_RESUME_DEFERRED_ECONOMIC_VIOLATION");
            notes.push(`NOTE_ECONOMIC_DEFER_${economicInvariantFailedGroup}`);

            // Emit RESUME_REEXEC_DEFERRED event
            await appendEventV1(
              createEventV1("RESUME_REEXEC_DEFERRED", "WARN", {
                resume_id: resumeId || "UNKNOWN",
                previous_run_id: previousRunId || "UNKNOWN",
                defer_reason: "ECONOMIC_INVARIANT_VIOLATION",
                einv_status: economicInvariantStatus,
                einv_failed_group: economicInvariantFailedGroup || "UNKNOWN",
                einv_action_override: economicActionOverride,
                einv_codes: economicInvariantCodes.join("|") || "NONE",
              })
            ).catch(() => {});

            // Return ACTION_ABORT (v1: defer treated as abort for manual review)
            return {
              status: "OK",
              action: "ACTION_ABORT",
              warnings,
              notes,
            };
          }
        }

        // PR236: Recovery Governance Layer v1 (Article XV - Final Gate)
        const governanceResult = deriveRecoveryGovernanceV1({
          nowMs: getNowMs(),
          resumeState: state.resumeState,
          quarantineStatus,
          quarantineSeverity,
          quarantineAction,
          capitalRiskAction,
          capitalRiskUsageLevel,
          econAction: econConstraintAction,
          budgetAction,
          invariantStatus,
          // operatorOverride: undefined (v1: no manual overrides)
        });

        recoveryPermission = governanceResult.permission;
        recoveryGateAction = governanceResult.action;
        recoveryGateReason = governanceResult.reason;
        recoveryCooldownClass = governanceResult.cooldownClass;
        recoveryAgeClass = governanceResult.ageClass;
        recoveryGateCodesSummary = summarizeCodeArrayV1(governanceResult.codes);

        // PR236: Apply state patch if provided
        if (governanceResult.statePatch && state.resumeState) {
          Object.assign(state.resumeState, governanceResult.statePatch);
        }

        // PR236: Handle RG_ABORT action (recovery blocked - PERMANENT_HALT or MANUAL_ONLY)
        if (recoveryGateAction === "RG_ABORT") {
          warnings.push("WARN_RESUME_BLOCKED_GOVERNANCE");
          notes.push(`NOTE_RECOVERY_${recoveryPermission}_${recoveryGateReason}`);

          // Emit RESUME_REEXEC_ABORTED event
          await appendEventV1(
            createEventV1("RESUME_REEXEC_ABORTED", "ERROR", {
              resume_id: resumeId || "UNKNOWN",
              previous_run_id: previousRunId || "UNKNOWN",
              abort_reason: "RECOVERY_GOVERNANCE_BLOCKED",
              // PR236: Recovery governance labels
              resume_recovery_permission: recoveryPermission,
              resume_recovery_gate_action: recoveryGateAction,
              resume_recovery_gate_reason: recoveryGateReason,
              resume_recovery_gate_cooldown_class: recoveryCooldownClass,
              resume_recovery_gate_age_class: recoveryAgeClass,
              resume_recovery_gate_codes_status: recoveryGateCodesSummary.status,
              resume_recovery_gate_codes: recoveryGateCodesSummary.joined,
            })
          ).catch(() => {});

          // Return ACTION_ABORT (skip runner call, keep resume state for manual intervention)
          return {
            status: "OK",
            action: "ACTION_ABORT",
            warnings,
            notes,
          };
        }

        // PR236: Handle RG_DEFER action (recovery deferred - COOLDOWN_ONLY with active cooldown)
        if (recoveryGateAction === "RG_DEFER") {
          warnings.push("WARN_RESUME_DEFERRED_GOVERNANCE_COOLDOWN");
          notes.push("NOTE_RECOVERY_COOLDOWN_ACTIVE");

          // Override timing to BACKOFF_LONG
          resumeDelayClass = "BACKOFF_LONG";
          resumeDelayOffsetLabel = "DELAY_1H"; // Defensive backoff (governance cooldown)
          resumeTimingReasonCodes.push("TIMING_OVERRIDDEN_BY_GOVERNANCE");
          timingSummary = summarizeStrategyCodesV1(resumeTimingReasonCodes);

          // Emit RESUME_REEXEC_DEFERRED event
          await appendEventV1(
            createEventV1("RESUME_REEXEC_DEFERRED", "WARN", {
              resume_id: resumeId || "UNKNOWN",
              previous_run_id: previousRunId || "UNKNOWN",
              defer_reason: "RECOVERY_GOVERNANCE_COOLDOWN",
              // PR236: Recovery governance labels
              resume_recovery_permission: recoveryPermission,
              resume_recovery_gate_action: recoveryGateAction,
              resume_recovery_gate_reason: recoveryGateReason,
              resume_recovery_gate_cooldown_class: recoveryCooldownClass,
              resume_recovery_gate_age_class: recoveryAgeClass,
              resume_recovery_gate_codes_status: recoveryGateCodesSummary.status,
              resume_recovery_gate_codes: recoveryGateCodesSummary.joined,
            })
          ).catch(() => {});

          // Return ACTION_ABORT (skip runner call, keep resume state for next cooldown check)
          return {
            status: "OK",
            action: "ACTION_ABORT",
            warnings,
            notes,
          };
        }

        // PR236: Handle RG_ABANDON action (recovery abandoned - clear resume state)
        if (recoveryGateAction === "RG_ABANDON") {
          warnings.push("WARN_RESUME_ABANDONED_GOVERNANCE");
          notes.push("NOTE_RECOVERY_ABANDONED");

          // Emit RESUME_REEXEC_ABANDONED event
          await appendEventV1(
            createEventV1("RESUME_REEXEC_ABANDONED", "ERROR", {
              resume_id: resumeId || "UNKNOWN",
              previous_run_id: previousRunId || "UNKNOWN",
              abandon_reason: "RECOVERY_GOVERNANCE_ABANDONED",
              // PR236: Recovery governance labels
              resume_recovery_permission: recoveryPermission,
              resume_recovery_gate_action: recoveryGateAction,
              resume_recovery_gate_reason: recoveryGateReason,
              resume_recovery_gate_cooldown_class: recoveryCooldownClass,
              resume_recovery_gate_age_class: recoveryAgeClass,
              resume_recovery_gate_codes_status: recoveryGateCodesSummary.status,
              resume_recovery_gate_codes: recoveryGateCodesSummary.joined,
            })
          ).catch(() => {});

          // Return ACTION_ABORT (skip runner call, clear resume state)
          return {
            status: "OK",
            action: "ACTION_ABORT",
            warnings,
            notes,
          };
        }

        // PR237: Learning Freeze & Drift Firewall v1 (Article XVI - Prevent Learning from Disequilibrium)
        const freezeResult = deriveLearningFreezeFirewallV1({
          signalConsensus: signalTruth?.consensus,
          quarantineStatus,
          quarantineSeverity,
          governancePermission: recoveryPermission,
          econSeverity, // Assuming econSeverity is available from PR233
          capitalRiskLevel: capitalRiskUsageLevel,
          oscillationStatus: oscStatus, // Assuming oscStatus is available from PR226
          invariantStatus,
          priorFreezeStatus: state.resumeState?.learningFreezeStatus,
          stableTickCount: state.resumeState?.learningFreezeStableTickCount || 0,
          nowMs: getNowMs(),
          // manualRelease: undefined (v1: no manual overrides)
        });

        learningFreezeStatus = freezeResult.freezeStatus;
        learningFreezeReason = freezeResult.reason;
        learningFreezeExit = freezeResult.exit;
        learningFreezeAction = freezeResult.action;
        learningFreezeCodesSummary = summarizeCodeArrayV1(freezeResult.codes);

        // PR237: Apply state updates
        if (state.resumeState) {
          state.resumeState.learningFreezeStatus = learningFreezeStatus;
          state.resumeState.learningFreezeReason = learningFreezeReason;
          state.resumeState.learningFreezeStableTickCount = freezeResult.stableTickCountNext;
          state.resumeState.learningFreezeLastDecisionCodes = freezeResult.codes;

          // Set freeze activation timestamp on first activation
          if (learningFreezeAction === "FREEZE_APPLY" && !state.resumeState.learningFreezeSinceTs) {
            state.resumeState.learningFreezeSinceTs = getNowMs();
          }

          // Clear freeze timestamp on release
          if (learningFreezeAction === "FREEZE_RELEASE") {
            state.resumeState.learningFreezeSinceTs = undefined;
            state.resumeState.learningFreezeStableTickCount = 0;
          }
        }

        // PR237: Enforcement - Apply freeze constraints
        if (learningFreezeStatus === "FREEZE_ON" || learningFreezeStatus === "FREEZE_ERROR") {
          // A) Escalation clamp: Prevent RETRY_IMMEDIATE during freeze
          if (escalatedStrategy === "RETRY_IMMEDIATE") {
            escalatedStrategy = "RETRY_SAFE_SIM_ONLY"; // Downgrade to conservative
            escalationCodes.push("FREEZE_CLAMP_NO_IMMEDIATE");
            warnings.push("WARN_FREEZE_CLAMP_ESCALATION");
          }

          // B) Regime clamp: Force conservative regime (optional, but recommended)
          // Note: In v1, we trust PR230a consensus enforcement, so this is defensive
          if (marketRegime && !["REGIME_ORACLE_UNCERTAIN", "REGIME_ORACLE_DEGRADED"].includes(marketRegime)) {
            // Add warning but don't override (PR230a already enforces)
            warnings.push("WARN_FREEZE_REGIME_AGGRESSIVE");
          }

          // C) Execution shaping clamp: No relaxation of constraints
          // Note: In v1, we don't have explicit shaping relaxation, so this is a marker
          notes.push("NOTE_FREEZE_NO_RELAX_SHAPING");
        }

        // PR213/PR214/PR215/PR219/PR220/PR228/PR229/PR231/PR232/PR236/PR237: Set resume fields on runPlan before execution
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
            // PR228: Observability pack (passthrough to runner)
            resumeRegimeInstant: regimeInstant,
            resumeRegimeConfirmed: regimeConfirmed,
            resumeRegimeHysteresisAction: regimeHysteresisAction,
            resumeRegimeHysteresisCodes: regimeHysteresisCodes,
            resumeConsecutiveSuccessesClass: consecutiveSuccessesClass,
            resumeSuccessGate: successGate,
            resumeSuccessGateCodes: successGateCodes,
            resumeOscWindowStatus: oscWindowStatus,
            resumeOscChangeLevelStrategy: oscChangeLevelStrategy,
            resumeOscChangeLevelRegime: oscChangeLevelRegime,
            resumeOscBasisCodes: oscBasisCodes,
            // PR229: Recovery Budgeting (label-only status fields)
            resumeBudgetAttemptStatus: budgetAttemptStatus,
            resumeBudgetImmediateRateStatus: budgetImmediateRateStatus,
            resumeBudgetFailedMarketRateStatus: budgetFailedMarketRateStatus,
            resumeBudgetOscCooldownStatus: budgetOscCooldownStatus,
            resumeBudgetAction: budgetAction,
            resumeBudgetCodes: budgetCodes,
            // PR230a: Signal trust & consensus layer (Article XI passthrough)
            resumeSignalConsensus: signalTruth?.consensus,
            resumeSignalConsensusCodesStatus: truthCodesSummary.status,
            resumeSignalConsensusCodes: truthCodesSummary.joined,
            resumeSignalOracleTrust: signalTruth?.oracle_trust,
            resumeSignalDexTrust: signalTruth?.dex_trust,
            resumeSignalRpcTrust: signalTruth?.rpc_trust,
            resumeSignalCrosscheckStatus: signalTruth?.crosscheck_status,
            // PR230b: Consensus → execution hard cap (NEVER LIVE)
            resumeSignalEnforcedExecutionMode: signalEnforcedMode,
            resumeSignalEnforcedCodes: signalCapCodes,
            resumeSignalExecCapStatus: signalCapStatus,
            // PR231: Invariant Checks v1 (Final defensive layer)
            resumeInvariantStatus: invariantStatus,
            resumeInvariantFailedGroup: invariantFailedGroup,
            resumeInvariantCodes: invariantCodes,
            // PR232: Economic Safety Invariants v1 (LIVE capital safety)
            resumeEconomicInvariantStatus: economicInvariantStatus,
            resumeEconomicInvariantFailedGroup: economicInvariantFailedGroup,
            resumeEconomicInvariantCodes: economicInvariantCodes,
            resumeEconomicActionOverride: economicActionOverride,
            // PR233: Economic Risk Constraints Layer v1 (Article XII)
            resumeEconLiquidityCondition: econLiquidityCondition,
            resumeEconSlippageRisk: econSlippageRisk,
            resumeEconExposureStatus: econExposureStatus,
            resumeEconDrawdownStatus: econDrawdownStatus,
            resumeEconConstraintClass: econConstraintClass,
            resumeEconConstraintAction: econConstraintAction,
            resumeEconConstraintCodes: econConstraintCodes,
            resumeEconConstraintCodesStatus: econConstraintCodesSummary.status,
            // PR233a: Economic Risk Observability Pack v1 (telemetry-only)
            resumeEconRiskSeverity: econRiskSeverity,
            resumeEconRiskCooldownStatus: econRiskCooldownStatus,
            resumeEconRiskWindowStatus: econRiskWindowStatus,
            // PR233b: Economic Execution Shaping v1
            resumeEconExecSizeCap: econSizeCap,
            resumeEconExecFreqCap: econFreqCap,
            resumeEconCapitalCap: econCapitalCap,
            resumeEconExecShapeStatus: econShapeStatus,
            resumeEconExecShapeCodes: econShapeResult.codes,
            // PR234: Capital-at-Risk Envelope v1 (Article XIII)
            resumeCapitalRiskWindowStatus: capitalRiskWindowStatus,
            resumeCapitalRiskUsageLevel: capitalRiskUsageLevel,
            resumeCapitalRiskAction: capitalRiskAction,
            resumeCapitalRiskCodes: capitalRiskResult.codes,
            resumeCapitalRiskCodesStatus: capitalRiskCodesSummary.status,
            // PR235: Adversarial Incident Quarantine v1 (Article XIV)
            resumeQuarantineStatus: quarantineStatus,
            resumeQuarantineIncidentType: quarantineIncidentType,
            resumeQuarantineSeverity: quarantineSeverity,
            resumeQuarantineExitCondition: quarantineExitCondition,
            resumeQuarantineAction: quarantineAction,
            resumeQuarantineCodes: quarantineResult.codes,
            resumeQuarantineCodesStatus: quarantineCodesSummary.status,
            // PR236: Recovery Governance Layer v1 (Article XV)
            resumeRecoveryPermission: recoveryPermission,
            resumeRecoveryGateAction: recoveryGateAction,
            resumeRecoveryGateReason: recoveryGateReason,
            resumeRecoveryGateCooldownClass: recoveryCooldownClass,
            resumeRecoveryGateAgeClass: recoveryAgeClass,
            resumeRecoveryGateCodes: governanceResult.codes.join("|"),
            resumeRecoveryGateCodesStatus: recoveryGateCodesSummary.status,
            // PR237: Learning Freeze & Drift Firewall v1 (Article XVI)
            resumeLearningFreezeStatus: learningFreezeStatus,
            resumeLearningFreezeReason: learningFreezeReason,
            resumeLearningFreezeExit: learningFreezeExit,
            resumeLearningFreezeAction: learningFreezeAction,
            resumeLearningFreezeCodes: freezeResult.codes,
            resumeLearningFreezeCodesStatus: learningFreezeCodesSummary.status,
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
        // PR228: Add observability pack (instant/confirmed, gate codes, osc basis)
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
            // PR228: Observability pack
            resume_regime_instant: regimeInstant, // Instant (before hysteresis)
            resume_regime_confirmed: regimeConfirmed, // Confirmed (after hysteresis)
            resume_regime_hysteresis_action: regimeHysteresisAction, // H0/H1/H2
            resume_regime_hysteresis_codes_status: regimeHysteresisCodesSummary.status,
            resume_regime_hysteresis_codes: regimeHysteresisCodesSummary.joined,
            resume_consecutive_successes_class: consecutiveSuccessesClass, // S0/S1/S2_PLUS
            resume_success_gate_codes_status: successGateCodesSummary.status,
            resume_success_gate_codes: successGateCodesSummary.joined,
            resume_osc_window_status: oscWindowStatus, // WINDOW_FRESH/RESET
            resume_osc_change_level_strategy: oscChangeLevelStrategy, // CHG_LOW/MEDIUM/HIGH/EXCEEDED
            resume_osc_change_level_regime: oscChangeLevelRegime, // CHG_LOW/MEDIUM/HIGH/EXCEEDED
            resume_osc_basis_codes_status: oscBasisCodesSummary.status,
            resume_osc_basis_codes: oscBasisCodesSummary.joined,
            // PR229: Recovery Budgeting labels
            resume_budget_attempt_status: budgetAttemptStatus, // B0_OK | B1_NEAR_LIMIT | B2_LIMIT_EXCEEDED
            resume_budget_immediate_rate_status: budgetImmediateRateStatus, // R0_OK | R1_NEAR_LIMIT | R2_LIMIT_EXCEEDED
            resume_budget_failed_market_rate_status: budgetFailedMarketRateStatus, // F0_OK | F1_NEAR_LIMIT | F2_LIMIT_EXCEEDED
            resume_budget_osc_cooldown_status: budgetOscCooldownStatus, // C0_OK | C1_COOLDOWN_ACTIVE
            resume_budget_action: budgetAction, // ALLOW | DEFER | ABANDON
            resume_budget_codes_status: budgetCodesSummary.status,
            resume_budget_codes: budgetCodesSummary.joined,
            // PR230a: Signal trust & consensus layer (Article XI)
            resume_signal_consensus: signalTruth?.consensus || "CONSENSUS_UNTRUSTED",
            resume_signal_consensus_codes_status: truthCodesSummary.status,
            resume_signal_consensus_codes: truthCodesSummary.joined,
            resume_signal_oracle_trust: signalTruth?.oracle_trust || "UNKNOWN",
            resume_signal_dex_trust: signalTruth?.dex_trust || "UNKNOWN",
            resume_signal_rpc_trust: signalTruth?.rpc_trust || "UNKNOWN",
            resume_signal_crosscheck_status: signalTruth?.crosscheck_status || "XCHK_UNKNOWN",
            // PR230b: Consensus → execution hard cap (NEVER LIVE)
            resume_signal_exec_cap_status: signalCapStatus,
            resume_signal_enforced_execution_mode: signalEnforcedMode || "NONE",
            resume_signal_enforced_codes_status: signalCapCodesSummary.status,
            resume_signal_enforced_codes: signalCapCodesSummary.joined,
            // PR231: Invariant Checks v1 (Final defensive layer)
            resume_invariant_status: invariantStatus,
            resume_invariant_failed_group: invariantFailedGroup || "NONE",
            resume_invariant_codes_status: invariantCodesSummary.status,
            resume_invariant_codes: invariantCodesSummary.joined,
            // PR232: Economic Safety Invariants v1 (LIVE capital safety)
            resume_einv_status: economicInvariantStatus,
            resume_einv_failed_group: economicInvariantFailedGroup || "NONE",
            resume_einv_action_override: economicActionOverride,
            resume_einv_codes_status: economicInvariantCodesSummary.status,
            resume_einv_codes: economicInvariantCodesSummary.joined,
            // PR233: Economic Risk Constraints v1 (Article XII)
            resume_econ_constraint_class: econConstraintClass,
            resume_econ_constraint_action: econConstraintAction,
            resume_econ_codes_status: econConstraintCodesSummary.status,
            resume_econ_codes: econConstraintCodesSummary.joined,
            // PR233a: Economic Risk Observability Pack v1 (telemetry-only)
            resume_econ_severity: econRiskSeverity,
            resume_econ_liquidity_class: econLiquidityCondition || "LIQ_UNKNOWN",
            resume_econ_slippage_class: econSlippageRisk || "SLIP_UNKNOWN",
            resume_econ_exposure_class: econExposureStatus || "EXP_UNKNOWN",
            resume_econ_drawdown_class: econDrawdownStatus || "DD_UNKNOWN",
            resume_econ_cooldown_status: econRiskCooldownStatus,
            resume_econ_window_status: econRiskWindowStatus,
            // PR233b: Economic execution shaping labels
            resume_econ_exec_size_cap: econSizeCap,
            resume_econ_exec_freq_cap: econFreqCap,
            resume_econ_capital_cap: econCapitalCap,
            resume_econ_exec_shape_status: econShapeStatus,
            resume_econ_exec_shape_codes_status: econShapeCodesSummary.status,
            resume_econ_exec_shape_codes: econShapeCodesSummary.joined,
            // PR234: Capital-at-Risk Envelope labels (Article XIII)
            resume_caprisk_window_status: capitalRiskWindowStatus,
            resume_caprisk_usage_level: capitalRiskUsageLevel,
            resume_caprisk_action: capitalRiskAction,
            resume_caprisk_codes_status: capitalRiskCodesSummary.status,
            resume_caprisk_codes: capitalRiskCodesSummary.joined,
            // PR235: Adversarial Incident Quarantine labels (Article XIV)
            resume_quarantine_status: quarantineStatus,
            resume_quarantine_incident_type: quarantineIncidentType,
            resume_quarantine_severity: quarantineSeverity,
            resume_quarantine_exit_condition: quarantineExitCondition,
            resume_quarantine_action: quarantineAction,
            resume_quarantine_codes_status: quarantineCodesSummary.status,
            resume_quarantine_codes: quarantineCodesSummary.joined,
            // PR236: Recovery Governance Layer labels (Article XV)
            resume_recovery_permission: recoveryPermission,
            resume_recovery_gate_action: recoveryGateAction,
            resume_recovery_gate_reason: recoveryGateReason,
            resume_recovery_gate_cooldown_class: recoveryCooldownClass,
            resume_recovery_gate_age_class: recoveryAgeClass,
            resume_recovery_gate_codes_status: recoveryGateCodesSummary.status,
            resume_recovery_gate_codes: recoveryGateCodesSummary.joined,
            // PR237: Learning Freeze & Drift Firewall labels (Article XVI)
            resume_learning_freeze_status: learningFreezeStatus,
            resume_learning_freeze_reason: learningFreezeReason,
            resume_learning_freeze_exit: learningFreezeExit,
            resume_learning_freeze_action: learningFreezeAction,
            resume_learning_freeze_codes_status: learningFreezeCodesSummary.status,
            resume_learning_freeze_codes: learningFreezeCodesSummary.joined,
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

        // PR229: Update recovery budget counters before execution (暴走防止)
        const HOUR_MS = 60 * 60 * 1000;
        const nowMsBudget = getNowMs();

        // Increment attempt count (always)
        const newAttemptCount = (state.resumeState?.recoveryAttemptCount || 0) + 1;

        // Window management (reset if > 1 hour old)
        const currentWindowAnchor = state.resumeState?.recoveryWindowAnchorTs || 0;
        const windowAge = currentWindowAnchor > 0 ? nowMsBudget - currentWindowAnchor : HOUR_MS + 1;
        const windowNeedsReset = windowAge > HOUR_MS;

        let newWindowAnchor = currentWindowAnchor;
        let newImmediateCount = state.resumeState?.recoveryImmediateCountInWindow || 0;
        let newFailedMarketCount = state.resumeState?.recoveryFailedMarketCountInWindow || 0;

        if (windowNeedsReset) {
          // Reset window (new 1-hour period)
          newWindowAnchor = nowMsBudget;
          newImmediateCount = 0;
          newFailedMarketCount = 0;
        }

        // Increment IMMEDIATE count if delayClass is IMMEDIATE
        if (resumeDelayClass === "IMMEDIATE") {
          newImmediateCount = newImmediateCount + 1;
        }

        // Increment FAILED_MARKET count if orchLastStatus is FAILED_MARKET
        if (state.resumeState?.orchLastStatus === "FAILED_MARKET") {
          newFailedMarketCount = newFailedMarketCount + 1;
        }

        // Update resumeState with new counters
        if (state.resumeState) {
          state.resumeState.recoveryAttemptCount = newAttemptCount;
          state.resumeState.recoveryWindowAnchorTs = newWindowAnchor;
          state.resumeState.recoveryImmediateCountInWindow = newImmediateCount;
          state.resumeState.recoveryFailedMarketCountInWindow = newFailedMarketCount;
          if (windowNeedsReset) {
            state.resumeState.recoveryWindowLastResetTs = nowMsBudget;
          }
        }

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
                // PR230a: Signal trust & consensus layer (Article XI)
                resume_signal_consensus: signalTruth?.consensus || "CONSENSUS_UNTRUSTED",
                resume_signal_consensus_codes_status: truthCodesSummary.status,
                resume_signal_consensus_codes: truthCodesSummary.joined,
                resume_signal_oracle_trust: signalTruth?.oracle_trust || "UNKNOWN",
                resume_signal_dex_trust: signalTruth?.dex_trust || "UNKNOWN",
                resume_signal_rpc_trust: signalTruth?.rpc_trust || "UNKNOWN",
                resume_signal_crosscheck_status: signalTruth?.crosscheck_status || "XCHK_UNKNOWN",
                // PR230b: Consensus → execution hard cap (NEVER LIVE)
                resume_signal_exec_cap_status: signalCapStatus,
                resume_signal_enforced_execution_mode: signalEnforcedMode || "NONE",
                resume_signal_enforced_codes_status: signalCapCodesSummary.status,
                resume_signal_enforced_codes: signalCapCodesSummary.joined,
                // PR231: Invariant Checks v1 (Final defensive layer)
                resume_invariant_status: invariantStatus,
                resume_invariant_failed_group: invariantFailedGroup || "NONE",
                resume_invariant_codes_status: invariantCodesSummary.status,
                resume_invariant_codes: invariantCodesSummary.joined,
                // PR232: Economic Safety Invariants v1 (LIVE capital safety)
                resume_einv_status: economicInvariantStatus,
                resume_einv_failed_group: economicInvariantFailedGroup || "NONE",
                resume_einv_action_override: economicActionOverride,
                resume_einv_codes_status: economicInvariantCodesSummary.status,
                resume_einv_codes: economicInvariantCodesSummary.joined,
                // PR233: Economic Risk Constraints v1 (Article XII)
                resume_econ_constraint_class: econConstraintClass,
                resume_econ_constraint_action: econConstraintAction,
                resume_econ_codes_status: econConstraintCodesSummary.status,
                resume_econ_codes: econConstraintCodesSummary.joined,
                // PR233a: Economic Risk Observability Pack v1 (telemetry-only)
                resume_econ_severity: econRiskSeverity,
                resume_econ_liquidity_class: econLiquidityCondition || "LIQ_UNKNOWN",
                resume_econ_slippage_class: econSlippageRisk || "SLIP_UNKNOWN",
                resume_econ_exposure_class: econExposureStatus || "EXP_UNKNOWN",
                resume_econ_drawdown_class: econDrawdownStatus || "DD_UNKNOWN",
                resume_econ_cooldown_status: econRiskCooldownStatus,
                resume_econ_window_status: econRiskWindowStatus,
                // PR233b: Economic execution shaping labels
                resume_econ_exec_size_cap: econSizeCap,
                resume_econ_exec_freq_cap: econFreqCap,
                resume_econ_capital_cap: econCapitalCap,
                resume_econ_exec_shape_status: econShapeStatus,
                resume_econ_exec_shape_codes_status: econShapeCodesSummary.status,
                resume_econ_exec_shape_codes: econShapeCodesSummary.joined,
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
                // PR230a: Signal trust & consensus layer (Article XI)
                resume_signal_consensus: signalTruth?.consensus || "CONSENSUS_UNTRUSTED",
                resume_signal_consensus_codes_status: truthCodesSummary.status,
                resume_signal_consensus_codes: truthCodesSummary.joined,
                resume_signal_oracle_trust: signalTruth?.oracle_trust || "UNKNOWN",
                resume_signal_dex_trust: signalTruth?.dex_trust || "UNKNOWN",
                resume_signal_rpc_trust: signalTruth?.rpc_trust || "UNKNOWN",
                resume_signal_crosscheck_status: signalTruth?.crosscheck_status || "XCHK_UNKNOWN",
                // PR230b: Consensus → execution hard cap (NEVER LIVE)
                resume_signal_exec_cap_status: signalCapStatus,
                resume_signal_enforced_execution_mode: signalEnforcedMode || "NONE",
                resume_signal_enforced_codes_status: signalCapCodesSummary.status,
                resume_signal_enforced_codes: signalCapCodesSummary.joined,
                // PR231: Invariant Checks v1 (Final defensive layer)
                resume_invariant_status: invariantStatus,
                resume_invariant_failed_group: invariantFailedGroup || "NONE",
                resume_invariant_codes_status: invariantCodesSummary.status,
                resume_invariant_codes: invariantCodesSummary.joined,
                // PR232: Economic Safety Invariants v1 (LIVE capital safety)
                resume_einv_status: economicInvariantStatus,
                resume_einv_failed_group: economicInvariantFailedGroup || "NONE",
                resume_einv_action_override: economicActionOverride,
                resume_einv_codes_status: economicInvariantCodesSummary.status,
                resume_einv_codes: economicInvariantCodesSummary.joined,
                // PR233: Economic Risk Constraints v1 (Article XII)
                resume_econ_constraint_class: econConstraintClass,
                resume_econ_constraint_action: econConstraintAction,
                resume_econ_codes_status: econConstraintCodesSummary.status,
                resume_econ_codes: econConstraintCodesSummary.joined,
                // PR233a: Economic Risk Observability Pack v1 (telemetry-only)
                resume_econ_severity: econRiskSeverity,
                resume_econ_liquidity_class: econLiquidityCondition || "LIQ_UNKNOWN",
                resume_econ_slippage_class: econSlippageRisk || "SLIP_UNKNOWN",
                resume_econ_exposure_class: econExposureStatus || "EXP_UNKNOWN",
                resume_econ_drawdown_class: econDrawdownStatus || "DD_UNKNOWN",
                resume_econ_cooldown_status: econRiskCooldownStatus,
                resume_econ_window_status: econRiskWindowStatus,
                // PR233b: Economic execution shaping labels
                resume_econ_exec_size_cap: econSizeCap,
                resume_econ_exec_freq_cap: econFreqCap,
                resume_econ_capital_cap: econCapitalCap,
                resume_econ_exec_shape_status: econShapeStatus,
                resume_econ_exec_shape_codes_status: econShapeCodesSummary.status,
                resume_econ_exec_shape_codes: econShapeCodesSummary.joined,
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
