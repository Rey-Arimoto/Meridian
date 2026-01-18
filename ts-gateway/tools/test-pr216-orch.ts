// tools/test-pr216-orch.ts
// PR216: Orchestration interface end-to-end test

import { runSupervisorOnceV1 } from "../src/supervisor/supervisor";
import { StateStore, MeridianStateV1 } from "../src/state";
import * as fs from "fs";
import * as path from "path";
import * as os from "os";

async function testOrchestrationFlow() {
  console.log("=== PR216: Orchestration Interface Test ===\n");

  // Mock state with GATE stop (should trigger BACKOFF_SHORT -> DEFER)
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
      stopReason: "STOP_NO_ROUTE",
      stopAtTs: Date.now() - 300000, // 5 minutes ago
      warnings: [],
      originStopCause: "GATE", // GATE -> RETRY_SAFE_SIM_ONLY -> BACKOFF_SHORT -> DEFER
      originRunReasonCodes: ["RUN_REASON_GATE_BLOCKED"],
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
  let capturedFields: any = {};

  console.log("Step 1: Run supervisor tick (should DEFER)");
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
        nowTs: Date.now(),
        oracleStatus: "AVAILABLE",
        gateStatus: "PASS",
        phaseLabel: "PHASE_NORMAL",
        routeAvailable: true,
        hardStopActive: false,
        policyEnvEnabled: true,
      }),
      setRunPlanResumeFields: (fields: any) => {
        capturedFields = fields;
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

  console.log("Supervisor result:", result);
  console.log("Execution called:", executionCalled);
  console.log("Captured fields:", JSON.stringify(capturedFields, null, 2));

  // Check queue file
  const queuePath = path.join(os.homedir(), ".meridian", "orch_queue.jsonl");
  console.log("\nStep 2: Check orchestration queue file");
  console.log(`Queue path: ${queuePath}`);

  if (fs.existsSync(queuePath)) {
    const content = fs.readFileSync(queuePath, "utf8");
    const lines = content.trim().split("\n");
    console.log(`Queue has ${lines.length} instructions`);
    console.log("Last 3 instructions:");
    lines.slice(-3).forEach((line) => {
      try {
        const instruction = JSON.parse(line);
        console.log(JSON.stringify(instruction, null, 2));
      } catch (e) {
        console.log("(malformed line)");
      }
    });
  } else {
    console.log("Queue file does not exist yet");
  }

  // Check telemetry
  const eventsPath = path.join(os.homedir(), ".meridian", "events.log");
  console.log("\nStep 3: Check telemetry events");
  console.log(`Events path: ${eventsPath}`);

  if (fs.existsSync(eventsPath)) {
    const content = fs.readFileSync(eventsPath, "utf8");
    const lines = content.trim().split("\n");

    // Find RESUME_REEXEC_DEFERRED events
    const deferredEvents = lines.filter((line) =>
      line.includes('"type":"RESUME_REEXEC_DEFERRED"')
    );
    console.log(`RESUME_REEXEC_DEFERRED events: ${deferredEvents.length}`);
    if (deferredEvents.length > 0) {
      console.log("Last DEFERRED event:");
      console.log(deferredEvents[deferredEvents.length - 1]);
    }

    // Find ORCH_ENQUEUE events
    const enqueueEvents = lines.filter((line) =>
      line.includes('"type":"ORCH_ENQUEUE"')
    );
    console.log(`\nORCH_ENQUEUE events: ${enqueueEvents.length}`);
    if (enqueueEvents.length > 0) {
      console.log("Last ENQUEUE event:");
      console.log(enqueueEvents[enqueueEvents.length - 1]);
    }

    // Find ORCH_ACK events
    const ackEvents = lines.filter((line) => line.includes('"type":"ORCH_ACK"'));
    console.log(`\nORCH_ACK events: ${ackEvents.length}`);
    if (ackEvents.length > 0) {
      console.log("Last ACK event:");
      console.log(ackEvents[ackEvents.length - 1]);
    }
  } else {
    console.log("Events file does not exist yet");
  }

  console.log("\n=== Test Complete ===");
  console.log("Next steps:");
  console.log("1. Run: npx ts-node tools/orch-ack.ts");
  console.log("2. Run this test again to see ORCH_ACK events");
}

testOrchestrationFlow().catch((e) => {
  console.error(e);
  process.exit(1);
});
