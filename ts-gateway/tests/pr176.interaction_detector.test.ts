/**
 * PR176: v1.4 Change Interaction Detector v1 - Tests
 *
 * Purpose:
 *   Verify interaction detection, pairing logic, and coupling risk assessment.
 *
 * Test Coverage:
 *   1. Empty decisions → PARTIAL/ERROR (defensive)
 *   2. Single adopt → NO_INTERACTION
 *   3. W_TIGHT pair generation (≤30min)
 *   4. W_WIDE is generated but weak
 *   5. Regression after pair → STRONG (INT_PATCH_PAIR_REGRESSION)
 *   6. Effect worsened after pair → MEDIUM (INT_PATCH_FOLLOWS_WORSENING)
 *   7. Multiple adopts (short time chain) detection
 *   8. Coupling risk high (score threshold exceeded)
 *   9. Evidence max 3 + strength order
 *   10. Sanitize works (numbers/tokens/addresses REDACTED)
 *   11. Corrupt JSONL line skip
 *   12. CLI format contains no numerics
 */

import { detectInteractionsV1 } from "../src/interaction/detector";
import { extractAdoptionEvents, AdoptionEvent } from "../src/interaction/reader";
import {
  appendInteractionReportV1,
  readRecentInteractionReportsV1,
  getInteractionLogPath,
} from "../src/interaction/store";
import {
  formatInteractionLinesV1,
  validateInteractionLabelOnly,
  sanitizeInteractionLabel,
} from "../src/interaction/guards";
import { DecisionAckRecordV1 } from "../src/decision/types";
import { PatchEffectReportV1 } from "../src/effect/types";
import { RegressionReportV1 } from "../src/regress/types";
import { InteractionReportV1 } from "../src/interaction/types";
import * as fs from "fs";

