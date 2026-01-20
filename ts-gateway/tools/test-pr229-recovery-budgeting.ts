// tools/test-pr229-recovery-budgeting.ts
// PR229: Recovery Budgeting v1 (暴走防止) - Comprehensive test

/**
 * Purpose:
 *   Test all 4 PR229 budget rules to prevent autonomous recovery runaway:
 *     Rule 1: Attempt limit (>=10 → ABANDON)
 *     Rule 2: Oscillation cooldown (CHG_EXCEEDED → DEFER BACKOFF_LONG)
 *     Rule 3: FAILED_MARKET cap (>=2/hour → DEFER MANUAL)
 *     Rule 4: IMMEDIATE rate limit (>=3/hour → DEFER BACKOFF_LONG)
 *
 * Test scenarios:
 *   1. Baseline: All budgets OK → ALLOW
 *   2. Rule 1 ABANDON: 10 attempts → ABANDON
 *   3. Rule 2 DEFER: CHG_EXCEEDED → DEFER BACKOFF_LONG
 *   4. Rule 3 DEFER: 2 FAILED_MARKET/hour → DEFER MANUAL
 *   5. Rule 4 DEFER: 3 IMMEDIATE/hour → DEFER BACKOFF_LONG
 *   6. Rule 4 Window Reset: Window expired → counts reset
 */

import { runSupervisorOnceV1 } from "../src/supervisor/supervisor";
import { StateStore, MeridianStateV1 } from "../src/state";
import * as fs from "fs";
import * as path from "path";
import * as os from "os";

