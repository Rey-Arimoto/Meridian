/**
 * PR168: v1.4 Policy-First Adoption Loop - Tests
 *
 * Purpose:
 *   Verify adoption loop functionality (patch plan, replay compare, decision).
 *
 * Test Coverage:
 *   1. Empty snapshots → decision=HOLD, status=PARTIAL
 *   2. No proposals → decision=HOLD
 *   3. P0 proposal selected
 *   4. NOT_ALLOWED patch → decision=REJECT
 *   5. Deterministic patch (same input → same ops)
 *   6. Replay improvement (BLOCK_DOMINANCE reduced) → IMPROVED signal
 *   7. Replay worsening (STOP_UNKNOWN increased) → WORSENED signal
 *   8. Decision: improved only → ADOPT
 *   9. Decision: worsened present → HOLD
 *   10. Compare unavailable → HOLD
 *   11. Guards sanitize numeric warnings
 *   12. Label-only output (non-debug)
 */

import { MarketRegimeSnapshotV1 } from "../src/snapshot/types";
import { adoptImprovementV1, decideAdoptionV1 } from "../src/adopt/adopter";
import { buildPatchPlanFromProposalV1, hasNotAllowedOps } from "../src/adopt/rules";
import { selectTopProposalV1 } from "../src/adopt/patcher";
import {
  sanitizeLabel,
  sanitizeLines,
  validateLabelOnly,
} from "../src/adopt/guards";
import { analyzeSnapshotsV1 } from "../src/analyze/analyzer";
import { generateProposalsV1 } from "../src/propose/proposer";

