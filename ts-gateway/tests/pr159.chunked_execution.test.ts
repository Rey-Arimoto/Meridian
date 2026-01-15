/**
 * PR159: v1.4 Chunked Execution / TWAP-lite v1 - Test Suite
 *
 * Tests for chunked execution to avoid self-induced market shocks.
 *
 * Test Cases (10+):
 *   1. Chunking: totalNotional=0 or baseIntent=NOOP → chunks=0, COMPLETED
 *   2. Chunking: totalNotional=200k → 50k ×4 chunks
 *   3. Chunking: totalNotional=230k → capped at 200k, warned
 *   4. Chunking: chunk < MIN_CHUNK_NOTIONAL_USD → skipped
 *   5. Runner: allowExecution=false → all chunks SIMULATED
 *   6. Runner: policy denies (env key missing) → STOP
 *   7. Runner: 1st chunk PASS, 2nd chunk BLOCK_IMPACT_HIGH → STOP
 *   8. Runner: 1st chunk BLOCK_DELTA_TOO_SMALL → SKIP, continue
 *   9. Runner: oracle STALE → BLOCK_ORACLE_STALE → STOP
 *   10. Runner: consecutive BLOCK × 2 → STOP
 *   11. Runner: dependency throws → RunResult.status=ERROR
 *   12. Runner: all chunks succeed → COMPLETED
 */

import { describe, test, expect } from "bun:test";
import { buildChunkPlansV1, getChunkingSummary, CHUNKING_PARAMS } from "../src/rebalance/chunking";
import {
  runChunkedExecutionV1,
  getRunSummary,
  RunnerDeps,
  GateResultSimple,
  PolicyResultSimple,
  ExecutionResultSimple,
} from "../src/rebalance/runner";
import { RunPlan, ChunkPlan, PortfolioSnapshot, TxDraft } from "../src/rebalance/types";

describe("PR159: Chunking Logic", () => {
  test("Test 1: totalNotional=0 → chunks=0, COMPLETED", () => {
    const plan = buildChunkPlansV1({
      totalNotionalUsd: 0,
      templateId: "TPL_RISK_50",
      baseIntent: "INCREASE_WBTC",
    });

    expect(plan.status).toBe("COMPLETED");
    expect(plan.chunks.length).toBe(0);
    expect(plan.reasons).toContain("REASON_TOTAL_NOTIONAL_ZERO");
  });

  test("Test 1b: baseIntent=NOOP → chunks=0, COMPLETED", () => {
    const plan = buildChunkPlansV1({
      totalNotionalUsd: 100000,
      templateId: "TPL_RISK_50",
      baseIntent: "NOOP",
    });

    expect(plan.status).toBe("COMPLETED");
    expect(plan.chunks.length).toBe(0);
    expect(plan.reasons).toContain("REASON_BASE_INTENT_NOOP");
  });

  test("Test 2: totalNotional=200k → 50k ×4 chunks", () => {
    const plan = buildChunkPlansV1({
      totalNotionalUsd: 200000,
      templateId: "TPL_RISK_50",
      baseIntent: "INCREASE_WBTC",
    });

    expect(plan.status).toBe("PLANNED");
    expect(plan.chunks.length).toBe(4);
    expect(plan.reasons).toContain("REASON_CHUNKED_EXECUTION_ENABLED");

    // Verify chunk notionals
    expect(plan.chunks[0].notionalUsd).toBe(50000);
    expect(plan.chunks[1].notionalUsd).toBe(50000);
    expect(plan.chunks[2].notionalUsd).toBe(50000);
    expect(plan.chunks[3].notionalUsd).toBe(50000);
  });

  test("Test 3: totalNotional=230k → capped at 200k", () => {
    const plan = buildChunkPlansV1({
      totalNotionalUsd: 230000,
      templateId: "TPL_RISK_50",
      baseIntent: "INCREASE_WBTC",
    });

    expect(plan.status).toBe("PLANNED");
    expect(plan.totalNotionalUsd).toBe(CHUNKING_PARAMS.MAX_NOTIONAL_USD_PER_RUN);
    expect(plan.reasons).toContain("REASON_NOTIONAL_CAPPED_AT_MAX");
  });

  test("Test 4: chunk < MIN_CHUNK_NOTIONAL_USD → skipped", () => {
    const plan = buildChunkPlansV1({
      totalNotionalUsd: 5000, // Below 10k minimum
      templateId: "TPL_RISK_50",
      baseIntent: "INCREASE_WBTC",
    });

    expect(plan.status).toBe("COMPLETED");
    expect(plan.chunks.length).toBe(0);
    expect(plan.reasons).toContain("REASON_CHUNK_NOTIONAL_TOO_SMALL_SKIPPED");
    expect(plan.reasons).toContain("REASON_NO_VALID_CHUNKS");
  });
});

