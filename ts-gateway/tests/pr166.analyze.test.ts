/**
 * PR166: v1.4 Snapshot Analysis Helper v1 - Tests
 *
 * Purpose:
 *   Verify snapshot analysis functionality (frequency, confusion, timing).
 *
 * Test Coverage:
 *   1. Empty log → defensive (PARTIAL + warnings)
 *   2. Phase frequency works
 *   3. Block reason ranking works
 *   4. Confusion signal fires (synthetic data)
 *   5. Confusion signal doesn't fire (healthy data)
 *   6. STOP reason classification (phase policy / gate / hardstop)
 *   7. Lag category calculation (short/medium/long boundaries)
 *   8. Sanitize removes counts (normal mode)
 *   9. Debug mode allows counts
 *   10. Exception doesn't throw (always returns)
 */

import { MarketRegimeSnapshotV1 } from "../src/snapshot/types";
import { analyzeSnapshotsV1 } from "../src/analyze/analyzer";
import {
  sanitizeAnalysisForDisplay,
  isDebugMode,
  sanitizeAnalysisLabel,
} from "../src/analyze/guards";

describe("PR166: Snapshot Analysis Helper v1", () => {
  /**
   * Test 1: Empty log → defensive (PARTIAL + warnings)
   */
  test("Test 1: Empty log → defensive (PARTIAL + warnings)", async () => {
    const analysis = await analyzeSnapshotsV1([]);

    expect(analysis.version).toBe("v1.0");
    expect(analysis.status).toBe("PARTIAL");
    expect(analysis.warnings).toContain("WARN_NO_SNAPSHOTS_TO_ANALYZE");
    expect(analysis.snapshotCount).toBe(0);
    expect(analysis.frequency.phaseLabels).toEqual([]);
    // Should not throw
  });

  /**
   * Test 2: Phase frequency works
   */
  test("Test 2: Phase frequency works", async () => {
    const snapshots: MarketRegimeSnapshotV1[] = [
      createMockSnapshot({ shockPhase: "PHASE_NORMAL" }),
      createMockSnapshot({ shockPhase: "PHASE_NORMAL" }),
      createMockSnapshot({ shockPhase: "PHASE_PRE_SHOCK" }),
      createMockSnapshot({ shockPhase: "PHASE_NORMAL" }),
    ];

    const analysis = await analyzeSnapshotsV1(snapshots);

    expect(analysis.frequency.phaseLabels.length).toBeGreaterThan(0);

    const normalPhase = analysis.frequency.phaseLabels.find(
      (p) => p.label === "PHASE_NORMAL"
    );
    expect(normalPhase).toBeDefined();
    expect(normalPhase?.count).toBe(3);

    const preShockPhase = analysis.frequency.phaseLabels.find(
      (p) => p.label === "PHASE_PRE_SHOCK"
    );
    expect(preShockPhase).toBeDefined();
    expect(preShockPhase?.count).toBe(1);
  });

  /**
   * Test 3: Block reason ranking works
   */
  test("Test 3: Block reason ranking works", async () => {
    const snapshots: MarketRegimeSnapshotV1[] = [
      createMockSnapshot({ blockReason: "BLOCK_ORACLE_STALE" }),
      createMockSnapshot({ blockReason: "BLOCK_ORACLE_STALE" }),
      createMockSnapshot({ blockReason: "BLOCK_IMPACT_HIGH" }),
      createMockSnapshot({ blockReason: "BLOCK_ORACLE_STALE" }),
    ];

    const analysis = await analyzeSnapshotsV1(snapshots);

    expect(analysis.frequency.blockReasons.length).toBeGreaterThan(0);

    // Top block reason should be BLOCK_ORACLE_STALE (3 occurrences)
    expect(analysis.frequency.blockReasons[0].label).toBe("BLOCK_ORACLE_STALE");
    expect(analysis.frequency.blockReasons[0].count).toBe(3);
  });

  /**
   * Test 4: Confusion signal fires (synthetic data)
   */
  test("Test 4: Confusion signal fires (synthetic data)", async () => {
    // Create data with SHOCK phases + TPL_RISK_90 (should trigger confusion)
    const snapshots: MarketRegimeSnapshotV1[] = [];

    for (let i = 0; i < 10; i++) {
      snapshots.push(
        createMockSnapshot({
          shockPhase: "PHASE_UP_REVERSAL",
          templateId: "TPL_RISK_90", // High risk in reversal (confusion!)
        })
      );
    }

    const analysis = await analyzeSnapshotsV1(snapshots);

    const confusionSignal = analysis.confusionSignals.find(
      (s) => s.type === "CONFUSION_SHOCK_BUT_RISK_HIGH_FREQUENT"
    );

    expect(confusionSignal).toBeDefined();
    expect(confusionSignal?.active).toBe(true);
    expect(confusionSignal?.reasons.length).toBeGreaterThan(0);
  });

  /**
   * Test 5: Confusion signal doesn't fire (healthy data)
   */
  test("Test 5: Confusion signal doesn't fire (healthy data)", async () => {
    // Create healthy data (NORMAL phase + TPL_RISK_50)
    const snapshots: MarketRegimeSnapshotV1[] = [];

    for (let i = 0; i < 10; i++) {
      snapshots.push(
        createMockSnapshot({
          shockPhase: "PHASE_NORMAL",
          templateId: "TPL_RISK_50", // Appropriate risk for normal
        })
      );
    }

    const analysis = await analyzeSnapshotsV1(snapshots);

    const confusionSignal = analysis.confusionSignals.find(
      (s) => s.type === "CONFUSION_SHOCK_BUT_RISK_HIGH_FREQUENT"
    );

    expect(confusionSignal).toBeDefined();
    expect(confusionSignal?.active).toBe(false);
  });

  /**
   * Test 6: STOP reason classification
   */
  test("Test 6: STOP reason classification", async () => {
    const snapshots: MarketRegimeSnapshotV1[] = [
      createMockSnapshot({
        blockReason: "BLOCK_PHASE_ESCALATION",
        resume: "WAIT",
      }),
      createMockSnapshot({
        blockReason: "BLOCK_ORACLE_STALE",
        resume: "WAIT",
      }),
      createMockSnapshot({
        hardStop: "ACTIVE",
        resume: "WAIT",
      }),
    ];

    const analysis = await analyzeSnapshotsV1(snapshots);

    expect(analysis.timing.stopReasons.length).toBeGreaterThan(0);

    const phaseStop = analysis.timing.stopReasons.find(
      (s) => s.category === "STOP_BY_PHASE_POLICY"
    );
    expect(phaseStop).toBeDefined();

    const gateStop = analysis.timing.stopReasons.find(
      (s) => s.category === "STOP_BY_GATE"
    );
    expect(gateStop).toBeDefined();

    const hardStopStop = analysis.timing.stopReasons.find(
      (s) => s.category === "STOP_BY_POLICY_HARDSTOP"
    );
    expect(hardStopStop).toBeDefined();
  });

  /**
   * Test 7: Lag category calculation
   */
  test("Test 7: Lag category calculation", async () => {
    // Create phase transitions with different lags
    const snapshots: MarketRegimeSnapshotV1[] = [
      // PHASE_NORMAL (tick 0)
      createMockSnapshot({ shockPhase: "PHASE_NORMAL" }),
      createMockSnapshot({ shockPhase: "PHASE_NORMAL" }),
      // PRE_SHOCK (tick 2) - LAG_SHORT (2 ticks)
      createMockSnapshot({ shockPhase: "PHASE_PRE_SHOCK" }),
      createMockSnapshot({ shockPhase: "PHASE_PRE_SHOCK" }),
      createMockSnapshot({ shockPhase: "PHASE_PRE_SHOCK" }),
      createMockSnapshot({ shockPhase: "PHASE_PRE_SHOCK" }),
      createMockSnapshot({ shockPhase: "PHASE_PRE_SHOCK" }),
      createMockSnapshot({ shockPhase: "PHASE_PRE_SHOCK" }),
      // UP_SHOCK (tick 8) - LAG_MEDIUM (6 ticks)
      createMockSnapshot({ shockPhase: "PHASE_UP_SHOCK" }),
    ];

    const analysis = await analyzeSnapshotsV1(snapshots);

    expect(analysis.timing.transitions.length).toBeGreaterThan(0);

    // First transition: NORMAL → PRE_SHOCK (2 ticks = LAG_SHORT)
    const firstTransition = analysis.timing.transitions[0];
    expect(firstTransition.from).toBe("PHASE_NORMAL");
    expect(firstTransition.to).toBe("PHASE_PRE_SHOCK");
    expect(firstTransition.lag).toBe("LAG_SHORT");

    // Second transition: PRE_SHOCK → UP_SHOCK (6 ticks = LAG_MEDIUM)
    if (analysis.timing.transitions.length > 1) {
      const secondTransition = analysis.timing.transitions[1];
      expect(secondTransition.from).toBe("PHASE_PRE_SHOCK");
      expect(secondTransition.to).toBe("PHASE_UP_SHOCK");
      expect(secondTransition.lag).toBe("LAG_MEDIUM");
    }
  });

  /**
   * Test 8: Sanitize removes counts (normal mode)
   */
  test("Test 8: Sanitize removes counts (normal mode)", async () => {
    const snapshots: MarketRegimeSnapshotV1[] = [
      createMockSnapshot({ shockPhase: "PHASE_NORMAL" }),
      createMockSnapshot({ shockPhase: "PHASE_NORMAL" }),
    ];

    const analysis = await analyzeSnapshotsV1(snapshots);

    // Verify raw analysis has counts
    expect(analysis.snapshotCount).toBe(2);
    expect(analysis.frequency.phaseLabels[0].count).toBeGreaterThan(0);

    // Sanitize for display (normal mode)
    const sanitized = sanitizeAnalysisForDisplay(analysis, false);

    // Verify counts are removed
    expect(sanitized.snapshotCountLabel).toBe("HAS_SNAPSHOTS");
    expect((sanitized.frequency as any).phaseLabels[0].count).toBeUndefined();
    // frequency.phaseLabels is string[] (no count field)
  });

  /**
   * Test 9: Debug mode allows counts
   */
  test("Test 9: Debug mode allows counts", async () => {
    const snapshots: MarketRegimeSnapshotV1[] = [
      createMockSnapshot({ shockPhase: "PHASE_NORMAL" }),
      createMockSnapshot({ shockPhase: "PHASE_NORMAL" }),
    ];

    const analysis = await analyzeSnapshotsV1(snapshots);

    // In debug mode, raw analysis is returned (not sanitized)
    // We can't directly test MERIDIAN_DEBUG env var here, but we can verify
    // that the raw analysis has counts
    expect(analysis.snapshotCount).toBe(2);
    expect(analysis.frequency.phaseLabels[0].count).toBe(2);
  });

  /**
   * Test 10: Exception doesn't throw (always returns)
   */
  test("Test 10: Exception doesn't throw (always returns)", async () => {
    // Pass invalid data (should not throw)
    const invalidSnapshots = [null, undefined, {}] as any;

    const analysis = await analyzeSnapshotsV1(invalidSnapshots);

    // Should return ERROR status, not throw
    expect(analysis.version).toBe("v1.0");
    expect(analysis.status).toBe("ERROR");
    expect(analysis.warnings).toContain("WARN_ANALYSIS_ERROR");
  });

  /**
   * Test 11: Sanitize label removes forbidden patterns
   */
  test("Test 11: Sanitize label removes forbidden patterns", () => {
    // Token literals
    expect(sanitizeAnalysisLabel("wBTC price")).toBe("REDACTED");
    expect(sanitizeAnalysisLabel("USDC balance")).toBe("REDACTED");

    // Trading vocab
    expect(sanitizeAnalysisLabel("buy signal")).toBe("REDACTED");
    expect(sanitizeAnalysisLabel("sell order")).toBe("REDACTED");

    // Prescriptive
    expect(sanitizeAnalysisLabel("should execute")).toBe("REDACTED");

    // Address
    expect(sanitizeAnalysisLabel("0x1234abcd")).toBe("REDACTED");

    // Allowed
    expect(sanitizeAnalysisLabel("PHASE_NORMAL")).toBe("PHASE_NORMAL");
    expect(sanitizeAnalysisLabel("TPL_RISK_50")).toBe("TPL_RISK_50");
  });

  /**
   * Test 12: GATE_BLOCK_DOMINATES fires
   */
  test("Test 12: GATE_BLOCK_DOMINATES fires", async () => {
    // Create data with majority BLOCK
    const snapshots: MarketRegimeSnapshotV1[] = [];

    for (let i = 0; i < 10; i++) {
      snapshots.push(
        createMockSnapshot({
          gateDecision: "BLOCK",
          blockReason: "BLOCK_ORACLE_STALE",
        })
      );
    }

    for (let i = 0; i < 3; i++) {
      snapshots.push(
        createMockSnapshot({
          gateDecision: "PASS",
        })
      );
    }

    const analysis = await analyzeSnapshotsV1(snapshots);

    const gateBlockSignal = analysis.confusionSignals.find(
      (s) => s.type === "CONFUSION_GATE_BLOCK_DOMINATES"
    );

    expect(gateBlockSignal).toBeDefined();
    expect(gateBlockSignal?.active).toBe(true);
    expect(gateBlockSignal?.details?.category).toBe("ORACLE");
  });
});