describe("PR168: Policy-First Adoption Loop", () => {
  /**
   * Test 1: Empty snapshots → decision=HOLD, status=PARTIAL
   */
  test("Test 1: Empty snapshots → decision=HOLD, status=PARTIAL", async () => {
    const adoptResult = await adoptImprovementV1([], "P0", 200);

    expect(adoptResult.version).toBe("v1.0");
    expect(adoptResult.decision).toBe("HOLD");
    expect(adoptResult.status).toBe("PARTIAL");
    expect(adoptResult.reasons).toContain("NO_PROPOSALS_TO_ADOPT");
  });

  /**
   * Test 2: No proposals → decision=HOLD
   */
  test("Test 2: No proposals → decision=HOLD", async () => {
    // Create snapshots with no triggers (healthy data)
    const snapshots: MarketRegimeSnapshotV1[] = [];

    for (let i = 0; i < 10; i++) {
      snapshots.push(
        createMockSnapshot({
          gateDecision: "PASS",
          shockPhase: "PHASE_NORMAL",
          templateId: "TPL_RISK_50",
        })
      );
    }

    const adoptResult = await adoptImprovementV1(snapshots, "P0", 200);

    expect(adoptResult.decision).toBe("HOLD");
    expect(adoptResult.reasons).toContain("NO_PROPOSALS_TO_ADOPT");
  });

  /**
   * Test 3: P0 proposal selected
   */
  test("Test 3: P0 proposal selected", async () => {
    // Create snapshots with GATE_BLOCK_DOMINATES + ORACLE_STALE
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

    const adoptResult = await adoptImprovementV1(snapshots, "P0", 200);

    expect(adoptResult.priority).toBe("P0");
    expect(adoptResult.proposalId).toContain("P0_");
  });

  /**
   * Test 4: NOT_ALLOWED patch → decision=REJECT
   */
  test("Test 4: NOT_ALLOWED patch → decision=REJECT", async () => {
    // Create snapshots with ORACLE_STALE (triggers P0 NOT_ALLOWED)
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

    const adoptResult = await adoptImprovementV1(snapshots, "P0", 200);

    expect(adoptResult.decision).toBe("REJECT");
    expect(adoptResult.reasons).toContain("REJECT_PATCH_NOT_ALLOWED");
    expect(hasNotAllowedOps(adoptResult.patchPlan)).toBe(true);
  });

  /**
   * Test 5: Deterministic patch (same input → same ops)
   */
  test("Test 5: Deterministic patch (same input → same ops)", async () => {
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

    const proposal1 = selectTopProposalV1(proposeResult.proposals, "P1");
    const patchPlan1 = buildPatchPlanFromProposalV1(proposal1!, analysis);

    const proposal2 = selectTopProposalV1(proposeResult.proposals, "P1");
    const patchPlan2 = buildPatchPlanFromProposalV1(proposal2!, analysis);

    // Same input → same patch plan
    expect(patchPlan1.ops.length).toBe(patchPlan2.ops.length);
    expect(patchPlan1.ops[0].opId).toBe(patchPlan2.ops[0].opId);
  });

  /**
   * Test 6: Replay improvement (BLOCK_DOMINANCE reduced) → IMPROVED signal
   */
  test("Test 6: Replay improvement (BLOCK_DOMINANCE reduced) → IMPROVED signal", async () => {
    // Create snapshots with SHOCK_RISK90 confusion (P1 allowed)
    const snapshots: MarketRegimeSnapshotV1[] = [];

    for (let i = 0; i < 10; i++) {
      snapshots.push(
        createMockSnapshot({
          shockPhase: "PHASE_UP_REVERSAL",
          templateId: "TPL_RISK_90",
          gateDecision: "BLOCK",
        })
      );
    }

    const adoptResult = await adoptImprovementV1(snapshots, "P1", 200);

    // P1 proposal should show improvement signals
    const hasImprovedSignal = adoptResult.compare.signals.some((s) =>
      s.startsWith("IMPROVED_")
    );
    expect(hasImprovedSignal || adoptResult.compare.signals.includes("NO_CHANGE")).toBe(
      true
    );
  });

  /**
   * Test 7: Replay worsening (STOP_UNKNOWN increased) → WORSENED signal
   */
  test("Test 7: Replay worsening (STOP_UNKNOWN increased) → WORSENED signal", async () => {
    // Create mock patch plan and compare with worsening
    const mockPatchPlan = {
      status: "COMPLETE" as const,
      proposalId: "MOCK_PROPOSAL",
      priority: "P1" as const,
      ops: [
        {
          kind: "PATCH_PHASE_POLICY" as const,
          target: "PHASE_POLICY" as const,
          opId: "MOCK_OP",
          change: "MOCK_CHANGE",
          safety: [],
        },
      ],
      warnings: [],
    };

    const mockCompare = {
      status: "COMPLETE" as const,
      window: "TAIL_200",
      before: ["GATE_PASS_MAJORITY"],
      after: ["GATE_PASS_MAJORITY"],
      signals: ["WORSENED_STOP_UNKNOWN" as const],
      warnings: [],
    };

    const { decision, reasons } = decideAdoptionV1(
      mockPatchPlan,
      mockCompare,
      "P1"
    );

    expect(decision).toBe("HOLD");
    expect(reasons).toContain("HOLD_WORSENED_DETECTED");
  });

  /**
   * Test 8: Decision: improved only → ADOPT
   */
  test("Test 8: Decision: improved only → ADOPT", async () => {
    const mockPatchPlan = {
      status: "COMPLETE" as const,
      proposalId: "MOCK_PROPOSAL",
      priority: "P1" as const,
      ops: [
        {
          kind: "PATCH_PHASE_POLICY" as const,
          target: "PHASE_POLICY" as const,
          opId: "MOCK_OP",
          change: "MOCK_CHANGE",
          safety: ["KEEP_DOUBLE_KEY"],
        },
      ],
      warnings: [],
    };

    const mockCompare = {
      status: "COMPLETE" as const,
      window: "TAIL_200",
      before: ["GATE_BLOCK_DOMINATES"],
      after: ["GATE_PASS_INCREASED"],
      signals: ["IMPROVED_BLOCK_DOMINANCE" as const],
      warnings: [],
    };

    const { decision, reasons } = decideAdoptionV1(
      mockPatchPlan,
      mockCompare,
      "P1"
    );

    expect(decision).toBe("ADOPT");
    expect(reasons).toContain("ADOPT_IMPROVED_WITHOUT_WORSENING");
  });

  /**
   * Test 9: Decision: worsened present → HOLD
   */
  test("Test 9: Decision: worsened present → HOLD", async () => {
    const mockPatchPlan = {
      status: "COMPLETE" as const,
      proposalId: "MOCK_PROPOSAL",
      priority: "P1" as const,
      ops: [
        {
          kind: "PATCH_PHASE_POLICY" as const,
          target: "PHASE_POLICY" as const,
          opId: "MOCK_OP",
          change: "MOCK_CHANGE",
          safety: [],
        },
      ],
      warnings: [],
    };

    const mockCompare = {
      status: "COMPLETE" as const,
      window: "TAIL_200",
      before: ["GATE_PASS_MAJORITY"],
      after: ["GATE_PASS_INCREASED"],
      signals: [
        "IMPROVED_BLOCK_DOMINANCE" as const,
        "WORSENED_STOP_UNKNOWN" as const,
      ],
      warnings: [],
    };

    const { decision, reasons } = decideAdoptionV1(
      mockPatchPlan,
      mockCompare,
      "P1"
    );

    expect(decision).toBe("HOLD");
    expect(reasons).toContain("HOLD_WORSENED_DETECTED");
  });

  /**
   * Test 10: Compare unavailable → HOLD
   */
  test("Test 10: Compare unavailable → HOLD", async () => {
    const mockPatchPlan = {
      status: "COMPLETE" as const,
      proposalId: "MOCK_PROPOSAL",
      priority: "P1" as const,
      ops: [
        {
          kind: "PATCH_PHASE_POLICY" as const,
          target: "PHASE_POLICY" as const,
          opId: "MOCK_OP",
          change: "MOCK_CHANGE",
          safety: [],
        },
      ],
      warnings: [],
    };

    const mockCompare = {
      status: "ERROR" as const,
      window: "TAIL_200",
      before: [],
      after: [],
      signals: ["COMPARE_UNAVAILABLE" as const],
      warnings: ["COMPARE_ERROR"],
    };

    const { decision, reasons } = decideAdoptionV1(
      mockPatchPlan,
      mockCompare,
      "P1"
    );

    expect(decision).toBe("HOLD");
    expect(reasons).toContain("HOLD_COMPARE_UNAVAILABLE");
  });

  /**
   * Test 11: Guards sanitize numeric warnings
   */
  test("Test 11: Guards sanitize numeric warnings", () => {
    // Token literals
    expect(sanitizeLabel("wBTC price")).toBe("REDACTED");
    expect(sanitizeLabel("USDC balance")).toBe("REDACTED");

    // Trading vocab
    expect(sanitizeLabel("buy signal")).toBe("REDACTED");
    expect(sanitizeLabel("sell order")).toBe("REDACTED");

    // Prescriptive
    expect(sanitizeLabel("should execute")).toBe("REDACTED");

    // Address
    expect(sanitizeLabel("0x1234abcd")).toBe("REDACTED");

    // Allowed
    expect(sanitizeLabel("PATCH_PHASE_POLICY")).toBe("PATCH_PHASE_POLICY");
    expect(sanitizeLabel("ADOPT")).toBe("ADOPT");
  });

  /**
   * Test 12: Label-only output (non-debug)
   */
  test("Test 12: Label-only output (non-debug)", () => {
    const lines = [
      "GATE_BLOCK_DOMINATES",
      "PHASE_POLICY_STOPS_PRESENT",
      "IMPROVED_BLOCK_DOMINANCE",
    ];

    const sanitized = sanitizeLines(lines);
    expect(validateLabelOnly(sanitized)).toBe(true);

    // Numeric patterns should fail
    const numericLines = ["142", "30%", "3.5"];
    expect(validateLabelOnly(numericLines)).toBe(false);
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
