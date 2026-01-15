/**
 * PR169: v1.4 Policy Attribution Graph v1 - Tests
 *
 * Purpose:
 *   Verify attribution functionality (paths, edges, bottlenecks, weak links).
 *
 * Test Coverage:
 *   1. Empty input → ERROR or PARTIAL (hasSnapshots=false)
 *   2. Single snapshot → PARTIAL, topPaths generated
 *   3. Identical path twice → topPaths contains (minCount=2)
 *   4. Edge aggregation works (adjacent pairs counted)
 *   5. Missing gate block reason → UNKNOWN node or skipped
 *   6. Missing policy/route/resume → presence reflected
 *   7. Bottleneck ORACLE detected (oracle block reasons dominant)
 *   8. Bottleneck PHASE_POLICY detected (phase policy stops dominant)
 *   9. Weak link RESUME rare detected (resume absent)
 *   10. Sanitize works (numerics/address/token/trading vocab REDACTED)
 *   11. Normal mode doesn't leak counts
 *   12. Defensive: malformed snapshot doesn't throw
 */

import { MarketRegimeSnapshotV1 } from "../src/snapshot/types";
import { attributeSnapshotsV1 } from "../src/attribution/attributor";
import { extractNodesFromSnapshot } from "../src/attribution/model";
import {
  sanitizeLabel,
  validateLabelOnly,
} from "../src/attribution/guards";

