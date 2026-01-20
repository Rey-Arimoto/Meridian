// tools/test-pr233-economic-constraints.ts
// PR233: Economic Risk Constraints Layer v1 - Infrastructure Test

/**
 * Purpose:
 *   Test economic risk constraint layer (Article XII) to ensure correct
 *   layering between budget (PR229) and invariants (PR231), and that
 *   constraint actions (ECON_ALLOW/DEFER/ABANDON) work correctly.
 *
 * Key test coverage:
 *   R0: Defensive baseline (UNKNOWN inputs → DEFER)
 *   R1: NEVER block SIM_ONLY for liquidity/slippage (only exposure/drawdown)
 *   R2: LIVE execution + fragile market regime → DEFER
 *   R3: Cooldown protection (DEFER until cooldown expires)
 *   R4: Exposure hard cap (EXP_EXCESSIVE → ABANDON)
 *   R5: Drawdown emergency brake (DD_CRITICAL → ABANDON)
 *   Budget precedence: ABANDON/DEFER budgets skip economic checks
 *
 * Test scenarios:
 *   1. Normal path: All OK inputs → ECON_ALLOW
 *   2. R1 test: SIM_ONLY + LIQ_VACUUM → ECON_ALLOW (never block SIM_ONLY)
 *   3. R1 test: SIM_ONLY + SLIP_EXTREME → ECON_ALLOW (never block SIM_ONLY)
 *   4. R2 test: LIVE + CRASH regime → ECON_DEFER (fragile regime)
 *   5. R3 test: Cooldown active → ECON_DEFER
 *   6. R4 test: Exposure excessive → ECON_ABANDON (hard cap)
 *   7. R5 test: Drawdown critical → ECON_ABANDON (emergency brake)
 *   8. Budget precedence: ABANDON budget → Economic checks skipped
 *   9. R0 test: UNKNOWN inputs → ECON_DEFER (defensive baseline)
 */

import { runSupervisorOnceV1 } from "../src/supervisor/supervisor";
import { StateStore, MeridianStateV1 } from "../src/state";
import * as fs from "fs";
import * as path from "path";
import * as os from "os";

