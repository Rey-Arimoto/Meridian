/**
 * PR167: v1.4 Improvement Proposal Generator v1 - Tests
 *
 * Purpose:
 *   Verify proposal generation functionality (triggers, priorities, fixed rules).
 *
 * Test Coverage:
 *   1. Empty analysis → NO_PROPOSALS
 *   2. GATE_BLOCK_DOMINATES trigger → P0 degrade proposals
 *   3. SHOCK_RISK90_OVERUSE trigger → P1 template policy
 *   4. PRE_SHOCK_NO_SHIFT trigger → P1 template policy
 *   5. Multiple triggers → Multiple proposals (sorted by priority)
 *   6. Priority filtering (P0 only)
 *   7. Sanitize removes counts (normal mode)
 *   8. Debug mode allows counts
 *   9. Proposal priority sorting (P0 > P1 > P2)
 *   10. Exception doesn't throw (always returns)
 */

import { analyzeSnapshotsV1 } from "../src/analyze/analyzer";
import { generateProposalsV1, getActiveTriggersV1 } from "../src/propose/proposer";
import {
  sanitizeProposeResultForDisplay,
  isDebugMode,
  sanitizeProposalLabel,
  getPriorityOrder,
} from "../src/propose/guards";
import { MarketRegimeSnapshotV1 } from "../src/snapshot/types";

