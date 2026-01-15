/**
 * PR159: v1.4 TWAP-lite Runner (READ-ONLY)
 *
 * Purpose:
 *   Execute chunked rebalance plans with per-chunk refreshing of:
 *   - Portfolio snapshot
 *   - Oracle prices
 *   - Quotes
 *   - Gate checks (PR153/155/157/158)
 *   - Policy checks (PR156)
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
} from "./types";
import { CHUNKING_PARAMS } from "./chunking";

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

        return {
          runId: runPlan.runId,
          status: "STOPPED",
          reasons,
          chunkResults,
          startedAtMs,
          finishedAtMs: getNowMs(),
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

        return {
          runId: runPlan.runId,
          status: "STOPPED",
          reasons,
          chunkResults,
          startedAtMs,
          finishedAtMs: getNowMs(),
        };
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

        return {
          runId: runPlan.runId,
          status: "STOPPED",
          reasons,
          chunkResults,
          startedAtMs,
          finishedAtMs: getNowMs(),
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
          });

          reasons.push("REASON_CRITICAL_BLOCK_STOP");
          reasons.push(...gateResult.blockReasons);

          return {
            runId: runPlan.runId,
            status: "STOPPED",
            reasons,
            chunkResults,
            startedAtMs,
            finishedAtMs: getNowMs(),
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
          });

          reasons.push("REASON_BLOCKED_STREAK_EXCEEDED_STOP");

          return {
            runId: runPlan.runId,
            status: "STOPPED",
            reasons,
            chunkResults,
            startedAtMs,
            finishedAtMs: getNowMs(),
          };
        }

        // Block this chunk, but don't STOP yet
        chunkResults.push({
          chunkId: chunk.chunkId,
          status: "BLOCKED",
          reasons: gateResult.blockReasons,
          createdAtMs: getNowMs(),
        });

        continue;
      } else if (gateResult.status === "ERROR") {
        // Gate error → STOP
        chunkResults.push({
          chunkId: chunk.chunkId,
          status: "ERROR",
          reasons: ["REASON_GATE_ERROR"],
          createdAtMs: getNowMs(),
        });

        reasons.push("REASON_GATE_ERROR_STOP");

        return {
          runId: runPlan.runId,
          status: "STOPPED",
          reasons,
          chunkResults,
          startedAtMs,
          finishedAtMs: getNowMs(),
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

        return {
          runId: runPlan.runId,
          status: "STOPPED",
          reasons,
          chunkResults,
          startedAtMs,
          finishedAtMs: getNowMs(),
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

        return {
          runId: runPlan.runId,
          status: "STOPPED",
          reasons,
          chunkResults,
          startedAtMs,
          finishedAtMs: getNowMs(),
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

        return {
          runId: runPlan.runId,
          status: "STOPPED",
          reasons,
          chunkResults,
          startedAtMs,
          finishedAtMs: getNowMs(),
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

        return {
          runId: runPlan.runId,
          status: "STOPPED",
          reasons,
          chunkResults,
          startedAtMs,
          finishedAtMs: getNowMs(),
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
        });
      } else if (executionResult.status === "SIMULATED") {
        chunkResults.push({
          chunkId: chunk.chunkId,
          status: "SIMULATED",
          reasons: executionResult.reasons,
          txDraft,
          createdAtMs: getNowMs(),
        });
      } else if (executionResult.status === "EXECUTION_DISABLED") {
        chunkResults.push({
          chunkId: chunk.chunkId,
          status: "SIMULATED",
          reasons: ["REASON_EXECUTION_DISABLED", ...executionResult.reasons],
          txDraft,
          createdAtMs: getNowMs(),
        });
      } else {
        // ERROR
        chunkResults.push({
          chunkId: chunk.chunkId,
          status: "ERROR",
          reasons: executionResult.reasons,
          txDraft,
          createdAtMs: getNowMs(),
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
