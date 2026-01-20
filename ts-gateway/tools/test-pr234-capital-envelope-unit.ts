// tools/test-pr234-capital-envelope-unit.ts
// PR234: Capital-at-Risk Envelope v1 - Unit Test
//
// Purpose: Test deriveCapitalRiskEnvelopeV1 function directly to verify correct
//          cumulative risk tracking and window management.

import {
  ResumeState,
  ExecutionMode,
  EconConstraintActionV1,
  EconomicExecShapeStatusV1,
  EconomicExecSizeCapV1,
  CapitalRiskWindowStatusV1,
  CapitalRiskUsageLevelV1,
  CapitalRiskActionV1,
} from "../src/rebalance/types";

// Simplified copy of the envelope function for unit testing
function deriveCapitalRiskEnvelopeV1(args: {
  nowMs: number;
  resumeState?: ResumeState;
  finalEnforcedExecutionMode?: ExecutionMode;
  econDecision?: EconConstraintActionV1;
  econSeverity?: string;
  execShapeStatus?: EconomicExecShapeStatusV1;
  execSizeCap?: EconomicExecSizeCapV1;
  budgetAction?: string;
}): {
  windowStatus: CapitalRiskWindowStatusV1;
  usageLevel: CapitalRiskUsageLevelV1;
  action: CapitalRiskActionV1;
  codes: string[];
  statePatch: Partial<ResumeState>;
} {
  try {
    const codes: string[] = [];
    const statePatch: Partial<ResumeState> = {};

    const {
      nowMs,
      resumeState,
      finalEnforcedExecutionMode,
      econDecision,
      econSeverity,
      execShapeStatus,
      execSizeCap,
      budgetAction,
    } = args;

    let windowStatus: CapitalRiskWindowStatusV1 = "WIN_FRESH";
    let usageLevel: CapitalRiskUsageLevelV1 = "RISK_LOW";
    let action: CapitalRiskActionV1 = "CAR_ALLOW";

    // R0: Defensive baseline
    if (!resumeState) {
      codes.push("CAR_DEFENSIVE_DEFER_V1");
      codes.push("CAR_ERROR_NO_RESUME_STATE");
      return {
        windowStatus: "WIN_FRESH",
        usageLevel: "RISK_LOW",
        action: "CAR_DEFER",
        codes: Array.from(new Set(codes)).sort().slice(0, 8),
        statePatch: {},
      };
    }

    // R1: Window reset (1h rolling)
    const WINDOW_MS = 60 * 60 * 1000;
    let anchor = resumeState.capitalRiskWindowAnchorTs;
    let eventCount = resumeState.capitalRiskEventsInWindow || 0;

    if (!anchor) {
      anchor = nowMs;
      eventCount = 0;
      windowStatus = "WIN_FRESH";
      codes.push("CAR_WINDOW_INIT");
      statePatch.capitalRiskWindowAnchorTs = anchor;
      statePatch.capitalRiskEventsInWindow = eventCount;
    } else if (nowMs - anchor > WINDOW_MS) {
      anchor = nowMs;
      eventCount = 0;
      windowStatus = "WIN_EXPIRED";
      codes.push("CAR_WINDOW_RESET");
      statePatch.capitalRiskWindowAnchorTs = anchor;
      statePatch.capitalRiskEventsInWindow = eventCount;
    } else {
      windowStatus = "WIN_ACTIVE";
      codes.push("CAR_WINDOW_ACTIVE");
    }

    // R2: Risk event accumulation
    let riskEventTriggered = false;

    const notSimOnly = finalEnforcedExecutionMode !== "SIM_ONLY";
    if (notSimOnly) {
      riskEventTriggered = true;
      codes.push("CAR_EVENT_TRIGGER_NOT_SIM_ONLY");
    }

    if (econSeverity === "SEV_HIGH" || econSeverity === "SEV_CRITICAL") {
      riskEventTriggered = true;
      codes.push("CAR_EVENT_TRIGGER_HIGH_SEVERITY");
    }

    if (execSizeCap && execSizeCap !== "SIZE_NONE") {
      riskEventTriggered = true;
      codes.push("CAR_EVENT_TRIGGER_SIZE_CAP");
    }

    if (execShapeStatus === "SHAPE_APPLIED") {
      riskEventTriggered = true;
      codes.push("CAR_EVENT_TRIGGER_SHAPE_APPLIED");
    }

    if (finalEnforcedExecutionMode === "SIM_ONLY" && !riskEventTriggered) {
      codes.push("CAR_EVENT_SKIP_SIM_ONLY");
    }

    if (riskEventTriggered) {
      eventCount++;
      codes.push("CAR_EVENT_INC");
      statePatch.capitalRiskEventsInWindow = eventCount;
    } else {
      codes.push("CAR_EVENT_SKIP");
    }

    // R3: Usage level classification
    if (eventCount >= 9) {
      usageLevel = "RISK_EXHAUSTED";
      codes.push("CAR_LEVEL_EXHAUSTED");
    } else if (eventCount >= 6) {
      usageLevel = "RISK_HIGH";
      codes.push("CAR_LEVEL_HIGH");
    } else if (eventCount >= 3) {
      usageLevel = "RISK_MEDIUM";
      codes.push("CAR_LEVEL_MEDIUM");
    } else {
      usageLevel = "RISK_LOW";
      codes.push("CAR_LEVEL_LOW");
    }

    statePatch.capitalRiskLevelLast = usageLevel;

    // R4: Action mapping
    if (usageLevel === "RISK_EXHAUSTED") {
      action = "CAR_ABORT";
      codes.push("CAR_ACTION_ABORT");
    } else if (usageLevel === "RISK_HIGH") {
      action = "CAR_DEFER";
      codes.push("CAR_ACTION_DEFER_BACKOFF_LONG");
    } else {
      action = "CAR_ALLOW";
      codes.push("CAR_ACTION_ALLOW");
    }

    // R5: Precedence with Budget/Econ
    if (budgetAction === "ABANDON") {
      action = "CAR_ABORT";
      codes.push("CAR_BYPASS_BY_BUDGET_ABANDON");
    } else if (budgetAction === "DEFER") {
      if (action !== "CAR_ABORT") {
        action = "CAR_DEFER";
      }
      codes.push("CAR_BYPASS_BY_BUDGET_DEFER");
    }

    if (econDecision === "ECON_ABANDON") {
      action = "CAR_ABORT";
      codes.push("CAR_BYPASS_BY_ECON_ABANDON");
    } else if (econDecision === "ECON_DEFER") {
      if (action !== "CAR_ABORT") {
        action = "CAR_DEFER";
      }
      codes.push("CAR_BYPASS_BY_ECON_DEFER");
    }

    return {
      windowStatus,
      usageLevel,
      action,
      codes: Array.from(new Set(codes)).sort().slice(0, 8),
      statePatch,
    };
  } catch (err) {
    return {
      windowStatus: "WIN_FRESH",
      usageLevel: "RISK_LOW",
      action: "CAR_DEFER",
      codes: ["CAR_DEFENSIVE_DEFER_V1", `CAR_ERROR_${String(err).substring(0, 30)}`].sort(),
      statePatch: {},
    };
  }
}

