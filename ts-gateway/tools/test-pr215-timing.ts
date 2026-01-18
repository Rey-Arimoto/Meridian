// tools/test-pr215-timing.ts
// PR215: Test resume timing control (IMMEDIATE vs DEFERRED)

import { runSupervisorOnceV1 } from "../src/supervisor/supervisor";
import { StateStore, MeridianStateV1 } from "../src/state";
import { buildChunkPlansV1 } from "../src/rebalance/chunking";

async function testScenario(scenarioName: string, stopCause: any) {
  console.log(`\n=== ${scenarioName} ===`);

  // Create a mock runPlan
  const runPlan = buildChunkPlansV1({
    totalNotionalUsd: 30000,
    templateId: "TPL_RISK_50",
    baseIntent: "INCREASE_WBTC",
    maxChunks: 2,
    chunkNotionalUsd: 15000,
    runId: `test-run-${Date.now()}`,
    getNowMs: () => Date.now(),
  });

  // Mock state with resume context
  const mockState: MeridianStateV1 = {
    version: "v1",
    updatedAtTs: Date.now(),
    warnings: [],
    lastRun: {
      status: "STOPPED",
      warnings: [],
    },
    resumeState: {
      status: "STOPPED",
      stopReason: "STOP_PHASE_POLICY",
      stopAtTs: Date.now() - 60000,
      warnings: [],
      originStopCause: stopCause, // Test different stop causes
      originRunReasonCodes: ["RUN_REASON_TIMEOUT"],
    },
  };

  // Mock store
  const mockStore: StateStore = {
    readState: async () => ({
      status: "OK" as const,
      state: mockState,
      warnings: [],
    }),
    writeState: async () => ({
      status: "OK" as const,
      state: mockState,
      warnings: [],
    }),
    patchState: async () => ({
      status: "OK" as const,
      state: mockState,
      warnings: [],
    }),
  };

  let executionCalled = false;

  // Track what fields were set on runPlan
  let capturedFields: any = {};

  // Execute supervisor tick
  const result = await runSupervisorOnceV1(
    mockStore,
    {}, // cfg
    {
      // deps
      evaluatePolicy: async () => ({
        allowExecution: true,
        hardStopActive: false,
        status: "ALLOW",
        reasons: [],
      }),
      getResumeInputs: async () => ({
        oracleStatus: "AVAILABLE",
        phase: "PHASE_NORMAL",
        stopAge: 65000,
        nowTs: Date.now(),
      }),
      setRunPlanResumeFields: (fields: any) => {
        // Capture fields that would be set on runPlan
        capturedFields = fields;
        // Apply them to our mock runPlan
        Object.assign(runPlan, fields);
      },
      runTwapExecution: async () => {
        executionCalled = true;
        return {
          status: "COMPLETED",
          reasons: [],
          runId: "test-run-next",
        };
      },
    }
  );

  console.log("Result:", result);
  console.log("Execution called:", executionCalled);
  console.log("Captured fields:", JSON.stringify(capturedFields, null, 2));
}

async function main() {
  console.log("PR215: Resume Timing Control Verification");
  console.log("==========================================");

  // Scenario 1: TIMEOUT → RETRY_IMMEDIATE → IMMEDIATE → Execute
  await testScenario("TIMEOUT (IMMEDIATE execution)", "TIMEOUT");

  // Scenario 2: GATE → RETRY_SAFE_SIM_ONLY → BACKOFF_SHORT → Deferred
  await testScenario("GATE (BACKOFF_SHORT deferred)", "GATE");

  // Scenario 3: POLICY → WAIT_FOR_UNLOCK → MANUAL → Deferred
  await testScenario("POLICY (MANUAL deferred)", "POLICY");

  // Show recent telemetry events
  console.log("\n--- Tail events.log (last 20) ---");
  try {
    const fs = require("fs");
    const os = require("os");
    const path = require("path");
    const p = path.join(os.homedir(), ".meridian", "events.log");
    const txt = fs.readFileSync(p, "utf8").trim().split("\n").slice(-20).join("\n");
    console.log(txt);
  } catch (e) {
    console.log("(events.log not found or unreadable)");
  }
}

main().catch((e) => {
  console.error(e);
  process.exit(1);
});
