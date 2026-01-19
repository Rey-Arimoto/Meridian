/**
 * PR159: v1.4 TWAP-lite Runner (READ-ONLY)
 * PR160: FAST Profile v1.1 - Updated timing parameters
 * PR161: Phase Re-eval STOP + Per-Chunk Route Reselect
 * PR162: Partial Resume Policy v1
 * PR164: Telemetry integration
 *
 * Purpose:
 *   Execute chunked rebalance plans with per-chunk refreshing of:
 *   - Portfolio snapshot
 *   - Oracle prices
 *   - Quotes
 *   - Gate checks (PR153/155/157/158)
 *   - Policy checks (PR156)
 *   - Phase evaluation (PR161) - STOP on dangerous escalation
 *   - Route selection (PR161) - Reselect venue per chunk
 *   - Resume evaluation (PR162) - Save/evaluate resume state on STOP
 *
 * Constitutional Constraints:
 *   - READ-ONLY: No learning, no optimization, no prediction
 *   - Double-key maintained: MERIDIAN_EXECUTION_ENABLED + HardStop (PR156)
 *   - Safe defaults: Uncertain → STOP
 *   - Label-only output: No numbers in reasons
 *   - Execution disabled by default: allowExecution via PolicyResult
 */

import {
  RunPlan,
  RunResult,
  ChunkResult,
  ChunkPlan,
  PortfolioSnapshot,
  TxDraft,
  ResumeState,
  StopReason,
  StopCause,
  ExecutionMode,
  LiveUnlockStatus,
  PhaseTransitionReasonCode,
  PhasePolicyInputsV1,
} from "./types";
import { CHUNKING_PARAMS } from "./chunking";
import {
  PhaseLabel,
  evaluatePhaseStopPolicyV1,
  getPhasePolicySummary,
  evaluatePhasePolicyV1,
} from "./phasePolicy";
import { createEventV1, appendEventV1 } from "../telemetry";
import {
  selectAndNormalizeQuote,
  type NormalizedQuoteV1,
  type QuoteSources,
  type TradeSide,
  sanitizeQuoteForLogs,
} from "../quoteNorm";

/**
 * Fixed runner parameters (constitutional constants)
 */
const RUNNER_PARAMS = {
  // Maximum consecutive BLOCK count before STOP
  MAX_BLOCKED_STREAK: 2,

  // Chunk interval (milliseconds)
  CHUNK_INTERVAL_MS: CHUNKING_PARAMS.CHUNK_INTERVAL_MS,

  // Maximum run duration (milliseconds)
  MAX_RUN_DURATION_MS: CHUNKING_PARAMS.MAX_RUN_DURATION_MS,

  // PR162: Blocked streak cooldown (milliseconds)
  BLOCKED_STREAK_COOLDOWN_MS: 30_000, // 30 seconds

  // PR162: Phase policy cooldown (milliseconds)
  PHASE_POLICY_COOLDOWN_MS: 10_000, // 10 seconds (FAST)
};

/**
 * PR192: Summarize execution reason codes for telemetry (label-only)
 *
 * @param codes - Array of reason code strings from TxDraft.executionReasonCodes
 * @param maxCodes - Maximum number of codes to include (default: 8)
 * @returns Summary object with status and joined string
 *
 * Purpose:
 *   Create deterministic, fixed-length summary of reason codes for CHUNK_RESULT telemetry.
 *   Ensures label-only, no numeric leakage, and consistent ordering.
 *
 * Rules:
 *   - Empty/undefined → {status: "EMPTY", joined: ""}
 *   - Filter to string-only values (defensive)
 *   - Deduplicate via Set
 *   - Sort alphabetically (deterministic ordering)
 *   - Take first maxCodes items
 *   - If truncated, append "REASONS_TRUNCATED"
 *   - Join with "|" separator
 *
 * Examples:
 *   - [] → {status: "EMPTY", joined: ""}
 *   - ["REASON_A", "REASON_B"] → {status: "PRESENT", joined: "REASON_A|REASON_B"}
 *   - 10 codes with maxCodes=8 → {status: "PRESENT", joined: "REASON_A|...|REASON_H|REASONS_TRUNCATED"}
 *
 * Constitutional: READ-ONLY, defensive (never throws)
 */
export function summarizeReasonCodesV1(
  codes?: string[],
  maxCodes = 8
): { status: "PRESENT" | "EMPTY"; joined: string } {
  try {
    // Empty/undefined → EMPTY
    if (!codes || codes.length === 0) {
      return { status: "EMPTY", joined: "" };
    }

    // Filter to strings only (defensive)
    const stringCodes = codes.filter((c) => typeof c === "string");
    if (stringCodes.length === 0) {
      return { status: "EMPTY", joined: "" };
    }

    // Deduplicate via Set
    const uniqueCodes = Array.from(new Set(stringCodes));

    // Sort alphabetically (deterministic ordering)
    uniqueCodes.sort();

    // Take first maxCodes items
    let selectedCodes = uniqueCodes.slice(0, maxCodes);

    // If truncated, append REASONS_TRUNCATED
    if (uniqueCodes.length > maxCodes) {
      selectedCodes.push("REASONS_TRUNCATED");
    }

    // Join with "|" separator
    const joined = selectedCodes.join("|");

    return { status: "PRESENT", joined };
  } catch (error) {
    // Defensive: Never throw, return EMPTY
    return { status: "EMPTY", joined: "" };
  }
}

/**
 * PR193: Summarize run-level reason codes for RUN_STOP telemetry (label-only)
 *
 * @param codes - Array of reason code strings from last chunk's executionReasonCodes
 * @param maxCodes - Maximum number of codes to include (default: 8)
 * @returns Summary object with status and joined string
 *
 * Purpose:
 *   Create deterministic summary of run-level reason codes for RUN_STOP telemetry.
 *   Uses last non-empty executionReasonCodes as source of truth for run outcome.
 *
 * Rules:
 *   - Same as summarizeReasonCodesV1 but for run-level
 *   - Empty/undefined → {status: "EMPTY", joined: ""}
 *   - Filter to strings (defensive)
 *   - Deduplicate via Set
 *   - Sort alphabetically (deterministic)
 *   - Take first maxCodes items
 *   - If truncated, append "REASONS_TRUNCATED"
 *   - Join with "|" separator
 *
 * Constitutional: READ-ONLY, defensive (never throws)
 */
export function summarizeRunReasonCodesV1(
  codes?: unknown[],
  maxCodes = 8
): { status: "PRESENT" | "EMPTY"; joined: string } {
  try {
    // Empty/undefined → EMPTY
    if (!Array.isArray(codes)) {
      return { status: "EMPTY", joined: "" };
    }

    // Filter to strings only (defensive)
    const filtered = codes.filter((c) => typeof c === "string") as string[];
    if (filtered.length === 0) {
      return { status: "EMPTY", joined: "" };
    }

    // Deduplicate via Set
    const unique = Array.from(new Set(filtered));

    // Sort alphabetically (deterministic)
    unique.sort();

    // Take first maxCodes items
    const sliced = unique.slice(0, maxCodes);

    // If truncated, append REASONS_TRUNCATED
    if (unique.length > maxCodes) {
      sliced.push("REASONS_TRUNCATED");
    }

    // Join with "|" separator
    const joined = sliced.join("|");

    return { status: "PRESENT", joined };
  } catch (error) {
    // Defensive: Never throw, return EMPTY
    return { status: "EMPTY", joined: "" };
  }
}

/**
 * PR210: Compute reason code diff between origin and current (label-only, defensive)
 *
 * @param args.originCodes - Origin reason codes (from resumeState)
 * @param args.currentCodes - Current reason codes (at run start)
 * @param args.maxCodes - Max codes to include (default 8)
 * @returns Resolved and introduced reason code summaries
 *
 * Constitutional: READ-ONLY, defensive (never throws), label-only, deterministic
 */
export function summarizeReasonDiffV1(args: {
  originCodes?: unknown[];
  currentCodes?: unknown[];
  maxCodes?: number;
}): {
  resolved: { status: "PRESENT" | "EMPTY"; joined: string };
  introduced: { status: "PRESENT" | "EMPTY"; joined: string };
} {
  try {
    const maxCodes = args.maxCodes ?? 8;

    // Defensive: filter to string-only sets
    const originSet = new Set<string>(
      Array.isArray(args.originCodes)
        ? (args.originCodes.filter((c) => typeof c === "string") as string[])
        : []
    );
    const currentSet = new Set<string>(
      Array.isArray(args.currentCodes)
        ? (args.currentCodes.filter((c) => typeof c === "string") as string[])
        : []
    );

    // Compute diffs
    // resolved = origin - current (codes that were in origin but not in current)
    const resolvedCodes = Array.from(originSet).filter((c) => !currentSet.has(c));
    // introduced = current - origin (codes in current but not in origin)
    const introducedCodes = Array.from(currentSet).filter((c) => !originSet.has(c));

    // Format resolved
    let resolvedSummary: { status: "PRESENT" | "EMPTY"; joined: string };
    if (resolvedCodes.length === 0) {
      resolvedSummary = { status: "EMPTY", joined: "" };
    } else {
      const sortedResolved = resolvedCodes.sort();
      const slicedResolved = sortedResolved.slice(0, maxCodes);
      if (sortedResolved.length > maxCodes) {
        slicedResolved.push("REASONS_TRUNCATED");
      }
      resolvedSummary = { status: "PRESENT", joined: slicedResolved.join("|") };
    }

    // Format introduced
    let introducedSummary: { status: "PRESENT" | "EMPTY"; joined: string };
    if (introducedCodes.length === 0) {
      introducedSummary = { status: "EMPTY", joined: "" };
    } else {
      const sortedIntroduced = introducedCodes.sort();
      const slicedIntroduced = sortedIntroduced.slice(0, maxCodes);
      if (sortedIntroduced.length > maxCodes) {
        slicedIntroduced.push("REASONS_TRUNCATED");
      }
      introducedSummary = { status: "PRESENT", joined: slicedIntroduced.join("|") };
    }

    return { resolved: resolvedSummary, introduced: introducedSummary };
  } catch (error) {
    // Defensive: Never throw, return EMPTY for both
    return {
      resolved: { status: "EMPTY", joined: "" },
      introduced: { status: "EMPTY", joined: "" },
    };
  }
}

/**
 * PR211: Summarize phase transition codes (label-only, defensive)
 *
 * @param codes - Phase transition reason codes (PHASE_TXN_* / PHASE_TRIG_*)
 * @param maxCodes - Max codes to include (default 8)
 * @returns Summary with status and joined string
 *
 * Constitutional: READ-ONLY, defensive (never throws), label-only, deterministic
 */
export function summarizePhaseTransitionCodesV1(
  codes?: unknown[],
  maxCodes = 8
): { status: "PRESENT" | "EMPTY"; joined: string } {
  try {
    // Empty/undefined → EMPTY
    if (!Array.isArray(codes)) {
      return { status: "EMPTY", joined: "" };
    }

    // Filter to strings only (defensive)
    const filtered = codes.filter((c) => typeof c === "string") as string[];
    if (filtered.length === 0) {
      return { status: "EMPTY", joined: "" };
    }

    // Deduplicate via Set
    const unique = Array.from(new Set(filtered));

    // Sort alphabetically (deterministic)
    unique.sort();

    // Take first maxCodes items
    const sliced = unique.slice(0, maxCodes);

    // If truncated, append REASONS_TRUNCATED
    if (unique.length > maxCodes) {
      sliced.push("REASONS_TRUNCATED");
    }

    // Join with "|" separator
    const joined = sliced.join("|");

    return { status: "PRESENT", joined };
  } catch (error) {
    // Defensive: Never throw, return EMPTY
    return { status: "EMPTY", joined: "" };
  }
}

