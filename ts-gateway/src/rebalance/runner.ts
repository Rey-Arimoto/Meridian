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
} from "./types";
import { CHUNKING_PARAMS } from "./chunking";
import {
  PhaseLabel,
  evaluatePhaseStopPolicyV1,
  getPhasePolicySummary,
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
 * Gate result (simplified for runner)
 */
export interface GateResultSimple {
  status: "PASS" | "BLOCK" | "ERROR";
  blockReasons: string[];
  warnings: string[];
}

/**
 * Policy result (simplified for runner)
 */
export interface PolicyResultSimple {
  allowExecution: boolean;
  status: "ALLOW" | "SIM_ONLY" | "BLOCKED" | "ERROR";
  reasons: string[];
}

/**
 * Execution result (simplified for runner)
 */
export interface ExecutionResultSimple {
  status: "EXECUTED" | "SIMULATED" | "EXECUTION_DISABLED" | "ERROR";
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

  // Execute transaction
  executeTx: (args: {
    txDraft: TxDraft;
    policy: PolicyResultSimple;
  }) => Promise<ExecutionResultSimple>;
}

/**
 * PR162: Create resume state (helper for STOP scenarios)
 *
 * @param stopReason - Stop reason (label-only)
 * @param nowMs - Current timestamp (internal numeric only)
 * @param runPlan - Run plan (for observability metadata)
 * @param lastPhase - Last phase label (optional, label-only)
 * @param lastRoute - Last route (optional, label-only)
 * @param warnings - Warnings (optional, label-only)
 * @returns Resume state
 */
function createResumeState(
  stopReason: StopReason,
  nowMs: number,
  runPlan: RunPlan,
  lastPhase?: string,
  lastRoute?: string,
  warnings: string[] = []
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

  // PR188c: Emit RUN_START lifecycle event
  await appendEventV1(
    createEventV1("RUN_START", "INFO", {
      run_id: runPlan.runId,
      template_id: runPlan.templateId,
      total_chunks: `${runPlan.chunks.length}`,
    })
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
            prevRoute
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
            ["WARN_PORTFOLIO_FETCH_ERROR"]
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
              phaseDecision.warnings
            ),
          };
        }

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
            ["WARN_GATE_EVALUATION_ERROR"]
          ),
        };
      }

      // Step 3: Check gate result
      gateStatus = gateResult.status; // PR189: Track gate status

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
              gateResult.warnings
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
              gateResult.warnings
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
            ["WARN_GATE_ERROR"]
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
            ["WARN_POLICY_EVALUATION_ERROR"]
          ),
        };
      }

      // PR189: Track policy status
      policyStatus = policyResult.status;

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
            ["WARN_POLICY_DENIES_EXECUTION"]
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
            ["WARN_TX_DRAFT_BUILD_ERROR"]
          ),
        };
      }

      // Step 6: Execute transaction
      let executionResult: ExecutionResultSimple;
      try {
        // PR195: Emit EXECUTE_ATTEMPT telemetry (before executeTx)
        await appendEventV1(
          createEventV1("EXECUTE_ATTEMPT", "INFO", {
            run_id: runPlan.runId,
            chunk_id: chunk.chunkId,
            route: txDraft.route || "UNKNOWN",
            action: txDraft.action || "UNKNOWN",
            simulate_only: txDraft.simulateOnly ? "TRUE" : "FALSE",
            phase: currentPhase,
          })
        ).catch(() => {}); // Defensive: Don't fail on telemetry error

        executionResult = await deps.executeTx({ txDraft, policy: policyResult });

        // PR194: Emit EXECUTE_RESULT telemetry (success path)
        const execReasonsSummary = summarizeReasonCodesV1(executionResult.reasons);
        const txDigestStatus = executionResult.txDigest ? "PRESENT" : "EMPTY";
        await appendEventV1(
          createEventV1("EXECUTE_RESULT", "INFO", {
            run_id: runPlan.runId,
            chunk_id: chunk.chunkId,
            exec_status: executionResult.status,
            exec_reasons_status: execReasonsSummary.status,
            exec_reasons: execReasonsSummary.joined,
            tx_digest_status: txDigestStatus,
            stop_cause: stopCause,
            phase: currentPhase,
          })
        ).catch(() => {}); // Defensive: Don't fail on telemetry error
      } catch (error) {
        // PR194: Emit EXECUTE_RESULT telemetry (exception path)
        const execReasonsSummary = summarizeReasonCodesV1(["EXECUTE_EXCEPTION"]);
        await appendEventV1(
          createEventV1("EXECUTE_RESULT", "ERROR", {
            run_id: runPlan.runId,
            chunk_id: chunk.chunkId,
            exec_status: "ERROR",
            exec_reasons_status: execReasonsSummary.status,
            exec_reasons: execReasonsSummary.joined,
            tx_digest_status: "EMPTY",
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
            ["WARN_TX_EXECUTION_ERROR"]
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
        await appendEventV1(
          createEventV1("CHUNK_RESULT", "INFO", {
            chunk_status: "EXECUTED",
            gate_status: gateStatus, // PR189
            policy_status: policyStatus, // PR189
            quote_impact_label: quoteImpactLabel, // PR190
            slippage_label: slippageLabel, // PR190
            minout_status: minOutStatus, // PR190
            tx_reason_codes_status: reasonCodesSummary.status, // PR192
            tx_reason_codes: reasonCodesSummary.joined, // PR192
            venue: txDraft.route,
            phase: currentPhase,
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
        await appendEventV1(
          createEventV1("CHUNK_RESULT", "INFO", {
            chunk_status: "SIMULATED",
            gate_status: gateStatus, // PR189
            policy_status: policyStatus, // PR189
            quote_impact_label: quoteImpactLabel, // PR190
            slippage_label: slippageLabel, // PR190
            minout_status: minOutStatus, // PR190
            tx_reason_codes_status: reasonCodesSummary2.status, // PR192
            tx_reason_codes: reasonCodesSummary2.joined, // PR192
            phase: currentPhase,
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
        await appendEventV1(
          createEventV1("CHUNK_RESULT", "INFO", {
            chunk_status: "SIMULATED",
            gate_status: gateStatus, // PR189
            policy_status: policyStatus, // PR189
            quote_impact_label: quoteImpactLabel, // PR190
            slippage_label: slippageLabel, // PR190
            minout_status: minOutStatus, // PR190
            tx_reason_codes_status: reasonCodesSummary3.status, // PR192
            tx_reason_codes: reasonCodesSummary3.joined, // PR192
            phase: currentPhase,
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
        await appendEventV1(
          createEventV1("CHUNK_RESULT", "ERROR", {
            chunk_status: "ERROR",
            gate_status: gateStatus, // PR189
            policy_status: policyStatus, // PR189
            quote_impact_label: quoteImpactLabel, // PR190
            slippage_label: slippageLabel, // PR190
            minout_status: minOutStatus, // PR190
            tx_reason_codes_status: reasonCodesSummary4.status, // PR192
            tx_reason_codes: reasonCodesSummary4.joined, // PR192
            phase: currentPhase,
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
    // PR188c/PR188d/PR189/PR193: Emit RUN_STOP lifecycle event (always runs)
    const runReasonSummary = summarizeRunReasonCodesV1(lastChunkReasonCodes);
    await appendEventV1(
      createEventV1("RUN_STOP", "INFO", {
        run_id: runPlan.runId,
        run_status: finalStatus,
        stop_cause: stopCause, // PR189: Stop attribution
        total_chunks: `${runPlan.chunks.length}`,
        executed_chunks: `${executedCount}`, // PR188d: Use counter
        simulated_chunks: `${simulatedCount}`, // PR188d: New counter
        chunk_results: `${chunkResultCount}`, // PR188d: New counter
        run_reason_codes_status: runReasonSummary.status, // PR193
        run_reason_codes: runReasonSummary.joined, // PR193
      })
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