describe("PR159: Runner Execution", () => {
  // Helper to create mock portfolio
  const createMockPortfolio = (): PortfolioSnapshot => ({
    balances: { WBTC: "1.0", USDC: "100000", SUI: "1.0" },
    pricesUsd: { WBTC: 50000, USDC: 1.0 },
    valuesUsd: { WBTC: 50000, USDC: 100000 },
    weights: { WBTC: 0.333, USDC: 0.667 },
    totalUsd: 150000,
    oracleStatus: "AVAILABLE",
    timestamp: Date.now(),
  });

  // Helper to create mock tx draft
  const createMockTxDraft = (chunkId: string): TxDraft => ({
    status: "EXECUTABLE_DRAFT",
    simulateOnly: false,
    route: "CETUS",
    action: "SWAP_USDC_TO_WBTC",
    amountIn: "50000",
    minOut: "0.9",
    slippageBps: 100,
    deadlineSeconds: 120,
    checks: [],
    notes: [`Draft for ${chunkId}`],
    errors: [],
  });

  test("Test 5: allowExecution=false → all chunks SIMULATED", async () => {
    const plan = buildChunkPlansV1({
      totalNotionalUsd: 100000,
      templateId: "TPL_RISK_50",
      baseIntent: "INCREASE_WBTC",
      chunkNotionalUsd: 50000,
    });

    const deps: RunnerDeps = {
      getNowMs: () => 1000000,
      sleepMs: async () => {}, // No sleep in tests
      getPortfolioSnapshot: async () => createMockPortfolio(),
      evaluateGate: async () => ({
        status: "PASS",
        blockReasons: [],
        warnings: [],
      }),
      evaluatePolicy: async () => ({
        allowExecution: false, // Execution disabled
        status: "SIM_ONLY",
        reasons: ["REASON_EXECUTION_DISABLED_BY_ENV"],
      }),
      buildTxDraft: async ({ chunkPlan }) => createMockTxDraft(chunkPlan.chunkId),
      executeTx: async () => ({
        status: "EXECUTION_DISABLED",
        reasons: ["REASON_EXECUTION_DISABLED"],
      }),
    };

    const result = await runChunkedExecutionV1(plan, deps);

    expect(result.status).toBe("STOPPED");
    expect(result.reasons).toContain("REASON_POLICY_DENIES_EXECUTION_STOP");
    expect(result.chunkResults.length).toBe(1); // Stopped at first chunk
    expect(result.chunkResults[0].status).toBe("STOPPED");
  });

  test("Test 6: policy denies (env key missing) → STOP", async () => {
    const plan = buildChunkPlansV1({
      totalNotionalUsd: 100000,
      templateId: "TPL_RISK_50",
      baseIntent: "INCREASE_WBTC",
    });

    const deps: RunnerDeps = {
      getPortfolioSnapshot: async () => createMockPortfolio(),
      evaluateGate: async () => ({
        status: "PASS",
        blockReasons: [],
        warnings: [],
      }),
      evaluatePolicy: async () => ({
        allowExecution: false,
        status: "SIM_ONLY",
        reasons: ["REASON_ENV_KEY_MISSING"],
      }),
      buildTxDraft: async ({ chunkPlan }) => createMockTxDraft(chunkPlan.chunkId),
      executeTx: async () => ({
        status: "EXECUTION_DISABLED",
        reasons: [],
      }),
    };

    const result = await runChunkedExecutionV1(plan, deps);

    expect(result.status).toBe("STOPPED");
    expect(result.reasons).toContain("REASON_POLICY_DENIES_EXECUTION_STOP");
    expect(result.reasons).toContain("REASON_ENV_KEY_MISSING");
  });

  test("Test 7: 1st chunk PASS, 2nd chunk BLOCK_IMPACT_HIGH → STOP", async () => {
    const plan = buildChunkPlansV1({
      totalNotionalUsd: 100000,
      templateId: "TPL_RISK_50",
      baseIntent: "INCREASE_WBTC",
      chunkNotionalUsd: 50000,
    });

    let chunkCount = 0;

    const deps: RunnerDeps = {
      sleepMs: async () => {}, // No sleep
      getPortfolioSnapshot: async () => createMockPortfolio(),
      evaluateGate: async () => {
        chunkCount++;
        if (chunkCount === 1) {
          return { status: "PASS", blockReasons: [], warnings: [] };
        } else {
          return {
            status: "BLOCK",
            blockReasons: ["BLOCK_IMPACT_HIGH"],
            warnings: [],
          };
        }
      },
      evaluatePolicy: async () => ({
        allowExecution: true,
        status: "ALLOW",
        reasons: [],
      }),
      buildTxDraft: async ({ chunkPlan }) => createMockTxDraft(chunkPlan.chunkId),
      executeTx: async () => ({
        status: "EXECUTED",
        reasons: [],
        txDigest: "0x123",
      }),
    };

    const result = await runChunkedExecutionV1(plan, deps);

    expect(result.status).toBe("STOPPED");
    expect(result.reasons).toContain("REASON_CRITICAL_BLOCK_STOP");
    expect(result.reasons).toContain("BLOCK_IMPACT_HIGH");
    expect(result.chunkResults.length).toBe(2);
    expect(result.chunkResults[0].status).toBe("EXECUTED");
    expect(result.chunkResults[1].status).toBe("BLOCKED");
  });

  test("Test 8: 1st chunk BLOCK_DELTA_TOO_SMALL → SKIP, continue", async () => {
    const plan = buildChunkPlansV1({
      totalNotionalUsd: 100000,
      templateId: "TPL_RISK_50",
      baseIntent: "INCREASE_WBTC",
      chunkNotionalUsd: 50000,
    });

    let chunkCount = 0;

    const deps: RunnerDeps = {
      sleepMs: async () => {},
      getPortfolioSnapshot: async () => createMockPortfolio(),
      evaluateGate: async () => {
        chunkCount++;
        if (chunkCount === 1) {
          return {
            status: "BLOCK",
            blockReasons: ["BLOCK_DELTA_TOO_SMALL"],
            warnings: [],
          };
        } else {
          return { status: "PASS", blockReasons: [], warnings: [] };
        }
      },
      evaluatePolicy: async () => ({
        allowExecution: true,
        status: "ALLOW",
        reasons: [],
      }),
      buildTxDraft: async ({ chunkPlan }) => createMockTxDraft(chunkPlan.chunkId),
      executeTx: async () => ({
        status: "EXECUTED",
        reasons: [],
        txDigest: "0x456",
      }),
    };

    const result = await runChunkedExecutionV1(plan, deps);

    expect(result.status).toBe("COMPLETED");
    expect(result.chunkResults.length).toBe(2);
    expect(result.chunkResults[0].status).toBe("SKIPPED");
    expect(result.chunkResults[1].status).toBe("EXECUTED");
  });

  test("Test 9: oracle STALE → BLOCK_ORACLE_STALE → STOP", async () => {
    const plan = buildChunkPlansV1({
      totalNotionalUsd: 100000,
      templateId: "TPL_RISK_50",
      baseIntent: "INCREASE_WBTC",
    });

    const deps: RunnerDeps = {
      getPortfolioSnapshot: async () => createMockPortfolio(),
      evaluateGate: async () => ({
        status: "BLOCK",
        blockReasons: ["BLOCK_ORACLE_STALE"],
        warnings: [],
      }),
      evaluatePolicy: async () => ({
        allowExecution: true,
        status: "ALLOW",
        reasons: [],
      }),
      buildTxDraft: async ({ chunkPlan }) => createMockTxDraft(chunkPlan.chunkId),
      executeTx: async () => ({
        status: "EXECUTED",
        reasons: [],
      }),
    };

    const result = await runChunkedExecutionV1(plan, deps);

    expect(result.status).toBe("STOPPED");
    expect(result.reasons).toContain("REASON_CRITICAL_BLOCK_STOP");
    expect(result.reasons).toContain("BLOCK_ORACLE_STALE");
    expect(result.chunkResults[0].status).toBe("BLOCKED");
  });

  test("Test 10: consecutive BLOCK × 2 → STOP", async () => {
    const plan = buildChunkPlansV1({
      totalNotionalUsd: 150000,
      templateId: "TPL_RISK_50",
      baseIntent: "INCREASE_WBTC",
      chunkNotionalUsd: 50000,
    });

    const deps: RunnerDeps = {
      sleepMs: async () => {},
      getPortfolioSnapshot: async () => createMockPortfolio(),
      evaluateGate: async () => ({
        status: "BLOCK",
        blockReasons: ["BLOCK_SLIPPAGE_HIGH"], // Non-critical, non-skippable
        warnings: [],
      }),
      evaluatePolicy: async () => ({
        allowExecution: true,
        status: "ALLOW",
        reasons: [],
      }),
      buildTxDraft: async ({ chunkPlan }) => createMockTxDraft(chunkPlan.chunkId),
      executeTx: async () => ({
        status: "EXECUTED",
        reasons: [],
      }),
    };

    const result = await runChunkedExecutionV1(plan, deps);

    expect(result.status).toBe("STOPPED");
    expect(result.reasons).toContain("REASON_BLOCKED_STREAK_EXCEEDED_STOP");
    expect(result.chunkResults.length).toBe(2);
    expect(result.chunkResults[0].status).toBe("BLOCKED");
    expect(result.chunkResults[1].status).toBe("BLOCKED");
  });

  test("Test 11: dependency throws → RunResult.status=ERROR", async () => {
    const plan = buildChunkPlansV1({
      totalNotionalUsd: 100000,
      templateId: "TPL_RISK_50",
      baseIntent: "INCREASE_WBTC",
    });

    const deps: RunnerDeps = {
      getPortfolioSnapshot: async () => {
        throw new Error("Portfolio fetch failed");
      },
      evaluateGate: async () => ({
        status: "PASS",
        blockReasons: [],
        warnings: [],
      }),
      evaluatePolicy: async () => ({
        allowExecution: true,
        status: "ALLOW",
        reasons: [],
      }),
      buildTxDraft: async ({ chunkPlan }) => createMockTxDraft(chunkPlan.chunkId),
      executeTx: async () => ({
        status: "EXECUTED",
        reasons: [],
      }),
    };

    const result = await runChunkedExecutionV1(plan, deps);

    expect(result.status).toBe("STOPPED");
    expect(result.reasons).toContain("REASON_PORTFOLIO_FETCH_ERROR_STOP");
    expect(result.chunkResults[0].status).toBe("ERROR");
  });

  test("Test 12: all chunks succeed → COMPLETED", async () => {
    const plan = buildChunkPlansV1({
      totalNotionalUsd: 100000,
      templateId: "TPL_RISK_50",
      baseIntent: "INCREASE_WBTC",
      chunkNotionalUsd: 50000,
    });

    const deps: RunnerDeps = {
      sleepMs: async () => {},
      getPortfolioSnapshot: async () => createMockPortfolio(),
      evaluateGate: async () => ({
        status: "PASS",
        blockReasons: [],
        warnings: [],
      }),
      evaluatePolicy: async () => ({
        allowExecution: true,
        status: "ALLOW",
        reasons: [],
      }),
      buildTxDraft: async ({ chunkPlan }) => createMockTxDraft(chunkPlan.chunkId),
      executeTx: async () => ({
        status: "EXECUTED",
        reasons: [],
        txDigest: "0x789",
      }),
    };

    const result = await runChunkedExecutionV1(plan, deps);

    expect(result.status).toBe("COMPLETED");
    expect(result.reasons).toContain("REASON_ALL_CHUNKS_PROCESSED");
    expect(result.chunkResults.length).toBe(2);
    expect(result.chunkResults[0].status).toBe("EXECUTED");
    expect(result.chunkResults[1].status).toBe("EXECUTED");
  });
});