/**
 * PR199: Derive LIVE unlock status from execution mode, env flag, and spec lock
 *
 * @param args.executionMode - Current execution mode
 * @param args.specLockStatus - Spec lock status from evaluateSpecLockV1 (optional)
 * @param args.envUnlock - Whether MERIDIAN_LIVE_UNLOCK env is TRUE
 * @returns LiveUnlockStatus (label-only, deterministic)
 *
 * Constitutional: READ-ONLY, defensive (never throws)
 */
export function deriveLiveUnlockStatusV1(args: {
  executionMode: ExecutionMode;
  specLockStatus?: string;
  envUnlock?: boolean;
}): LiveUnlockStatus {
  try {
    // If not LIVE mode, return LOCKED_UNKNOWN (not applicable)
    if (args.executionMode !== "LIVE") {
      return "LOCKED_UNKNOWN";
    }

    // Check env flag first
    if (args.envUnlock !== true) {
      return "LOCKED_ENV";
    }

    // Check spec lock status
    const specStatus = args.specLockStatus || "UNKNOWN";
    if (specStatus === "ACTIVE_OK") {
      return "UNLOCKED";
    } else if (specStatus === "LOCKED_EXPIRED") {
      return "LOCKED_SPEC_EXPIRED";
    } else if (specStatus === "LOCKED_PENDING_ACK") {
      return "LOCKED_SPEC_PENDING_ACK";
    } else {
      return "LOCKED_SPEC";
    }
  } catch (error) {
    // Defensive: Never throw
    return "LOCKED_UNKNOWN";
  }
}

/**
 * Gate result (simplified for runner)
 * PR204: Added reasonCodes for market safety explainability
 */
export interface GateResultSimple {
  status: "PASS" | "BLOCK" | "ERROR";
  blockReasons: string[]; // legacy
  reasonCodes?: import("./types").GateReasonCode[]; // PR204: normalized safety reasons
  warnings: string[];
}

/**
 * Policy result (simplified for runner)
 * PR205: Added reasonCodes and hardStopActive for constitutional explainability
 */
export interface PolicyResultSimple {
  allowExecution: boolean;
  hardStopActive?: boolean; // PR205: HardStop flag
  status: "ALLOW" | "SIM_ONLY" | "BLOCKED" | "ERROR";
  reasons: string[]; // legacy
  reasonCodes?: import("./types").PolicyReasonCode[]; // PR205: normalized policy reasons
}

/**
 * Execution result (simplified for runner)
 */
export interface ExecutionResultSimple {
  status: "EXECUTED" | "SIMULATED" | "DRY_RUN" | "EXECUTION_DISABLED" | "ERROR";
  reasons: string[];
  txDigest?: string;
}

/**
 * Runner dependencies (for testing/DI)
 */
export interface RunnerDeps {
  // Get current timestamp
  getNowMs?: () => number;

  // Sleep function (for chunk interval)
  sleepMs?: (ms: number) => Promise<void>;

  // Get portfolio snapshot (refreshed per chunk)
  getPortfolioSnapshot: () => Promise<PortfolioSnapshot>;

  // PR161: Get current phase label (refreshed per chunk)
  getPhaseLabel?: () => Promise<PhaseLabel>;

  // PR161: Select route (refreshed per chunk)
  selectRoute?: (args: {
    chunkPlan: ChunkPlan;
    portfolio: PortfolioSnapshot;
  }) => Promise<{
    venue: "CETUS" | "DEEPBOOK" | "NONE";
    reasons: string[];
  }>;

  // PR184: Get observe state (refreshed per chunk)
  getObserveState?: () => Promise<any>;

  // PR187: Get quote sources (refreshed per chunk)
  getQuoteSources?: (args: {
    chunkPlan: ChunkPlan;
    portfolio: PortfolioSnapshot;
  }) => Promise<QuoteSources>;

  // Evaluate gate (PR153/155/157/158/184)
  evaluateGate: (args: {
    chunkPlan: ChunkPlan;
    portfolio: PortfolioSnapshot;
    observeDegradeLevel?: string;
  }) => Promise<GateResultSimple>;

  // Evaluate policy (PR156)
  evaluatePolicy: (args: {
    portfolio: PortfolioSnapshot;
  }) => Promise<PolicyResultSimple>;

  // Build transaction draft (PR186/PR187: enhanced with context and normalized quote)
  buildTxDraft: (args: {
    chunkPlan: ChunkPlan;
    portfolio: PortfolioSnapshot;
    venue?: "CETUS" | "DEEPBOOK" | "NONE"; // PR161/PR186: route venue
    phaseLabel?: string; // PR161/PR186: phase label
    stressLabel?: string; // PR186: stress label
    impactLabel?: string; // PR186: impact label (from normalizedQuote)
    observeDegradeLevel?: string; // PR184/PR186: observe degrade level
    normalizedQuote?: NormalizedQuoteV1; // PR187: normalized quote for minOut calculation
  }) => Promise<TxDraft>;

  // Execute transaction (PR197: executionMode added)
  executeTx: (args: {
    txDraft: TxDraft;
    policy: PolicyResultSimple;
    executionMode: ExecutionMode; // PR197: Mode-aware execution
  }) => Promise<ExecutionResultSimple>;

  // PR199: Get spec lock status (optional for LIVE unlock handshake)
  getSpecLockStatus?: () => Promise<{
    status: string;
    activeSpec?: string;
    latestSpec?: string;
    warnings?: string[];
  }>;
}

/**
 * PR162/PR209: Create resume state (helper for STOP scenarios)
 *
 * @param stopReason - Stop reason (label-only)
 * @param nowMs - Current timestamp (internal numeric only)
 * @param runPlan - Run plan (for observability metadata)
 * @param lastPhase - Last phase label (optional, label-only)
 * @param lastRoute - Last route (optional, label-only)
 * @param warnings - Warnings (optional, label-only)
 * @param originStopCause - PR209: Origin stop cause for resume traceability (optional)
 * @param originRunReasonCodes - PR209: Origin run reason codes for resume traceability (optional)
 * @returns Resume state
 */
function createResumeState(
  stopReason: StopReason,
  nowMs: number,
  runPlan: RunPlan,
  lastPhase?: string,
  lastRoute?: string,
  warnings: string[] = [],
  originStopCause?: StopCause,
  originRunReasonCodes?: string[]
): ResumeState {
  const state: ResumeState = {
    status: "STOPPED",
    stopReason,
    stopAtTs: nowMs,
    lastPhaseLabel: lastPhase,
    lastRoute,
    lastTemplateId: runPlan.templateId,
    lastIntent: runPlan.chunks[0]?.intent, // Use first chunk intent
    warnings,
    // PR209: Resume origin context (defensive defaults)
    originStopCause: originStopCause ?? "NONE",
    originRunReasonCodes: originRunReasonCodes ?? [],
  };

  // Add resumeAfterTs for specific stop reasons
  if (stopReason === "STOP_BLOCKED_STREAK") {
    state.resumeAfterTs = nowMs + RUNNER_PARAMS.BLOCKED_STREAK_COOLDOWN_MS;
  } else if (stopReason === "STOP_PHASE_POLICY") {
    state.resumeAfterTs = nowMs + RUNNER_PARAMS.PHASE_POLICY_COOLDOWN_MS;
  }

  return state;
}

/**
 * PR200: LIVE block stop reason code constant
 * Used to track LIVE mode blocks in run-level reason codes
 */
const LIVE_BLOCK_STOP_REASON = "REASON_LIVE_MODE_BLOCKED_STOP";

/**
 * PR201: LIVE block detailed reason code constants
 * Track specific causes of LIVE mode blocks in run-level reason codes
 */
const LIVE_BLOCK_ENV_REASON = "REASON_LIVE_UNLOCK_LOCKED_ENV";
const LIVE_BLOCK_SPEC_REASON = "REASON_LIVE_UNLOCK_LOCKED_SPEC";
const LIVE_BLOCK_SPEC_EXPIRED_REASON = "REASON_LIVE_UNLOCK_LOCKED_SPEC_EXPIRED";
const LIVE_BLOCK_SPEC_PENDING_REASON = "REASON_LIVE_UNLOCK_LOCKED_SPEC_PENDING_ACK";
const LIVE_BLOCK_UNKNOWN_REASON = "REASON_LIVE_UNLOCK_LOCKED_UNKNOWN";
const LIVE_BLOCK_POLICY_REASON = "REASON_LIVE_POLICY_NOT_ALLOW";

/**
 * PR203: RUN_REASON_* taxonomy constants for run-level stop causes
 * Normalized taxonomy with legacy REASON_* preserved for backward compatibility
 */
const RUN_LIVE_BLOCK_STOP_REASON = "RUN_REASON_LIVE_MODE_BLOCKED_STOP";
const RUN_LIVE_BLOCK_ENV_REASON = "RUN_REASON_LIVE_UNLOCK_LOCKED_ENV";
const RUN_LIVE_BLOCK_SPEC_REASON = "RUN_REASON_LIVE_UNLOCK_LOCKED_SPEC";
const RUN_LIVE_BLOCK_SPEC_EXPIRED_REASON = "RUN_REASON_LIVE_UNLOCK_LOCKED_SPEC_EXPIRED";
const RUN_LIVE_BLOCK_SPEC_PENDING_REASON = "RUN_REASON_LIVE_UNLOCK_LOCKED_SPEC_PENDING_ACK";
const RUN_LIVE_BLOCK_UNKNOWN_REASON = "RUN_REASON_LIVE_UNLOCK_LOCKED_UNKNOWN";
const RUN_LIVE_BLOCK_POLICY_REASON = "RUN_REASON_LIVE_POLICY_NOT_ALLOW";

/**
 * PR206: Phase/Timeout/Streak STOP reason code constants
 * Track run-level STOP causes for Phase escalation, Timeout, and Blocked Streak
 */
const RUN_PHASE_ESCALATION_STOP = "RUN_PHASE_ESCALATION_STOP";
const RUN_PHASE_DOWN_SHOCK = "RUN_PHASE_DOWN_SHOCK";
const RUN_PHASE_UP_REVERSAL = "RUN_PHASE_UP_REVERSAL";
const RUN_TIMEOUT_STOP = "RUN_TIMEOUT_STOP";
const RUN_BLOCKED_STREAK_STOP = "RUN_BLOCKED_STREAK_STOP";

/**
 * PR210: Resume re-execution start context reason codes
 * Used to build "current" reason set at RUN_START for diff computation
 */
