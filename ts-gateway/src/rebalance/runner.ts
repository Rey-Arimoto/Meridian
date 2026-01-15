/**
 * PR159: v1.4 TWAP-lite Runner (READ-ONLY)
 * PR160: FAST Profile v1.1 - Updated timing parameters
 * PR161: Phase Re-eval STOP + Per-Chunk Route Reselect
 * PR162: Partial Resume Policy v1
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

  // Evaluate gate (PR153/155/157/158)
  evaluateGate: (args: {
    chunkPlan: ChunkPlan;
    portfolio: PortfolioSnapshot;
  }) => Promise<GateResultSimple>;

  // Evaluate policy (PR156)
  evaluatePolicy: (args: {
    portfolio: PortfolioSnapshot;
  }) => Promise<PolicyResultSimple>;

  // Build transaction draft
  buildTxDraft: (args: {
    chunkPlan: ChunkPlan;
    portfolio: PortfolioSnapshot;
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

  let consecutiveBlockCount = 0;

  try {
    // Check if run plan has no chunks
    if (runPlan.chunks.length === 0) {
      reasons.push("REASON_NO_CHUNKS_TO_EXECUTE");

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

      // Sleep between chunks (except before first chunk)
      if (!isFirstChunk) {
        await sleepMs(RUNNER_PARAMS.CHUNK_INTERVAL_MS);
      }

      // Check run duration
      const elapsed = getNowMs() - startedAtMs;
      if (elapsed > RUNNER_PARAMS.MAX_RUN_DURATION_MS) {
        reasons.push("REASON_RUN_DURATION_EXCEEDED");

        const nowMs = getNowMs();
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
        } catch (error) {
          // Defensive: Route selection failed → NONE
          selectedRoute = "NONE";
        }
      }

      // Step 2: Evaluate gate
      let gateResult: GateResultSimple;
      try {
        gateResult = await deps.evaluateGate({ chunkPlan: chunk, portfolio });
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
      if (gateResult.status === "BLOCK") {
        consecutiveBlockCount++;

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
          });

          reasons.push("REASON_BLOCKED_STREAK_EXCEEDED_STOP");

          const nowMs = getNowMs();
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
        });

        reasons.push("REASON_GATE_ERROR_STOP");

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

      // Step 5: Build transaction draft
      let txDraft: TxDraft;
      try {
        txDraft = await deps.buildTxDraft({ chunkPlan: chunk, portfolio });
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
        executionResult = await deps.executeTx({ txDraft, policy: policyResult });
      } catch (error) {
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
        });
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
        });
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
        });
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
        });

        reasons.push("REASON_CHUNK_EXECUTION_ERROR");
      }
    }

    // All chunks processed
    reasons.push("REASON_ALL_CHUNKS_PROCESSED");

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

    return {
      runId: runPlan.runId,
      status: "ERROR",
      reasons,
      chunkResults,
      startedAtMs,
      finishedAtMs: getNowMs(),
    };
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
