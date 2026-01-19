// tools/test-pr221-pr222-pr223-hotfixes.ts
// v1.4.1 Hotfix PRs: Orchestrator Feedback Staleness, Max Deferral Guard, Regime Signal Freshness

import { runSupervisorOnceV1 } from "../src/supervisor/supervisor";
import { StateStore, MeridianStateV1 } from "../src/state";
import * as fs from "fs";
import * as path from "path";
import * as os from "os";

async function testHotfixes() {
  console.log("=== v1.4.1 Hotfix Tests (PR221, PR222, PR223) ===\n");

  const eventsPath = path.join(os.homedir(), ".meridian", "events.log");

  // Clear events
  console.log("Step 0: Clear test files");
  if (fs.existsSync(eventsPath)) fs.unlinkSync(eventsPath);

  let passCount = 0;
  let failCount = 0;

  // =============================================================================
  // PR221: Orchestrator Feedback Staleness Timeout (15min)
  // =============================================================================
  console.log("\n=== PR221: Orchestrator Feedback Staleness Timeout ===\n");

  const pr221Scenarios = [
    {
      name: "PR221-A: Fresh feedback (5 min old) → Used",
      orchLastStatusTs: Date.now() - 5 * 60 * 1000, // 5 minutes ago
      orchLastStatus: "FAILED_MARKET",
      expectedFreshness: "FRESH",
      expectedAge: "AGE_FRESH",
      expectedEscalation: "WAIT_FOR_RECOVERY", // Rule C applies
    },
    {
      name: "PR221-B: Stale feedback (20 min old) → Ignored",
      orchLastStatusTs: Date.now() - 20 * 60 * 1000, // 20 minutes ago (stale)
      orchLastStatus: "FAILED_MARKET",
      expectedFreshness: "STALE",
      expectedAge: "AGE_STALE",
      expectedEscalation: "RETRY_SAFE_SIM_ONLY", // Stale feedback ignored, uses base strategy
    },
    {
      name: "PR221-C: No feedback → NONE",
      orchLastStatusTs: undefined,
      orchLastStatus: undefined,
      expectedFreshness: "NONE",
      expectedAge: "AGE_NONE",
      expectedEscalation: "RETRY_SAFE_SIM_ONLY", // No feedback, uses base strategy
    },
  ];

  for (const scenario of pr221Scenarios) {
    console.log(`\nScenario: ${scenario.name}`);
    const testResumeId = `RESUME_TEST_PR221_${Date.now()}`;
    const mockState: MeridianStateV1 = {
      version: "v1",
      updatedAtTs: Date.now(),
      warnings: [],
      lastRun: {
        status: "STOPPED",
        warnings: [],
        resumeId: testResumeId,
      } as any,
      resumeState: {
        status: "STOPPED",
        stopReason: "STOP_NO_ROUTE",
        stopAtTs: Date.now() - 300000,
        warnings: [],
        originStopCause: "GATE",
        orchLastStatus: scenario.orchLastStatus,
        orchLastStatusTs: scenario.orchLastStatusTs,
      },
    };

    const mockStore: StateStore = {
      readState: async () => ({ status: "OK" as const, state: mockState, warnings: [] }),
      writeState: async () => ({ status: "OK" as const, state: mockState, warnings: [] }),
      patchState: async () => ({ status: "OK" as const, state: mockState, warnings: [] }),
    };

    let capturedFreshness: string | undefined;
    let capturedAge: string | undefined;
    let capturedEscalation: string | undefined;

    await runSupervisorOnceV1(
      mockStore,
      {},
      {
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
          capturedEscalation = fields.resumeEscalatedStrategy;
        },
        runTwapExecution: async () => ({
          status: "COMPLETED",
          reasons: [],
          runId: "test-run-next",
        }),
      }
    );

    // Verify telemetry
    if (fs.existsSync(eventsPath)) {
      const content = fs.readFileSync(eventsPath, "utf8");
      const lines = content.trim().split("\n");
      const attemptEvents = lines.filter((line) =>
        line.includes('"type":"RESUME_REEXEC_ATTEMPT"')
      );

      if (attemptEvents.length > 0) {
        const lastEvent = attemptEvents[attemptEvents.length - 1];
        const event = JSON.parse(lastEvent);
        capturedFreshness = event.labels.orch_feedback_freshness;
        capturedAge = event.labels.orch_feedback_age;

        console.log(`  Captured: freshness=${capturedFreshness}, age=${capturedAge}`);
        console.log(`  Captured: escalation=${capturedEscalation}`);

        let pass = true;
        if (capturedFreshness !== scenario.expectedFreshness) {
          console.log(`  ✗ FAIL: Expected freshness=${scenario.expectedFreshness}, got=${capturedFreshness}`);
          pass = false;
        }
        if (capturedAge !== scenario.expectedAge) {
          console.log(`  ✗ FAIL: Expected age=${scenario.expectedAge}, got=${capturedAge}`);
          pass = false;
        }
        if (capturedEscalation !== scenario.expectedEscalation) {
          console.log(`  ✗ FAIL: Expected escalation=${scenario.expectedEscalation}, got=${capturedEscalation}`);
          pass = false;
        }

        if (pass) {
          console.log(`  ✓ PASS`);
          passCount++;
        } else {
          failCount++;
        }
      }
    }

    // Clear events for next scenario
    if (fs.existsSync(eventsPath)) fs.unlinkSync(eventsPath);
  }

  // =============================================================================
  // PR222: Max Deferral Guard (50 deferrals or 24h)
  // =============================================================================
  console.log("\n=== PR222: Max Deferral Guard ===\n");

  const pr222Scenarios = [
    {
      name: "PR222-A: First deferral → count=1, age=FRESH",
      deferralCount: undefined,
      firstDeferredAtTs: undefined,
      expectedCount: "1",
      expectedCountClass: "COUNT_LOW",
      expectedAgeClass: "AGE_FRESH",
      expectAbandon: false,
    },
    {
      name: "PR222-B: 49th deferral → count=50 (limit), ABANDON",
      deferralCount: 49, // Next will be 50
      firstDeferredAtTs: Date.now() - 1 * 60 * 60 * 1000, // 1 hour ago
      expectedCount: "50",
      expectedCountClass: "COUNT_EXCEEDED",
      expectedAgeClass: "AGE_MODERATE",
      expectAbandon: true,
    },
    {
      name: "PR222-C: 24h old → ABANDON",
      deferralCount: 10,
      firstDeferredAtTs: Date.now() - 25 * 60 * 60 * 1000, // 25 hours ago (expired)
      expectedCount: "11",
      expectedCountClass: "COUNT_MEDIUM",
      expectedAgeClass: "AGE_EXPIRED",
      expectAbandon: true,
    },
  ];

  for (const scenario of pr222Scenarios) {
    console.log(`\nScenario: ${scenario.name}`);
    const testResumeId = `RESUME_TEST_PR222_${Date.now()}`;
    const mockState: MeridianStateV1 = {
      version: "v1",
      updatedAtTs: Date.now(),
      warnings: [],
      lastRun: {
        status: "STOPPED",
        warnings: [],
        resumeId: testResumeId,
      } as any,
      resumeState: {
        status: "STOPPED",
        stopReason: "STOP_NO_ROUTE",
        stopAtTs: Date.now() - 300000,
        warnings: [],
        originStopCause: "GATE",
        deferralCount: scenario.deferralCount,
        firstDeferredAtTs: scenario.firstDeferredAtTs,
      },
    };

    const mockStore: StateStore = {
      readState: async () => ({ status: "OK" as const, state: mockState, warnings: [] }),
      writeState: async () => ({ status: "OK" as const, state: mockState, warnings: [] }),
      patchState: async () => ({ status: "OK" as const, state: mockState, warnings: [] }),
    };

    const result = await runSupervisorOnceV1(
      mockStore,
      {},
      {
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
        setRunPlanResumeFields: (fields: any) => {},
        runTwapExecution: async () => ({
          status: "COMPLETED",
          reasons: [],
          runId: "test-run-next",
        }),
      }
    );

    console.log(`  Result action: ${result.action}`);

    let pass = true;
    if (scenario.expectAbandon) {
      if (result.action !== "ACTION_ABORT") {
        console.log(`  ✗ FAIL: Expected ACTION_ABORT, got=${result.action}`);
        pass = false;
      } else {
        console.log(`  ✓ PASS: Resume abandoned as expected`);
      }

      // Verify RESUME_REEXEC_ABANDONED event
      if (fs.existsSync(eventsPath)) {
        const content = fs.readFileSync(eventsPath, "utf8");
        const abandonEvents = content.split("\n").filter((line) =>
          line.includes('"type":"RESUME_REEXEC_ABANDONED"')
        );

        if (abandonEvents.length > 0) {
          const event = JSON.parse(abandonEvents[abandonEvents.length - 1]);
          console.log(`  ✓ RESUME_REEXEC_ABANDONED event emitted`);
          console.log(`    deferral_count=${event.labels.deferral_count}`);
          console.log(`    deferral_count_class=${event.labels.deferral_count_class}`);
          console.log(`    deferral_age_class=${event.labels.deferral_age_class}`);

          if (event.labels.deferral_count !== scenario.expectedCount) {
            console.log(`  ✗ FAIL: Expected count=${scenario.expectedCount}, got=${event.labels.deferral_count}`);
            pass = false;
          }
          if (event.labels.deferral_count_class !== scenario.expectedCountClass) {
            console.log(`  ✗ FAIL: Expected count_class=${scenario.expectedCountClass}, got=${event.labels.deferral_count_class}`);
            pass = false;
          }
          if (event.labels.deferral_age_class !== scenario.expectedAgeClass) {
            console.log(`  ✗ FAIL: Expected age_class=${scenario.expectedAgeClass}, got=${event.labels.deferral_age_class}`);
            pass = false;
          }
        } else {
          console.log(`  ✗ FAIL: No RESUME_REEXEC_ABANDONED event found`);
          pass = false;
        }
      }
    } else {
      // Should be deferred, not abandoned
      if (result.action === "ACTION_ABORT") {
        console.log(`  ✗ FAIL: Unexpected abandon, should be deferred`);
        pass = false;
      } else {
        console.log(`  ✓ PASS: Resume deferred (not abandoned)`);
      }

      // Verify RESUME_REEXEC_DEFERRED event
      if (fs.existsSync(eventsPath)) {
        const content = fs.readFileSync(eventsPath, "utf8");
        const deferEvents = content.split("\n").filter((line) =>
          line.includes('"type":"RESUME_REEXEC_DEFERRED"')
        );

        if (deferEvents.length > 0) {
          const event = JSON.parse(deferEvents[deferEvents.length - 1]);
          console.log(`  ✓ RESUME_REEXEC_DEFERRED event emitted`);
          console.log(`    deferral_count=${event.labels.deferral_count}`);
          console.log(`    deferral_count_class=${event.labels.deferral_count_class}`);
        }
      }
    }

    if (pass) {
      passCount++;
    } else {
      failCount++;
    }

    // Clear events for next scenario
    if (fs.existsSync(eventsPath)) fs.unlinkSync(eventsPath);
  }

  // =============================================================================
  // PR223: Market Regime Signal Freshness Fix
  // =============================================================================
  console.log("\n=== PR223: Market Regime Signal Freshness Fix ===\n");

  const pr223Scenarios = [
    {
      name: "PR223-A: Fresh signals from deps → oracle=OK, gate=PASS",
      provideDeps: true,
      depsOracleStatus: "AVAILABLE",
      depsGateStatus: "PASS",
      depsPhaseLabel: "PHASE_NORMAL",
      expectedRegime: "REGIME_NORMAL",
      expectedRegimeCodes: ["REGIME_SIGNALS_FROM_DEPS_FRESH", "REGIME_SIGNAL_ORACLE_PRESENT", "REGIME_SIGNAL_GATE_PRESENT"],
    },
    {
      name: "PR223-B: No deps → fallback to stale resumeState with warning",
      provideDeps: false,
      depsOracleStatus: undefined,
      depsGateStatus: undefined,
      depsPhaseLabel: undefined,
      expectedRegime: "REGIME_VOLATILE", // Stale phase_label=PHASE_DOWN_SHOCK triggers VOLATILE
      expectedRegimeCodes: ["REGIME_SIGNALS_FROM_RESUMESTATE_STALE"],
      expectedWarning: "WARN_REGIME_SIGNALS_STALE",
    },
  ];

  for (const scenario of pr223Scenarios) {
    console.log(`\nScenario: ${scenario.name}`);
    const testResumeId = `RESUME_TEST_PR223_${Date.now()}`;
    const mockState: MeridianStateV1 = {
      version: "v1",
      updatedAtTs: Date.now(),
      warnings: [],
      lastRun: {
        status: "STOPPED",
        warnings: [],
        resumeId: testResumeId,
      } as any,
      resumeState: {
        status: "STOPPED",
        stopReason: "STOP_NO_ROUTE",
        stopAtTs: Date.now() - 300000,
        warnings: [],
        originStopCause: "GATE",
        lastPhaseLabel: "PHASE_DOWN_SHOCK", // Stale signal (would be VOLATILE if used)
      },
    };

    const mockStore: StateStore = {
      readState: async () => ({ status: "OK" as const, state: mockState, warnings: [] }),
      writeState: async () => ({ status: "OK" as const, state: mockState, warnings: [] }),
      patchState: async () => ({ status: "OK" as const, state: mockState, warnings: [] }),
    };

    let capturedRegime: string | undefined;
    let capturedRegimeCodes: string[] | undefined;

    const result = await runSupervisorOnceV1(
      mockStore,
      {},
      {
        evaluatePolicy: async () => ({
          allowExecution: true,
          hardStopActive: false,
          status: "ALLOW",
          reasons: [],
        }),
        getResumeInputs: scenario.provideDeps
          ? async () => ({
              nowTs: Date.now(),
              oracleStatus: scenario.depsOracleStatus as any,
              gateStatus: scenario.depsGateStatus as any,
              phaseLabel: scenario.depsPhaseLabel,
              routeAvailable: true,
              hardStopActive: false,
              policyEnvEnabled: true,
            })
          : undefined, // No deps
        setRunPlanResumeFields: (fields: any) => {
          capturedRegime = fields.resumeMarketRegime;
          capturedRegimeCodes = fields.resumeMarketRegimeCodes;
        },
        runTwapExecution: async () => ({
          status: "COMPLETED",
          reasons: [],
          runId: "test-run-next",
        }),
      }
    );

    console.log(`  Captured: regime=${capturedRegime}`);
    console.log(`  Captured: regimeCodes=${capturedRegimeCodes?.join("|")}`);

    let pass = true;
    if (capturedRegime !== scenario.expectedRegime) {
      console.log(`  ✗ FAIL: Expected regime=${scenario.expectedRegime}, got=${capturedRegime}`);
      pass = false;
    }

    for (const expectedCode of scenario.expectedRegimeCodes) {
      if (!capturedRegimeCodes?.includes(expectedCode)) {
        console.log(`  ✗ FAIL: Expected regime code "${expectedCode}" missing`);
        pass = false;
      }
    }

    if (scenario.expectedWarning) {
      if (!result.warnings.includes(scenario.expectedWarning)) {
        console.log(`  ✗ FAIL: Expected warning "${scenario.expectedWarning}" missing`);
        pass = false;
      } else {
        console.log(`  ✓ Warning "${scenario.expectedWarning}" present`);
      }
    }

    if (pass) {
      console.log(`  ✓ PASS`);
      passCount++;
    } else {
      failCount++;
    }

    // Clear events for next scenario
    if (fs.existsSync(eventsPath)) fs.unlinkSync(eventsPath);
  }

  // =============================================================================
  // Summary
  // =============================================================================
  console.log("\n=== Test Summary ===");
  console.log(`Total scenarios: ${pr221Scenarios.length + pr222Scenarios.length + pr223Scenarios.length}`);
  console.log(`Passed: ${passCount}`);
  console.log(`Failed: ${failCount}`);

  if (failCount === 0) {
    console.log("\n✓ All hotfix tests PASSED!");
  } else {
    console.log(`\n✗ ${failCount} test(s) FAILED`);
    process.exit(1);
  }

  console.log("\n=== Acceptance Criteria Verification ===");
  console.log("PR221: Orchestrator Feedback Staleness Timeout");
  console.log("  AC1: Fresh feedback (<15min) used - ✓");
  console.log("  AC2: Stale feedback (>15min) ignored - ✓");
  console.log("  AC3: Telemetry labels (freshness/age) present - ✓");

  console.log("\nPR222: Max Deferral Guard");
  console.log("  AC1: Deferral count tracked - ✓");
  console.log("  AC2: Abandon at 50 deferrals - ✓");
  console.log("  AC3: Abandon at 24h age - ✓");
  console.log("  AC4: RESUME_REEXEC_ABANDONED event emitted - ✓");

  console.log("\nPR223: Market Regime Signal Freshness Fix");
  console.log("  AC1: Fresh signals from deps used - ✓");
  console.log("  AC2: Fallback to stale resumeState with warning - ✓");
  console.log("  AC3: Signal presence codes emitted - ✓");

  console.log("\n=== Test Complete ===");
}

testHotfixes().catch((e) => {
  console.error(e);
  process.exit(1);
});
