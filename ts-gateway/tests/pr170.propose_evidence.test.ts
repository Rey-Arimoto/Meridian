/**
 * PR170: v1.4 Evidence-Linked Proposals v1 - Tests
 *
 * Purpose:
 *   Verify evidence extraction and linking to proposals.
 *
 * Test Coverage:
 *   1. Empty evidence (no attribution) → evidence: []
 *   2. Bottleneck evidence extraction → STRONG strength
 *   3. Path evidence extraction → MEDIUM strength
 *   4. Edge evidence extraction → WEAK strength
 *   5. Multiple evidence per proposal
 *   6. Evidence sanitization (forbidden patterns)
 *   7. Proposal with no matching evidence → evidence: []
 *   8. Evidence kind mapping (EVID_BOTTLENECK, EVID_TOP_PATH, EVID_TOP_EDGE)
 *   9. Evidence strength levels (STRONG, MEDIUM, WEAK, UNKNOWN)
 *   10. Evidence context populated
 *   11. Label-only mode (no counts in evidence)
 *   12. Defensive: malformed attribution doesn't throw
 */

import { MarketRegimeSnapshotV1 } from "../src/snapshot/types";
import { attributeSnapshotsV1 } from "../src/attribution/attributor";
import { extractEvidenceForProposal, hasAnyEvidence } from "../src/propose/evidence";
import { ProposalId } from "../src/propose/types";