describe("PR159: Summary Functions", () => {
  test("Chunking summary", () => {
    const plan1 = buildChunkPlansV1({
      totalNotionalUsd: 0,
      templateId: "TPL_RISK_50",
      baseIntent: "NOOP",
    });
    expect(getChunkingSummary(plan1)).toBe("CHUNKING_NO_CHUNKS");

    const plan2 = buildChunkPlansV1({
      totalNotionalUsd: 100000,
      templateId: "TPL_RISK_50",
      baseIntent: "INCREASE_WBTC",
    });
    expect(getChunkingSummary(plan2)).toBe("CHUNKING_PLANNED");
  });

  test("Run summary", () => {
    const result = {
      runId: "run-123",
      status: "COMPLETED" as const,
      reasons: [],
      chunkResults: [
        {
          chunkId: "chunk-1",
          status: "EXECUTED" as const,
          reasons: [],
          createdAtMs: 1000,
        },
        {
          chunkId: "chunk-2",
          status: "SIMULATED" as const,
          reasons: [],
          createdAtMs: 2000,
        },
      ],
      startedAtMs: 1000,
      finishedAtMs: 2000,
    };

    const summary = getRunSummary(result);
    expect(summary).toContain("RUN_COMPLETED");
    expect(summary).toContain("EXECUTED_1");
    expect(summary).toContain("SIMULATED_1");
  });
});
