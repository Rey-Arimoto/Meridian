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

  // PR196/PR197/PR198/PR199: Set execution mode (default: SIM_ONLY for safety)
  // Available modes: "SIM_ONLY" | "DRY_RUN" | "LIVE"
  (runPlan as any).executionMode = "SIM_ONLY";
  // Uncomment to test DRY_RUN mode:
  // (runPlan as any).executionMode = "DRY_RUN";
  // Uncomment to test LIVE unlock scenarios (PR199):
  // (runPlan as any).executionMode = "LIVE";
  //
  // PR199: To test LIVE unlock scenarios, also set environment variable:
  // - UNLOCKED: export MERIDIAN_LIVE_UNLOCK=TRUE + getSpecLockStatus returns "ACTIVE_OK"
  // - LOCKED_ENV: (no env var) + getSpecLockStatus returns "ACTIVE_OK"
  // - LOCKED_SPEC: export MERIDIAN_LIVE_UNLOCK=TRUE + getSpecLockStatus returns "LOCKED_EXPIRED"

  // PR212d: Harness forced timeout for parity proof
  // When MERIDIAN_HARNESS_FORCE_TIMEOUT=TRUE, force timeoutStatus to TIMEOUT_EXCEEDED
  const forceTimeout = process.env.MERIDIAN_HARNESS_FORCE_TIMEOUT === "TRUE";
  const TIMEOUT_OFFSET_MS = 61_000; // 61 seconds (exceeds MAX_RUN_DURATION_MS = 60s)

  // getNowMs: Allow a few calls before forcing timeout
  // This lets us pass the initial chunk timeout check and reach PHASE_POLICY_EVAL
  // Call sequence: 1=startedAtMs, 2=first timeout check, 3=PHASE_POLICY_EVAL
  let callCount = 0;
  let startTime: number | undefined;
  const CALLS_BEFORE_TIMEOUT = 2; // Trigger timeout on call 3 (PHASE_POLICY_EVAL)

  const getNowMsForced = () => {
    callCount++;
    if (startTime === undefined) {
      startTime = Date.now();
    }
    if (callCount <= CALLS_BEFORE_TIMEOUT) {
      return startTime;
    }
    return startTime + TIMEOUT_OFFSET_MS;
  };

  const res = await runChunkedExecutionV1(runPlan as any, {
    // PR212d: Provide getNowMs to control timeout in harness
    getNowMs: forceTimeout ? getNowMsForced : undefined, // Use default Date.now() when not forcing

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

    // PR199: Spec lock status for LIVE unlock handshake
    getSpecLockStatus: async () => ({ status: "ACTIVE_OK" }), // Default: unlocked

    // PR212c: Provide phase label in harness so PHASE_POLICY_EVAL emits
    getPhaseLabel: async () => "PHASE_NORMAL",

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
        // PR192/PR203: Add execution reason codes for telemetry testing
        // PR203: Include normalized TX_REASON_* taxonomy with legacy REASON_*
        executionReasonCodes: [
          "TX_REASON_DRAFT_OK",
          "REASON_DRAFT_OK",
          "TX_REASON_SIMULATE_ONLY",
          "REASON_SIMULATE_ONLY",
          "TX_REASON_ROUTE_CETUS_SELECTED",
          "REASON_ROUTE_CETUS_SELECTED",
          "TX_REASON_SLIPPAGE_ELEVATED",
          "REASON_SLIPPAGE_ELEVATED",
          "REASON_SLIPPAGE_SLIPPAGE_ELEVATED", // legacy duplicated form
          "TX_REASON_MINOUT_ZERO",
          "REASON_MINOUT_ZERO",
        ],
      } as any),

    // ---- Execute: Mode-aware (PR197/PR198/PR203) ----
    executeTx: async (args: any) => {
      // PR197: Respect executionMode
      // PR203: Add EXEC_REASON_* taxonomy (legacy REASON_* preserved)
      const mode = args.executionMode || "SIM_ONLY";
      if (mode === "SIM_ONLY") {
        return {
          status: "SIMULATED",
          reasons: ["EXEC_REASON_SIM_ONLY", "REASON_EXEC_SIM_ONLY"],
        } as any;
      } else if (mode === "DRY_RUN") {
        return {
          status: "DRY_RUN",
          reasons: ["EXEC_REASON_DRY_RUN", "REASON_EXEC_DRY_RUN"],
        } as any;
      } else if (mode === "LIVE") {
        // PR198: Structural block - LIVE execution impossible in v1.4
        // This guarantees no broadcast can occur
        return {
          status: "EXECUTION_DISABLED",
          reasons: ["EXEC_REASON_LIVE_BLOCKED_V1_4", "REASON_EXEC_LIVE_BLOCKED_V1_4"],
        } as any;
      }
      return {
        status: "ERROR",
        reasons: ["EXEC_REASON_UNKNOWN_MODE", "REASON_EXEC_UNKNOWN_MODE"],
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
