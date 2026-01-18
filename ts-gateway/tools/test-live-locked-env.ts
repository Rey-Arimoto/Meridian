// Test LIVE LOCKED_ENV scenario (no env var)
import { buildChunkPlansV1 } from "../src/rebalance/chunking";
import { runChunkedExecutionV1 } from "../src/rebalance/runner";

async function main() {
  const runPlan = buildChunkPlansV1({
    totalNotionalUsd: 30000,
    templateId: "TPL_RISK_50",
    baseIntent: "INCREASE_WBTC",
    maxChunks: 1,
    chunkNotionalUsd: 30000,
    runId: "run-test-locked-env",
    getNowMs: () => Date.now(),
  });

  // Set LIVE mode (but env var MERIDIAN_LIVE_UNLOCK is not set)
  (runPlan as any).executionMode = "LIVE";

  const res = await runChunkedExecutionV1(runPlan as any, {
    getPortfolioSnapshot: async () =>
      ({
        balances: { SUI: "1", USDC: "1000", WBTC: "0" },
        weights: { USDC: 1, WBTC: 0 },
        pricesUsd: { USDC: 1, WBTC: 45000, SUI: 1 },
        timestamp: Date.now(),
      } as any),

    getObserveState: async () =>
      ({
        status: "AVAILABLE",
        sdkHealth: "WS_ALIVE",
        sourceStatus: "AVAILABLE",
        warnings: [],
      } as any),

    getSpecLockStatus: async () => ({ status: "ACTIVE_OK" }), // Spec lock OK, but env var missing

    evaluateGate: async () => ({
      status: "PASS",
      blockReasons: [],
      warnings: [],
    }),

    evaluatePolicy: async () =>
      ({
        allowExecution: true,
        status: "ALLOW",
        reasons: [],
      } as any),

    getQuoteSources: async () =>
      ({
        deepbookWs: { bids: [], asks: [], ts: Date.now(), status: "UNAVAILABLE" },
        deepbookHttp: { bids: [], asks: [], ts: Date.now(), status: "UNAVAILABLE" },
        cetusPool: {
          ts: Date.now(),
          status: "AVAILABLE",
          liquidityUsd: 500000,
          price: 45000,
        },
      } as any),

    buildTxDraft: async (_args: any) =>
      ({
        status: "DRAFT",
        simulateOnly: true,
        route: "CETUS",
        action: "SWAP_USDC_TO_WBTC",
        amountIn: "100",
        minOut: "0",
        slippageBps: 200,
        slippageLabel: "SLIPPAGE_ELEVATED",
        deadlineSeconds: 120,
        checks: [],
        notes: ["NOTE_TEST_LIVE_LOCKED_ENV"],
        errors: [],
        executionReasonCodes: ["REASON_TEST_LIVE_LOCKED_ENV"],
      } as any),

    executeTx: async (args: any) => {
      const mode = args.executionMode || "SIM_ONLY";
      if (mode === "LIVE") {
        return {
          status: "EXECUTION_DISABLED",
          reasons: ["REASON_EXEC_LIVE_BLOCKED_V1_4"],
        } as any;
      }
      return {
        status: "ERROR",
        reasons: ["REASON_EXEC_UNKNOWN_MODE"],
      } as any;
    },

    sleepMs: async () => {},
  } as any);

  console.log("Test result:", res.status);
  console.log("Reasons:", res.reasons);
}

main().catch((e) => {
  console.error(e);
  process.exit(1);
});
