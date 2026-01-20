// tools/test-pr240-market-phase.ts
// PR240: Market Phase Graph v1 - Unit Test
//
// Purpose: Test deriveMarketPhaseGraphV1 function directly to verify
//          correct phase classification and edge derivation.

/**
 * Minimal implementation to test the market phase graph function directly.
 * We'll extract and test just the deriveMarketPhaseGraphV1 logic.
 */

import {
  MarketPhaseV1,
  MarketPhaseEdgeV1,
  MarketPhaseConfidenceV1,
  MarketPhaseTruthV1,
  SignalConsensusV1,
  MarketRegimeV1,
  ExecutionMode,
  QuarantineStatusV1,
  IncidentSeverityV1,
  CapitalRiskUsageLevelV1,
  RecoveryPermissionV1,
  LearningFreezeStatusV1,
} from "../src/rebalance/types";

// Copy of the market phase function for testing (matches supervisor.ts implementation)
function deriveMarketPhaseGraphV1(args: {
  // Inputs (label-only, from v1.4 layers)
  signalConsensus?: SignalConsensusV1;
  regime?: MarketRegimeV1;
  executionModeEnforced?: ExecutionMode;
  quarantineStatus?: QuarantineStatusV1;
  quarantineSeverity?: IncidentSeverityV1;
  capitalRiskLevel?: CapitalRiskUsageLevelV1;
  econSeverity?: string; // SEV_LOW | SEV_MEDIUM | SEV_HIGH | SEV_CRITICAL
  recoveryGovernance?: RecoveryPermissionV1;
  learningFreezeStatus?: LearningFreezeStatusV1;
  oscillationWarn?: boolean; // true = WARN, false = OK
  lastPhase?: MarketPhaseV1;
  nowMs: number;
}): MarketPhaseTruthV1 {
  try {
    const phase_codes: string[] = [];
    const phase_edge_codes: string[] = [];

    const {
      signalConsensus,
      regime,
      executionModeEnforced,
      quarantineStatus,
      quarantineSeverity,
      capitalRiskLevel,
      econSeverity,
      recoveryGovernance,
      learningFreezeStatus,
      oscillationWarn,
      lastPhase,
      nowMs,
    } = args;

    let phase: MarketPhaseV1 = "PHASE_CALM";
    let edge: MarketPhaseEdgeV1 = "EDGE_STAY";
    let confidence: MarketPhaseConfidenceV1 = "CONF_STRONG";

    // R1: Hard overrides (highest priority → PHASE_DISLOCATION)
    if (quarantineStatus === "Q1_ACTIVE" || quarantineSeverity === "SEV3_CRITICAL") {
      phase = "PHASE_DISLOCATION";
      confidence = "CONF_STRONG";
      phase_codes.push("PHASE_FROM_QUARANTINE");
      phase_codes.push("PHASE_R1_DISLOCATION");
    } else if (capitalRiskLevel === "RISK_EXHAUSTED") {
      phase = "PHASE_DISLOCATION";
      confidence = "CONF_STRONG";
      phase_codes.push("PHASE_FROM_CAPITAL_RISK_EXHAUSTED");
      phase_codes.push("PHASE_R1_DISLOCATION");
    } else if (recoveryGovernance === "PERMANENT_HALT") {
      phase = "PHASE_DISLOCATION";
      confidence = "CONF_STRONG";
      phase_codes.push("PHASE_FROM_GOV_PERMANENT_HALT");
      phase_codes.push("PHASE_R1_DISLOCATION");
    }
    // R2: Stress classification
    else if (signalConsensus === "CONSENSUS_UNTRUSTED") {
      // Check if combined with high risk → DISLOCATION
      if (capitalRiskLevel === "RISK_HIGH" || econSeverity === "SEV_CRITICAL") {
        phase = "PHASE_DISLOCATION";
        phase_codes.push("PHASE_FROM_SIGNAL_UNTRUSTED_HIGH_RISK");
        phase_codes.push("PHASE_R2_DISLOCATION");
      } else {
        phase = "PHASE_STRESS";
        phase_codes.push("PHASE_FROM_SIGNAL_UNTRUSTED");
        phase_codes.push("PHASE_R2_STRESS");
      }
      confidence = "CONF_WEAK";
    } else if (signalConsensus === "CONSENSUS_DEGRADED") {
      phase = "PHASE_STRESS";
      confidence = "CONF_WEAK";
      phase_codes.push("PHASE_FROM_SIGNAL_DEGRADED");
      phase_codes.push("PHASE_R2_STRESS");
    } else if (econSeverity === "SEV_CRITICAL") {
      // Check if combined with high capital risk → DISLOCATION
      const riskLevel = capitalRiskLevel as CapitalRiskUsageLevelV1 | undefined;
      const isHighRisk = riskLevel === "RISK_HIGH" || riskLevel === "RISK_EXHAUSTED";
      if (isHighRisk) {
        phase = "PHASE_DISLOCATION";
        phase_codes.push("PHASE_FROM_ECON_CRITICAL_HIGH_RISK");
        phase_codes.push("PHASE_R2_DISLOCATION");
      } else {
        phase = "PHASE_STRESS";
        phase_codes.push("PHASE_FROM_ECON_CRITICAL");
        phase_codes.push("PHASE_R2_STRESS");
      }
      confidence = "CONF_WEAK";
    } else if (learningFreezeStatus === "FREEZE_ON") {
      // Minimum PHASE_TENSION (never CALM)
      phase = "PHASE_TENSION";
      confidence = "CONF_WEAK";
      phase_codes.push("PHASE_FROM_FREEZE");
      phase_codes.push("PHASE_R2_TENSION_FROM_FREEZE");
    }
    // R5: Recovery classification (check before R3/R4)
    else if (
      (lastPhase === "PHASE_DISLOCATION" || lastPhase === "PHASE_STRESS") &&
      (!quarantineStatus || (quarantineStatus as QuarantineStatusV1) !== "Q1_ACTIVE") &&
      (recoveryGovernance === "COOLDOWN_ONLY" || recoveryGovernance === "MANUAL_ONLY")
    ) {
      phase = "PHASE_RECOVERY";
      confidence = signalConsensus === "CONSENSUS_STRONG" ? "CONF_STRONG" : "CONF_WEAK";
      phase_codes.push("PHASE_FROM_POST_INCIDENT_GOV");
      phase_codes.push("PHASE_R5_RECOVERY");
    }
    // R3: Tension classification
    else if (
      signalConsensus === "CONSENSUS_WEAK" ||
      oscillationWarn === true ||
      econSeverity === "SEV_HIGH"
    ) {
      phase = "PHASE_TENSION";
      confidence = signalConsensus === "CONSENSUS_WEAK" ? "CONF_WEAK" : "CONF_STRONG";
      phase_codes.push("PHASE_FROM_WEAK_OR_OSC_OR_ECON_HIGH");
      phase_codes.push("PHASE_R3_TENSION");
    }
    // R4: Calm classification
    else if (
      signalConsensus === "CONSENSUS_STRONG" &&
      (econSeverity === "SEV_LOW" || econSeverity === "SEV_MEDIUM" || !econSeverity) &&
      (capitalRiskLevel === "RISK_LOW" || capitalRiskLevel === "RISK_MEDIUM" || !capitalRiskLevel) &&
      (!quarantineStatus || (quarantineStatus as QuarantineStatusV1) !== "Q1_ACTIVE") &&
      (!learningFreezeStatus || (learningFreezeStatus as LearningFreezeStatusV1) !== "FREEZE_ON")
    ) {
      phase = "PHASE_CALM";
      confidence = "CONF_STRONG";
      phase_codes.push("PHASE_FROM_STRONG_STABLE");
      phase_codes.push("PHASE_R4_CALM");
    }
    // Fallback to TENSION if no other rules matched
    else {
      phase = "PHASE_TENSION";
      confidence = signalConsensus === "CONSENSUS_STRONG" ? "CONF_STRONG" : "CONF_WEAK";
      phase_codes.push("PHASE_FALLBACK_TENSION");
    }

    // R6: Confidence adjustment
    // Only adjust confidence if not already set by specific rules (e.g., freeze, quarantine)
    // Freeze ON always means CONF_WEAK, even if signals are strong
    if (!signalConsensus) {
      confidence = "CONF_UNKNOWN";
      phase_codes.push("PHASE_CONF_UNKNOWN_NO_CONSENSUS");
    } else if (learningFreezeStatus === "FREEZE_ON") {
      // Keep CONF_WEAK from freeze rule (don't override)
      confidence = "CONF_WEAK";
    } else if (signalConsensus === "CONSENSUS_STRONG") {
      confidence = "CONF_STRONG";
    } else if (signalConsensus === "CONSENSUS_WEAK" || signalConsensus === "CONSENSUS_DEGRADED") {
      confidence = "CONF_WEAK";
    } else if (signalConsensus === "CONSENSUS_UNTRUSTED") {
      confidence = "CONF_WEAK";
    }

    // R7: Edge derivation
    const phaseSeverity: { [key in MarketPhaseV1]: number } = {
      PHASE_CALM: 0,
      PHASE_TENSION: 1,
      PHASE_RECOVERY: 1.5, // Between TENSION and STRESS
      PHASE_STRESS: 2,
      PHASE_DISLOCATION: 3,
      PHASE_UNKNOWN_SAFE: 4,
    };

    if (!lastPhase) {
      // No prior phase
      if (phase === "PHASE_CALM") {
        edge = "EDGE_STAY"; // Starting in calm is not a reset
        phase_edge_codes.push("EDGE_STAY_INITIAL_CALM");
      } else {
        edge = "EDGE_RESET_SAFE"; // Starting in non-calm is a safe reset
        phase_edge_codes.push("EDGE_RESET_SAFE_INITIAL");
      }
    } else if (phase === lastPhase) {
      edge = "EDGE_STAY";
      phase_edge_codes.push("EDGE_STAY_NO_CHANGE");
    } else if (phaseSeverity[phase] > phaseSeverity[lastPhase]) {
      edge = "EDGE_ESCALATE";
      phase_edge_codes.push(`EDGE_ESCALATE_${lastPhase}_TO_${phase}`);
    } else if (phaseSeverity[phase] < phaseSeverity[lastPhase]) {
      edge = "EDGE_DEESCALATE";
      phase_edge_codes.push(`EDGE_DEESCALATE_${lastPhase}_TO_${phase}`);
    } else {
      edge = "EDGE_STAY"; // Safety fallback
      phase_edge_codes.push("EDGE_STAY_FALLBACK");
    }

    return {
      phase,
      edge,
      confidence,
      phase_codes: Array.from(new Set(phase_codes)).sort().slice(0, 8),
      phase_edge_codes: Array.from(new Set(phase_edge_codes)).sort().slice(0, 8),
    };
  } catch (err) {
    // R0: Defensive: On error, return PHASE_UNKNOWN_SAFE
    return {
      phase: "PHASE_UNKNOWN_SAFE",
      edge: "EDGE_ERROR_SAFE",
      confidence: "CONF_UNKNOWN",
      phase_codes: ["PHASE_ERR_FALLBACK", `PHASE_ERR_${String(err).substring(0, 30)}`].sort().slice(0, 8),
      phase_edge_codes: ["EDGE_ERR_FALLBACK"].slice(0, 8),
    };
  }
}