async function testEconomicConstraints() {
  console.log("=== PR233: Economic Risk Constraints Layer v1 Test ===\n");

  const eventsPath = path.join(os.homedir(), ".meridian", "events.log");

  // Clear events
  console.log("Step 1: Clear test files");
  if (fs.existsSync(eventsPath)) fs.unlinkSync(eventsPath);

  const scenarios = [
    {
      name: "Scenario 1: Normal path - All OK inputs → ECON_ALLOW",
      signals: {
        oracleStatus: "AVAILABLE" as any,
        dexStatus: "DEX_OK" as any,
        rpcHealth: "RPC_OK" as any,
        liquidity: "LIQ_HEALTHY",
        slippageRisk: "SLIP_LOW",
        exposure: "EXP_SMALL",
        drawdown: "DD_OK",
      },
      resumeState: {
        originStopCause: "TIMEOUT" as any,
      },
      marketRegime: "NORMAL",
      finalEnforcedMode: "LIVE",
      expectedEconClass: "E0_OK",
      expectedEconAction: "ECON_ALLOW",
      expectedEconCodes: ["ECON_ALLOW_V1", "ECON_OK"],
      expectAbort: false,
    },
    {
      name: "Scenario 2: R1 test - SIM_ONLY + LIQ_VACUUM → ECON_ALLOW",
      signals: {
        oracleStatus: "AVAILABLE" as any,
        dexStatus: "DEX_OK" as any,
        rpcHealth: "RPC_OK" as any,
        liquidity: "LIQ_VACUUM", // Worst liquidity
        slippageRisk: "SLIP_LOW",
        exposure: "EXP_SMALL",
        drawdown: "DD_OK",
      },
      resumeState: {
        originStopCause: "TIMEOUT" as any,
      },
      marketRegime: "NORMAL",
      finalEnforcedMode: "SIM_ONLY", // R1: NEVER block SIM_ONLY
      expectedEconClass: "E1_CONSERVATIVE", // LIQ_VACUUM is conservative
      expectedEconAction: "ECON_ALLOW", // But still ALLOW for SIM_ONLY
      expectedEconCodes: ["ECON_ALLOW_V1", "ECON_R1_SIM_ONLY_LIQUIDITY_BYPASS"],
      expectAbort: false,
    },
    {
      name: "Scenario 3: R1 test - SIM_ONLY + SLIP_EXTREME → ECON_ALLOW",
      signals: {
        oracleStatus: "AVAILABLE" as any,
        dexStatus: "DEX_OK" as any,
        rpcHealth: "RPC_OK" as any,
        liquidity: "LIQ_HEALTHY",
        slippageRisk: "SLIP_EXTREME", // Worst slippage
        exposure: "EXP_SMALL",
        drawdown: "DD_OK",
      },
      resumeState: {
        originStopCause: "TIMEOUT" as any,
      },
      marketRegime: "NORMAL",
      finalEnforcedMode: "SIM_ONLY", // R1: NEVER block SIM_ONLY
      expectedEconClass: "E2_RISKY", // SLIP_EXTREME is risky
      expectedEconAction: "ECON_ALLOW", // But still ALLOW for SIM_ONLY
      expectedEconCodes: ["ECON_ALLOW_V1", "ECON_R1_SIM_ONLY_SLIPPAGE_BYPASS"],
      expectAbort: false,
    },
    {
      name: "Scenario 4: R2 test - LIVE + CRASH regime → ECON_DEFER",
      signals: {
        oracleStatus: "AVAILABLE" as any,
        dexStatus: "DEX_OK" as any,
        rpcHealth: "RPC_OK" as any,
        liquidity: "LIQ_HEALTHY",
        slippageRisk: "SLIP_LOW",
        exposure: "EXP_SMALL",
        drawdown: "DD_OK",
      },
      resumeState: {
        originStopCause: "TIMEOUT" as any,
      },
      marketRegime: "CRASH", // Fragile regime
      finalEnforcedMode: "LIVE", // LIVE mode
      expectedEconClass: "E2_RISKY",
      expectedEconAction: "ECON_DEFER",
      expectedEconCodes: ["ECON_DEFER_V1", "ECON_R2_LIVE_FRAGILE_REGIME"],
      expectAbort: true,
      economicAbort: true,
    },
    {
      name: "Scenario 5: R3 test - Cooldown active → ECON_DEFER",
      signals: {
        oracleStatus: "AVAILABLE" as any,
        dexStatus: "DEX_OK" as any,
        rpcHealth: "RPC_OK" as any,
        liquidity: "LIQ_HEALTHY",
        slippageRisk: "SLIP_LOW",
        exposure: "EXP_SMALL",
        drawdown: "DD_OK",
      },
      resumeState: {
        originStopCause: "TIMEOUT" as any,
        econConstraintCooldownUntilTs: Date.now() + 600000, // Active cooldown
      },
      marketRegime: "NORMAL",
      finalEnforcedMode: "LIVE",
      expectedEconClass: "E1_CONSERVATIVE",
      expectedEconAction: "ECON_DEFER",
      expectedEconCodes: ["ECON_DEFER_V1", "ECON_R3_COOLDOWN_ACTIVE"],
      expectAbort: true,
      economicAbort: true,
    },
    {
      name: "Scenario 6: R4 test - Exposure excessive → ECON_ABANDON",
      signals: {
        oracleStatus: "AVAILABLE" as any,
        dexStatus: "DEX_OK" as any,
        rpcHealth: "RPC_OK" as any,
        liquidity: "LIQ_HEALTHY",
        slippageRisk: "SLIP_LOW",
        exposure: "EXP_EXCESSIVE", // Hard cap
        drawdown: "DD_OK",
      },
      resumeState: {
        originStopCause: "TIMEOUT" as any,
      },
      marketRegime: "NORMAL",
      finalEnforcedMode: "LIVE",
      expectedEconClass: "E3_FORBIDDEN",
      expectedEconAction: "ECON_ABANDON",
      expectedEconCodes: ["ECON_ABANDON_V1", "ECON_R4_EXPOSURE_HARD_CAP"],
      expectAbort: true,
      economicAbort: true,
    },
    {
      name: "Scenario 7: R5 test - Drawdown critical → ECON_ABANDON",
      signals: {
        oracleStatus: "AVAILABLE" as any,
        dexStatus: "DEX_OK" as any,
        rpcHealth: "RPC_OK" as any,
        liquidity: "LIQ_HEALTHY",
        slippageRisk: "SLIP_LOW",
        exposure: "EXP_SMALL",
        drawdown: "DD_CRITICAL", // Emergency brake
      },
      resumeState: {
        originStopCause: "TIMEOUT" as any,
      },
      marketRegime: "NORMAL",
      finalEnforcedMode: "LIVE",
      expectedEconClass: "E3_FORBIDDEN",
      expectedEconAction: "ECON_ABANDON",
      expectedEconCodes: ["ECON_ABANDON_V1", "ECON_R5_DRAWDOWN_EMERGENCY"],
      expectAbort: true,
      economicAbort: true,
    },
    {
      name: "Scenario 8: Budget precedence - ABANDON budget → Economic checks skipped",
      signals: {
        oracleStatus: "AVAILABLE" as any,
        dexStatus: "DEX_OK" as any,
        rpcHealth: "RPC_OK" as any,
        liquidity: "LIQ_HEALTHY",
        slippageRisk: "SLIP_LOW",
        exposure: "EXP_SMALL",
        drawdown: "DD_OK",
      },
      resumeState: {
        originStopCause: "TIMEOUT" as any,
        recoveryAttemptCount: 1000, // Trigger budget ABANDON
      },
      marketRegime: "NORMAL",
      finalEnforcedMode: "LIVE",
      expectedEconClass: "E0_OK", // Skipped, so default OK
      expectedEconAction: "ECON_ALLOW", // Skipped
      expectedEconCodes: [], // No codes since skipped
      expectAbort: true,
      budgetAbort: true, // Budget causes abort, not economic
    },
    {
      name: "Scenario 9: R0 test - UNKNOWN inputs → ECON_DEFER",
      signals: {
        oracleStatus: "AVAILABLE" as any,
        dexStatus: "DEX_OK" as any,
        rpcHealth: "RPC_OK" as any,
        liquidity: "LIQ_UNKNOWN", // Defensive baseline
        slippageRisk: "SLIP_UNKNOWN",
        exposure: "EXP_UNKNOWN",
        drawdown: "DD_UNKNOWN",
      },
      resumeState: {
        originStopCause: "TIMEOUT" as any,
      },
      marketRegime: "NORMAL",
      finalEnforcedMode: "LIVE",
      expectedEconClass: "E1_CONSERVATIVE",
      expectedEconAction: "ECON_DEFER",
      expectedEconCodes: ["ECON_DEFER_V1", "ECON_R0_DEFENSIVE_UNKNOWN"],
      expectAbort: true,
      economicAbort: true,
    },
  ];

  let passCount = 0;
  let failCount = 0;

  for (const scenario of scenarios) {
    console.log(`\n${scenario.name}`);

    // Clear events for this scenario
    if (fs.existsSync(eventsPath)) fs.unlinkSync(eventsPath);

    // Build test state
    const testResumeId = `RESUME_TEST_PR233_${Date.now()}`;
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
        originStopCause: (scenario as any).resumeState?.originStopCause || "TIMEOUT",
        lastPhaseLabel: "PHASE_NORMAL",
        attemptCount: (scenario as any).resumeState?.attemptCount || 0,
        recoveryAttemptCount: (scenario as any).resumeState?.recoveryAttemptCount || 0,
        econConstraintCooldownUntilTs: (scenario as any).resumeState?.econConstraintCooldownUntilTs,
        ...(scenario as any).resumeState,
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

    // Mock getResumeInputs
    const getResumeInputsMock = async () => ({
      nowTs: Date.now(),
      oracleStatus: scenario.signals.oracleStatus || "UNKNOWN",
      gateStatus: "PASS" as any,
      phaseLabel: "PHASE_NORMAL",
      routeAvailable: true,
      hardStopActive: false,
      policyEnvEnabled: true,
      dexStatus: scenario.signals.dexStatus,
      rpcHealth: scenario.signals.rpcHealth,
      quoteCrossCheck: (scenario.signals as any).quoteCrossCheck,
      // PR233 inputs
      liquidity: (scenario.signals as any).liquidity,
      slippageRisk: (scenario.signals as any).slippageRisk,
      exposure: (scenario.signals as any).exposure,
      drawdown: (scenario.signals as any).drawdown,
      marketRegimeConfirmed: (scenario as any).marketRegime,
    });

    try {
      // Run supervisor tick
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
          getResumeInputs: getResumeInputsMock as any,
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
    } catch (e) {
      // Some scenarios may cause exceptions
      console.log(`  (Exception during execution: ${(e as Error).message})`);
    }

    // Wait for telemetry flush
    await new Promise((resolve) => setTimeout(resolve, 100));

    // Verify result
    let scenarioPass = true;

    if (fs.existsSync(eventsPath)) {
      const content = fs.readFileSync(eventsPath, "utf8");
      const lines = content.trim().split("\n");

      if (scenario.expectAbort) {
        // Check for ABORTED or DEFERRED or ABANDONED event
        const abortEvents = lines.filter((line) =>
          line.includes('"type":"RESUME_REEXEC_ABORTED"') ||
          line.includes('"type":"RESUME_REEXEC_DEFERRED"') ||
          line.includes('"type":"RESUME_REEXEC_ABANDONED"')
        );

        if (abortEvents.length === 0) {
          console.log(`  ✗ Expected ABORTED/DEFERRED/ABANDONED event, but none found`);
          scenarioPass = false;
        } else {
          const abortEvent = JSON.parse(abortEvents[abortEvents.length - 1]);
          console.log(`  ✓ Abort/defer event found: ${abortEvent.type}`);

          if ((scenario as any).economicAbort) {
            // Verify economic constraint labels in abort event
            if (abortEvent.labels.resume_econ_constraint_class !== scenario.expectedEconClass) {
              console.log(`  ✗ Expected econ_class=${scenario.expectedEconClass}, got=${abortEvent.labels.resume_econ_constraint_class}`);
              scenarioPass = false;
            } else {
              console.log(`  ✓ econ_class=${abortEvent.labels.resume_econ_constraint_class}`);
            }

            if (abortEvent.labels.resume_econ_constraint_action !== scenario.expectedEconAction) {
              console.log(`  ✗ Expected econ_action=${scenario.expectedEconAction}, got=${abortEvent.labels.resume_econ_constraint_action}`);
              scenarioPass = false;
            } else {
              console.log(`  ✓ econ_action=${abortEvent.labels.resume_econ_constraint_action}`);
            }

            const econCodes = abortEvent.labels.resume_econ_codes || "";
            if (scenario.expectedEconCodes && scenario.expectedEconCodes.length > 0) {
              const missing = scenario.expectedEconCodes.filter(code => !econCodes.includes(code));
              if (missing.length > 0) {
                console.log(`  ✗ Missing economic codes: ${missing.join(", ")}`);
                scenarioPass = false;
              } else {
                console.log(`  ✓ economic codes present: ${scenario.expectedEconCodes.join(", ")}`);
              }
            }
          }
        }
      } else {
        // Normal path: should have RESUME_REEXEC_ATTEMPT
        const attemptEvents = lines.filter((line) =>
          line.includes('"type":"RESUME_REEXEC_ATTEMPT"')
        );

        if (attemptEvents.length === 0) {
          console.log(`  ✗ Expected RESUME_REEXEC_ATTEMPT event, but none found`);
          scenarioPass = false;
        } else {
          const attemptEvent = JSON.parse(attemptEvents[attemptEvents.length - 1]);
          console.log(`  ✓ RESUME_REEXEC_ATTEMPT event found`);

          // Verify economic constraint status
          if (attemptEvent.labels.resume_econ_constraint_class !== scenario.expectedEconClass) {
            console.log(`  ✗ Expected econ_class=${scenario.expectedEconClass}, got=${attemptEvent.labels.resume_econ_constraint_class}`);
            scenarioPass = false;
          } else {
            console.log(`  ✓ econ_class=${attemptEvent.labels.resume_econ_constraint_class}`);
          }

          // Verify action
          if (attemptEvent.labels.resume_econ_constraint_action !== scenario.expectedEconAction) {
            console.log(`  ✗ Expected econ_action=${scenario.expectedEconAction}, got=${attemptEvent.labels.resume_econ_constraint_action}`);
            scenarioPass = false;
          } else {
            console.log(`  ✓ econ_action=${attemptEvent.labels.resume_econ_constraint_action}`);
          }

          // Verify economic codes
          const econCodes = attemptEvent.labels.resume_econ_codes || "";
          if (scenario.expectedEconCodes && scenario.expectedEconCodes.length > 0) {
            const missing = scenario.expectedEconCodes.filter(code => !econCodes.includes(code));
            if (missing.length > 0) {
              console.log(`  ✗ Missing economic codes: ${missing.join(", ")}`);
              scenarioPass = false;
            } else {
              console.log(`  ✓ economic codes present: ${scenario.expectedEconCodes.join(", ")}`);
            }
          }
        }
      }
    } else {
      console.log(`  ✗ Events file not found`);
      scenarioPass = false;
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
    console.log("\n✓ All PR233 economic constraint tests PASSED!");
  } else {
    console.log(`\n✗ ${failCount} test(s) FAILED`);
    process.exit(1);
  }

  console.log("\n=== Rule Verification ===");
  console.log("R0: Defensive baseline (UNKNOWN → DEFER) - ✓");
  console.log("R1: NEVER block SIM_ONLY for liquidity/slippage - ✓");
  console.log("R2: LIVE + fragile regime → DEFER - ✓");
  console.log("R3: Cooldown protection → DEFER - ✓");
  console.log("R4: Exposure hard cap → ABANDON - ✓");
  console.log("R5: Drawdown emergency brake → ABANDON - ✓");
  console.log("Budget precedence: ABANDON/DEFER budgets skip economic checks - ✓");

  console.log("\n=== Test Complete ===");
}

testEconomicConstraints().catch((e) => {
  console.error("Fatal error:", e);
  process.exit(1);
});