const RUN_REASON_RESUME_REEXEC_START = "RUN_REASON_RESUME_REEXEC_START";
const RUN_REASON_EXEC_MODE_SIM_ONLY = "RUN_REASON_EXEC_MODE_SIM_ONLY";
const RUN_REASON_EXEC_MODE_DRY_RUN = "RUN_REASON_EXEC_MODE_DRY_RUN";
const RUN_REASON_EXEC_MODE_LIVE = "RUN_REASON_EXEC_MODE_LIVE";
const RUN_REASON_RESUME_FROM_GATE = "RUN_REASON_RESUME_FROM_GATE";
const RUN_REASON_RESUME_FROM_POLICY = "RUN_REASON_RESUME_FROM_POLICY";
const RUN_REASON_RESUME_FROM_PHASE = "RUN_REASON_RESUME_FROM_PHASE";
const RUN_REASON_RESUME_FROM_TIMEOUT = "RUN_REASON_RESUME_FROM_TIMEOUT";
const RUN_REASON_RESUME_FROM_NONE = "RUN_REASON_RESUME_FROM_NONE";
const RUN_REASON_LIVE_UNLOCK_UNLOCKED = "RUN_REASON_LIVE_UNLOCK_UNLOCKED";
const RUN_REASON_LIVE_UNLOCK_LOCKED_ENV = "RUN_REASON_LIVE_UNLOCK_LOCKED_ENV";
const RUN_REASON_LIVE_UNLOCK_LOCKED_SPEC = "RUN_REASON_LIVE_UNLOCK_LOCKED_SPEC";
const RUN_REASON_LIVE_UNLOCK_LOCKED_SPEC_EXPIRED = "RUN_REASON_LIVE_UNLOCK_LOCKED_SPEC_EXPIRED";
const RUN_REASON_LIVE_UNLOCK_LOCKED_SPEC_PENDING_ACK = "RUN_REASON_LIVE_UNLOCK_LOCKED_SPEC_PENDING_ACK";
const RUN_REASON_LIVE_UNLOCK_LOCKED_UNKNOWN = "RUN_REASON_LIVE_UNLOCK_LOCKED_UNKNOWN";

/**
 * PR212b: Phase policy STOP causality reason codes
 * Used to track PhasePolicy→Runner STOP parity for audit-grade telemetry
 */
const RUN_PHASE_POLICY_SHOULD_STOP = "RUN_PHASE_POLICY_SHOULD_STOP";
const RUN_PHASE_POLICY_STOP_CAUSE_PHASE = "RUN_PHASE_POLICY_STOP_CAUSE_PHASE";
const RUN_PHASE_POLICY_STOP_CAUSE_TIMEOUT = "RUN_PHASE_POLICY_STOP_CAUSE_TIMEOUT";
const RUN_PHASE_POLICY_STOP_CAUSE_GATE = "RUN_PHASE_POLICY_STOP_CAUSE_GATE";
const RUN_PHASE_POLICY_STOP_CAUSE_POLICY = "RUN_PHASE_POLICY_STOP_CAUSE_POLICY";
const RUN_PHASE_POLICY_STOP_CAUSE_NONE = "RUN_PHASE_POLICY_STOP_CAUSE_NONE";

/**
 * PR211: Phase transition reason code constants
 * Used for tracking phase transitions in chunk-level and run-level telemetry
 */
// Transition types (state machine edges)
const PHASE_TXN_NORMAL_TO_RANGE: PhaseTransitionReasonCode = "PHASE_TXN_NORMAL_TO_RANGE";
const PHASE_TXN_RANGE_TO_DOWN_SHOCK: PhaseTransitionReasonCode = "PHASE_TXN_RANGE_TO_DOWN_SHOCK";
const PHASE_TXN_RANGE_TO_UP_REVERSAL: PhaseTransitionReasonCode = "PHASE_TXN_RANGE_TO_UP_REVERSAL";
const PHASE_TXN_DOWN_SHOCK_TO_RANGE: PhaseTransitionReasonCode = "PHASE_TXN_DOWN_SHOCK_TO_RANGE";
const PHASE_TXN_UP_REVERSAL_TO_RANGE: PhaseTransitionReasonCode = "PHASE_TXN_UP_REVERSAL_TO_RANGE";
const PHASE_TXN_UNKNOWN: PhaseTransitionReasonCode = "PHASE_TXN_UNKNOWN";

// Trigger categories (root causes)
const PHASE_TRIG_GATE_BLOCK: PhaseTransitionReasonCode = "PHASE_TRIG_GATE_BLOCK";
const PHASE_TRIG_POLICY_HARDSTOP: PhaseTransitionReasonCode = "PHASE_TRIG_POLICY_HARDSTOP";
const PHASE_TRIG_QUOTE_IMPACT_ELEVATED: PhaseTransitionReasonCode = "PHASE_TRIG_QUOTE_IMPACT_ELEVATED";
const PHASE_TRIG_SLIPPAGE_ELEVATED: PhaseTransitionReasonCode = "PHASE_TRIG_SLIPPAGE_ELEVATED";
const PHASE_TRIG_MINOUT_ZERO: PhaseTransitionReasonCode = "PHASE_TRIG_MINOUT_ZERO";
const PHASE_TRIG_MINOUT_UNAVAILABLE: PhaseTransitionReasonCode = "PHASE_TRIG_MINOUT_UNAVAILABLE";
const PHASE_TRIG_EXEC_ERROR: PhaseTransitionReasonCode = "PHASE_TRIG_EXEC_ERROR";
const PHASE_TRIG_EXEC_DISABLED: PhaseTransitionReasonCode = "PHASE_TRIG_EXEC_DISABLED";
const PHASE_TRIG_TIMEOUT_PRESSURE: PhaseTransitionReasonCode = "PHASE_TRIG_TIMEOUT_PRESSURE";
const PHASE_TRIG_UNKNOWN: PhaseTransitionReasonCode = "PHASE_TRIG_UNKNOWN";

/**
 * Run chunked execution (TWAP-lite v1)
 *
 * @param runPlan - Run plan from buildChunkPlansV1
 * @param deps - Dependencies (for testing/DI)
 * @returns Run result
 *
 * Execution Rules (fixed):
 *   1. For each chunk:
 *      a. Refresh portfolio/oracle
 *      b. Evaluate gate
 *      c. Evaluate policy
 *      d. Build tx draft
 *      e. Execute/simulate
 *   2. STOP conditions (safe defaults):
 *      - Policy denies execution (env key missing or HardStop active)
 *      - Gate blocks with critical reasons (ORACLE_*, IMPACT_HIGH, QUOTE_INCONSISTENT, NOTIONAL_UNAVAILABLE)
 *      - Consecutive BLOCK count >= MAX_BLOCKED_STREAK (2)
 *      - Run duration exceeds MAX_RUN_DURATION_MS (10 min)
 *   3. SKIP conditions (continue to next chunk):
 *      - BLOCK_DELTA_TOO_SMALL / BLOCK_DRIFT_TOO_SMALL (micro-changes)
 *   4. Chunk interval: CHUNK_INTERVAL_MS (30s) between chunks
 *
 * IMPORTANT: Never throws, always returns RunResult (defensive)
 */