async function testRecoveryBudgeting() {
  console.log("=== PR229: Recovery Budgeting v1 Test ===\n");

  const eventsPath = path.join(os.homedir(), ".meridian", "events.log");

  // Clear events
  console.log("Step 1: Clear test files");
  if (fs.existsSync(eventsPath)) fs.unlinkSync(eventsPath);

  const scenarios = [
    {
      name: "Baseline: All budgets OK → ALLOW",
      resumeState: {
        recoveryAttemptCount: 0,
        recoveryWindowAnchorTs: Date.now(),
        recoveryImmediateCountInWindow: 0,
        recoveryFailedMarketCountInWindow: 0,
      },
      oscChangeLevelStrategy: "CHG_LOW",
      desiredDelayClass: "IMMEDIATE",
      expectedBudgetAction: "ALLOW",
      expectedBudgetAttemptStatus: "B0_OK",
      expectedBudgetImmediateRateStatus: "R0_OK",
      expectedBudgetFailedMarketRateStatus: "F0_OK",
      expectedBudgetOscCooldownStatus: "C0_OK",
    },
    {
      name: "Rule 1 ABANDON: 10 attempts → ABANDON",
      resumeState: {
        recoveryAttemptCount: 10,
        recoveryWindowAnchorTs: Date.now(),
        recoveryImmediateCountInWindow: 0,
        recoveryFailedMarketCountInWindow: 0,
      },
      oscChangeLevelStrategy: "CHG_LOW",
      desiredDelayClass: "IMMEDIATE",
      expectedBudgetAction: "ABANDON",
      expectedBudgetAttemptStatus: "B2_LIMIT_EXCEEDED",
      expectedEventType: "RESUME_REEXEC_ABANDONED",
      expectedAbandonReason: "BUDGET_LIMIT_EXCEEDED",
    },
    {
      name: "Rule 2 DEFER: CHG_EXCEEDED → DEFER BACKOFF_LONG",
      resumeState: {
        recoveryAttemptCount: 0,
        recoveryWindowAnchorTs: Date.now(),
        recoveryImmediateCountInWindow: 0,
        recoveryFailedMarketCountInWindow: 0,
        strategyChangeCount: 12, // CHG_EXCEEDED (>10)
        lastStrategyChangeTs: Date.now() - 30 * 60 * 1000, // 30 min ago (within 1h)
      },
      oscChangeLevelStrategy: "CHG_EXCEEDED",
      desiredDelayClass: "IMMEDIATE",
      expectedBudgetAction: "DEFER",
      expectedBudgetOscCooldownStatus: "C1_COOLDOWN_ACTIVE",
      expectedOverrideDelayClass: "BACKOFF_LONG",
      expectedOverrideDelayOffsetLabel: "DELAY_15M",
    },
    {
      name: "Rule 3 DEFER: 2 FAILED_MARKET/hour → DEFER MANUAL",
      resumeState: {
        recoveryAttemptCount: 0,
        recoveryWindowAnchorTs: Date.now(),
        recoveryImmediateCountInWindow: 0,
        recoveryFailedMarketCountInWindow: 2, // At limit
        orchLastStatus: "FAILED_MARKET",
      },
      oscChangeLevelStrategy: "CHG_LOW",
      desiredDelayClass: "IMMEDIATE",
      expectedBudgetAction: "DEFER",
      expectedBudgetFailedMarketRateStatus: "F2_LIMIT_EXCEEDED",
      expectedOverrideDelayClass: "MANUAL",
      expectedOverrideDelayOffsetLabel: "DELAY_1H",
    },
    {
      name: "Rule 4 DEFER: 3 IMMEDIATE/hour → DEFER BACKOFF_LONG",
      resumeState: {
        recoveryAttemptCount: 0,
        recoveryWindowAnchorTs: Date.now(),
        recoveryImmediateCountInWindow: 3, // At limit
        recoveryFailedMarketCountInWindow: 0,
      },
      oscChangeLevelStrategy: "CHG_LOW",
      desiredDelayClass: "IMMEDIATE",
      expectedBudgetAction: "DEFER",
      expectedBudgetImmediateRateStatus: "R2_LIMIT_EXCEEDED",
      expectedOverrideDelayClass: "BACKOFF_LONG",
      expectedOverrideDelayOffsetLabel: "DELAY_15M",
    },
    {
      name: "Rule 4 Window Reset: Window expired → counts reset",
      resumeState: {
        recoveryAttemptCount: 0,
        recoveryWindowAnchorTs: Date.now() - 2 * 60 * 60 * 1000, // 2 hours ago (expired)
        recoveryImmediateCountInWindow: 3, // Stale count
        recoveryFailedMarketCountInWindow: 2, // Stale count
      },
      oscChangeLevelStrategy: "CHG_LOW",
      desiredDelayClass: "IMMEDIATE",
      expectedBudgetAction: "ALLOW",
      expectedBudgetImmediateRateStatus: "R0_OK", // Reset (window expired)
      expectedBudgetFailedMarketRateStatus: "F0_OK", // Reset (window expired)
    },
  ];

  let passCount = 0;
  let failCount = 0;

  for (const scenario of scenarios) {
    console.log(`\nScenario: ${scenario.name}`);

    // Clear events for this scenario
    if (fs.existsSync(eventsPath)) fs.unlinkSync(eventsPath);

    // Build test state
    const testResumeId = `RESUME_TEST_PR229_${Date.now()}`;
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
        originStopCause: "TIMEOUT", // TIMEOUT → IMMEDIATE path
        lastPhaseLabel: "PHASE_NORMAL",
        ...scenario.resumeState,
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

    // Run supervisor tick
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
        setRunPlanResumeFields: () => {
          // No-op for this test
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

    // Wait for telemetry flush
    await new Promise((resolve) => setTimeout(resolve, 100));

    // Verify result
    let scenarioPass = true;

    // Check for ABANDON action
    if ((scenario as any).expectedEventType === "RESUME_REEXEC_ABANDONED") {
      if (result.action !== "ACTION_ABORT") {
        console.log(`  ✗ Expected ACTION_ABORT, got ${result.action}`);
        scenarioPass = false;
      }

      // Verify ABANDONED event
      if (fs.existsSync(eventsPath)) {
        const content = fs.readFileSync(eventsPath, "utf8");
        const lines = content.trim().split("\n");
        const abandonEvents = lines.filter((line) =>
          line.includes('"type":"RESUME_REEXEC_ABANDONED"')
        );

        if (abandonEvents.length > 0) {
          const event = JSON.parse(abandonEvents[abandonEvents.length - 1]);
          if (event.labels.abandon_reason !== (scenario as any).expectedAbandonReason) {
            console.log(`  ✗ Expected abandon_reason=${(scenario as any).expectedAbandonReason}, got=${event.labels.abandon_reason}`);
            scenarioPass = false;
          } else {
            console.log(`  ✓ ABANDONED event emitted with correct reason`);
          }
        } else {
          console.log(`  ✗ No ABANDON event found`);
          scenarioPass = false;
        }
      }
    } else {
      // Check RESUME_REEXEC_ATTEMPT event for budget labels
      if (fs.existsSync(eventsPath)) {
        const content = fs.readFileSync(eventsPath, "utf8");
        const lines = content.trim().split("\n");
        const attemptEvents = lines.filter((line) =>
          line.includes('"type":"RESUME_REEXEC_ATTEMPT"')
        );

        if (attemptEvents.length > 0) {
          const event = JSON.parse(attemptEvents[attemptEvents.length - 1]);

          // Check budget action
          if ((scenario as any).expectedBudgetAction) {
            const action = event.labels.resume_budget_action;
            if (action !== (scenario as any).expectedBudgetAction) {
              console.log(`  ✗ Expected budget_action=${(scenario as any).expectedBudgetAction}, got=${action}`);
              scenarioPass = false;
            } else {
              console.log(`  ✓ budget_action=${action}`);
            }
          }

          // Check budget status labels
          if ((scenario as any).expectedBudgetAttemptStatus) {
            const status = event.labels.resume_budget_attempt_status;
            if (status !== (scenario as any).expectedBudgetAttemptStatus) {
              console.log(`  ✗ Expected budget_attempt_status=${(scenario as any).expectedBudgetAttemptStatus}, got=${status}`);
              scenarioPass = false;
            } else {
              console.log(`  ✓ budget_attempt_status=${status}`);
            }
          }

          if ((scenario as any).expectedBudgetImmediateRateStatus) {
            const status = event.labels.resume_budget_immediate_rate_status;
            if (status !== (scenario as any).expectedBudgetImmediateRateStatus) {
              console.log(`  ✗ Expected budget_immediate_rate_status=${(scenario as any).expectedBudgetImmediateRateStatus}, got=${status}`);
              scenarioPass = false;
            } else {
              console.log(`  ✓ budget_immediate_rate_status=${status}`);
            }
          }

          if ((scenario as any).expectedBudgetFailedMarketRateStatus) {
            const status = event.labels.resume_budget_failed_market_rate_status;
            if (status !== (scenario as any).expectedBudgetFailedMarketRateStatus) {
              console.log(`  ✗ Expected budget_failed_market_rate_status=${(scenario as any).expectedBudgetFailedMarketRateStatus}, got=${status}`);
              scenarioPass = false;
            } else {
              console.log(`  ✓ budget_failed_market_rate_status=${status}`);
            }
          }

          if ((scenario as any).expectedBudgetOscCooldownStatus) {
            const status = event.labels.resume_budget_osc_cooldown_status;
            if (status !== (scenario as any).expectedBudgetOscCooldownStatus) {
              console.log(`  ✗ Expected budget_osc_cooldown_status=${(scenario as any).expectedBudgetOscCooldownStatus}, got=${status}`);
              scenarioPass = false;
            } else {
              console.log(`  ✓ budget_osc_cooldown_status=${status}`);
            }
          }

          // Check override timing (if DEFER)
          if ((scenario as any).expectedOverrideDelayClass) {
            const delayClass = event.labels.resume_delay_class;
            if (delayClass !== (scenario as any).expectedOverrideDelayClass) {
              console.log(`  ✗ Expected delay_class=${(scenario as any).expectedOverrideDelayClass}, got=${delayClass}`);
              scenarioPass = false;
            } else {
              console.log(`  ✓ delay_class=${delayClass} (budget override)`);
            }
          }

          if ((scenario as any).expectedOverrideDelayOffsetLabel) {
            const delayOffset = event.labels.resume_delay_offset_label;
            if (delayOffset !== (scenario as any).expectedOverrideDelayOffsetLabel) {
              console.log(`  ✗ Expected delay_offset_label=${(scenario as any).expectedOverrideDelayOffsetLabel}, got=${delayOffset}`);
              scenarioPass = false;
            } else {
              console.log(`  ✓ delay_offset_label=${delayOffset} (budget override)`);
            }
          }
        } else {
          console.log(`  ✗ No RESUME_REEXEC_ATTEMPT event found`);
          scenarioPass = false;
        }
      } else {
        console.log(`  ✗ Events file not found`);
        scenarioPass = false;
      }
    }

    if (scenarioPass) {
      console.log(`  ✓ Scenario PASSED`);
      passCount++;
    } else {
      console.log(`  ✗ Scenario FAILED`);
      failCount++;
    }
  }

  console.log("\n=== Test Summary ===");
  console.log(`Total scenarios: ${scenarios.length}`);
  console.log(`Passed: ${passCount}`);
  console.log(`Failed: ${failCount}`);

  if (failCount === 0) {
    console.log("\n✓ All PR229 recovery budgeting tests PASSED!");
  } else {
    console.log(`\n✗ ${failCount} test(s) FAILED`);
    process.exit(1);
  }

  console.log("\n=== AC Verification ===");
  console.log("AC1: Attempt Budget (>=10 → ABANDON) - ✓");
  console.log("AC2: IMMEDIATE Rate Limit (>=3/hour → DEFER) - ✓");
  console.log("AC3: FAILED_MARKET Cap (>=2/hour → DEFER) - ✓");
  console.log("AC4: Oscillation Cooldown (CHG_EXCEEDED → DEFER) - ✓");
  console.log("AC5: Window Reset (>1 hour → counts reset) - ✓");

  console.log("\n=== Test Complete ===");
}

testRecoveryBudgeting().catch((e) => {
  console.error("Fatal error:", e);
  process.exit(1);
});
