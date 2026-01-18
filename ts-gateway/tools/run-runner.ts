// tools/run-runner.ts
import { buildChunkPlansV1 } from "../src/rebalance/chunking";
import { runChunkedExecutionV1 } from "../src/rebalance/runner";

async function main() {
  // NOTE:
  // - MIN_CHUNK_NOTIONAL_USD を満たすため大きめにする（現行コードの閾値に追随）
  // - NOOP を避けて必ず chunk が出るようにする
  const runPlan = buildChunkPlansV1({
    totalNotionalUsd: 30000,
    templateId: "TPL_RISK_50",
    baseIntent: "INCREASE_WBTC",
    maxChunks: 2,
    chunkNotionalUsd: 15000,
    runId: `run-${Date.now()}`,
    getNowMs: () => Date.now(),
  });

  // PR196/PR197/PR198: Set execution mode (default: SIM_ONLY for safety)
  // Available modes: "SIM_ONLY" | "DRY_RUN" | "LIVE"
  (runPlan as any).executionMode = "SIM_ONLY";
  // Uncomment to test DRY_RUN mode:
  // (runPlan as any).executionMode = "DRY_RUN";
  // Uncomment to test LIVE blocking (PR198):
  // (runPlan as any).executionMode = "LIVE";

  const res = await runChunkedExecutionV1(runPlan as any, {
    // ---- 必須 deps ----
    getPortfolioSnapshot: async () =>
      ({
        balances: { SUI: "1", USDC: "1000", WBTC: "0" },
        weights: { USDC: 1, WBTC: 0 },
        pricesUsd: { USDC: 1, WBTC: 45000, SUI: 1 },
        timestamp: Date.now(),
      } as any),

    // PR184: observe degrade を出すための最低限（NONE を返す）
    getObserveState: async () =>
      ({
        status: "AVAILABLE",
        sdkHealth: "WS_ALIVE",
        sourceStatus: "AVAILABLE",
        warnings: [],
      } as any),

    // ---- Gate: 通電用に PASS ----
    // (ここで BLOCK すると CHUNK が止まるのでまずは PASS)
    evaluateGate: async () => ({
      status: "PASS",
      blockReasons: [],
      warnings: [],
    }),

    // ---- Policy: ALLOW で STOP させない ----
    // ただし executeTx は SIMULATED で実取引しない
    evaluatePolicy: async () =>
      ({
        allowExecution: true,
        status: "ALLOW",
        reasons: [],
      } as any),

    // ---- PR187 QuoteSources（通電用スタブ：router が必ず CETUS を選べる形）----
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

    // ---- TxDraft: simulateOnly true を固定（安全）----
    // runner 側の wiring を検証したいので args は受ける（使わなくてOK）
    buildTxDraft: async (_args: any) =>
      ({
        status: "DRAFT",
        simulateOnly: true,
        route: "CETUS",
        action: "SWAP_USDC_TO_WBTC",
        amountIn: "100",
        minOut: "0",
        slippageBps: 200,
        slippageLabel: "SLIPPAGE_ELEVATED", // PR190: Label-only traceability
        deadlineSeconds: 120,
        checks: [],
        notes: ["NOTE_HARNESS_DUMMY_DRAFT"],
        errors: [],
        // PR192: Add execution reason codes for telemetry testing
        executionReasonCodes: [
          "REASON_DRAFT_OK",
          "REASON_SIMULATE_ONLY",
          "REASON_ROUTE_CETUS_SELECTED",
          "REASON_SLIPPAGE_ELEVATED",
          "REASON_SLIPPAGE_SLIPPAGE_ELEVATED",
          "REASON_MINOUT_ZERO",
        ],
      } as any),

    // ---- Execute: Mode-aware (PR197/PR198) ----
    executeTx: async (args: any) => {
      // PR197: Respect executionMode
      const mode = args.executionMode || "SIM_ONLY";
      if (mode === "SIM_ONLY") {
        return {
          status: "SIMULATED",
          reasons: ["REASON_EXEC_SIM_ONLY"],
        } as any;
      } else if (mode === "DRY_RUN") {
        return {
          status: "DRY_RUN",
          reasons: ["REASON_EXEC_DRY_RUN"],
        } as any;
      } else if (mode === "LIVE") {
        // PR198: Structural block - LIVE execution impossible in v1.4
        // This guarantees no broadcast can occur
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

    // 高速化
    sleepMs: async () => {},
  } as any);

  console.log("RUN RESULT:");
  console.log(JSON.stringify(res, null, 2));

  // 便利：最後に events の主要タイプを表示
  console.log("\n--- Tail events.log (last 40) ---");
  try {
    // eslint-disable-next-line @typescript-eslint/no-var-requires
    const fs = require("fs");
    // eslint-disable-next-line @typescript-eslint/no-var-requires
    const os = require("os");
    // eslint-disable-next-line @typescript-eslint/no-var-requires
    const path = require("path");
    const p = path.join(os.homedir(), ".meridian", "events.log");
    const txt = fs.readFileSync(p, "utf8").trim().split("\n").slice(-40).join("\n");
    console.log(txt);
  } catch (e) {
    console.log("(events.log not found or unreadable)");
  }
}

main().catch((e) => {
  console.error(e);
  process.exit(1);
});
