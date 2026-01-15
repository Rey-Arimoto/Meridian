/**
 * PR161: v1.4 TWAP-lite Phase Re-eval STOP + Per-Chunk Route Reselect - Test Suite
 *
 * Tests for phase escalation STOP policy and route reselection per chunk.
 *
 * Test Cases (10):
 *   Phase Policy (6):
 *     1. now=PHASE_UNKNOWN → STOP_PHASE_UNKNOWN
 *     2. prev=NORMAL, now=PRE_SHOCK → STOP_PHASE_ESCALATED
 *     3. prev=PRE_SHOCK, now=DOWN_SHOCK → STOP_PHASE_ESCALATED
 *     4. prev=UP_SHOCK, now=UP_REVERSAL → STOP_PHASE_CHANGED
 *     5. prev=DOWN_SHOCK, now=DOWN_REVERSAL → STOP_PHASE_CHANGED
 *     6. prev=SHOCK, now=RECOVERY → NO_STOP
 *   Route Reselection (4):
 *     7. chunk1 CETUS, chunk2 DEEPBOOK → routeChanged=true
 *     8. both chunks route=NONE → BLOCK_NO_ROUTE
 *     9. Runner calls selectRoute per chunk (verified)
 *     10. Phase + route diagnostics recorded in ChunkResult
 */

import { describe, test, expect } from "bun:test";
import {
  PhaseLabel,
  evaluatePhaseStopPolicyV1,
  getPhasePolicySummary,
} from "../src/rebalance/phasePolicy";
import { buildChunkPlansV1 } from "../src/rebalance/chunking";
import { runChunkedExecutionV1, RunnerDeps } from "../src/rebalance/runner";
import { PortfolioSnapshot, TxDraft } from "../src/rebalance/types";

describe("PR161: Phase Policy", () => {
  test("Test 1: now=PHASE_UNKNOWN → STOP_PHASE_UNKNOWN", () => {
    const decision = evaluatePhaseStopPolicyV1(undefined, "PHASE_UNKNOWN");

    expect(decision.shouldStop).toBe(true);
    expect(decision.reason).toBe("STOP_PHASE_UNKNOWN");
    expect(decision.warnings).toContain("WARN_PHASE_UNKNOWN");
  });

  test("Test 2: prev=NORMAL, now=PRE_SHOCK → STOP_PHASE_ESCALATED", () => {
    const decision = evaluatePhaseStopPolicyV1("PHASE_NORMAL", "PHASE_PRE_SHOCK");

    expect(decision.shouldStop).toBe(true);
    expect(decision.reason).toBe("STOP_PHASE_ESCALATED");
    expect(decision.warnings).toContain("WARN_PHASE_ESCALATED_TO_PRE_SHOCK");
  });

  test("Test 3: prev=PRE_SHOCK, now=DOWN_SHOCK → STOP_PHASE_ESCALATED", () => {
    const decision = evaluatePhaseStopPolicyV1("PHASE_PRE_SHOCK", "PHASE_DOWN_SHOCK");

    expect(decision.shouldStop).toBe(true);
    expect(decision.reason).toBe("STOP_PHASE_ESCALATED");
    expect(decision.warnings).toContain("WARN_PHASE_ESCALATED_TO_SHOCK");
  });

  test("Test 4: prev=UP_SHOCK, now=UP_REVERSAL → STOP_PHASE_CHANGED", () => {
    const decision = evaluatePhaseStopPolicyV1("PHASE_UP_SHOCK", "PHASE_UP_REVERSAL");

    expect(decision.shouldStop).toBe(true);
    expect(decision.reason).toBe("STOP_PHASE_CHANGED");
    expect(decision.warnings).toContain("WARN_PHASE_CHANGED_TO_REVERSAL");
  });

  test("Test 5: prev=DOWN_SHOCK, now=DOWN_REVERSAL → STOP_PHASE_CHANGED", () => {
    const decision = evaluatePhaseStopPolicyV1("PHASE_DOWN_SHOCK", "PHASE_DOWN_REVERSAL");

    expect(decision.shouldStop).toBe(true);
    expect(decision.reason).toBe("STOP_PHASE_CHANGED");
    expect(decision.warnings).toContain("WARN_PHASE_CHANGED_TO_REVERSAL");
  });

  test("Test 6: prev=SHOCK, now=RECOVERY → NO_STOP", () => {
    const decision = evaluatePhaseStopPolicyV1("PHASE_DOWN_SHOCK", "PHASE_RECOVERY");

    expect(decision.shouldStop).toBe(false);
    expect(decision.reason).toBe("NO_STOP");
  });
});