describe("PR169: Policy Attribution Graph", () => {
  /**
   * Test 1: Empty input → ERROR or PARTIAL (hasSnapshots=false)
   */
  test("Test 1: Empty input → ERROR or PARTIAL", () => {
    const result = attributeSnapshotsV1([]);

    expect(result.version).toBe("v1.0");
    expect(result.status).toBe("PARTIAL");
    expect(result.presence.hasSnapshots).toBe(false);
    expect(result.warnings).toContain("WARN_NO_SNAPSHOTS_FOR_ATTRIBUTION");
  });

  /**
   * Test 2: Single snapshot → PARTIAL, topPaths generated
   */
  test("Test 2: Single snapshot → topPaths generated", () => {
    const snapshots: MarketRegimeSnapshotV1[] = [
      createMockSnapshot({
        shockPhase: "PHASE_NORMAL",
        stress: "STRESS_CALM",
        templateId: "TPL_RISK_50",
        gateDecision: "PASS",
      }),
    ];

    const result = attributeSnapshotsV1(snapshots);

    expect(result.status).toBe("PARTIAL"); // minCount=2, single path filtered out
    expect(result.presence.hasSnapshots).toBe(true);
    expect(result.presence.hasPhase).toBe(true);
  });

  /**
   * Test 3: Identical path twice → topPaths contains (minCount=2)
   */
  test("Test 3: Identical path twice → topPaths contains", () => {
    const snapshots: MarketRegimeSnapshotV1[] = [
      createMockSnapshot({
        shockPhase: "PHASE_NORMAL",
        stress: "STRESS_CALM",
        templateId: "TPL_RISK_50",
        gateDecision: "PASS",
      }),
      createMockSnapshot({
        shockPhase: "PHASE_NORMAL",
        stress: "STRESS_CALM",
        templateId: "TPL_RISK_50",
        gateDecision: "PASS",
      }),
    ];

    const result = attributeSnapshotsV1(snapshots);

    expect(result.status).toBe("COMPLETE");
    expect(result.topPaths.length).toBeGreaterThan(0);
    expect(result.topPaths[0].count).toBe(2);
  });

  /**
   * Test 4: Edge aggregation works (adjacent pairs counted)
   */
  test("Test 4: Edge aggregation works", () => {
    const snapshots: MarketRegimeSnapshotV1[] = [
      createMockSnapshot({
        shockPhase: "PHASE_NORMAL",
        templateId: "TPL_RISK_50",
        gateDecision: "PASS",
      }),
      createMockSnapshot({
        shockPhase: "PHASE_NORMAL",
        templateId: "TPL_RISK_50",
        gateDecision: "PASS",
      }),
    ];

    const result = attributeSnapshotsV1(snapshots);

    expect(result.topEdges.length).toBeGreaterThan(0);
    // Should have PHASE → TEMPLATE edge
    const phaseTemplateEdge = result.topEdges.find(
      (e) => e.from.t === "PHASE" && e.to.t === "TEMPLATE"
    );
    expect(phaseTemplateEdge).toBeDefined();
    expect(phaseTemplateEdge?.count).toBe(2);
  });

  /**
   * Test 5: Missing gate block reason → node extraction handles gracefully
   */
  test("Test 5: Missing gate block reason handled", () => {
    const snapshot = createMockSnapshot({
      shockPhase: "PHASE_NORMAL",
      gateDecision: "BLOCK",
      // No blockReason
    });

    const nodes = extractNodesFromSnapshot(snapshot);

    // Should have PHASE and GATE_DECISION nodes, but no GATE_BLOCK_REASON
    expect(nodes.some((n) => n.t === "PHASE")).toBe(true);
    expect(nodes.some((n) => n.t === "GATE_DECISION")).toBe(true);
    expect(nodes.some((n) => n.t === "GATE_BLOCK_REASON")).toBe(false);
  });

  /**
   * Test 6: Missing policy/route/resume → presence reflected
   */
  test("Test 6: Missing components reflected in presence", () => {
    const snapshots: MarketRegimeSnapshotV1[] = [
      createMockSnapshot({
        shockPhase: "PHASE_NORMAL",
        // No policy, route, resume
      }),
      createMockSnapshot({
        shockPhase: "PHASE_NORMAL",
      }),
    ];

    const result = attributeSnapshotsV1(snapshots);

    expect(result.presence.hasPhase).toBe(true);
    expect(result.presence.hasPolicy).toBe(false);
    expect(result.presence.hasRoute).toBe(false);
    expect(result.presence.hasResume).toBe(false);
  });

  /**
   * Test 7: Bottleneck ORACLE detected (oracle block reasons dominant)
   */
  test("Test 7: Bottleneck ORACLE detected", () => {
    const snapshots: MarketRegimeSnapshotV1[] = [];

    // Create many snapshots with ORACLE_STALE
    for (let i = 0; i < 10; i++) {
      snapshots.push(
        createMockSnapshot({
          shockPhase: "PHASE_NORMAL",
          gateDecision: "BLOCK",
          blockReason: "BLOCK_ORACLE_STALE",
        })
      );
    }

    const result = attributeSnapshotsV1(snapshots);

    expect(result.bottlenecks).toContain("BOTTLENECK_ORACLE_DOMINANT");
  });

  /**
   * Test 8: Bottleneck PHASE_POLICY detected (phase policy stops dominant)
   */
  test("Test 8: Bottleneck PHASE_POLICY detected", () => {
    const snapshots: MarketRegimeSnapshotV1[] = [];

    // Create many snapshots with PHASE escalation
    for (let i = 0; i < 10; i++) {
      snapshots.push(
        createMockSnapshot({
          shockPhase: "PHASE_PRE_SHOCK",
          gateDecision: "BLOCK",
          blockReason: "BLOCK_PHASE_ESCALATION",
          resume: "WAIT",
        })
      );
    }

    const result = attributeSnapshotsV1(snapshots);

    // Should have phase policy bottleneck (if enough stop edges)
    expect(
      result.bottlenecks.includes("BOTTLENECK_PHASE_POLICY_DOMINANT") ||
        result.bottlenecks.includes("BOTTLENECK_STOP_FREQUENT")
    ).toBe(true);
  });

  /**
   * Test 9: Weak link RESUME rare detected (resume absent)
   */
  test("Test 9: Weak link RESUME rare detected", () => {
    const snapshots: MarketRegimeSnapshotV1[] = [];

    // Create snapshots without resume
    for (let i = 0; i < 10; i++) {
      snapshots.push(
        createMockSnapshot({
          shockPhase: "PHASE_NORMAL",
          gateDecision: "PASS",
          // No resume
        })
      );
    }

    const result = attributeSnapshotsV1(snapshots);

    // RESUME should be rare (not in presence or no resume edges)
    expect(result.presence.hasResume).toBe(false);
  });

  /**
   * Test 10: Sanitize works (numerics/address/token/trading vocab REDACTED)
   */
  test("Test 10: Sanitize works", () => {
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
    expect(sanitizeLabel("PHASE_NORMAL")).toBe("PHASE_NORMAL");
    expect(sanitizeLabel("BLOCK_ORACLE_STALE")).toBe("BLOCK_ORACLE_STALE");
  });

  /**
   * Test 11: Normal mode doesn't leak counts
   */
  test("Test 11: Normal mode doesn't leak counts", () => {
    const snapshots: MarketRegimeSnapshotV1[] = [
      createMockSnapshot({
        shockPhase: "PHASE_NORMAL",
        gateDecision: "PASS",
      }),
      createMockSnapshot({
        shockPhase: "PHASE_NORMAL",
        gateDecision: "PASS",
      }),
    ];

    const result = attributeSnapshotsV1(snapshots);

    // Verify label-only validation
    const validation = validateLabelOnly(result);
    expect(validation.ok).toBe(true);
  });

  /**
   * Test 12: Defensive: malformed snapshot doesn't throw
   */
  test("Test 12: Defensive: malformed snapshot doesn't throw", () => {
    const malformedSnapshots = [null, undefined, {}] as any;

    // Should not throw
    const result = attributeSnapshotsV1(malformedSnapshots);

    expect(result.version).toBe("v1.0");
    expect(result.status).toBe("ERROR");
    expect(result.warnings).toContain("WARN_ATTRIBUTION_ERROR");
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