// Test scenarios
function runTests() {
  let passedTests = 0;
  let failedTests = 0;

  console.log("Starting PR240 Market Phase Graph v1 Tests...\n");

  // Test 1: Strong stable → CALM
  console.log("Test 1: Strong stable → CALM");
  const test1 = deriveMarketPhaseGraphV1({
    signalConsensus: "CONSENSUS_STRONG",
    econSeverity: "SEV_LOW",
    capitalRiskLevel: "RISK_LOW",
    quarantineStatus: "Q0_NONE",
    learningFreezeStatus: "FREEZE_OFF",
    nowMs: Date.now(),
  });
  if (test1.phase === "PHASE_CALM" && test1.confidence === "CONF_STRONG") {
    console.log("✓ PASS: Phase is CALM with CONF_STRONG");
    passedTests++;
  } else {
    console.log(`✗ FAIL: Expected PHASE_CALM + CONF_STRONG, got ${test1.phase} + ${test1.confidence}`);
    failedTests++;
  }

  // Test 2: Weak consensus → TENSION
  console.log("\nTest 2: Weak consensus → TENSION");
  const test2 = deriveMarketPhaseGraphV1({
    signalConsensus: "CONSENSUS_WEAK",
    econSeverity: "SEV_LOW",
    capitalRiskLevel: "RISK_LOW",
    quarantineStatus: "Q0_NONE",
    learningFreezeStatus: "FREEZE_OFF",
    nowMs: Date.now(),
  });
  if (test2.phase === "PHASE_TENSION" && test2.confidence === "CONF_WEAK") {
    console.log("✓ PASS: Phase is TENSION with CONF_WEAK");
    passedTests++;
  } else {
    console.log(`✗ FAIL: Expected PHASE_TENSION + CONF_WEAK, got ${test2.phase} + ${test2.confidence}`);
    failedTests++;
  }

  // Test 3: Degraded consensus → STRESS
  console.log("\nTest 3: Degraded consensus → STRESS");
  const test3 = deriveMarketPhaseGraphV1({
    signalConsensus: "CONSENSUS_DEGRADED",
    econSeverity: "SEV_MEDIUM",
    capitalRiskLevel: "RISK_MEDIUM",
    quarantineStatus: "Q0_NONE",
    learningFreezeStatus: "FREEZE_OFF",
    nowMs: Date.now(),
  });
  if (test3.phase === "PHASE_STRESS" && test3.confidence === "CONF_WEAK") {
    console.log("✓ PASS: Phase is STRESS with CONF_WEAK");
    passedTests++;
  } else {
    console.log(`✗ FAIL: Expected PHASE_STRESS + CONF_WEAK, got ${test3.phase} + ${test3.confidence}`);
    failedTests++;
  }

  // Test 4: Untrusted consensus → STRESS
  console.log("\nTest 4: Untrusted consensus → STRESS");
  const test4 = deriveMarketPhaseGraphV1({
    signalConsensus: "CONSENSUS_UNTRUSTED",
    econSeverity: "SEV_MEDIUM",
    capitalRiskLevel: "RISK_MEDIUM",
    quarantineStatus: "Q0_NONE",
    learningFreezeStatus: "FREEZE_OFF",
    nowMs: Date.now(),
  });
  if (test4.phase === "PHASE_STRESS" && test4.confidence === "CONF_WEAK") {
    console.log("✓ PASS: Phase is STRESS with CONF_WEAK");
    passedTests++;
  } else {
    console.log(`✗ FAIL: Expected PHASE_STRESS + CONF_WEAK, got ${test4.phase} + ${test4.confidence}`);
    failedTests++;
  }

  // Test 5: Quarantine active → DISLOCATION
  console.log("\nTest 5: Quarantine active → DISLOCATION");
  const test5 = deriveMarketPhaseGraphV1({
    signalConsensus: "CONSENSUS_STRONG",
    quarantineStatus: "Q1_ACTIVE",
    quarantineSeverity: "SEV2_HIGH",
    capitalRiskLevel: "RISK_LOW",
    learningFreezeStatus: "FREEZE_OFF",
    nowMs: Date.now(),
  });
  if (test5.phase === "PHASE_DISLOCATION" && test5.confidence === "CONF_STRONG") {
    console.log("✓ PASS: Phase is DISLOCATION with CONF_STRONG");
    passedTests++;
  } else {
    console.log(`✗ FAIL: Expected PHASE_DISLOCATION + CONF_STRONG, got ${test5.phase} + ${test5.confidence}`);
    failedTests++;
  }

  // Test 6: Capital risk exhausted → DISLOCATION
  console.log("\nTest 6: Capital risk exhausted → DISLOCATION");
  const test6 = deriveMarketPhaseGraphV1({
    signalConsensus: "CONSENSUS_STRONG",
    capitalRiskLevel: "RISK_EXHAUSTED",
    quarantineStatus: "Q0_NONE",
    learningFreezeStatus: "FREEZE_OFF",
    nowMs: Date.now(),
  });
  if (test6.phase === "PHASE_DISLOCATION" && test6.confidence === "CONF_STRONG") {
    console.log("✓ PASS: Phase is DISLOCATION with CONF_STRONG");
    passedTests++;
  } else {
    console.log(`✗ FAIL: Expected PHASE_DISLOCATION + CONF_STRONG, got ${test6.phase} + ${test6.confidence}`);
    failedTests++;
  }

  // Test 7: Post-incident governance cooldown → RECOVERY
  console.log("\nTest 7: Post-incident governance cooldown → RECOVERY");
  const test7 = deriveMarketPhaseGraphV1({
    signalConsensus: "CONSENSUS_STRONG",
    econSeverity: "SEV_LOW",
    capitalRiskLevel: "RISK_LOW",
    quarantineStatus: "Q0_NONE",
    recoveryGovernance: "COOLDOWN_ONLY",
    learningFreezeStatus: "FREEZE_OFF",
    lastPhase: "PHASE_DISLOCATION",
    nowMs: Date.now(),
  });
  if (test7.phase === "PHASE_RECOVERY" && test7.confidence === "CONF_STRONG") {
    console.log("✓ PASS: Phase is RECOVERY with CONF_STRONG");
    passedTests++;
  } else {
    console.log(`✗ FAIL: Expected PHASE_RECOVERY + CONF_STRONG, got ${test7.phase} + ${test7.confidence}`);
    failedTests++;
  }

  // Test 8: Freeze ON prevents CALM → TENSION
  console.log("\nTest 8: Freeze ON prevents CALM → TENSION");
  const test8 = deriveMarketPhaseGraphV1({
    signalConsensus: "CONSENSUS_STRONG",
    econSeverity: "SEV_LOW",
    capitalRiskLevel: "RISK_LOW",
    quarantineStatus: "Q0_NONE",
    learningFreezeStatus: "FREEZE_ON",
    nowMs: Date.now(),
  });
  if (test8.phase === "PHASE_TENSION" && test8.confidence === "CONF_WEAK") {
    console.log("✓ PASS: Phase is TENSION with CONF_WEAK (freeze prevents CALM)");
    passedTests++;
  } else {
    console.log(`✗ FAIL: Expected PHASE_TENSION + CONF_WEAK, got ${test8.phase} + ${test8.confidence}`);
    failedTests++;
  }

  // Test 9: Edge escalate CALM → TENSION
  console.log("\nTest 9: Edge escalate CALM → TENSION");
  const test9 = deriveMarketPhaseGraphV1({
    signalConsensus: "CONSENSUS_WEAK",
    econSeverity: "SEV_LOW",
    capitalRiskLevel: "RISK_LOW",
    quarantineStatus: "Q0_NONE",
    learningFreezeStatus: "FREEZE_OFF",
    lastPhase: "PHASE_CALM",
    nowMs: Date.now(),
  });
  if (test9.phase === "PHASE_TENSION" && test9.edge === "EDGE_ESCALATE") {
    console.log("✓ PASS: Phase escalated from CALM to TENSION");
    passedTests++;
  } else {
    console.log(`✗ FAIL: Expected PHASE_TENSION + EDGE_ESCALATE, got ${test9.phase} + ${test9.edge}`);
    failedTests++;
  }

  // Test 10: Edge deescalate STRESS → RECOVERY
  console.log("\nTest 10: Edge deescalate STRESS → RECOVERY");
  const test10 = deriveMarketPhaseGraphV1({
    signalConsensus: "CONSENSUS_STRONG",
    econSeverity: "SEV_LOW",
    capitalRiskLevel: "RISK_LOW",
    quarantineStatus: "Q0_NONE",
    recoveryGovernance: "COOLDOWN_ONLY",
    learningFreezeStatus: "FREEZE_OFF",
    lastPhase: "PHASE_STRESS",
    nowMs: Date.now(),
  });
  if (test10.phase === "PHASE_RECOVERY" && test10.edge === "EDGE_DEESCALATE") {
    console.log("✓ PASS: Phase deescalated from STRESS to RECOVERY");
    passedTests++;
  } else {
    console.log(`✗ FAIL: Expected PHASE_RECOVERY + EDGE_DEESCALATE, got ${test10.phase} + ${test10.edge}`);
    failedTests++;
  }

  // Test 11: Defensive missing labels → UNKNOWN_SAFE
  console.log("\nTest 11: Defensive missing signalConsensus → safe fallback");
  const test11 = deriveMarketPhaseGraphV1({
    // signalConsensus: missing (undefined)
    econSeverity: "SEV_MEDIUM",
    capitalRiskLevel: "RISK_MEDIUM",
    quarantineStatus: "Q0_NONE",
    learningFreezeStatus: "FREEZE_OFF",
    nowMs: Date.now(),
  });
  if (test11.confidence === "CONF_UNKNOWN") {
    console.log("✓ PASS: Confidence is CONF_UNKNOWN when signalConsensus missing");
    passedTests++;
  } else {
    console.log(`✗ FAIL: Expected CONF_UNKNOWN, got ${test11.confidence}`);
    failedTests++;
  }

  // Test 12: Edge STAY (no phase change)
  console.log("\nTest 12: Edge STAY (no phase change)");
  const test12 = deriveMarketPhaseGraphV1({
    signalConsensus: "CONSENSUS_STRONG",
    econSeverity: "SEV_LOW",
    capitalRiskLevel: "RISK_LOW",
    quarantineStatus: "Q0_NONE",
    learningFreezeStatus: "FREEZE_OFF",
    lastPhase: "PHASE_CALM",
    nowMs: Date.now(),
  });
  if (test12.phase === "PHASE_CALM" && test12.edge === "EDGE_STAY") {
    console.log("✓ PASS: Edge is STAY (no phase change)");
    passedTests++;
  } else {
    console.log(`✗ FAIL: Expected PHASE_CALM + EDGE_STAY, got ${test12.phase} + ${test12.edge}`);
    failedTests++;
  }

  // Test 13: EDGE_RESET_SAFE (initial non-calm state)
  console.log("\nTest 13: EDGE_RESET_SAFE (initial non-calm state)");
  const test13 = deriveMarketPhaseGraphV1({
    signalConsensus: "CONSENSUS_WEAK",
    econSeverity: "SEV_MEDIUM",
    capitalRiskLevel: "RISK_MEDIUM",
    quarantineStatus: "Q0_NONE",
    learningFreezeStatus: "FREEZE_OFF",
    // lastPhase: undefined (no prior phase)
    nowMs: Date.now(),
  });
  if (test13.phase === "PHASE_TENSION" && test13.edge === "EDGE_RESET_SAFE") {
    console.log("✓ PASS: Edge is EDGE_RESET_SAFE for initial non-calm state");
    passedTests++;
  } else {
    console.log(`✗ FAIL: Expected PHASE_TENSION + EDGE_RESET_SAFE, got ${test13.phase} + ${test13.edge}`);
    failedTests++;
  }

  // Summary
  console.log("\n========================================");
  console.log(`Total Tests: ${passedTests + failedTests}`);
  console.log(`Passed: ${passedTests}`);
  console.log(`Failed: ${failedTests}`);
  console.log("========================================");

  if (failedTests === 0) {
    console.log("\n✓ All tests passed!");
    process.exit(0);
  } else {
    console.log("\n✗ Some tests failed!");
    process.exit(1);
  }
}

// Run tests
runTests();
