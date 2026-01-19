// tools/test-pr217-orch-hooks.ts
// PR217: Orchestrator Policy Hooks verification test

import { runSupervisorOnceV1 } from "../src/supervisor/supervisor";
import { StateStore, MeridianStateV1 } from "../src/state";
import * as fs from "fs";
import * as path from "path";
import * as os from "os";

async function testPolicyHooks() {
  console.log("=== PR217: Orchestrator Policy Hooks Test ===\n");

  // Mock state with GATE stop (should trigger BACKOFF_SHORT -> DEFER + policy hooks)
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
      originStopCause: "GATE", // GATE -> RETRY_5 + GUARD_GATE_PASS
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

  console.log("Step 1: Run supervisor tick (should DEFER with policy hooks)");
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
        // no-op
      },
      runTwapExecution: async () => {
        return {
          status: "COMPLETED",
          reasons: [],
          runId: "test-run-next",
        };
      },
    }
  );

  console.log("Supervisor result:", result);

  // Check queue file
  const queuePath = path.join(os.homedir(), ".meridian", "orch_queue.jsonl");
  console.log("\nStep 2: Check orchestration queue file (policy hooks)");
  console.log(`Queue path: ${queuePath}`);

  if (fs.existsSync(queuePath)) {
    const content = fs.readFileSync(queuePath, "utf8");
    const lines = content.trim().split("\n");
    console.log(`Queue has ${lines.length} instructions`);

    if (lines.length > 0) {
      const lastLine = lines[lines.length - 1];
      try {
        const instruction = JSON.parse(lastLine);
        console.log("\nLast instruction (policy hooks):");
        console.log(JSON.stringify({
          resume_id: instruction.resume_id,
          orch_policy_class: instruction.orch_policy_class,
          orch_not_before: instruction.orch_not_before,
          orch_deadline: instruction.orch_deadline,
          orch_retry_limit: instruction.orch_retry_limit,
          orch_market_guard: instruction.orch_market_guard,
          delay_class_v1: instruction.delay_class_v1,
          delay_offset_v1: instruction.delay_offset_v1,
        }, null, 2));
      } catch (e) {
        console.log("(malformed line)");
      }
    }
  } else {
    console.log("Queue file does not exist yet");
  }

  // Check telemetry
  const eventsPath = path.join(os.homedir(), ".meridian", "events.log");
  console.log("\nStep 3: Check ORCH_ENQUEUE telemetry (policy hooks)");
  console.log(`Events path: ${eventsPath}`);

  if (fs.existsSync(eventsPath)) {
    const content = fs.readFileSync(eventsPath, "utf8");
    const lines = content.trim().split("\n");

    // Find ORCH_ENQUEUE events
    const enqueueEvents = lines.filter((line) =>
      line.includes('"type":"ORCH_ENQUEUE"')
    );
    console.log(`\nORCH_ENQUEUE events: ${enqueueEvents.length}`);

    if (enqueueEvents.length > 0) {
      const lastEvent = enqueueEvents[enqueueEvents.length - 1];
      try {
        const event = JSON.parse(lastEvent);
        console.log("\nLast ORCH_ENQUEUE event (policy hooks labels):");
        console.log(JSON.stringify({
          orch_policy_class: event.labels.orch_policy_class,
          orch_not_before: event.labels.orch_not_before,
          orch_deadline: event.labels.orch_deadline,
          orch_retry_limit: event.labels.orch_retry_limit,
          orch_market_guard: event.labels.orch_market_guard,
          delay_class_v1: event.labels.delay_class_v1,
          delay_offset_v1: event.labels.delay_offset_v1,
        }, null, 2));
      } catch (e) {
        console.log("(malformed event)");
      }
    }
  } else {
    console.log("Events file does not exist yet");
  }

  console.log("\n=== Verification ===");
  console.log("Expected for GATE stop with BACKOFF_SHORT:");
  console.log("  orch_policy_class: DELAY_WINDOW");
  console.log("  orch_not_before: NB_2M");
  console.log("  orch_deadline: DL_1H");
  console.log("  orch_retry_limit: RETRY_5");
  console.log("  orch_market_guard: GUARD_GATE_PASS");
  console.log("\n=== Test Complete ===");
}

testPolicyHooks().catch((e) => {
  console.error(e);
  process.exit(1);
});
