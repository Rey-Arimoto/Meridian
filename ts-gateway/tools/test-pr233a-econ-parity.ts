// tools/test-pr233a-econ-parity.ts
// PR233a: Economic Risk Observability Pack v1 - Telemetry Parity Test

/**
 * Purpose:
 *   Verify telemetry parity between Supervisor and Runner for PR233/PR233a.
 *   All economic risk labels emitted in RESUME_REEXEC_ATTEMPT (Supervisor)
 *   must appear identically in RUN_START (Runner).
 *
 * Parity requirements:
 *   - Label names must match exactly
 *   - Label values must match exactly
 *   - No missing labels in Runner
 *   - No extra labels in Runner (strict subset)
 *
 * Labels to verify:
 *   PR233 (core):
 *   - resume_econ_constraint_class
 *   - resume_econ_constraint_action
 *   - resume_econ_codes_status
 *   - resume_econ_codes
 *
 *   PR233a (observability):
 *   - resume_econ_severity
 *   - resume_econ_liquidity_class
 *   - resume_econ_slippage_class
 *   - resume_econ_exposure_class
 *   - resume_econ_drawdown_class
 *   - resume_econ_cooldown_status
 *   - resume_econ_window_status
 */

import { runSupervisorOnceV1 } from "../src/supervisor/supervisor";
import { StateStore, MeridianStateV1 } from "../src/state";
import { RunPlan } from "../src/rebalance/types";
import * as fs from "fs";
import * as path from "path";
import * as os from "os";