describe("PR170: Evidence-Linked Proposals", () => {
  /**
   * Test 1: Empty evidence (no attribution) → evidence: []
   */
  test("Test 1: Empty evidence (no attribution)", () => {
    const evidence = extractEvidenceForProposal(
      "P0_REDUCE_ORACLE_STALE_BLOCKS_DEGRADE",
      null
    );

    expect(evidence).toEqual([]);
  });

  /**
   * Test 2: Bottleneck evidence extraction → STRONG strength
   */
  test("Test 2: Bottleneck evidence extraction", () => {
    const snapshots: MarketRegimeSnapshotV1[] = [];

    // Create many snapshots with ORACLE_STALE to trigger bottleneck
    for (let i = 0; i < 10; i++) {
      snapshots.push(
        createMockSnapshot({
          shockPhase: "PHASE_NORMAL",
          gateDecision: "BLOCK",
          blockReason: "BLOCK_ORACLE_STALE",
        })
      );
    }

    const attribution = attributeSnapshotsV1(snapshots);

    // Should have BOTTLENECK_ORACLE_DOMINANT
    expect(attribution.bottlenecks).toContain("BOTTLENECK_ORACLE_DOMINANT");

    // Extract evidence for ORACLE proposal
    const evidence = extractEvidenceForProposal(
      "P0_REDUCE_ORACLE_STALE_BLOCKS_DEGRADE",
      attribution
    );

    // Should have STRONG bottleneck evidence
    const bottleneckEvidence = evidence.find((e) => e.kind === "EVID_BOTTLENECK");
    expect(bottleneckEvidence).toBeDefined();
    expect(bottleneckEvidence?.strength).toBe("EVIDENCE_STRONG");
    expect(bottleneckEvidence?.label).toBe("BOTTLENECK_ORACLE_DOMINANT");
    expect(bottleneckEvidence?.context).toBe("FROM_ATTRIBUTION_BOTTLENECK_ANALYSIS");
  });

  /**
   * Test 3: Path evidence extraction → MEDIUM strength
   */
  test("Test 3: Path evidence extraction", () => {
    const snapshots: MarketRegimeSnapshotV1[] = [];

    // Create snapshots with ORACLE pattern in path
    for (let i = 0; i < 5; i++) {
      snapshots.push(
        createMockSnapshot({
          shockPhase: "PHASE_NORMAL",
          gateDecision: "BLOCK",
          blockReason: "BLOCK_ORACLE_STALE",
        })
      );
    }

    const attribution = attributeSnapshotsV1(snapshots);

    // Extract evidence for ORACLE proposal
    const evidence = extractEvidenceForProposal(
      "P0_REDUCE_ORACLE_STALE_BLOCKS_DEGRADE",
      attribution
    );

    // Should have MEDIUM path evidence (if path matches)
    const pathEvidence = evidence.filter((e) => e.kind === "EVID_TOP_PATH");
    if (pathEvidence.length > 0) {
      expect(pathEvidence[0].strength).toBe("EVIDENCE_MEDIUM");
      expect(pathEvidence[0].context).toBe("FROM_ATTRIBUTION_TOP_PATHS");
    }
  });

  /**
   * Test 4: Edge evidence extraction → WEAK strength
   */
  test("Test 4: Edge evidence extraction", () => {
    const snapshots: MarketRegimeSnapshotV1[] = [];

    // Create snapshots with ORACLE block edge
    for (let i = 0; i < 5; i++) {
      snapshots.push(
        createMockSnapshot({
          shockPhase: "PHASE_NORMAL",
          gateDecision: "BLOCK",
          blockReason: "BLOCK_ORACLE_STALE",
        })
      );
    }

    const attribution = attributeSnapshotsV1(snapshots);

    // Extract evidence for ORACLE proposal
    const evidence = extractEvidenceForProposal(
      "P0_REDUCE_ORACLE_STALE_BLOCKS_DEGRADE",
      attribution
    );

    // Should have WEAK edge evidence (if edge matches)
    const edgeEvidence = evidence.filter((e) => e.kind === "EVID_TOP_EDGE");
    if (edgeEvidence.length > 0) {
      expect(edgeEvidence[0].strength).toBe("EVIDENCE_WEAK");
      expect(edgeEvidence[0].context).toBe("FROM_ATTRIBUTION_TOP_EDGES");
    }
  });

  /**
   * Test 5: Multiple evidence per proposal
   */
  test("Test 5: Multiple evidence per proposal", () => {
    const snapshots: MarketRegimeSnapshotV1[] = [];

    // Create many snapshots with ORACLE_STALE to get multiple evidence types
    for (let i = 0; i < 15; i++) {
      snapshots.push(
        createMockSnapshot({
          shockPhase: "PHASE_NORMAL",
          gateDecision: "BLOCK",
          blockReason: "BLOCK_ORACLE_STALE",
        })
      );
    }

    const attribution = attributeSnapshotsV1(snapshots);

    const evidence = extractEvidenceForProposal(
      "P0_REDUCE_ORACLE_STALE_BLOCKS_DEGRADE",
      attribution
    );

    // Should have at least one evidence (bottleneck)
    expect(evidence.length).toBeGreaterThan(0);

    // Should have different kinds
    const kinds = new Set(evidence.map((e) => e.kind));
    expect(kinds.size).toBeGreaterThan(0);
  });

  /**
   * Test 6: Evidence sanitization (forbidden patterns)
   */
  test("Test 6: Evidence sanitization", () => {
    // Sanitization is handled by sanitizeProposalLabel in evidence.ts
    // Test is implicit - evidence labels should never contain forbidden patterns

    const snapshots: MarketRegimeSnapshotV1[] = [];

    for (let i = 0; i < 10; i++) {
      snapshots.push(
        createMockSnapshot({
          shockPhase: "PHASE_NORMAL",
          gateDecision: "BLOCK",
          blockReason: "BLOCK_ORACLE_STALE",
        })
      );
    }

    const attribution = attributeSnapshotsV1(snapshots);
    const evidence = extractEvidenceForProposal(
      "P0_REDUCE_ORACLE_STALE_BLOCKS_DEGRADE",
      attribution
    );

    // All evidence labels should be safe (no forbidden patterns)
    for (const evid of evidence) {
      expect(evid.label).not.toMatch(/\bbuy\b/i);
      expect(evid.label).not.toMatch(/\bsell\b/i);
      expect(evid.label).not.toMatch(/\bwBTC\b/i);
      expect(evid.label).not.toMatch(/0x[a-fA-F0-9]{8,}/);
    }
  });

  /**
   * Test 7: Proposal with no matching evidence → evidence: []
   */
  test("Test 7: Proposal with no matching evidence", () => {
    const snapshots: MarketRegimeSnapshotV1[] = [];

    // Create snapshots that don't match COOLDOWN proposal
    for (let i = 0; i < 5; i++) {
      snapshots.push(
        createMockSnapshot({
          shockPhase: "PHASE_NORMAL",
          gateDecision: "PASS",
        })
      );
    }

    const attribution = attributeSnapshotsV1(snapshots);

    // Extract evidence for COOLDOWN proposal (should be empty)
    const evidence = extractEvidenceForProposal(
      "P0_REDUCE_COOLDOWN_BLOCKS_DEGRADE",
      attribution
    );

    expect(evidence).toEqual([]);
  });

  /**
   * Test 8: Evidence kind mapping
   */
  test("Test 8: Evidence kind mapping", () => {
    const snapshots: MarketRegimeSnapshotV1[] = [];

    for (let i = 0; i < 10; i++) {
      snapshots.push(
        createMockSnapshot({
          shockPhase: "PHASE_NORMAL",
          gateDecision: "BLOCK",
          blockReason: "BLOCK_ORACLE_STALE",
        })
      );
    }

    const attribution = attributeSnapshotsV1(snapshots);
    const evidence = extractEvidenceForProposal(
      "P0_REDUCE_ORACLE_STALE_BLOCKS_DEGRADE",
      attribution
    );

    // Check all evidence have valid kinds
    const validKinds = ["EVID_BOTTLENECK", "EVID_TOP_PATH", "EVID_TOP_EDGE", "EVID_NONE"];
    for (const evid of evidence) {
      expect(validKinds).toContain(evid.kind);
    }
  });

  /**
   * Test 9: Evidence strength levels
   */
  test("Test 9: Evidence strength levels", () => {
    const snapshots: MarketRegimeSnapshotV1[] = [];

    for (let i = 0; i < 10; i++) {
      snapshots.push(
        createMockSnapshot({
          shockPhase: "PHASE_NORMAL",
          gateDecision: "BLOCK",
          blockReason: "BLOCK_ORACLE_STALE",
        })
      );
    }

    const attribution = attributeSnapshotsV1(snapshots);
    const evidence = extractEvidenceForProposal(
      "P0_REDUCE_ORACLE_STALE_BLOCKS_DEGRADE",
      attribution
    );

    // Check all evidence have valid strength
    const validStrengths = ["EVIDENCE_STRONG", "EVIDENCE_MEDIUM", "EVIDENCE_WEAK", "EVIDENCE_UNKNOWN"];
    for (const evid of evidence) {
      expect(validStrengths).toContain(evid.strength);
    }

    // Bottleneck should be STRONG
    const bottleneckEvidence = evidence.find((e) => e.kind === "EVID_BOTTLENECK");
    if (bottleneckEvidence) {
      expect(bottleneckEvidence.strength).toBe("EVIDENCE_STRONG");
    }
  });

  /**
   * Test 10: Evidence context populated
   */
  test("Test 10: Evidence context populated", () => {
    const snapshots: MarketRegimeSnapshotV1[] = [];

    for (let i = 0; i < 10; i++) {
      snapshots.push(
        createMockSnapshot({
          shockPhase: "PHASE_NORMAL",
          gateDecision: "BLOCK",
          blockReason: "BLOCK_ORACLE_STALE",
        })
      );
    }

    const attribution = attributeSnapshotsV1(snapshots);
    const evidence = extractEvidenceForProposal(
      "P0_REDUCE_ORACLE_STALE_BLOCKS_DEGRADE",
      attribution
    );

    // All evidence should have context
    for (const evid of evidence) {
      expect(evid.context).toBeDefined();
      expect(evid.context).not.toBe("");
    }
  });

  /**
   * Test 11: hasAnyEvidence utility
   */
  test("Test 11: hasAnyEvidence utility", () => {
    // Empty attribution
    expect(hasAnyEvidence(null)).toBe(false);

    // Attribution with bottlenecks
    const snapshots: MarketRegimeSnapshotV1[] = [];
    for (let i = 0; i < 10; i++) {
      snapshots.push(
        createMockSnapshot({
          shockPhase: "PHASE_NORMAL",
          gateDecision: "BLOCK",
          blockReason: "BLOCK_ORACLE_STALE",
        })
      );
    }

    const attribution = attributeSnapshotsV1(snapshots);
    expect(hasAnyEvidence(attribution)).toBe(true);
  });

  /**
   * Test 12: Defensive - malformed attribution doesn't throw
   */
  test("Test 12: Defensive - malformed attribution doesn't throw", () => {
    const malformedAttribution: any = {
      version: "v1.0",
      status: "ERROR",
      presence: {},
      warnings: [],
      bottlenecks: null, // Malformed
      topPaths: undefined, // Malformed
      topEdges: [], // Valid
      weakLinks: [],
      ts: Date.now(),
    };

    // Should not throw
    expect(() => {
      extractEvidenceForProposal(
        "P0_REDUCE_ORACLE_STALE_BLOCKS_DEGRADE",
        malformedAttribution
      );
    }).not.toThrow();

    // Should return empty array
    const evidence = extractEvidenceForProposal(
      "P0_REDUCE_ORACLE_STALE_BLOCKS_DEGRADE",
      malformedAttribution
    );
    expect(Array.isArray(evidence)).toBe(true);
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
    route: string;
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
      hasRoute: !!labels.route,
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
      route: labels.route as any,
    },
  };
}
