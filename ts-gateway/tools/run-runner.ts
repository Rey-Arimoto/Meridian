// tools/run-runner.ts
import { buildChunkPlansV1 } from "../src/rebalance/chunking";
import { runChunkedExecutionV1 } from "../src/rebalance/runner";

async function main() {
  // 1) ここが重要：chunks を自作しない。必ず builder を使う。
  const runPlan = buildChunkPlansV1({
    totalNotionalUsd: 30000, // >0 (must exceed MIN_CHUNK_NOTIONAL_USD=10k per chunk)
    templateId: "TPL_RISK_50",
    baseIntent: "INCREASE_WBTC", // NOOP だと chunks が空になり得る
    maxChunks: 2, // 1以上
    chunkNotionalUsd: 15000, // >0 (must exceed MIN_CHUNK_NOTIONAL_USD=10k)
    runId: `run-${Date.now()}`,
    getNowMs: () => Date.now(),
  });

  const res = await runChunkedExecutionV1(runPlan as any, {
    // --- PR161/PR184: 通電証拠を増やす（任意だが推奨） ---
    getPhaseLabel: async () => "PHASE_NORMAL" as any,
    getObserveState: async () => ({ status: "AVAILABLE" } as any),

    // ---- 必須 deps ----
    getPortfolioSnapshot: async () =>
      ({
        balances: { SUI: "1", USDC: "1000", WBTC: "0" },
        weights: { USDC: 1, WBTC: 0 },
        pricesUsd: { USDC: 1, WBTC: 45000, SUI: 1 }, // 最低限
        timestamp: Date.now(), // 必須
      } as any),

    evaluateGate: async () => ({ status: "PASS", blockReasons: [], warnings: [] }),

    evaluatePolicy: async () => ({
      allowExecution: false, // SIM_ONLY
      status: "SIM_ONLY",
      reasons: ["SIM_ONLY"],
    }),

    // ---- PR187 QuoteSources（通電用スタブ：最低限）----
    // Runner の型に寄せて args を受け取る（将来 as any を外しやすい）
    getQuoteSources: async (_args: any) =>
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

    // ---- 通電用：Draft/Execute はダミーでOK ----
    buildTxDraft: async (_args: any) =>
      ({
        status: "DRAFT",
        simulateOnly: true,
        route: "CETUS",
        action: "SWAP_USDC_TO_WBTC",
        amountIn: "100",
        minOut: "0",
        slippageBps: 200,
        deadlineSeconds: 120,
        checks: [],
        notes: [],
        errors: [],
      } as any),

    executeTx: async () => ({ status: "SIMULATED", reasons: ["SIM_ONLY"] } as any),

    // 速度上げたいなら sleep は 0 に
    sleepMs: async () => {},
  } as any);

  console.log("RUN RESULT:");
  console.log(JSON.stringify(res, null, 2));

  console.log("\nEVENTS (tail):");
  console.log(
    "Run: grep -nE 'QUOTE_NORMALIZED|OBSERVE_DEGRADED_LEVEL|RUN_' ~/.meridian/events.log | tail -n 200"
  );
}

main().catch((e) => {
  console.error(e);
  process.exit(1);
});