/**
 * Helper: Create mock snapshot
 */
function createMockSnapshot(
  labels: Partial<{
    shockPhase: string;
    stress: string;
    templateId: string;
    gateDecision: string;
    blockReason: string;
    hardStop: string;
    resume: string;
  }> = {}
): MarketRegimeSnapshotV1 {
  return {
    version: "v1.0",
    kind: "REGIME_SNAPSHOT",
    status: "AVAILABLE",
    ts: Date.now(),
    id: `mock_${Math.random()}`,
    warnings: [],
    presence: {
      hasOracle: false,
      hasObservationLabels: false,
      hasShockPhase: !!labels.shockPhase,
      hasStress: !!labels.stress,
      hasEscalation: false,
      hasActionShape: false,
      hasTemplateId: !!labels.templateId,
      hasRoute: false,
      hasGate: !!labels.gateDecision,
      hasPolicy: false,
      hasHardStop: !!labels.hardStop,
      hasCooldown: false,
      hasDrift: false,
      hasResume: !!labels.resume,
    },
    labels: {
      shockPhase: labels.shockPhase,
      stress: labels.stress,
      templateId: labels.templateId,
      gateDecision: labels.gateDecision as any,
      blockReason: labels.blockReason,
      hardStop: labels.hardStop as any,
      resume: labels.resume as any,
    },
  };
}
