// tools/test-pr218-orch-feedback.ts
// PR218: Orchestrator Feedback Loop end-to-end test

import { runSupervisorOnceV1 } from "../src/supervisor/supervisor";
import { StateStore, MeridianStateV1 } from "../src/state";
import {
  OrchestrationResultV1,
  appendOrchResultV1,
  loadOrchResultLinesV1,
  loadOrchResultSeenSetV1,
} from "../src/orchestrator/interface";
import * as fs from "fs";
import * as path from "path";
import * as os from "os";

async function testOrchFeedback() {
  console.log("=== PR218: Orchestrator Feedback Loop Test ===\n");

  // Setup: Clear result and seen files
  const resultPath = path.join(os.homedir(), ".meridian", "orch_result.jsonl");
  const seenPath = path.join(os.homedir(), ".meridian", "orch_result_seen.jsonl");
  const eventsPath = path.join(os.homedir(), ".meridian", "events.log");

  console.log("Step 1: Clear result, seen, and events files");
  if (fs.existsSync(resultPath)) {
    fs.unlinkSync(resultPath);
    console.log("  Cleared orch_result.jsonl");
  }
  if (fs.existsSync(seenPath)) {
    fs.unlinkSync(seenPath);
    console.log("  Cleared orch_result_seen.jsonl");
  }
  if (fs.existsSync(eventsPath)) {
    fs.unlinkSync(eventsPath);
    console.log("  Cleared events.log");
  }

  // Test resume_id (will be used for result matching)
  const testResumeId = "RESUME_TEST_PR218";

  // Mock state with STOPPED resume (no active run)
  const mockState: MeridianStateV1 = {
    version: "v1",
    updatedAtTs: Date.now(),
    warnings: [],
    lastRun: {
      status: "STOPPED",
      warnings: [],
      resumeId: testResumeId, // Match the test resume_id
    } as any,
    resumeState: {
      status: "STOPPED",
      stopReason: "STOP_NO_ROUTE",
      stopAtTs: Date.now() - 300000, // 5 minutes ago
      warnings: [],
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
    patchState: async (partial: any) => {
      // Update mockState with partial
      if (partial.resumeState) {
        mockState.resumeState = {
          ...mockState.resumeState,
          ...partial.resumeState,
        };
      }
      return {
        status: "OK" as const,
        state: mockState,
        warnings: [],
      };
    },
  };

  console.log("\nStep 2: Run supervisor tick (no results available yet)");
  const result1 = await runSupervisorOnceV1(
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

  console.log("  Supervisor result:", result1);
  console.log("  (Should show no results processed)");

  // Step 3: Write a result record (simulating orchestrator)
  console.log("\nStep 3: Write orchestrator result (SUCCEEDED)");
  const testResultId = `RESULT_${Date.now()}_${Math.floor(Math.random() * 100000)}`;

  const testResult: OrchestrationResultV1 = {
    v: "v1",
    resume_id: testResumeId,
    result_id: testResultId,
    status: "SUCCEEDED",
    outcome_codes: ["ORCH_EXEC_SUCCESS", "ORCH_POLICY_PASS"],
    hint_codes: ["TIMING_DELAY_2M", "STRAT_FROM_GATE"],
  };

  await appendOrchResultV1(testResult);
  console.log("  Written result:");
  console.log(JSON.stringify(testResult, null, 2));

  // Verify file was written
  const resultsLoaded = loadOrchResultLinesV1(10);
  console.log(`  Loaded ${resultsLoaded.length} results from file`);

  // Step 4: Run supervisor tick again (should process the result)
  console.log("\nStep 4: Run supervisor tick (should process result)");
  const result2 = await runSupervisorOnceV1(
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

  console.log("  Supervisor result:", result2);

  // Step 5: Verify result was marked as seen
  console.log("\nStep 5: Verify result was marked as seen");
  const seenSet = loadOrchResultSeenSetV1();
  console.log(`  Seen set size: ${seenSet.size}`);
  if (seenSet.has(testResultId)) {
    console.log(`  ✓ Result ${testResultId} marked as seen`);
  } else {
    console.log(`  ✗ Result ${testResultId} NOT marked as seen`);
  }

  // Step 6: Verify ORCH_RESULT telemetry event
  console.log("\nStep 6: Verify ORCH_RESULT telemetry event");
  if (fs.existsSync(eventsPath)) {
    const content = fs.readFileSync(eventsPath, "utf8");
    const lines = content.trim().split("\n");

    // Find ORCH_RESULT events
    const resultEvents = lines.filter((line) =>
      line.includes('"type":"ORCH_RESULT"')
    );
    console.log(`  ORCH_RESULT events: ${resultEvents.length}`);

    if (resultEvents.length > 0) {
      const lastEvent = resultEvents[resultEvents.length - 1];
      try {
        const event = JSON.parse(lastEvent);
        console.log("  Last ORCH_RESULT event:");
        console.log(JSON.stringify({
          resume_id: event.labels.resume_id,
          orch_result_id: event.labels.orch_result_id,
          orch_result_status: event.labels.orch_result_status,
          orch_outcome_codes_status: event.labels.orch_outcome_codes_status,
          orch_outcome_codes: event.labels.orch_outcome_codes,
          orch_hint_codes_status: event.labels.orch_hint_codes_status,
          orch_hint_codes: event.labels.orch_hint_codes,
        }, null, 2));
      } catch (e) {
        console.log("  (malformed event)");
      }
    }
  } else {
    console.log("  Events file does not exist");
  }

  // Step 7: Verify ResumeState was updated
  console.log("\nStep 7: Verify ResumeState feedback fields");
  if (mockState.resumeState?.orchLastStatus) {
    console.log(`  ✓ orchLastStatus: ${mockState.resumeState.orchLastStatus}`);
    console.log(`  ✓ orchLastResultId: ${mockState.resumeState.orchLastResultId}`);
    if (mockState.resumeState.orchLastOutcomeCodes) {
      console.log(`  ✓ orchLastOutcomeCodes: ${mockState.resumeState.orchLastOutcomeCodes.join(", ")}`);
    }
  } else {
    console.log("  ✗ ResumeState feedback fields NOT set");
  }

  // Step 8: Verify idempotency (run again, should not reprocess)
  console.log("\nStep 8: Verify idempotency (run again)");
  const result3 = await runSupervisorOnceV1(
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

  console.log("  Supervisor result:", result3);
  console.log("  (Should show result already seen, not reprocessed)");

  // Count ORCH_RESULT events
  if (fs.existsSync(eventsPath)) {
    const content = fs.readFileSync(eventsPath, "utf8");
    const lines = content.trim().split("\n");
    const resultEvents = lines.filter((line) =>
      line.includes('"type":"ORCH_RESULT"')
    );
    console.log(`  Total ORCH_RESULT events: ${resultEvents.length}`);
    console.log("  (Should be 1, not 2 - idempotency working)");
  }

  console.log("\n=== Verification Summary ===");
  console.log("Expected behavior:");
  console.log("  1. No results on first tick");
  console.log("  2. Result written to orch_result.jsonl");
  console.log("  3. Second tick processes result, emits ORCH_RESULT event");
  console.log("  4. Result marked as seen in orch_result_seen.jsonl");
  console.log("  5. ResumeState updated with orchLastStatus/orchLastResultId");
  console.log("  6. Third tick skips already-seen result (idempotency)");
  console.log("\n=== Test Complete ===");
}

testOrchFeedback().catch((e) => {
  console.error(e);
  process.exit(1);
});