export async function runChunkedExecutionV1(
  runPlan: RunPlan,
  deps: RunnerDeps
): Promise<RunResult> {
  const getNowMs = deps.getNowMs || (() => Date.now());
  const sleepMs =
    deps.sleepMs || ((ms: number) => new Promise((resolve) => setTimeout(resolve, ms)));

  const startedAtMs = getNowMs();
  const reasons: string[] = [];
  const chunkResults: ChunkResult[] = [];

  // PR196: Execution mode (default: SIM_ONLY for safety)
  const executionMode: ExecutionMode = runPlan.executionMode ?? "SIM_ONLY";

  // PR199: LIVE unlock handshake (env flag + spec lock)
  const envUnlock = process.env.MERIDIAN_LIVE_UNLOCK === "TRUE";
  let specLockStatus: string = "UNKNOWN";
  if (deps.getSpecLockStatus) {
    try {
      const specLock = await deps.getSpecLockStatus();
      specLockStatus = specLock.status || "UNKNOWN";
    } catch (error) {
      specLockStatus = "ERROR";
    }
  }
  const liveUnlockStatus = deriveLiveUnlockStatusV1({
    executionMode,
    specLockStatus,
    envUnlock,
  });

  // PR188c/PR196/PR199/PR208: Emit RUN_START lifecycle event
  const runStartLabels: Record<string, string> = {
    run_id: runPlan.runId,
    template_id: runPlan.templateId,
    total_chunks: `${runPlan.chunks.length}`,
    execution_mode: executionMode, // PR196
    live_unlock_status: liveUnlockStatus, // PR199
  };

  // PR208: Add resume link labels (if resume re-execution)
  if (runPlan.resumeId) {
    runStartLabels.resume_id = runPlan.resumeId;
  }
  if (runPlan.previousRunId) {
    runStartLabels.previous_run_id = runPlan.previousRunId;
  }
  if (runPlan.resumeStopReason) {
    runStartLabels.resume_stop_reason = runPlan.resumeStopReason;
  }

  // PR209: Add resume origin labels (if origin context present)
  if (runPlan.resumeOriginStopCause) {
    runStartLabels.resume_origin_stop_cause = runPlan.resumeOriginStopCause;
  }
  if (runPlan.resumeOriginRunReasonCodes) {
    const originSummary = summarizeRunReasonCodesV1(runPlan.resumeOriginRunReasonCodes);
    runStartLabels.resume_origin_reason_codes_status = originSummary.status;
    runStartLabels.resume_origin_reason_codes = originSummary.joined;
  }

  // PR213: Add resume strategy labels (if strategy present)
  if (runPlan.resumeStrategy) {
    runStartLabels.resume_strategy = runPlan.resumeStrategy;
  }
  if (runPlan.resumeStrategyCodes) {
    const strategySummary = summarizeRunReasonCodesV1(runPlan.resumeStrategyCodes);
    runStartLabels.resume_strategy_codes_status = strategySummary.status;
    runStartLabels.resume_strategy_codes = strategySummary.joined;
  }

  // PR214: Add resume enforcement labels (if enforcement present)
  if (runPlan.resumeStrategyEnforcedExecutionMode) {
    runStartLabels.resume_enforced_execution_mode = runPlan.resumeStrategyEnforcedExecutionMode;
  }
  if (runPlan.resumeStrategyEnforcedCodes) {
    const enforcedSummary = summarizeRunReasonCodesV1(runPlan.resumeStrategyEnforcedCodes);
    runStartLabels.resume_enforced_codes_status = enforcedSummary.status;
    runStartLabels.resume_enforced_codes = enforcedSummary.joined;
  }

  // PR215: Add resume timing labels (if timing control present)
  if (runPlan.resumeDelayClassV1) {
    runStartLabels.resume_delay_class = runPlan.resumeDelayClassV1;
  }
  if (runPlan.resumeDelayOffsetLabelV1) {
    runStartLabels.resume_delay_offset_label = runPlan.resumeDelayOffsetLabelV1;
  }
  if (runPlan.resumeDelayReasonCodesV1) {
    const timingSummary = summarizeRunReasonCodesV1(runPlan.resumeDelayReasonCodesV1);
    runStartLabels.resume_timing_codes_status = timingSummary.status;
    runStartLabels.resume_timing_codes = timingSummary.joined;
  }

  // PR219: Add resume escalation labels (if escalation present)
  if (runPlan.resumeEscalatedStrategy) {
    runStartLabels.resume_escalated_strategy = runPlan.resumeEscalatedStrategy;
  }
  if (runPlan.resumeEscalationCodes) {
    const escalationSummary = summarizeRunReasonCodesV1(runPlan.resumeEscalationCodes);
    runStartLabels.resume_escalation_codes_status = escalationSummary.status;
    runStartLabels.resume_escalation_codes = escalationSummary.joined;
  }

  // PR220: Add resume regime/matrix labels (if regime present)
  if (runPlan.resumeMarketRegime) {
    runStartLabels.resume_market_regime = runPlan.resumeMarketRegime;
  }
  if (runPlan.resumeMarketRegimeCodes) {
    const regimeSummary = summarizeRunReasonCodesV1(runPlan.resumeMarketRegimeCodes);
    runStartLabels.resume_market_regime_codes_status = regimeSummary.status;
    runStartLabels.resume_market_regime_codes = regimeSummary.joined;
  }
  if (runPlan.resumeMatrixStrategy) {
    runStartLabels.resume_matrix_strategy = runPlan.resumeMatrixStrategy;
  }
  if (runPlan.resumeMatrixCodes) {
    const matrixSummary = summarizeRunReasonCodesV1(runPlan.resumeMatrixCodes);
    runStartLabels.resume_matrix_codes_status = matrixSummary.status;
    runStartLabels.resume_matrix_codes = matrixSummary.joined;
  }

  // PR210: Add resume diff labels (origin vs current start context)
  if (runPlan.resumeOriginRunReasonCodes) {
    // Build "current" start context reasons (deterministic, label-only)
    const currentStartReasons: string[] = [];

    // Always add resume re-exec marker
    currentStartReasons.push(RUN_REASON_RESUME_REEXEC_START);

    // Add execution mode reason
    if (executionMode === "SIM_ONLY") {
      currentStartReasons.push(RUN_REASON_EXEC_MODE_SIM_ONLY);
    } else if (executionMode === "DRY_RUN") {
      currentStartReasons.push(RUN_REASON_EXEC_MODE_DRY_RUN);
    } else if (executionMode === "LIVE") {
      currentStartReasons.push(RUN_REASON_EXEC_MODE_LIVE);
    }

    // Add LIVE unlock status reason (if LIVE mode)
    if (executionMode === "LIVE") {
      if (liveUnlockStatus === "UNLOCKED") {
        currentStartReasons.push(RUN_REASON_LIVE_UNLOCK_UNLOCKED);
      } else if (liveUnlockStatus === "LOCKED_ENV") {
        currentStartReasons.push(RUN_REASON_LIVE_UNLOCK_LOCKED_ENV);
      } else if (liveUnlockStatus === "LOCKED_SPEC") {
        currentStartReasons.push(RUN_REASON_LIVE_UNLOCK_LOCKED_SPEC);
      } else if (liveUnlockStatus === "LOCKED_SPEC_EXPIRED") {
        currentStartReasons.push(RUN_REASON_LIVE_UNLOCK_LOCKED_SPEC_EXPIRED);
      } else if (liveUnlockStatus === "LOCKED_SPEC_PENDING_ACK") {
        currentStartReasons.push(RUN_REASON_LIVE_UNLOCK_LOCKED_SPEC_PENDING_ACK);
      } else if (liveUnlockStatus === "LOCKED_UNKNOWN") {
        currentStartReasons.push(RUN_REASON_LIVE_UNLOCK_LOCKED_UNKNOWN);
      }
    }

    // Add resume-from reason (origin stop cause)
    if (runPlan.resumeOriginStopCause) {
      if (runPlan.resumeOriginStopCause === "GATE") {
        currentStartReasons.push(RUN_REASON_RESUME_FROM_GATE);
      } else if (runPlan.resumeOriginStopCause === "POLICY") {
        currentStartReasons.push(RUN_REASON_RESUME_FROM_POLICY);
      } else if (runPlan.resumeOriginStopCause === "PHASE") {
        currentStartReasons.push(RUN_REASON_RESUME_FROM_PHASE);
      } else if (runPlan.resumeOriginStopCause === "TIMEOUT") {
        currentStartReasons.push(RUN_REASON_RESUME_FROM_TIMEOUT);
      } else if (runPlan.resumeOriginStopCause === "NONE") {
        currentStartReasons.push(RUN_REASON_RESUME_FROM_NONE);
      }
    }

    // Compute diff: origin vs current start context
    const diff = summarizeReasonDiffV1({
      originCodes: runPlan.resumeOriginRunReasonCodes,
      currentCodes: currentStartReasons,
    });

    // Add diff labels
    runStartLabels.resume_resolved_reason_codes_status = diff.resolved.status;
    runStartLabels.resume_resolved_reason_codes = diff.resolved.joined;
    runStartLabels.resume_introduced_reason_codes_status = diff.introduced.status;
    runStartLabels.resume_introduced_reason_codes = diff.introduced.joined;
  }

  await appendEventV1(
    createEventV1("RUN_START", "INFO", runStartLabels)
  ).catch(() => {}); // Defensive: Don't fail on telemetry error

  let consecutiveBlockCount = 0;
  let finalStatus: "COMPLETED" | "STOPPED" | "ERROR" = "ERROR"; // Default to ERROR

  // PR188d: Track chunk outcome counters
  let executedCount = 0;
  let simulatedCount = 0;
  let chunkResultCount = 0;

  // PR189: Track stop attribution
  let stopCause: "GATE" | "POLICY" | "PHASE" | "TIMEOUT" | "NONE" = "NONE";

  // PR193: Track last non-empty reason codes for RUN_STOP summary
  let lastChunkReasonCodes: string[] | undefined = undefined;

  // PR200: Track run-level reason codes (LIVE blocks, etc.)
  const runLevelReasonCodes = new Set<string>();

  // PR211: Track phase transitions
  let prevPhase: PhaseLabel = "PHASE_UNKNOWN"; // Track previous phase for transition detection
  let phaseTransitionCodes: PhaseTransitionReasonCode[] = []; // Transition codes for current chunk

  try {
    // Check if run plan has no chunks
    if (runPlan.chunks.length === 0) {
      reasons.push("REASON_NO_CHUNKS_TO_EXECUTE");
      finalStatus = "COMPLETED";

      return {
        runId: runPlan.runId,
        status: "COMPLETED",
        reasons,
        chunkResults: [],
        startedAtMs,
        finishedAtMs: getNowMs(),
      };
    }

    reasons.push("REASON_CHUNKED_EXECUTION_STARTED");

    // PR161: Track phase across chunks
    let prevPhase: PhaseLabel | undefined = undefined;
    let prevRoute: "CETUS" | "DEEPBOOK" | "NONE" | undefined = undefined;

    // Execute each chunk
    for (let i = 0; i < runPlan.chunks.length; i++) {
      const chunk = runPlan.chunks[i];
      const isFirstChunk = i === 0;
      const isLastChunk = i === runPlan.chunks.length - 1;

      // PR189: Track gate/policy status for telemetry
      let gateStatus: "PASS" | "BLOCK" | "ERROR" = "ERROR";
      let policyStatus: "ALLOW" | "SIM_ONLY" | "BLOCKED" | "ERROR" = "ERROR";

      // PR190: Track quote → slippage → minOut traceability
      let quoteImpactLabel: string = "IMPACT_UNKNOWN";
      let slippageLabel: string = "SLIPPAGE_UNKNOWN";
      let minOutStatus: "OK" | "ZERO" | "UNAVAILABLE" = "UNAVAILABLE";

      // PR212b: Track phase policy decision for CHUNK_RESULT labels
      let phasePolicyShouldStop: "TRUE" | "FALSE" = "FALSE";
      let phasePolicyStopCause: string = "NONE";

      // PR164: Emit CHUNK_START event
      await appendEventV1(
        createEventV1("CHUNK_START", "INFO", {
          chunk_id: chunk.chunkId,
          chunk_index: `${i + 1}/${runPlan.chunks.length}`,
        })
      ).catch(() => {}); // Defensive: Don't fail on telemetry error

      // Sleep between chunks (except before first chunk)
      if (!isFirstChunk) {
        await sleepMs(RUNNER_PARAMS.CHUNK_INTERVAL_MS);
      }

      // Check run duration
      const elapsed = getNowMs() - startedAtMs;
      if (elapsed > RUNNER_PARAMS.MAX_RUN_DURATION_MS) {
        reasons.push("REASON_RUN_DURATION_EXCEEDED");

        // PR206: Add run-level timeout STOP reason
        runLevelReasonCodes.add(RUN_TIMEOUT_STOP);

        const nowMs = getNowMs();
        finalStatus = "STOPPED";
        stopCause = "TIMEOUT"; // PR189

        return {
          runId: runPlan.runId,
          status: "STOPPED",
          reasons,
          chunkResults,
          startedAtMs,
          finishedAtMs: nowMs,
          resumeState: createResumeState(
            "STOP_DURATION_EXCEEDED",
            nowMs,
            runPlan,
            prevPhase,
            prevRoute,
            [], // warnings
            stopCause, // PR209: origin stopCause
            Array.from(runLevelReasonCodes) // PR209: origin run reason codes
          ),
        };
      }

      // Step 1: Refresh portfolio snapshot
      let portfolio: PortfolioSnapshot;
      try {
        portfolio = await deps.getPortfolioSnapshot();
      } catch (error) {
        // Defensive: If portfolio fetch fails, STOP
        chunkResults.push({
          chunkId: chunk.chunkId,
          status: "ERROR",
          reasons: ["REASON_PORTFOLIO_FETCH_ERROR"],
          createdAtMs: getNowMs(),
        });

        reasons.push("REASON_PORTFOLIO_FETCH_ERROR_STOP");

        const nowMs = getNowMs();
        return {
          runId: runPlan.runId,
          status: "STOPPED",
          reasons,
          chunkResults,
          startedAtMs,
          finishedAtMs: nowMs,
          resumeState: createResumeState(
            "STOP_ERROR",
            nowMs,
            runPlan,
            prevPhase,
            prevRoute,
            ["WARN_PORTFOLIO_FETCH_ERROR"],
            stopCause, // PR209: origin stopCause (NONE for error path)
            Array.from(runLevelReasonCodes) // PR209: origin run reason codes
          ),
        };
      }

      // Step 1.5 (PR161): Evaluate phase STOP policy
      let currentPhase: PhaseLabel = "PHASE_UNKNOWN";
      if (deps.getPhaseLabel) {
        try {
          currentPhase = await deps.getPhaseLabel();
        } catch (error) {
          currentPhase = "PHASE_ERROR";
        }

        const phaseDecision = evaluatePhaseStopPolicyV1(prevPhase, currentPhase);

        if (phaseDecision.shouldStop) {
          // Phase escalated → STOP entire run
          chunkResults.push({
            chunkId: chunk.chunkId,
            status: "STOPPED",
            reasons: [
              "REASON_PHASE_STOP",
              phaseDecision.reason,
              ...phaseDecision.warnings,
            ],
            createdAtMs: getNowMs(),
            phaseLabel: currentPhase,
          });

          reasons.push("REASON_PHASE_ESCALATION_STOP");
          reasons.push(phaseDecision.reason);
          reasons.push(...phaseDecision.warnings);

          // PR206: Add run-level phase STOP reasons
          runLevelReasonCodes.add(RUN_PHASE_ESCALATION_STOP);
          if (currentPhase === "PHASE_DOWN_SHOCK") {
            runLevelReasonCodes.add(RUN_PHASE_DOWN_SHOCK);
          } else if (currentPhase === "PHASE_UP_REVERSAL") {
            runLevelReasonCodes.add(RUN_PHASE_UP_REVERSAL);
          }

          const nowMs = getNowMs();
          finalStatus = "STOPPED";
          stopCause = "PHASE"; // PR189

          return {
            runId: runPlan.runId,
            status: "STOPPED",
            reasons,
            chunkResults,
            startedAtMs,
            finishedAtMs: nowMs,
            resumeState: createResumeState(
              "STOP_PHASE_POLICY",
              nowMs,
              runPlan,
              currentPhase,
              prevRoute,
              phaseDecision.warnings,
              stopCause, // PR209: origin stopCause
              Array.from(runLevelReasonCodes) // PR209: origin run reason codes
            ),
          };
        }

        // PR212a: Compute label-only status for phase policy inputs
        const nowMs = getNowMs();
        const elapsedMs = nowMs - startedAtMs;

        const blockedStreakStatus: "STREAK_OK" | "STREAK_EXCEEDED" =
          consecutiveBlockCount >= RUNNER_PARAMS.MAX_BLOCKED_STREAK
            ? "STREAK_EXCEEDED"
            : "STREAK_OK";

        const timeoutStatus: "TIMEOUT_OK" | "TIMEOUT_EXCEEDED" =
          elapsedMs > RUNNER_PARAMS.MAX_RUN_DURATION_MS
            ? "TIMEOUT_EXCEEDED"
            : "TIMEOUT_OK";

        // PR212: Evaluate phase transition policy
        const phasePolicyInputs: PhasePolicyInputsV1 = {
          prevPhase: prevPhase ?? "PHASE_UNKNOWN",
          currentPhase: currentPhase,
          stopCause: stopCause,
          gateStatus: "PASS", // Default: gate not evaluated yet
          policyStatus: "ALLOW", // Default: policy not evaluated yet
          blockedStreakStatus: blockedStreakStatus,
          timeoutStatus: timeoutStatus,
        };

        const phasePolicyDecision = evaluatePhasePolicyV1(phasePolicyInputs);

        // PR212a: Emit PHASE_POLICY_EVAL event (defensive)
        const phaseTransitionSummary = summarizePhaseTransitionCodesV1(
          phasePolicyDecision.transitionCodes
        );
        await appendEventV1(
          createEventV1("PHASE_POLICY_EVAL", "INFO", {
            // Inputs
            prev_phase: phasePolicyInputs.prevPhase,
            current_phase: phasePolicyInputs.currentPhase,
            stop_cause: phasePolicyInputs.stopCause,
            gate_status: phasePolicyInputs.gateStatus,
            policy_status: phasePolicyInputs.policyStatus,
            blocked_streak_status: phasePolicyInputs.blockedStreakStatus,
            timeout_status: phasePolicyInputs.timeoutStatus,
            // Decision
            phase_changed: phasePolicyDecision.changed ? "TRUE" : "FALSE",
            next_phase: phasePolicyDecision.nextPhase,
            should_stop: phasePolicyDecision.shouldStop ? "TRUE" : "FALSE",
            decision_stop_cause: phasePolicyDecision.stopCause ?? "NONE",
            phase_transition_status: phaseTransitionSummary.status,
            phase_transition_codes: phaseTransitionSummary.joined,
          })
        ).catch(() => {}); // Defensive: Don't fail on telemetry error

        // PR212b: Wire phase policy STOP decision to run-level reason codes
        // This establishes causality chain: PHASE_POLICY_EVAL → Runner STOP → RUN_STOP
        if (phasePolicyDecision.shouldStop === true) {
          runLevelReasonCodes.add(RUN_PHASE_POLICY_SHOULD_STOP);

          const dc = phasePolicyDecision.stopCause ?? "NONE";
          if (dc === "PHASE") {
            runLevelReasonCodes.add(RUN_PHASE_POLICY_STOP_CAUSE_PHASE);
          } else if (dc === "TIMEOUT") {
            runLevelReasonCodes.add(RUN_PHASE_POLICY_STOP_CAUSE_TIMEOUT);
          } else if (dc === "GATE") {
            runLevelReasonCodes.add(RUN_PHASE_POLICY_STOP_CAUSE_GATE);
          } else if (dc === "POLICY") {
            runLevelReasonCodes.add(RUN_PHASE_POLICY_STOP_CAUSE_POLICY);
          } else {
            runLevelReasonCodes.add(RUN_PHASE_POLICY_STOP_CAUSE_NONE);
          }
        }

        // Extract transition codes from policy decision
        phaseTransitionCodes = phasePolicyDecision.transitionCodes as PhaseTransitionReasonCode[];

        // PR211: Promote phase transition codes to run-level
        if (phasePolicyDecision.changed) {
          for (const code of phaseTransitionCodes) {
            runLevelReasonCodes.add(`RUN_${code}`);
          }
        }

        // PR212b: Update phase policy decision for CHUNK_RESULT labels
        phasePolicyShouldStop = phasePolicyDecision.shouldStop ? "TRUE" : "FALSE";
        phasePolicyStopCause = phasePolicyDecision.stopCause ?? "NONE";

        // Update prevPhase for next chunk
        prevPhase = currentPhase;
      }

      // Step 1.6 (PR161): Select route per chunk
      let selectedRoute: "CETUS" | "DEEPBOOK" | "NONE" = "NONE";
      let routeChanged = false;

      if (deps.selectRoute) {
        try {
          const routeResult = await deps.selectRoute({
            chunkPlan: chunk,
            portfolio,
          });
          selectedRoute = routeResult.venue;
          routeChanged = prevRoute !== undefined && prevRoute !== selectedRoute;
          prevRoute = selectedRoute;

          // PR164: Emit ROUTE_SELECTED event
          await appendEventV1(
            createEventV1("ROUTE_SELECTED", "INFO", {
              route: selectedRoute,
              route_changed: routeChanged ? "YES" : "NO",
              phase: currentPhase,
            })
          ).catch(() => {}); // Defensive: Don't fail on telemetry error
        } catch (error) {
          // Defensive: Route selection failed → NONE
          selectedRoute = "NONE";
        }
      }

      // Step 1.7 (PR184): Get observe state and derive degrade level
      let observeDegradeLevel: string = "DEGRADED_NONE";
      if (deps.getObserveState) {
        try {
          const observeState = await deps.getObserveState();
          // Import deriveObserveDegradeLevel function
          const { deriveObserveDegradeLevel } = await import(
            "./observeDegrade"
          );
          observeDegradeLevel = deriveObserveDegradeLevel(observeState);

          // PR184: Emit OBSERVE_DEGRADED_LEVEL event (defensive)
          await appendEventV1(
            createEventV1("OBSERVE_DEGRADED_LEVEL", "INFO", {
              level: observeDegradeLevel,
              phase: currentPhase,
            })
          ).catch(() => {}); // Defensive: Don't fail on telemetry error
        } catch (error) {
          // Defensive: Failed to get observe state → UNKNOWN (safe side)
          observeDegradeLevel = "DEGRADED_UNKNOWN";
        }
      }

      // Step 1.8 (PR187): Select and normalize quote
      let normalizedQuote: NormalizedQuoteV1 | undefined;
      if (deps.getQuoteSources) {
        try {
          const quoteSources = await deps.getQuoteSources({
            chunkPlan: chunk,
            portfolio,
          });

          // Determine trade side from chunk plan intent
          let tradeSide: TradeSide = "UNKNOWN";
          if (chunk.intent.includes("INCREASE_WBTC") || chunk.intent.includes("BUY")) {
            tradeSide = "BUY_WBTC_WITH_USDC";
          } else if (chunk.intent.includes("DECREASE_WBTC") || chunk.intent.includes("SELL")) {
            tradeSide = "SELL_WBTC_FOR_USDC";
          }

          // Select and normalize quote
          normalizedQuote = selectAndNormalizeQuote({
            quoteSources,
            side: tradeSide,
            amountIn: chunk.notionalUsd || 0,
          });

          // PR190: Set quote impact label for traceability
          quoteImpactLabel = normalizedQuote?.impactLabel ?? "IMPACT_UNKNOWN";

          // PR187: Emit QUOTE_NORMALIZED event (defensive, sanitized)
          const sanitized = sanitizeQuoteForLogs(normalizedQuote);
          await appendEventV1(
            createEventV1("QUOTE_NORMALIZED", "INFO", {
              venue: sanitized.venue,
              status: sanitized.status,
              impact: sanitized.impactLabel,
              depth: sanitized.depthLabel,
              phase: currentPhase,
            })
          ).catch(() => {}); // Defensive: Don't fail on telemetry error
        } catch (error) {
          // Defensive: Quote normalization failed → undefined (buildTxDraft will handle)
          normalizedQuote = undefined;
        }
      }

      // Step 2: Evaluate gate (PR184: with observeDegradeLevel)
      let gateResult: GateResultSimple;
      try {
        gateResult = await deps.evaluateGate({
          chunkPlan: chunk,
          portfolio,
            observeDegradeLevel,
        });
      } catch (error) {
        // Defensive: If gate evaluation fails, STOP
        chunkResults.push({
          chunkId: chunk.chunkId,
          status: "ERROR",
          reasons: ["REASON_GATE_EVALUATION_ERROR"],
          createdAtMs: getNowMs(),
        });

        reasons.push("REASON_GATE_EVALUATION_ERROR_STOP");

        const nowMs = getNowMs();
        return {
          runId: runPlan.runId,
          status: "STOPPED",
          reasons,
          chunkResults,
          startedAtMs,
          finishedAtMs: nowMs,
          resumeState: createResumeState(
            "STOP_ERROR",
            nowMs,
            runPlan,
            currentPhase,
            selectedRoute,
            ["WARN_GATE_EVALUATION_ERROR"],
            stopCause, // PR209
            Array.from(runLevelReasonCodes) // PR209
          ),
        };
      }

      // Step 3: Check gate result
      gateStatus = gateResult.status; // PR189: Track gate status

      // PR204: Summarize gate reason codes for telemetry
      const gateReasonSummary = summarizeReasonCodesV1(
        gateResult.reasonCodes as string[] | undefined
      );

      if (gateResult.status === "BLOCK") {
        consecutiveBlockCount++;

        // PR164: Emit GATE_BLOCK event
        await appendEventV1(
          createEventV1("GATE_BLOCK", "WARN", {
            gate_reason: gateResult.blockReasons[0] || "BLOCK_UNKNOWN",
            consecutive_blocks: `${consecutiveBlockCount}`,
          }, gateResult.blockReasons)
        ).catch(() => {}); // Defensive: Don't fail on telemetry error

        // Check if BLOCK reason is critical (should STOP)
        const hasCriticalBlock = gateResult.blockReasons.some((reason) =>
          [
            "BLOCK_ORACLE_UNAVAILABLE",
            "BLOCK_ORACLE_STALE",
            "BLOCK_IMPACT_HIGH",
            "BLOCK_QUOTE_INCONSISTENT",
            "BLOCK_NOTIONAL_UNAVAILABLE",
            "BLOCK_NO_ROUTE",
          ].includes(reason)
        );

        if (hasCriticalBlock) {
          // Critical block → STOP
          chunkResults.push({
            chunkId: chunk.chunkId,
            status: "BLOCKED",
            reasons: gateResult.blockReasons,
            createdAtMs: getNowMs(),
            phaseLabel: currentPhase, // PR161
            routeSelected: selectedRoute, // PR161
            routeChanged, // PR161
            observeDegradeLevel, // PR184
          });

          reasons.push("REASON_CRITICAL_BLOCK_STOP");
          reasons.push(...gateResult.blockReasons);

          // PR204: Promote gate reason codes to run-level codes
          if (gateResult.reasonCodes && gateResult.reasonCodes.length > 0) {
            gateResult.reasonCodes.forEach((code) => {
              runLevelReasonCodes.add(`RUN_${code}`);
            });
          }

          const nowMs = getNowMs();
          // Determine stop reason from critical block
          let stopReason: StopReason = "STOP_UNKNOWN";
          if (gateResult.blockReasons.includes("BLOCK_NO_ROUTE")) {
            stopReason = "STOP_NO_ROUTE";
          } else if (gateResult.blockReasons.includes("BLOCK_ORACLE_STALE")) {
            stopReason = "STOP_ORACLE_STALE";
          } else if (gateResult.blockReasons.includes("BLOCK_ORACLE_UNAVAILABLE")) {
            stopReason = "STOP_ORACLE_ERROR";
          } else if (gateResult.blockReasons.includes("BLOCK_QUOTE_INCONSISTENT")) {
            stopReason = "STOP_QUOTE_INCONSISTENT";
          } else if (gateResult.blockReasons.includes("BLOCK_IMPACT_HIGH")) {
            stopReason = "STOP_IMPACT_HIGH";
          }

          finalStatus = "STOPPED";
          stopCause = "GATE"; // PR189

          return {
            runId: runPlan.runId,
            status: "STOPPED",
            reasons,
            chunkResults,
            startedAtMs,
            finishedAtMs: nowMs,
            resumeState: createResumeState(
              stopReason,
              nowMs,
              runPlan,
              currentPhase,
              selectedRoute,
              gateResult.warnings,
              stopCause, // PR209
              Array.from(runLevelReasonCodes) // PR209
            ),
          };
        }

        // Check if BLOCK reason is skippable (micro-changes)
        const isSkippableBlock = gateResult.blockReasons.some((reason) =>
          [
            "BLOCK_DELTA_TOO_SMALL",
            "BLOCK_DRIFT_TOO_SMALL",
          ].includes(reason)
        );

        if (isSkippableBlock) {
          // Skippable block → SKIP this chunk, continue to next
          chunkResults.push({
            chunkId: chunk.chunkId,
            status: "SKIPPED",
            reasons: gateResult.blockReasons,
            createdAtMs: getNowMs(),
            phaseLabel: currentPhase, // PR161
            routeSelected: selectedRoute, // PR161
            routeChanged, // PR161
            observeDegradeLevel, // PR184
          });

          consecutiveBlockCount = 0; // Reset streak
          continue;
        }

        // Non-critical, non-skippable block → check streak
        if (consecutiveBlockCount >= RUNNER_PARAMS.MAX_BLOCKED_STREAK) {
          chunkResults.push({
            chunkId: chunk.chunkId,
            status: "BLOCKED",
            reasons: gateResult.blockReasons,
            createdAtMs: getNowMs(),
            phaseLabel: currentPhase, // PR161
            routeSelected: selectedRoute, // PR161
            routeChanged, // PR161
            observeDegradeLevel, // PR184
          });

          reasons.push("REASON_BLOCKED_STREAK_EXCEEDED_STOP");

          // PR206: Add run-level blocked streak STOP reason
          runLevelReasonCodes.add(RUN_BLOCKED_STREAK_STOP);

          // PR204: Promote gate reason codes to run-level codes
          if (gateResult.reasonCodes && gateResult.reasonCodes.length > 0) {
            gateResult.reasonCodes.forEach((code) => {
              runLevelReasonCodes.add(`RUN_${code}`);
            });
          }

          const nowMs = getNowMs();
          finalStatus = "STOPPED";
          stopCause = "GATE"; // PR189

          return {
            runId: runPlan.runId,
            status: "STOPPED",
            reasons,
            chunkResults,
            startedAtMs,
            finishedAtMs: nowMs,
            resumeState: createResumeState(
              "STOP_BLOCKED_STREAK",
              nowMs,
              runPlan,
              currentPhase,
              selectedRoute,
              gateResult.warnings,
              stopCause, // PR209
              Array.from(runLevelReasonCodes) // PR209
            ),
          };
        }

        // Block this chunk, but don't STOP yet
        chunkResults.push({
          chunkId: chunk.chunkId,
          status: "BLOCKED",
          reasons: gateResult.blockReasons,
          createdAtMs: getNowMs(),
          phaseLabel: currentPhase, // PR161
          routeSelected: selectedRoute, // PR161
          routeChanged, // PR161
            observeDegradeLevel, // PR184
        });

        continue;
      } else if (gateResult.status === "ERROR") {
        // Gate error → STOP
        chunkResults.push({
          chunkId: chunk.chunkId,
          status: "ERROR",
          reasons: ["REASON_GATE_ERROR"],
          createdAtMs: getNowMs(),
          phaseLabel: currentPhase, // PR161
          routeSelected: selectedRoute, // PR161
          routeChanged, // PR161
            observeDegradeLevel, // PR184
        });

        reasons.push("REASON_GATE_ERROR_STOP");

        const nowMs = getNowMs();
        finalStatus = "STOPPED";

        return {
          runId: runPlan.runId,
          status: "STOPPED",
          reasons,
          chunkResults,
          startedAtMs,
          finishedAtMs: nowMs,
          resumeState: createResumeState(
            "STOP_ERROR",
            nowMs,
            runPlan,
            currentPhase,
            selectedRoute,
            ["WARN_GATE_ERROR"],
            stopCause, // PR209
            Array.from(runLevelReasonCodes) // PR209
          ),
        };
      }

      // Gate PASS → reset consecutive block count
      consecutiveBlockCount = 0;

      // Step 4: Evaluate policy
      let policyResult: PolicyResultSimple;
      try {
        policyResult = await deps.evaluatePolicy({ portfolio });
      } catch (error) {
        // Defensive: If policy evaluation fails, STOP
        chunkResults.push({
          chunkId: chunk.chunkId,
          status: "ERROR",
          reasons: ["REASON_POLICY_EVALUATION_ERROR"],
          createdAtMs: getNowMs(),
        });

        reasons.push("REASON_POLICY_EVALUATION_ERROR_STOP");

        const nowMs = getNowMs();
        finalStatus = "STOPPED";

        return {
          runId: runPlan.runId,
          status: "STOPPED",
          reasons,
          chunkResults,
          startedAtMs,
          finishedAtMs: nowMs,
          resumeState: createResumeState(
            "STOP_ERROR",
            nowMs,
            runPlan,
            currentPhase,
            selectedRoute,
            ["WARN_POLICY_EVALUATION_ERROR"],
            stopCause, // PR209
            Array.from(runLevelReasonCodes) // PR209
          ),
        };
      }

      // PR189: Track policy status
      policyStatus = policyResult.status;

      // PR205: Defensively populate policy reason codes if missing
      if (!policyResult.reasonCodes || policyResult.reasonCodes.length === 0) {
        const codes: import("./types").PolicyReasonCode[] = [];

        // Map from status
        if (policyResult.status === "ALLOW") {
          codes.push("POLICY_ALLOW");
        } else if (policyResult.status === "SIM_ONLY") {
          codes.push("POLICY_SIM_ONLY");
        } else if (policyResult.status === "BLOCKED") {
          codes.push("POLICY_HARDSTOP_ACTIVE");
        } else if (policyResult.status === "ERROR") {
          codes.push("POLICY_UNKNOWN");
        } else {
          codes.push("POLICY_UNKNOWN");
        }

        // Add HARDSTOP flag if present
        if (policyResult.hardStopActive) {
          codes.push("POLICY_HARDSTOP_ACTIVE");
        }

        // Defensive: If still empty, add UNKNOWN
        if (codes.length === 0) {
          codes.push("POLICY_UNKNOWN");
        }

        policyResult.reasonCodes = codes;
      }

      // PR205: Summarize policy reason codes for telemetry
      const policyReasonSummary = summarizeReasonCodesV1(
        policyResult.reasonCodes as string[] | undefined
      );

      // Check if policy allows execution
      if (!policyResult.allowExecution) {
        // Policy denies execution → STOP entire run
        chunkResults.push({
          chunkId: chunk.chunkId,
          status: "STOPPED",
          reasons: ["REASON_POLICY_DENIES_EXECUTION", ...policyResult.reasons],
          createdAtMs: getNowMs(),
        });

        reasons.push("REASON_POLICY_DENIES_EXECUTION_STOP");
        reasons.push(...policyResult.reasons);

        // PR205: Promote policy reason codes to run-level codes
        if (policyResult.reasonCodes && policyResult.reasonCodes.length > 0) {
          policyResult.reasonCodes.forEach((code) => {
            runLevelReasonCodes.add(`RUN_${code}`);
          });
        }

        const nowMs2 = getNowMs();
        // Determine if HARDSTOP or POLICY_DENY
        let stopReason: StopReason = "STOP_POLICY_DENY";
        if (policyResult.status === "BLOCKED") {
          stopReason = "STOP_HARDSTOP_ACTIVE";
        } else if (policyResult.status === "SIM_ONLY") {
          stopReason = "STOP_POLICY_DENY";
        }

        finalStatus = "STOPPED";
        stopCause = "POLICY"; // PR189

        return {
          runId: runPlan.runId,
          status: "STOPPED",
          reasons,
          chunkResults,
          startedAtMs,
          finishedAtMs: nowMs2,
          resumeState: createResumeState(
            stopReason,
            nowMs2,
            runPlan,
            currentPhase,
            selectedRoute,
            ["WARN_POLICY_DENIES_EXECUTION"],
            stopCause, // PR209
            Array.from(runLevelReasonCodes) // PR209
          ),
        };
      }

      // Step 5: Build transaction draft (PR186/PR187: pass context and normalized quote)
      let txDraft: TxDraft;
      try {
        txDraft = await deps.buildTxDraft({
          chunkPlan: chunk,
          portfolio,
          venue: selectedRoute, // PR186: route venue for slippage
          phaseLabel: currentPhase, // PR186: phase for slippage
          observeDegradeLevel, // PR186: degrade level for slippage
          impactLabel: normalizedQuote?.impactLabel, // PR187: impact from normalized quote
          normalizedQuote, // PR187: normalized quote for minOut calculation
        });

        // PR190: Set slippage label and minOut status for traceability
        slippageLabel = txDraft.slippageLabel ?? "SLIPPAGE_UNKNOWN";
        if (txDraft.minOut === null || txDraft.minOut === undefined) {
          minOutStatus = "UNAVAILABLE";
        } else if (txDraft.minOut === "0") {
          minOutStatus = "ZERO";
        } else {
          minOutStatus = "OK";
        }
      } catch (error) {
        // Defensive: If draft building fails, STOP
        chunkResults.push({
          chunkId: chunk.chunkId,
          status: "ERROR",
          reasons: ["REASON_TX_DRAFT_BUILD_ERROR"],
          createdAtMs: getNowMs(),
        });

        reasons.push("REASON_TX_DRAFT_BUILD_ERROR_STOP");

        const nowMs = getNowMs();
        finalStatus = "STOPPED";

        return {
          runId: runPlan.runId,
          status: "STOPPED",
          reasons,
          chunkResults,
          startedAtMs,
          finishedAtMs: nowMs,
          resumeState: createResumeState(
            "STOP_ERROR",
            nowMs,
            runPlan,
            currentPhase,
            selectedRoute,
            ["WARN_TX_DRAFT_BUILD_ERROR"],
            stopCause, // PR209
            Array.from(runLevelReasonCodes) // PR209
          ),
        };
      }

      // Step 6: Execute transaction
      // PR196/PR199: LIVE safety guard - STOP if LIVE mode without ALLOW policy or not unlocked
      if (executionMode === "LIVE" && (policyStatus !== "ALLOW" || liveUnlockStatus !== "UNLOCKED")) {
        const blockReasons: string[] = [];
        if (policyStatus !== "ALLOW") {
          blockReasons.push("REASON_LIVE_MODE_POLICY_NOT_ALLOW");
        }
        if (liveUnlockStatus !== "UNLOCKED") {
          // Add specific unlock block reason
          if (liveUnlockStatus === "LOCKED_ENV") {
            blockReasons.push("REASON_LIVE_LOCKED_ENV");
          } else if (liveUnlockStatus === "LOCKED_SPEC_EXPIRED") {
            blockReasons.push("REASON_LIVE_LOCKED_SPEC_EXPIRED");
          } else if (liveUnlockStatus === "LOCKED_SPEC_PENDING_ACK") {
            blockReasons.push("REASON_LIVE_LOCKED_SPEC_PENDING_ACK");
          } else if (liveUnlockStatus === "LOCKED_SPEC") {
            blockReasons.push("REASON_LIVE_LOCKED_SPEC");
          } else {
            blockReasons.push("REASON_LIVE_LOCKED_UNKNOWN");
          }
        }

        chunkResults.push({
          chunkId: chunk.chunkId,
          status: "BLOCKED",
          reasons: blockReasons,
          txDraft,
          createdAtMs: getNowMs(),
        });

        reasons.push("REASON_LIVE_MODE_BLOCKED_STOP");
        // PR200/PR203: Add run-level reason codes (normalized + legacy)
        runLevelReasonCodes.add(RUN_LIVE_BLOCK_STOP_REASON); // PR203: Normalized
        runLevelReasonCodes.add(LIVE_BLOCK_STOP_REASON); // PR200: Legacy

        // PR201/PR203: Add detailed LIVE block reasons to run-level codes
        if (policyStatus !== "ALLOW") {
          runLevelReasonCodes.add(RUN_LIVE_BLOCK_POLICY_REASON); // PR203: Normalized
          runLevelReasonCodes.add(LIVE_BLOCK_POLICY_REASON); // PR201: Legacy
        }
        if (liveUnlockStatus !== "UNLOCKED") {
          switch (liveUnlockStatus) {
            case "LOCKED_ENV":
              runLevelReasonCodes.add(RUN_LIVE_BLOCK_ENV_REASON); // PR203: Normalized
              runLevelReasonCodes.add(LIVE_BLOCK_ENV_REASON); // PR201: Legacy
              break;
            case "LOCKED_SPEC":
              runLevelReasonCodes.add(RUN_LIVE_BLOCK_SPEC_REASON); // PR203: Normalized
              runLevelReasonCodes.add(LIVE_BLOCK_SPEC_REASON); // PR201: Legacy
              break;
            case "LOCKED_SPEC_EXPIRED":
              runLevelReasonCodes.add(RUN_LIVE_BLOCK_SPEC_EXPIRED_REASON); // PR203: Normalized
              runLevelReasonCodes.add(LIVE_BLOCK_SPEC_EXPIRED_REASON); // PR201: Legacy
              break;
            case "LOCKED_SPEC_PENDING_ACK":
              runLevelReasonCodes.add(RUN_LIVE_BLOCK_SPEC_PENDING_REASON); // PR203: Normalized
              runLevelReasonCodes.add(LIVE_BLOCK_SPEC_PENDING_REASON); // PR201: Legacy
              break;
            default:
              runLevelReasonCodes.add(RUN_LIVE_BLOCK_UNKNOWN_REASON); // PR203: Normalized
              runLevelReasonCodes.add(LIVE_BLOCK_UNKNOWN_REASON); // PR201: Legacy
          }
        }

        stopCause = "POLICY"; // PR189/PR199: Policy attribution
        finalStatus = "STOPPED";

        const nowMs = getNowMs();
        return {
          runId: runPlan.runId,
          status: "STOPPED",
          reasons,
          chunkResults,
          startedAtMs,
          finishedAtMs: nowMs,
          resumeState: createResumeState(
            "STOP_POLICY_DENY",
            nowMs,
            runPlan,
            currentPhase,
            selectedRoute,
            ["WARN_LIVE_MODE_NOT_UNLOCKED"],
            stopCause, // PR209
            Array.from(runLevelReasonCodes) // PR209
          ),
        };
      }

      let executionResult: ExecutionResultSimple;
      try {
        // PR195/PR196/PR202: Emit EXECUTE_ATTEMPT telemetry (before executeTx)
        // PR202: Summarize TxDraft reason codes for telemetry
        const txReasonSummaryAttempt = summarizeReasonCodesV1(
          txDraft.executionReasonCodes
        );

        await appendEventV1(
          createEventV1("EXECUTE_ATTEMPT", "INFO", {
            run_id: runPlan.runId,
            chunk_id: chunk.chunkId,
            route: txDraft.route || "UNKNOWN",
            action: txDraft.action || "UNKNOWN",
            simulate_only: txDraft.simulateOnly ? "TRUE" : "FALSE",
            execution_mode: executionMode, // PR196
            live_unlock_status: liveUnlockStatus, // PR199
            tx_reason_codes_status: txReasonSummaryAttempt.status, // PR202
            tx_reason_codes: txReasonSummaryAttempt.joined, // PR202
            phase: currentPhase,
          })
        ).catch(() => {}); // Defensive: Don't fail on telemetry error

        executionResult = await deps.executeTx({
          txDraft,
          policy: policyResult,
          executionMode, // PR197: Pass execution mode to executor
        });

        // PR194/PR196/PR202: Emit EXECUTE_RESULT telemetry (success path)
        const execReasonsSummary = summarizeReasonCodesV1(executionResult.reasons);
        const txDigestStatus = executionResult.txDigest ? "PRESENT" : "EMPTY";
        // PR202: Summarize TxDraft reason codes for telemetry
        const txReasonSummaryResult = summarizeReasonCodesV1(
          txDraft.executionReasonCodes
        );

        await appendEventV1(
          createEventV1("EXECUTE_RESULT", "INFO", {
            run_id: runPlan.runId,
            chunk_id: chunk.chunkId,
            exec_status: executionResult.status,
            exec_reasons_status: execReasonsSummary.status,
            exec_reasons: execReasonsSummary.joined,
            tx_digest_status: txDigestStatus,
            execution_mode: executionMode, // PR196
            live_unlock_status: liveUnlockStatus, // PR199
            tx_reason_codes_status: txReasonSummaryResult.status, // PR202
            tx_reason_codes: txReasonSummaryResult.joined, // PR202
            stop_cause: stopCause,
            phase: currentPhase,
          })
        ).catch(() => {}); // Defensive: Don't fail on telemetry error
      } catch (error) {
        // PR194/PR196/PR202: Emit EXECUTE_RESULT telemetry (exception path)
        const execReasonsSummary = summarizeReasonCodesV1(["EXECUTE_EXCEPTION"]);
        // PR202: Summarize TxDraft reason codes for telemetry
        const txReasonSummaryError = summarizeReasonCodesV1(
          txDraft.executionReasonCodes
        );

        await appendEventV1(
          createEventV1("EXECUTE_RESULT", "ERROR", {
            run_id: runPlan.runId,
            chunk_id: chunk.chunkId,
            exec_status: "ERROR",
            exec_reasons_status: execReasonsSummary.status,
            exec_reasons: execReasonsSummary.joined,
            tx_digest_status: "EMPTY",
            execution_mode: executionMode, // PR196
            live_unlock_status: liveUnlockStatus, // PR199
            tx_reason_codes_status: txReasonSummaryError.status, // PR202
            tx_reason_codes: txReasonSummaryError.joined, // PR202
            stop_cause: stopCause,
            phase: currentPhase,
          })
        ).catch(() => {}); // Defensive: Don't fail on telemetry error

        // Defensive: If execution fails, STOP
        chunkResults.push({
          chunkId: chunk.chunkId,
          status: "ERROR",
          reasons: ["REASON_TX_EXECUTION_ERROR"],
          txDraft,
          createdAtMs: getNowMs(),
        });

        reasons.push("REASON_TX_EXECUTION_ERROR_STOP");

        const nowMs = getNowMs();
        finalStatus = "STOPPED";

        return {
          runId: runPlan.runId,
          status: "STOPPED",
          reasons,
          chunkResults,
          startedAtMs,
          finishedAtMs: nowMs,
          resumeState: createResumeState(
            "STOP_ERROR",
            nowMs,
            runPlan,
            currentPhase,
            selectedRoute,
            ["WARN_TX_EXECUTION_ERROR"],
            stopCause, // PR209
            Array.from(runLevelReasonCodes) // PR209
          ),
        };
      }

      // Step 7: Record chunk result
      if (executionResult.status === "EXECUTED") {
        chunkResults.push({
          chunkId: chunk.chunkId,
          status: "EXECUTED",
          reasons: executionResult.reasons,
          txDraft,
          venue: txDraft.route as "CETUS" | "DEEPBOOK" | "NONE",
          createdAtMs: getNowMs(),
          phaseLabel: currentPhase, // PR161
          routeSelected: selectedRoute, // PR161
          routeChanged, // PR161
            observeDegradeLevel, // PR184
        });

        // PR164/PR189/PR190/PR192: Emit CHUNK_RESULT event
        const reasonCodesSummary = summarizeReasonCodesV1(
          txDraft.executionReasonCodes
        );
        // PR193: Track last non-empty reason codes for RUN_STOP
        if (
          Array.isArray(txDraft.executionReasonCodes) &&
          txDraft.executionReasonCodes.length > 0
        ) {
          lastChunkReasonCodes = txDraft.executionReasonCodes;
        }
        // PR211: Summarize phase transition codes
        const phaseTransitionSummary = summarizePhaseTransitionCodesV1(phaseTransitionCodes);
        await appendEventV1(
          createEventV1("CHUNK_RESULT", "INFO", {
            chunk_status: "EXECUTED",
            gate_status: gateStatus, // PR189
            gate_reason_codes_status: gateReasonSummary.status, // PR204
            gate_reason_codes: gateReasonSummary.joined, // PR204
            policy_status: policyStatus, // PR189
            policy_reason_codes_status: policyReasonSummary.status, // PR205
            policy_reason_codes: policyReasonSummary.joined, // PR205
            quote_impact_label: quoteImpactLabel, // PR190
            slippage_label: slippageLabel, // PR190
            minout_status: minOutStatus, // PR190
            tx_reason_codes_status: reasonCodesSummary.status, // PR192
            tx_reason_codes: reasonCodesSummary.joined, // PR192
            execution_mode: executionMode, // PR196
            live_unlock_status: liveUnlockStatus, // PR199
            venue: txDraft.route,
            phase: currentPhase,
            phase_transition_status: phaseTransitionSummary.status, // PR211
            phase_transition_codes: phaseTransitionSummary.joined, // PR211
            phase_policy_should_stop: phasePolicyShouldStop, // PR212b
            phase_policy_stop_cause: phasePolicyStopCause, // PR212b
          })
        ).catch(() => {}); // Defensive: Don't fail on telemetry error

        // PR188d: Increment outcome counters
        executedCount++;
        chunkResultCount++;
      } else if (executionResult.status === "SIMULATED") {
        chunkResults.push({
          chunkId: chunk.chunkId,
          status: "SIMULATED",
          reasons: executionResult.reasons,
          txDraft,
          createdAtMs: getNowMs(),
          phaseLabel: currentPhase, // PR161
          routeSelected: selectedRoute, // PR161
          routeChanged, // PR161
            observeDegradeLevel, // PR184
        });

        // PR164/PR189/PR190/PR192: Emit CHUNK_RESULT event
        const reasonCodesSummary2 = summarizeReasonCodesV1(
          txDraft.executionReasonCodes
        );
        // PR193: Track last non-empty reason codes for RUN_STOP
        if (
          Array.isArray(txDraft.executionReasonCodes) &&
          txDraft.executionReasonCodes.length > 0
        ) {
          lastChunkReasonCodes = txDraft.executionReasonCodes;
        }
        // PR211: Summarize phase transition codes
        const phaseTransitionSummary2 = summarizePhaseTransitionCodesV1(phaseTransitionCodes);
        await appendEventV1(
          createEventV1("CHUNK_RESULT", "INFO", {
            chunk_status: "SIMULATED",
            gate_status: gateStatus, // PR189
            gate_reason_codes_status: gateReasonSummary.status, // PR204
            gate_reason_codes: gateReasonSummary.joined, // PR204
            policy_status: policyStatus, // PR189
            policy_reason_codes_status: policyReasonSummary.status, // PR205
            policy_reason_codes: policyReasonSummary.joined, // PR205
            quote_impact_label: quoteImpactLabel, // PR190
            slippage_label: slippageLabel, // PR190
            minout_status: minOutStatus, // PR190
            tx_reason_codes_status: reasonCodesSummary2.status, // PR192
            tx_reason_codes: reasonCodesSummary2.joined, // PR192
            execution_mode: executionMode, // PR196
            live_unlock_status: liveUnlockStatus, // PR199
            phase: currentPhase,
            phase_transition_status: phaseTransitionSummary2.status, // PR211
            phase_transition_codes: phaseTransitionSummary2.joined, // PR211
            phase_policy_should_stop: phasePolicyShouldStop, // PR212b
            phase_policy_stop_cause: phasePolicyStopCause, // PR212b
          })
        ).catch(() => {}); // Defensive: Don't fail on telemetry error

        // PR188d: Increment outcome counters
        simulatedCount++;
        chunkResultCount++;
      } else if (executionResult.status === "DRY_RUN") {
        // PR197: DRY_RUN mode (tx constructed but never broadcast)
        chunkResults.push({
          chunkId: chunk.chunkId,
          status: "SIMULATED", // DRY_RUN is a form of simulation
          reasons: executionResult.reasons,
          txDraft,
          createdAtMs: getNowMs(),
          phaseLabel: currentPhase, // PR161
          routeSelected: selectedRoute, // PR161
          routeChanged, // PR161
          observeDegradeLevel, // PR184
        });

        // PR197: Emit CHUNK_RESULT event
        const reasonCodesSummaryDryRun = summarizeReasonCodesV1(
          txDraft.executionReasonCodes
        );
        // PR193: Track last non-empty reason codes for RUN_STOP
        if (
          Array.isArray(txDraft.executionReasonCodes) &&
          txDraft.executionReasonCodes.length > 0
        ) {
          lastChunkReasonCodes = txDraft.executionReasonCodes;
        }
        const phaseTransitionSummary3 = summarizePhaseTransitionCodesV1(phaseTransitionCodes);
        await appendEventV1(
          createEventV1("CHUNK_RESULT", "INFO", {
            chunk_status: "SIMULATED", // DRY_RUN counted as SIMULATED
            gate_status: gateStatus, // PR189
            gate_reason_codes_status: gateReasonSummary.status, // PR204
            gate_reason_codes: gateReasonSummary.joined, // PR204
            policy_status: policyStatus, // PR189
            policy_reason_codes_status: policyReasonSummary.status, // PR205
            policy_reason_codes: policyReasonSummary.joined, // PR205
            quote_impact_label: quoteImpactLabel, // PR190
            slippage_label: slippageLabel, // PR190
            minout_status: minOutStatus, // PR190
            tx_reason_codes_status: reasonCodesSummaryDryRun.status, // PR192
            tx_reason_codes: reasonCodesSummaryDryRun.joined, // PR192
            execution_mode: executionMode, // PR196
            live_unlock_status: liveUnlockStatus, // PR199
            phase: currentPhase,
            phase_transition_status: phaseTransitionSummary3.status, // PR211
            phase_transition_codes: phaseTransitionSummary3.joined, // PR211
            phase_policy_should_stop: phasePolicyShouldStop, // PR212b
            phase_policy_stop_cause: phasePolicyStopCause, // PR212b
          })
        ).catch(() => {}); // Defensive: Don't fail on telemetry error

        // PR188d: Increment outcome counters
        simulatedCount++;
        chunkResultCount++;
      } else if (executionResult.status === "EXECUTION_DISABLED") {
        chunkResults.push({
          chunkId: chunk.chunkId,
          status: "SIMULATED",
          reasons: ["REASON_EXECUTION_DISABLED", ...executionResult.reasons],
          txDraft,
          createdAtMs: getNowMs(),
          phaseLabel: currentPhase, // PR161
          routeSelected: selectedRoute, // PR161
          routeChanged, // PR161
            observeDegradeLevel, // PR184
        });

        // PR164/PR189/PR190/PR192: Emit CHUNK_RESULT event
        const reasonCodesSummary3 = summarizeReasonCodesV1(
          txDraft.executionReasonCodes
        );
        // PR193: Track last non-empty reason codes for RUN_STOP
        if (
          Array.isArray(txDraft.executionReasonCodes) &&
          txDraft.executionReasonCodes.length > 0
        ) {
          lastChunkReasonCodes = txDraft.executionReasonCodes;
        }
        const phaseTransitionSummary4 = summarizePhaseTransitionCodesV1(phaseTransitionCodes);
        await appendEventV1(
          createEventV1("CHUNK_RESULT", "INFO", {
            chunk_status: "SIMULATED",
            gate_status: gateStatus, // PR189
            gate_reason_codes_status: gateReasonSummary.status, // PR204
            gate_reason_codes: gateReasonSummary.joined, // PR204
            policy_status: policyStatus, // PR189
            policy_reason_codes_status: policyReasonSummary.status, // PR205
            policy_reason_codes: policyReasonSummary.joined, // PR205
            quote_impact_label: quoteImpactLabel, // PR190
            slippage_label: slippageLabel, // PR190
            minout_status: minOutStatus, // PR190
            tx_reason_codes_status: reasonCodesSummary3.status, // PR192
            tx_reason_codes: reasonCodesSummary3.joined, // PR192
            execution_mode: executionMode, // PR196
            live_unlock_status: liveUnlockStatus, // PR199
            phase: currentPhase,
            phase_transition_status: phaseTransitionSummary4.status, // PR211
            phase_transition_codes: phaseTransitionSummary4.joined, // PR211
            phase_policy_should_stop: phasePolicyShouldStop, // PR212b
            phase_policy_stop_cause: phasePolicyStopCause, // PR212b
          })
        ).catch(() => {}); // Defensive: Don't fail on telemetry error

        // PR188d: Increment outcome counters
        simulatedCount++;
        chunkResultCount++;
      } else {
        // ERROR
        chunkResults.push({
          chunkId: chunk.chunkId,
          status: "ERROR",
          reasons: executionResult.reasons,
          txDraft,
          createdAtMs: getNowMs(),
          phaseLabel: currentPhase, // PR161
          routeSelected: selectedRoute, // PR161
          routeChanged, // PR161
            observeDegradeLevel, // PR184
        });

        // PR164/PR189/PR190/PR192: Emit CHUNK_RESULT event
        const reasonCodesSummary4 = summarizeReasonCodesV1(
          txDraft.executionReasonCodes
        );
        // PR193: Track last non-empty reason codes for RUN_STOP
        if (
          Array.isArray(txDraft.executionReasonCodes) &&
          txDraft.executionReasonCodes.length > 0
        ) {
          lastChunkReasonCodes = txDraft.executionReasonCodes;
        }
        const phaseTransitionSummary5 = summarizePhaseTransitionCodesV1(phaseTransitionCodes);
        await appendEventV1(
          createEventV1("CHUNK_RESULT", "ERROR", {
            chunk_status: "ERROR",
            gate_status: gateStatus, // PR189
            gate_reason_codes_status: gateReasonSummary.status, // PR204
            gate_reason_codes: gateReasonSummary.joined, // PR204
            policy_status: policyStatus, // PR189
            policy_reason_codes_status: policyReasonSummary.status, // PR205
            policy_reason_codes: policyReasonSummary.joined, // PR205
            quote_impact_label: quoteImpactLabel, // PR190
            slippage_label: slippageLabel, // PR190
            minout_status: minOutStatus, // PR190
            tx_reason_codes_status: reasonCodesSummary4.status, // PR192
            tx_reason_codes: reasonCodesSummary4.joined, // PR192
            execution_mode: executionMode, // PR196
            live_unlock_status: liveUnlockStatus, // PR199
            phase: currentPhase,
            phase_transition_status: phaseTransitionSummary5.status, // PR211
            phase_transition_codes: phaseTransitionSummary5.joined, // PR211
            phase_policy_should_stop: phasePolicyShouldStop, // PR212b
            phase_policy_stop_cause: phasePolicyStopCause, // PR212b
          })
        ).catch(() => {}); // Defensive: Don't fail on telemetry error

        // PR188d: Increment outcome counters
        chunkResultCount++;

        reasons.push("REASON_CHUNK_EXECUTION_ERROR");
      }
    }

    // All chunks processed
    reasons.push("REASON_ALL_CHUNKS_PROCESSED");
    finalStatus = "COMPLETED";

    return {
      runId: runPlan.runId,
      status: "COMPLETED",
      reasons,
      chunkResults,
      startedAtMs,
      finishedAtMs: getNowMs(),
    };
  } catch (error) {
    // Defensive: Unexpected error → return ERROR status
    reasons.push("REASON_RUNNER_UNEXPECTED_ERROR");
    finalStatus = "ERROR";

    return {
      runId: runPlan.runId,
      status: "ERROR",
      reasons,
      chunkResults,
      startedAtMs,
      finishedAtMs: getNowMs(),
    };
  } finally {
    // PR188c/PR188d/PR189/PR193/PR196/PR200/PR209: Emit RUN_STOP lifecycle event (always runs)
    // PR200: Merge chunk-level and run-level reason codes for RUN_STOP summary
    const mergedRunReasons = [
      ...(lastChunkReasonCodes ?? []),
      ...Array.from(runLevelReasonCodes),
    ];
    const runReasonSummary = summarizeRunReasonCodesV1(mergedRunReasons);

    // PR209: Build RUN_STOP labels with origin context (if present)
    const runStopLabels: Record<string, string> = {
      run_id: runPlan.runId,
      run_status: finalStatus,
      stop_cause: stopCause, // PR189: Stop attribution
      total_chunks: `${runPlan.chunks.length}`,
      executed_chunks: `${executedCount}`, // PR188d: Use counter
      simulated_chunks: `${simulatedCount}`, // PR188d: New counter
      chunk_results: `${chunkResultCount}`, // PR188d: New counter
      run_reason_codes_status: runReasonSummary.status, // PR193
      run_reason_codes: runReasonSummary.joined, // PR193
      execution_mode: executionMode, // PR196
      live_unlock_status: liveUnlockStatus, // PR199
    };

    // PR209: Add resume origin labels (if origin context present)
    if (runPlan.resumeOriginStopCause) {
      runStopLabels.resume_origin_stop_cause = runPlan.resumeOriginStopCause;
    }
    if (runPlan.resumeOriginRunReasonCodes) {
      const originSummary = summarizeRunReasonCodesV1(runPlan.resumeOriginRunReasonCodes);
      runStopLabels.resume_origin_reason_codes_status = originSummary.status;
      runStopLabels.resume_origin_reason_codes = originSummary.joined;
    }

    await appendEventV1(
      createEventV1("RUN_STOP", "INFO", runStopLabels)
    ).catch(() => {}); // Defensive: Don't fail on telemetry error
  }
}

/**
 * Get run summary (for logging/debugging)
 *
 * @param result - Run result
 * @returns Summary string (label-only)
 */
export function getRunSummary(result: RunResult): string {
  const executedCount = result.chunkResults.filter(
    (r) => r.status === "EXECUTED"
  ).length;
  const simulatedCount = result.chunkResults.filter(
    (r) => r.status === "SIMULATED"
  ).length;
  const blockedCount = result.chunkResults.filter(
    (r) => r.status === "BLOCKED"
  ).length;
  const skippedCount = result.chunkResults.filter(
    (r) => r.status === "SKIPPED"
  ).length;
  const errorCount = result.chunkResults.filter(
    (r) => r.status === "ERROR"
  ).length;

  return `RUN_${result.status}_EXECUTED_${executedCount}_SIMULATED_${simulatedCount}_BLOCKED_${blockedCount}_SKIPPED_${skippedCount}_ERROR_${errorCount}`;
}

/**
 * Export runner parameters for testing
 */
export { RUNNER_PARAMS };