describe("PR161: Route Reselection", () => {
  const createMockPortfolio = (): PortfolioSnapshot => ({
    balances: { WBTC: "1.0", USDC: "100000", SUI: "1.0" },
    pricesUsd: { WBTC: 50000, USDC: 1.0 },
    valuesUsd: { WBTC: 50000, USDC: 100000 },
    weights: { WBTC: 0.333, USDC: 0.667 },
    totalUsd: 150000,
    oracleStatus: "AVAILABLE",
    timestamp: Date.now(),
  });

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

  test("Test 7: chunk1 CETUS, chunk2 DEEPBOOK → routeChanged=true", async () => {
    const plan = buildChunkPlansV1({
      totalNotionalUsd: 100000,
      templateId: "TPL_RISK_50",
      baseIntent: "INCREASE_WBTC",
    });

    let chunkCount = 0;

    const deps: RunnerDeps = {
      sleepMs: async () => {},
      getPortfolioSnapshot: async () => createMockPortfolio(),
      getPhaseLabel: async () => "PHASE_NORMAL",
      selectRoute: async () => {
        chunkCount++;
        return {
          venue: chunkCount === 1 ? "CETUS" : "DEEPBOOK",
          reasons: [],
        };
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
        txDigest: "0x123",
      }),
    };

    const result = await runChunkedExecutionV1(plan, deps);

    expect(result.status).toBe("COMPLETED");
    expect(result.chunkResults.length).toBe(2);
    expect(result.chunkResults[0].routeSelected).toBe("CETUS");
    expect(result.chunkResults[0].routeChanged).toBe(false); // First chunk
    expect(result.chunkResults[1].routeSelected).toBe("DEEPBOOK");
    expect(result.chunkResults[1].routeChanged).toBe(true); // Route changed!
  });

  test("Test 8: both chunks route=NONE → gate may BLOCK_NO_ROUTE", async () => {
    const plan = buildChunkPlansV1({
      totalNotionalUsd: 100000,
      templateId: "TPL_RISK_50",
      baseIntent: "INCREASE_WBTC",
    });

    const deps: RunnerDeps = {
      sleepMs: async () => {},
      getPortfolioSnapshot: async () => createMockPortfolio(),
      getPhaseLabel: async () => "PHASE_NORMAL",
      selectRoute: async () => ({
        venue: "NONE",
        reasons: ["REASON_NO_AVAILABLE_ROUTES"],
      }),
      evaluateGate: async () => ({
        status: "BLOCK",
        blockReasons: ["BLOCK_NO_ROUTE"],
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
    expect(result.reasons).toContain("BLOCK_NO_ROUTE");
    expect(result.chunkResults[0].routeSelected).toBe("NONE");
  });

  test("Test 9: Runner calls selectRoute per chunk (verified)", async () => {
    const plan = buildChunkPlansV1({
      totalNotionalUsd: 100000,
      templateId: "TPL_RISK_50",
      baseIntent: "INCREASE_WBTC",
    });

    let routeCallCount = 0;

    const deps: RunnerDeps = {
      sleepMs: async () => {},
      getPortfolioSnapshot: async () => createMockPortfolio(),
      getPhaseLabel: async () => "PHASE_NORMAL",
      selectRoute: async () => {
        routeCallCount++;
        return { venue: "CETUS", reasons: [] };
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

    expect(result.status).toBe("COMPLETED");
    expect(routeCallCount).toBe(2); // selectRoute called for each chunk
  });

  test("Test 10: Phase + route diagnostics recorded in ChunkResult", async () => {
    const plan = buildChunkPlansV1({
      totalNotionalUsd: 60000,
      templateId: "TPL_RISK_50",
      baseIntent: "INCREASE_WBTC",
    });

    const deps: RunnerDeps = {
      sleepMs: async () => {},
      getPortfolioSnapshot: async () => createMockPortfolio(),
      getPhaseLabel: async () => "PHASE_PRE_SHOCK",
      selectRoute: async () => ({ venue: "DEEPBOOK", reasons: [] }),
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
        status: "SIMULATED",
        reasons: [],
      }),
    };

    const result = await runChunkedExecutionV1(plan, deps);

    expect(result.status).toBe("COMPLETED");
    expect(result.chunkResults[0].phaseLabel).toBe("PHASE_PRE_SHOCK");
    expect(result.chunkResults[0].routeSelected).toBe("DEEPBOOK");
    expect(result.chunkResults[0].routeChanged).toBe(false);
  });
});