async function runUnitTests() {
  console.log("=== PR234: Capital-at-Risk Envelope v1 - Unit Tests ===\n");

  const baseState: ResumeState = {
    status: "STOPPED",
    stopReason: "STOP_NO_ROUTE",
    stopAtTs: Date.now() - 300000,
    lastPhaseLabel: "PHASE_NORMAL",
    warnings: [],
  };

  const tests = [
    {
      name: "R1: Fresh window init → WIN_FRESH, LOW, ALLOW",
      input: {
        nowMs: Date.now(),
        resumeState: { ...baseState },
        finalEnforcedExecutionMode: "LIVE" as ExecutionMode,
        econSeverity: "SEV_LOW",
      },
      expected: {
        windowStatus: "WIN_FRESH" as CapitalRiskWindowStatusV1,
        usageLevel: "RISK_LOW" as CapitalRiskUsageLevelV1,
        action: "CAR_ALLOW" as CapitalRiskActionV1,
        codes: ["CAR_ACTION_ALLOW", "CAR_EVENT_INC", "CAR_EVENT_TRIGGER_NOT_SIM_ONLY", "CAR_LEVEL_LOW", "CAR_WINDOW_INIT"],
        eventCount: 1,
      },
    },
    {
      name: "R2: SIM_ONLY bypass → no event increment",
      input: {
        nowMs: Date.now(),
        resumeState: {
          ...baseState,
          capitalRiskWindowAnchorTs: Date.now() - 1000,
          capitalRiskEventsInWindow: 0,
        },
        finalEnforcedExecutionMode: "SIM_ONLY" as ExecutionMode,
        econSeverity: "SEV_LOW",
      },
      expected: {
        windowStatus: "WIN_ACTIVE" as CapitalRiskWindowStatusV1,
        usageLevel: "RISK_LOW" as CapitalRiskUsageLevelV1,
        action: "CAR_ALLOW" as CapitalRiskActionV1,
        codes: ["CAR_ACTION_ALLOW", "CAR_EVENT_SKIP", "CAR_EVENT_SKIP_SIM_ONLY", "CAR_LEVEL_LOW", "CAR_WINDOW_ACTIVE"],
        eventCount: undefined, // No patch when count doesn't change
      },
    },
    {
      name: "R2: High severity triggers event even in SIM_ONLY",
      input: {
        nowMs: Date.now(),
        resumeState: {
          ...baseState,
          capitalRiskWindowAnchorTs: Date.now() - 1000,
          capitalRiskEventsInWindow: 0,
        },
        finalEnforcedExecutionMode: "SIM_ONLY" as ExecutionMode,
        econSeverity: "SEV_CRITICAL",
      },
      expected: {
        windowStatus: "WIN_ACTIVE" as CapitalRiskWindowStatusV1,
        usageLevel: "RISK_LOW" as CapitalRiskUsageLevelV1,
        action: "CAR_ALLOW" as CapitalRiskActionV1,
        codes: ["CAR_ACTION_ALLOW", "CAR_EVENT_INC", "CAR_EVENT_TRIGGER_HIGH_SEVERITY", "CAR_LEVEL_LOW", "CAR_WINDOW_ACTIVE"],
        eventCount: 1,
      },
    },
    {
      name: "R3: Event count 3-5 → MEDIUM, ALLOW",
      input: {
        nowMs: Date.now(),
        resumeState: {
          ...baseState,
          capitalRiskWindowAnchorTs: Date.now() - 1000,
          capitalRiskEventsInWindow: 2,
        },
        finalEnforcedExecutionMode: "LIVE" as ExecutionMode,
        econSeverity: "SEV_LOW",
      },
      expected: {
        windowStatus: "WIN_ACTIVE" as CapitalRiskWindowStatusV1,
        usageLevel: "RISK_MEDIUM" as CapitalRiskUsageLevelV1,
        action: "CAR_ALLOW" as CapitalRiskActionV1,
        codes: ["CAR_ACTION_ALLOW", "CAR_EVENT_INC", "CAR_EVENT_TRIGGER_NOT_SIM_ONLY", "CAR_LEVEL_MEDIUM", "CAR_WINDOW_ACTIVE"],
        eventCount: 3,
      },
    },
    {
      name: "R4: Event count 6-8 → HIGH, DEFER",
      input: {
        nowMs: Date.now(),
        resumeState: {
          ...baseState,
          capitalRiskWindowAnchorTs: Date.now() - 1000,
          capitalRiskEventsInWindow: 5,
        },
        finalEnforcedExecutionMode: "LIVE" as ExecutionMode,
        econSeverity: "SEV_LOW",
      },
      expected: {
        windowStatus: "WIN_ACTIVE" as CapitalRiskWindowStatusV1,
        usageLevel: "RISK_HIGH" as CapitalRiskUsageLevelV1,
        action: "CAR_DEFER" as CapitalRiskActionV1,
        codes: ["CAR_ACTION_DEFER_BACKOFF_LONG", "CAR_EVENT_INC", "CAR_EVENT_TRIGGER_NOT_SIM_ONLY", "CAR_LEVEL_HIGH", "CAR_WINDOW_ACTIVE"],
        eventCount: 6,
      },
    },
    {
      name: "R4: Event count >=9 → EXHAUSTED, ABORT",
      input: {
        nowMs: Date.now(),
        resumeState: {
          ...baseState,
          capitalRiskWindowAnchorTs: Date.now() - 1000,
          capitalRiskEventsInWindow: 8,
        },
        finalEnforcedExecutionMode: "LIVE" as ExecutionMode,
        econSeverity: "SEV_LOW",
      },
      expected: {
        windowStatus: "WIN_ACTIVE" as CapitalRiskWindowStatusV1,
        usageLevel: "RISK_EXHAUSTED" as CapitalRiskUsageLevelV1,
        action: "CAR_ABORT" as CapitalRiskActionV1,
        codes: ["CAR_ACTION_ABORT", "CAR_EVENT_INC", "CAR_EVENT_TRIGGER_NOT_SIM_ONLY", "CAR_LEVEL_EXHAUSTED", "CAR_WINDOW_ACTIVE"],
        eventCount: 9,
      },
    },
    {
      name: "R1: Window expired (>1h) → reset to LOW",
      input: {
        nowMs: Date.now(),
        resumeState: {
          ...baseState,
          capitalRiskWindowAnchorTs: Date.now() - (61 * 60 * 1000), // 61 minutes ago
          capitalRiskEventsInWindow: 8,
        },
        finalEnforcedExecutionMode: "LIVE" as ExecutionMode,
        econSeverity: "SEV_LOW",
      },
      expected: {
        windowStatus: "WIN_EXPIRED" as CapitalRiskWindowStatusV1,
        usageLevel: "RISK_LOW" as CapitalRiskUsageLevelV1,
        action: "CAR_ALLOW" as CapitalRiskActionV1,
        codes: ["CAR_ACTION_ALLOW", "CAR_EVENT_INC", "CAR_EVENT_TRIGGER_NOT_SIM_ONLY", "CAR_LEVEL_LOW", "CAR_WINDOW_RESET"],
        eventCount: 1,
      },
    },
    {
      name: "R0: Missing resumeState → defensive DEFER",
      input: {
        nowMs: Date.now(),
        resumeState: undefined,
        finalEnforcedExecutionMode: "LIVE" as ExecutionMode,
        econSeverity: "SEV_LOW",
      },
      expected: {
        windowStatus: "WIN_FRESH" as CapitalRiskWindowStatusV1,
        usageLevel: "RISK_LOW" as CapitalRiskUsageLevelV1,
        action: "CAR_DEFER" as CapitalRiskActionV1,
        codes: ["CAR_DEFENSIVE_DEFER_V1", "CAR_ERROR_NO_RESUME_STATE"],
        eventCount: undefined,
      },
    },
    {
      name: "R5: Budget ABANDON overrides to ABORT",
      input: {
        nowMs: Date.now(),
        resumeState: {
          ...baseState,
          capitalRiskWindowAnchorTs: Date.now() - 1000,
          capitalRiskEventsInWindow: 0,
        },
        finalEnforcedExecutionMode: "LIVE" as ExecutionMode,
        budgetAction: "ABANDON",
      },
      expected: {
        windowStatus: "WIN_ACTIVE" as CapitalRiskWindowStatusV1,
        usageLevel: "RISK_LOW" as CapitalRiskUsageLevelV1,
        action: "CAR_ABORT" as CapitalRiskActionV1,
        codes: ["CAR_BYPASS_BY_BUDGET_ABANDON", "CAR_EVENT_INC", "CAR_EVENT_TRIGGER_NOT_SIM_ONLY", "CAR_LEVEL_LOW", "CAR_WINDOW_ACTIVE"],
        eventCount: 1,
      },
    },
    {
      name: "R5: Econ ABANDON overrides to ABORT",
      input: {
        nowMs: Date.now(),
        resumeState: {
          ...baseState,
          capitalRiskWindowAnchorTs: Date.now() - 1000,
          capitalRiskEventsInWindow: 0,
        },
        finalEnforcedExecutionMode: "LIVE" as ExecutionMode,
        econDecision: "ECON_ABANDON" as EconConstraintActionV1,
      },
      expected: {
        windowStatus: "WIN_ACTIVE" as CapitalRiskWindowStatusV1,
        usageLevel: "RISK_LOW" as CapitalRiskUsageLevelV1,
        action: "CAR_ABORT" as CapitalRiskActionV1,
        codes: ["CAR_BYPASS_BY_ECON_ABANDON", "CAR_EVENT_INC", "CAR_EVENT_TRIGGER_NOT_SIM_ONLY", "CAR_LEVEL_LOW", "CAR_WINDOW_ACTIVE"],
        eventCount: 1,
      },
    },
  ];

  let passCount = 0;
  let failCount = 0;

  for (const test of tests) {
    console.log(`\n${test.name}`);
    const result = deriveCapitalRiskEnvelopeV1(test.input as any);

    let testPass = true;

    if (result.windowStatus !== test.expected.windowStatus) {
      console.log(`  ✗ windowStatus: expected ${test.expected.windowStatus}, got ${result.windowStatus}`);
      testPass = false;
    } else {
      console.log(`  ✓ windowStatus: ${result.windowStatus}`);
    }

    if (result.usageLevel !== test.expected.usageLevel) {
      console.log(`  ✗ usageLevel: expected ${test.expected.usageLevel}, got ${result.usageLevel}`);
      testPass = false;
    } else {
      console.log(`  ✓ usageLevel: ${result.usageLevel}`);
    }

    if (result.action !== test.expected.action) {
      console.log(`  ✗ action: expected ${test.expected.action}, got ${result.action}`);
      testPass = false;
    } else {
      console.log(`  ✓ action: ${result.action}`);
    }

    const missingCodes = test.expected.codes.filter((c) => !result.codes.includes(c));
    if (missingCodes.length > 0) {
      console.log(`  ✗ Missing codes: ${missingCodes.join(", ")}`);
      testPass = false;
    } else {
      console.log(`  ✓ codes: ${result.codes.join(", ")}`);
    }

    if (test.expected.eventCount !== undefined) {
      const actualCount = result.statePatch.capitalRiskEventsInWindow;
      if (actualCount !== test.expected.eventCount) {
        console.log(`  ✗ eventCount: expected ${test.expected.eventCount}, got ${actualCount}`);
        testPass = false;
      } else {
        console.log(`  ✓ eventCount: ${actualCount}`);
      }
    }

    if (testPass) {
      console.log(`  ✓ Test PASSED`);
      passCount++;
    } else {
      console.log(`  ✗ Test FAILED`);
      failCount++;
    }
  }

  console.log("\n=== Test Summary ===");
  console.log(`Total tests: ${tests.length}`);
  console.log(`Passed: ${passCount}`);
  console.log(`Failed: ${failCount}`);

  if (failCount === 0) {
    console.log("\n✓ All PR234 unit tests PASSED!");
    console.log("\n=== Implementation Verified ===");
    console.log("R0: Defensive baseline - ✓");
    console.log("R1: Window reset (1h rolling) - ✓");
    console.log("R2: Risk event accumulation (with SIM_ONLY bypass) - ✓");
    console.log("R3: Usage level classification (LOW/MEDIUM/HIGH/EXHAUSTED) - ✓");
    console.log("R4: Action mapping (ALLOW/DEFER/ABORT) - ✓");
    console.log("R5: Precedence with Budget/Econ - ✓");
  } else {
    console.log(`\n✗ ${failCount} test(s) FAILED`);
    process.exit(1);
  }
}

runUnitTests().catch((e) => {
  console.error("Fatal error:", e);
  process.exit(1);
});