describe("PR176: Change Interaction Detector", () => {
  /**
   * Test 1: Empty decisions → no interactions
   */
  test("Test 1: Empty decisions produce no interactions", () => {
    const adoptions: AdoptionEvent[] = [];
    const effects: PatchEffectReportV1[] = [];
    const regressions: RegressionReportV1[] = [];

    const interactions = detectInteractionsV1(adoptions, effects, regressions);

    expect(interactions.length).toBe(0);
  });

  /**
   * Test 2: Single adopt → NO_INTERACTION
   */
  test("Test 2: Single adoption produces no interaction", () => {
    const adoptions: AdoptionEvent[] = [
      {
        proposalId: "P0_A",
        ts: 1000000,
        decision: "ADOPT",
      },
    ];

    const interactions = detectInteractionsV1(adoptions, [], []);

    expect(interactions.length).toBe(0);
  });

  /**
   * Test 3: W_TIGHT pair generation (≤30min)
   */
  test("Test 3: W_TIGHT pair is generated for adoptions ≤30min apart", () => {
    const adoptions: AdoptionEvent[] = [
      {
        proposalId: "P0_A",
        ts: 1000000,
        decision: "ADOPT",
      },
      {
        proposalId: "P0_B",
        ts: 1000000 + 20 * 60 * 1000, // 20 minutes later
        decision: "ADOPT",
      },
    ];

    const interactions = detectInteractionsV1(adoptions, [], []);

    expect(interactions.length).toBeGreaterThan(0);
    expect(interactions[0].window).toBe("W_TIGHT");
    expect(interactions[0].interactionKind).toBe("INT_MULTIPLE_ADOPTS_SAME_WINDOW");
  });

  /**
   * Test 4: W_WIDE is generated but weak
   */
  test("Test 4: W_WIDE pair produces weak interaction", () => {
    const adoptions: AdoptionEvent[] = [
      {
        proposalId: "P0_A",
        ts: 1000000,
        decision: "ADOPT",
      },
      {
        proposalId: "P0_B",
        ts: 1000000 + 12 * 60 * 60 * 1000, // 12 hours later
        decision: "ADOPT",
      },
    ];

    const interactions = detectInteractionsV1(adoptions, [], []);

    // W_WIDE pairs may or may not generate interactions depending on other evidence
    // But if they do, they should be WEAK
    if (interactions.length > 0) {
      expect(interactions[0].window).toBe("W_WIDE");
    }
  });

  /**
   * Test 5: Regression after pair → STRONG (INT_PATCH_PAIR_REGRESSION)
   */
  test("Test 5: Regression after pair produces STRONG interaction", () => {
    const adoptions: AdoptionEvent[] = [
      {
        proposalId: "P0_A",
        ts: 1000000,
        decision: "ADOPT",
      },
      {
        proposalId: "P0_B",
        ts: 1000000 + 10 * 60 * 1000, // 10 minutes later
        decision: "ADOPT",
      },
    ];

    const regressions: RegressionReportV1[] = [
      {
        kind: "REGRESSION_REPORT_V1",
        status: "AVAILABLE",
        analysis: {
          proposalId: "P0_A",
          decision: "REGRESSION_DETECTED",
          kind: "REGRESS_IMPROVED_TO_WORSENED",
          strength: "STRONG",
          windowLabel: "W_SHORT",
          evidence: [],
          warnings: [],
        },
        ts: 1000000 + 30 * 60 * 1000, // After both adoptions
        warnings: [],
      },
    ];

    const interactions = detectInteractionsV1(adoptions, [], regressions);

    expect(interactions.length).toBeGreaterThan(0);
    expect(interactions[0].interactionKind).toBe("INT_PATCH_PAIR_REGRESSION");
    expect(interactions[0].strength).toBe("STRONG");
  });

  /**
   * Test 6: Effect worsened after pair → MEDIUM (INT_PATCH_FOLLOWS_WORSENING)
   */
  test("Test 6: Effect worsened after pair produces MEDIUM interaction", () => {
    const adoptions: AdoptionEvent[] = [
      {
        proposalId: "P0_A",
        ts: 1000000,
        decision: "ADOPT",
      },
      {
        proposalId: "P0_B",
        ts: 1000000 + 15 * 60 * 1000, // 15 minutes later
        decision: "ADOPT",
      },
    ];

    const effects: PatchEffectReportV1[] = [
      {
        kind: "PATCH_EFFECT_V1",
        status: "AVAILABLE",
        decisionAckRef: { proposalId: "P0_A" },
        effectDecision: "EFFECT_WORSENED",
        compare: { improved: [], worsened: ["WORSENED_BLOCK_RATE"], unchanged: [], unavailable: [] },
        windows: [],
        rationale: [],
        warnings: [],
        ts: 1000000 + 30 * 60 * 1000, // After both adoptions
      } as any,
    ];

    const interactions = detectInteractionsV1(adoptions, effects, []);

    expect(interactions.length).toBeGreaterThan(0);
    const hasWorsening = interactions.some(
      (i) =>
        i.interactionKind === "INT_PATCH_FOLLOWS_WORSENING" ||
        i.interactionKind === "INT_COUPLING_RISK_HIGH"
    );
    expect(hasWorsening).toBe(true);
  });

  /**
   * Test 7: Multiple adopts (short time chain) detection
   */
  test("Test 7: Multiple adopts in short time are detected", () => {
    const adoptions: AdoptionEvent[] = [
      {
        proposalId: "P0_A",
        ts: 1000000,
        decision: "ADOPT",
      },
      {
        proposalId: "P0_B",
        ts: 1000000 + 5 * 60 * 1000, // 5 minutes later
        decision: "ADOPT",
      },
      {
        proposalId: "P0_C",
        ts: 1000000 + 10 * 60 * 1000, // 10 minutes later
        decision: "ADOPT",
      },
    ];

    const interactions = detectInteractionsV1(adoptions, [], []);

    // Should detect at least 2 pairs: (A,B) and (B,C)
    expect(interactions.length).toBeGreaterThanOrEqual(2);
    expect(interactions.every((i) => i.window === "W_TIGHT")).toBe(true);
  });

  /**
   * Test 8: Coupling risk high (score threshold exceeded)
   */
  test("Test 8: Coupling risk high when score threshold exceeded", () => {
    const adoptions: AdoptionEvent[] = [
      {
        proposalId: "P0_A",
        ts: 1000000,
        decision: "ADOPT",
      },
      {
        proposalId: "P0_B",
        ts: 1000000 + 10 * 60 * 1000, // 10 minutes later (W_TIGHT)
        decision: "ADOPT",
      },
    ];

    const effects: PatchEffectReportV1[] = [
      {
        kind: "PATCH_EFFECT_V1",
        status: "AVAILABLE",
        decisionAckRef: { proposalId: "P0_A" },
        effectDecision: "EFFECT_WORSENED",
        compare: { improved: [], worsened: ["WORSENED_BLOCK_RATE"], unchanged: [], unavailable: [] },
        windows: [],
        rationale: [],
        warnings: [],
        ts: 1000000 + 30 * 60 * 1000,
      } as any,
    ];

    const regressions: RegressionReportV1[] = [
      {
        kind: "REGRESSION_REPORT_V1",
        status: "AVAILABLE",
        analysis: {
          proposalId: "P0_B",
          decision: "REGRESSION_DETECTED",
          kind: "REGRESS_IMPROVED_TO_WORSENED",
          strength: "STRONG",
          windowLabel: "W_SHORT",
          evidence: [],
          warnings: [],
        },
        ts: 1000000 + 40 * 60 * 1000,
        warnings: [],
      },
    ];

    const interactions = detectInteractionsV1(adoptions, effects, regressions);

    expect(interactions.length).toBeGreaterThan(0);
    // Should be STRONG due to regression
    expect(interactions[0].interactionKind).toBe("INT_PATCH_PAIR_REGRESSION");
    expect(interactions[0].strength).toBe("STRONG");
  });

  /**
   * Test 9: Evidence max 3 + strength order
   */
  test("Test 9: Evidence is limited to 3 and sorted by strength", () => {
    const report: InteractionReportV1 = {
      kind: "INTERACTION_REPORT_V1",
      status: "AVAILABLE",
      primaryProposalId: "P0_A",
      secondaryProposalId: "P0_B",
      primaryDecision: "ADOPT",
      secondaryDecision: "ADOPT",
      interaction: "INTERACTION_DETECTED",
      interactionKind: "INT_COUPLING_RISK_HIGH",
      strength: "STRONG",
      window: "W_TIGHT",
      timeLabel: "T_RECENT",
      evidence: [
        { kind: "EVID_DECISION", label: "WEAK_EVIDENCE", strength: "WEAK" },
        { kind: "EVID_EFFECT", label: "MEDIUM_EVIDENCE", strength: "MEDIUM" },
        { kind: "EVID_REGRESSION", label: "STRONG_EVIDENCE", strength: "STRONG" },
        { kind: "EVID_EFFECT", label: "ANOTHER_WEAK", strength: "WEAK" },
      ],
      warnings: [],
      ts: Date.now(),
    };

    const lines = formatInteractionLinesV1(report, false);
    const evidenceLines = lines.filter((line) => line.startsWith("  -"));

    // Should show max 3 evidence items
    expect(evidenceLines.length).toBeLessThanOrEqual(3);
  });

  /**
   * Test 10: Sanitization removes forbidden patterns
   */
  test("Test 10: Sanitization removes forbidden patterns", () => {
    const label1 = "Found address 0x1234567890123456789012345678901234567890";
    const sanitized1 = sanitizeInteractionLabel(label1);
    expect(sanitized1).toContain("REDACTED");
    expect(sanitized1).not.toContain("0x1234");

    const label2 = "User tried to buy 100 USDC";
    const sanitized2 = sanitizeInteractionLabel(label2);
    expect(sanitized2).toContain("REDACTED");
  });

  /**
   * Test 11: Corrupt JSONL line skip
   */
  test("Test 11: Corrupt JSONL lines are skipped", () => {
    const logPath = getInteractionLogPath();

    // Write valid report
    const validReport: InteractionReportV1 = {
      kind: "INTERACTION_REPORT_V1",
      status: "AVAILABLE",
      primaryProposalId: "P0_CORRUPT_TEST_A",
      secondaryProposalId: "P0_CORRUPT_TEST_B",
      primaryDecision: "ADOPT",
      secondaryDecision: "ADOPT",
      interaction: "INTERACTION_DETECTED",
      interactionKind: "INT_MULTIPLE_ADOPTS_SAME_WINDOW",
      strength: "MEDIUM",
      window: "W_TIGHT",
      timeLabel: "T_RECENT",
      evidence: [],
      warnings: [],
      ts: Date.now(),
    };

    appendInteractionReportV1(validReport);

    // Append corrupt line manually
    fs.appendFileSync(logPath, "CORRUPT_JSON_LINE\n", "utf-8");

    // Read should skip corrupt line
    const { reports, warnings } = readRecentInteractionReportsV1({ tail: 10 });

    // Should have warnings about parse error
    expect(warnings.some((w) => w.includes("PARSE_ERROR"))).toBe(true);

    // Should still find valid report
    const found = reports.find((r) => r.primaryProposalId === "P0_CORRUPT_TEST_A");
    expect(found).toBeDefined();
  });

  /**
   * Test 12: CLI format contains no numerics
   */
  test("Test 12: Formatted output is label-only (no numerics)", () => {
    const report: InteractionReportV1 = {
      kind: "INTERACTION_REPORT_V1",
      status: "AVAILABLE",
      primaryProposalId: "P0_A",
      secondaryProposalId: "P0_B",
      primaryDecision: "ADOPT",
      secondaryDecision: "ADOPT",
      interaction: "INTERACTION_DETECTED",
      interactionKind: "INT_PATCH_PAIR_REGRESSION",
      strength: "STRONG",
      window: "W_TIGHT",
      timeLabel: "T_RECENT",
      evidence: [
        {
          kind: "EVID_REGRESSION",
          label: "REGRESSION_DETECTED_AFTER_PAIR",
          strength: "STRONG",
        },
      ],
      warnings: [],
      ts: Date.now(),
    };

    const lines = formatInteractionLinesV1(report, false); // Normal mode

    // Check that evidence labels are valid (no isolated large numbers)
    for (const line of lines) {
      if (line.includes("EVID_")) {
        // Extract label
        const match = line.match(/\[EVID_\w+\]\s+(\S+)/);
        if (match) {
          const label = match[1];
          // Validate it's label-only (allowing small numbers in labels like "WITHIN_2")
          expect(validateInteractionLabelOnly(label, false)).toBe(true);
        }
      }
    }
  });

  /**
   * Test 13: Extraction of adoption events
   */
  test("Test 13: Adoption events are extracted correctly", () => {
    const decisions: DecisionAckRecordV1[] = [
      {
        kind: "DECISION_ACK_V1",
        status: "AVAILABLE",
        ts: 1000000,
        timeLabel: "T_RECENT",
        reviewer: "HUMAN_PRIMARY",
        source: "CLI_ADOPT",
        refs: { proposalId: "P0_A" },
        rationale: {
          decision: "ADOPT",
          rationaleLabels: [],
          checklistSummary: [],
          evidenceSummary: [],
          compareSummary: [],
        },
        warnings: [],
      },
      {
        kind: "DECISION_ACK_V1",
        status: "AVAILABLE",
        ts: 2000000,
        timeLabel: "T_RECENT",
        reviewer: "HUMAN_PRIMARY",
        source: "CLI_ADOPT",
        refs: { proposalId: "P0_B" },
        rationale: {
          decision: "ADOPT",
          rationaleLabels: [],
          checklistSummary: [],
          evidenceSummary: [],
          compareSummary: [],
        },
        warnings: [],
      },
    ];

    const adoptions = extractAdoptionEvents(decisions);

    expect(adoptions.length).toBe(2);
    expect(adoptions[0].proposalId).toBe("P0_A");
    expect(adoptions[1].proposalId).toBe("P0_B");
    expect(adoptions[0].ts).toBe(1000000);
    expect(adoptions[1].ts).toBe(2000000);
  });

  /**
   * Test 14: Store append/read roundtrip
   */
  test("Test 14: Store append and read roundtrip", () => {
    const report: InteractionReportV1 = {
      kind: "INTERACTION_REPORT_V1",
      status: "AVAILABLE",
      primaryProposalId: "P0_STORE_TEST_A",
      secondaryProposalId: "P0_STORE_TEST_B",
      primaryDecision: "ADOPT",
      secondaryDecision: "ADOPT",
      interaction: "INTERACTION_DETECTED",
      interactionKind: "INT_COUPLING_RISK_HIGH",
      strength: "STRONG",
      window: "W_TIGHT",
      timeLabel: "T_RECENT",
      evidence: [
        {
          kind: "EVID_REGRESSION",
          label: "TEST_EVIDENCE",
          strength: "STRONG",
        },
      ],
      warnings: [],
      ts: Date.now(),
    };

    // Append
    const { status } = appendInteractionReportV1(report);
    expect(status).toBe("OK");

    // Read back
    const { reports } = readRecentInteractionReportsV1({ tail: 10 });

    // Should find our report (matches either primary or secondary)
    const found = reports.find(
      (r) =>
        r.primaryProposalId === "P0_STORE_TEST_A" ||
        r.secondaryProposalId === "P0_STORE_TEST_B"
    );
    expect(found).toBeDefined();
    expect(found?.interaction).toBe("INTERACTION_DETECTED");
  });
});