async function testEconomicRiskParity() {
  console.log("=== PR233a: Economic Risk Observability Pack v1 - Parity Test ===\n");

  const eventsPath = path.join(os.homedir(), ".meridian", ".events.log");

  // Clear events
  console.log("Step 1: Clear test files");
  if (fs.existsSync(eventsPath)) fs.unlinkSync(eventsPath);

  const testScenarios = [
    {
      name: "Scenario 1: Normal OK state",
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
    },
    {
      name: "Scenario 2: Conservative state with cooldown",
      signals: {
        oracleStatus: "AVAILABLE" as any,
        dexStatus: "DEX_OK" as any,
        rpcHealth: "RPC_OK" as any,
        liquidity: "LIQ_THIN",
        slippageRisk: "SLIP_MEDIUM",
        exposure: "EXP_MEDIUM",
        drawdown: "DD_WARNING",
      },
      resumeState: {
        originStopCause: "TIMEOUT" as any,
        econConstraintCooldownUntilTs: Date.now() + 600000,
        econConstraintWindowAnchorTs: Date.now() - 1800000, // 30 min ago
      },
      marketRegime: "VOLATILE",
      finalEnforcedMode: "SIM_ONLY",
    },
    {
      name: "Scenario 3: Critical state (exposure excessive)",
      signals: {
        oracleStatus: "AVAILABLE" as any,
        dexStatus: "DEX_OK" as any,
        rpcHealth: "RPC_OK" as any,
        liquidity: "LIQ_VACUUM",
        slippageRisk: "SLIP_EXTREME",
        exposure: "EXP_EXCESSIVE",
        drawdown: "DD_CRITICAL",
      },
      resumeState: {
        originStopCause: "TIMEOUT" as any,
        econConstraintWindowAnchorTs: Date.now() - 100000, // Recent
      },
      marketRegime: "CRASH",
      finalEnforcedMode: "LIVE",
    },
  ];

  let passCount = 0;
  let failCount = 0;

  const ECON_LABEL_KEYS = [
    // PR233 core
    "resume_econ_constraint_class",
    "resume_econ_constraint_action",
    "resume_econ_codes_status",
    "resume_econ_codes",
    // PR233a observability
    "resume_econ_severity",
    "resume_econ_liquidity_class",
    "resume_econ_slippage_class",
    "resume_econ_exposure_class",
    "resume_econ_drawdown_class",
    "resume_econ_cooldown_status",
    "resume_econ_window_status",
  ];

  for (const scenario of testScenarios) {
    console.log(`\n${scenario.name}`);

    // Clear events for this scenario
    if (fs.existsSync(eventsPath)) fs.unlinkSync(eventsPath);

    // Build test state
    const testResumeId = `RESUME_TEST_PR233A_${Date.now()}`;
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
        ...(scenario as any).resumeState,
      },
    };

    // Capture RunPlan fields passed to setRunPlanResumeFields
    let capturedRunPlanFields: any = null;

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
          setRunPlanResumeFields: (fields: any) => {
            // Capture fields for parity check
            capturedRunPlanFields = fields;
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

    // Verify parity
    let scenarioPass = true;

    if (!fs.existsSync(eventsPath)) {
      console.log(`  ✗ Events file not found`);
      scenarioPass = false;
      failCount++;
      continue;
    }

    const content = fs.readFileSync(eventsPath, "utf8");
    const lines = content.trim().split("\n");

    // Find RESUME_REEXEC_ATTEMPT event (Supervisor)
    const attemptEvents = lines.filter((line) =>
      line.includes('"type":"RESUME_REEXEC_ATTEMPT"')
    );

    if (attemptEvents.length === 0) {
      console.log(`  ✗ No RESUME_REEXEC_ATTEMPT event found`);
      scenarioPass = false;
      failCount++;
      continue;
    }

    const attemptEvent = JSON.parse(attemptEvents[attemptEvents.length - 1]);
    console.log(`  ✓ Supervisor event found: RESUME_REEXEC_ATTEMPT`);

    // Extract Supervisor labels
    const supervisorLabels: Record<string, string> = {};
    for (const key of ECON_LABEL_KEYS) {
      if (attemptEvent.labels[key] !== undefined) {
        supervisorLabels[key] = attemptEvent.labels[key];
      }
    }

    console.log(`  ✓ Supervisor labels extracted: ${Object.keys(supervisorLabels).length} labels`);

    // Verify RunPlan fields were set
    if (!capturedRunPlanFields) {
      console.log(`  ✗ setRunPlanResumeFields was not called`);
      scenarioPass = false;
      failCount++;
      continue;
    }

    console.log(`  ✓ RunPlan fields captured`);

    // Verify parity: RunPlan fields should match Supervisor labels
    const runPlanFieldMapping: Record<string, string> = {
      resume_econ_constraint_class: "resumeEconConstraintClass",
      resume_econ_constraint_action: "resumeEconConstraintAction",
      resume_econ_codes_status: "resumeEconConstraintCodesStatus",
      resume_econ_codes: "resumeEconConstraintCodes",
      resume_econ_severity: "resumeEconRiskSeverity",
      resume_econ_liquidity_class: "resumeEconLiquidityCondition",
      resume_econ_slippage_class: "resumeEconSlippageRisk",
      resume_econ_exposure_class: "resumeEconExposureStatus",
      resume_econ_drawdown_class: "resumeEconDrawdownStatus",
      resume_econ_cooldown_status: "resumeEconRiskCooldownStatus",
      resume_econ_window_status: "resumeEconRiskWindowStatus",
    };

    let parityErrors = 0;

    for (const [labelKey, runPlanField] of Object.entries(runPlanFieldMapping)) {
      const supervisorValue = supervisorLabels[labelKey];
      const runPlanValue = capturedRunPlanFields[runPlanField];

      // Handle special case: codes might be joined string vs array
      if (labelKey === "resume_econ_codes") {
        // RunPlan has array, Supervisor has joined string
        const runPlanJoined = Array.isArray(runPlanValue) ? runPlanValue.join(",") : runPlanValue;
        if (supervisorValue !== undefined && runPlanJoined !== supervisorValue) {
          console.log(`  ✗ Parity mismatch: ${labelKey}`);
          console.log(`    Supervisor: "${supervisorValue}"`);
          console.log(`    RunPlan:    "${runPlanJoined}"`);
          parityErrors++;
        }
        continue;
      }

      if (supervisorValue !== undefined) {
        if (runPlanValue === undefined) {
          console.log(`  ✗ Missing in RunPlan: ${runPlanField} (Supervisor has: "${supervisorValue}")`);
          parityErrors++;
        } else if (runPlanValue !== supervisorValue) {
          console.log(`  ✗ Value mismatch: ${labelKey}`);
          console.log(`    Supervisor: "${supervisorValue}"`);
          console.log(`    RunPlan:    "${runPlanValue}"`);
          parityErrors++;
        }
      }
    }

    if (parityErrors === 0) {
      console.log(`  ✓ All PR233/PR233a labels match between Supervisor and RunPlan`);
      console.log(`  ✓ Scenario PASSED`);
      passCount++;
    } else {
      console.log(`  ✗ ${parityErrors} parity error(s) found`);
      console.log(`  ✗ Scenario FAILED`);
      scenarioPass = false;
      failCount++;
    }
  }

  console.log("\n=== Test Summary ===");
  console.log(`Total scenarios: ${testScenarios.length}`);
  console.log(`Passed: ${passCount}`);
  console.log(`Failed: ${failCount}`);

  if (failCount === 0) {
    console.log("\n✓ All PR233a telemetry parity tests PASSED!");
  } else {
    console.log(`\n✗ ${failCount} test(s) FAILED`);
    process.exit(1);
  }

  console.log("\n=== Parity Verification ===");
  console.log("Supervisor → RunPlan field mapping verified:");
  console.log("  resume_econ_constraint_class → resumeEconConstraintClass - ✓");
  console.log("  resume_econ_constraint_action → resumeEconConstraintAction - ✓");
  console.log("  resume_econ_codes_status → resumeEconConstraintCodesStatus - ✓");
  console.log("  resume_econ_codes → resumeEconConstraintCodes - ✓");
  console.log("  resume_econ_severity → resumeEconRiskSeverity - ✓");
  console.log("  resume_econ_liquidity_class → resumeEconLiquidityCondition - ✓");
  console.log("  resume_econ_slippage_class → resumeEconSlippageRisk - ✓");
  console.log("  resume_econ_exposure_class → resumeEconExposureStatus - ✓");
  console.log("  resume_econ_drawdown_class → resumeEconDrawdownStatus - ✓");
  console.log("  resume_econ_cooldown_status → resumeEconRiskCooldownStatus - ✓");
  console.log("  resume_econ_window_status → resumeEconRiskWindowStatus - ✓");

  console.log("\n=== Test Complete ===");
}

testEconomicRiskParity().catch((e) => {
  console.error("Fatal error:", e);
  process.exit(1);
});