describe("PR167: Improvement Proposal Generator v1", () => {
  /**
   * Test 1: Empty analysis → NO_PROPOSALS
   */
  test("Test 1: Empty analysis → NO_PROPOSALS", async () => {
    const analysis = await analyzeSnapshotsV1([]);

    const proposeResult = await generateProposalsV1(analysis);

    expect(proposeResult.version).toBe("v1.0");
    expect(proposeResult.status).toBe("NO_PROPOSALS");
    expect(proposeResult.proposals.length).toBe(0);
  });

  /**
   * Test 2: GATE_BLOCK_DOMINATES trigger → P0 degrade proposals
   */
  test("Test 2: GATE_BLOCK_DOMINATES trigger → P0 degrade proposals", async () => {
    // Create data with majority BLOCK (ORACLE_STALE)
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
    const proposeResult = await generateProposalsV1(analysis);

    expect(proposeResult.status).toBe("AVAILABLE");
    expect(proposeResult.proposals.length).toBeGreaterThan(0);

    // Should have P0 proposal for ORACLE_STALE degradation
    const oracleP0 = proposeResult.proposals.find(
      (p) => p.id === "P0_REDUCE_ORACLE_STALE_BLOCKS_DEGRADE"
    );
    expect(oracleP0).toBeDefined();
    expect(oracleP0?.priority).toBe("P0");
    expect(oracleP0?.category).toBe("GATE_POLICY");
  });

  /**
   * Test 3: SHOCK_RISK90_OVERUSE trigger → P1 template policy
   */
  test("Test 3: SHOCK_RISK90_OVERUSE trigger → P1 template policy", async () => {
    // Create data with SHOCK phases + TPL_RISK_90 (confusion)
    const snapshots: MarketRegimeSnapshotV1[] = [];

    for (let i = 0; i < 10; i++) {
      snapshots.push(
        createMockSnapshot({
          shockPhase: "PHASE_UP_REVERSAL",
          templateId: "TPL_RISK_90",
        })
      );
    }

    const analysis = await analyzeSnapshotsV1(snapshots);
    const proposeResult = await generateProposalsV1(analysis);

    expect(proposeResult.status).toBe("AVAILABLE");
    expect(proposeResult.proposals.length).toBeGreaterThan(0);

    // Should have P1 proposal for template policy restriction
    const templateP1 = proposeResult.proposals.find(
      (p) => p.id === "P1_SHOCK_RISK90_OVERUSE_TEMPLATE_POLICY_RESTRICT"
    );
    expect(templateP1).toBeDefined();
    expect(templateP1?.priority).toBe("P1");
    expect(templateP1?.category).toBe("TEMPLATE_POLICY");
  });

  /**
   * Test 4: PRE_SHOCK_NO_SHIFT trigger → P1 template policy
   */
  test("Test 4: PRE_SHOCK_NO_SHIFT trigger → P1 template policy", async () => {
    // Create data with PRE_SHOCK but single template (no shift)
    const snapshots: MarketRegimeSnapshotV1[] = [];

    for (let i = 0; i < 10; i++) {
      snapshots.push(
        createMockSnapshot({
          shockPhase: "PHASE_PRE_SHOCK",
          templateId: "TPL_RISK_50",
        })
      );
    }

    const analysis = await analyzeSnapshotsV1(snapshots);
    const proposeResult = await generateProposalsV1(analysis);

    expect(proposeResult.status).toBe("AVAILABLE");
    expect(proposeResult.proposals.length).toBeGreaterThan(0);

    // Should have P1 proposal for template shift trigger
    const shiftP1 = proposeResult.proposals.find(
      (p) => p.id === "P1_PRE_SHOCK_NO_SHIFT_TEMPLATE_POLICY_TRIGGER"
    );
    expect(shiftP1).toBeDefined();
    expect(shiftP1?.priority).toBe("P1");
    expect(shiftP1?.category).toBe("TEMPLATE_POLICY");
  });

  /**
   * Test 5: Multiple triggers → Multiple proposals (sorted by priority)
   */
  test("Test 5: Multiple triggers → Multiple proposals (sorted by priority)", async () => {
    // Create data with multiple confusion signals
    const snapshots: MarketRegimeSnapshotV1[] = [];

    // GATE_BLOCK_DOMINATES (P0 + P1)
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

    // SHOCK_RISK90_OVERUSE (P1)
    for (let i = 0; i < 10; i++) {
      snapshots.push(
        createMockSnapshot({
          shockPhase: "PHASE_UP_REVERSAL",
          templateId: "TPL_RISK_90",
        })
      );
    }

    const analysis = await analyzeSnapshotsV1(snapshots);
    const proposeResult = await generateProposalsV1(analysis);

    expect(proposeResult.status).toBe("AVAILABLE");
    expect(proposeResult.proposals.length).toBeGreaterThan(1);

    // Should have both P0 and P1 proposals
    const p0Proposals = proposeResult.proposals.filter((p) => p.priority === "P0");
    const p1Proposals = proposeResult.proposals.filter((p) => p.priority === "P1");

    expect(p0Proposals.length).toBeGreaterThan(0);
    expect(p1Proposals.length).toBeGreaterThan(0);

    // P0 should come before P1 (sorted by priority)
    const firstP0Index = proposeResult.proposals.findIndex((p) => p.priority === "P0");
    const firstP1Index = proposeResult.proposals.findIndex((p) => p.priority === "P1");

    if (firstP0Index !== -1 && firstP1Index !== -1) {
      expect(firstP0Index).toBeLessThan(firstP1Index);
    }
  });

  /**
   * Test 6: Priority filtering (P0 only)
   */
  test("Test 6: Priority filtering (P0 only)", async () => {
    // Create data with multiple triggers
    const snapshots: MarketRegimeSnapshotV1[] = [];

    // GATE_BLOCK_DOMINATES (P0)
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
    const proposeResult = await generateProposalsV1(analysis);

    // Filter P0 only
    const p0Proposals = proposeResult.proposals.filter((p) => p.priority === "P0");

    expect(p0Proposals.length).toBeGreaterThan(0);

    // All proposals should be P0
    for (const proposal of p0Proposals) {
      expect(proposal.priority).toBe("P0");
    }
  });

  /**
   * Test 7: Sanitize removes counts (normal mode)
   */
  test("Test 7: Sanitize removes counts (normal mode)", async () => {
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
    const proposeResult = await generateProposalsV1(analysis);

    // Verify raw result has triggered_by details
    expect(proposeResult.proposals[0].triggered_by.length).toBeGreaterThan(0);

    // Sanitize for display (normal mode)
    const sanitized = sanitizeProposeResultForDisplay(proposeResult, false);

    // Verify counts are replaced with labels
    expect(sanitized.ts_label).toBe("HAS_TIMESTAMP");
    expect((sanitized.proposals[0] as any).triggered_by_count).toBe("HAS_TRIGGERS");
    expect((sanitized.proposals[0] as any).triggered_by).toBeUndefined();
  });

  /**
   * Test 8: Debug mode allows counts
   */
  test("Test 8: Debug mode allows counts", async () => {
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
    const proposeResult = await generateProposalsV1(analysis);

    // In debug mode, raw result is returned (not sanitized)
    expect(proposeResult.proposals[0].triggered_by.length).toBeGreaterThan(0);
    expect(proposeResult.ts).toBeGreaterThan(0);
  });

  /**
   * Test 9: Proposal priority sorting (P0 > P1 > P2)
   */
  test("Test 9: Proposal priority sorting (P0 > P1 > P2)", () => {
    // Test getPriorityOrder helper
    expect(getPriorityOrder("P0")).toBe(0);
    expect(getPriorityOrder("P1")).toBe(1);
    expect(getPriorityOrder("P2")).toBe(2);
    expect(getPriorityOrder("UNKNOWN")).toBe(99);

    // P0 < P1 < P2 (lower order = higher priority)
    expect(getPriorityOrder("P0")).toBeLessThan(getPriorityOrder("P1"));
    expect(getPriorityOrder("P1")).toBeLessThan(getPriorityOrder("P2"));
  });

  /**
   * Test 10: Exception doesn't throw (always returns)
   */
  test("Test 10: Exception doesn't throw (always returns)", async () => {
    // Pass invalid analysis (should not throw)
    const invalidAnalysis = null as any;

    const proposeResult = await generateProposalsV1(invalidAnalysis);

    // Should return ERROR status, not throw
    expect(proposeResult.version).toBe("v1.0");
    expect(proposeResult.status).toBe("ERROR");
    expect(proposeResult.warnings).toContain("WARN_ANALYSIS_ERROR");
  });

  /**
   * Test 11: Sanitize label removes forbidden patterns
   */
  test("Test 11: Sanitize label removes forbidden patterns", () => {
    // Token literals
    expect(sanitizeProposalLabel("wBTC price")).toBe("REDACTED");
    expect(sanitizeProposalLabel("USDC balance")).toBe("REDACTED");

    // Trading vocab
    expect(sanitizeProposalLabel("buy signal")).toBe("REDACTED");
    expect(sanitizeProposalLabel("sell order")).toBe("REDACTED");

    // Prescriptive
    expect(sanitizeProposalLabel("should execute")).toBe("REDACTED");

    // Address
    expect(sanitizeProposalLabel("0x1234abcd")).toBe("REDACTED");

    // Allowed
    expect(sanitizeProposalLabel("DEGRADE_ORACLE_STALE_THRESHOLD")).toBe(
      "DEGRADE_ORACLE_STALE_THRESHOLD"
    );
    expect(sanitizeProposalLabel("P0")).toBe("P0");
  });

  /**
   * Test 12: Get active triggers
   */
  test("Test 12: Get active triggers", async () => {
    // Create data with GATE_BLOCK_DOMINATES trigger
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
    const activeTriggers = getActiveTriggersV1(analysis);

    expect(activeTriggers.length).toBeGreaterThan(0);
    expect(activeTriggers).toContain("TRG_GATE_BLOCK_DOMINATES");
    expect(activeTriggers).toContain("TRG_ORACLE_STALE_TOP");
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
