/**
 * PR172: v1.4 Patch Review Checklist + Decision Rationale v1 - Tests
 *
 * Purpose:
 *   Verify review checklist, decision rationale, and sanitization.
 *
 * Test Coverage:
 *   1. All 6 checklist items evaluate correctly
 *   2. NOT_REVIEWABLE → CANDIDATE_REJECT
 *   3. PATCH_NOT_ALLOWED → CANDIDATE_REJECT
 *   4. Worsening signals → CANDIDATE_REJECT
 *   5. Weak evidence only → CANDIDATE_HOLD
 *   6. Multi-area (>2 ops) → CANDIDATE_HOLD
 *   7. No evidence → CANDIDATE_HOLD
 *   8. Strong evidence + no worsening → CANDIDATE_ADOPT
 *   9. Sanitization: forbidden patterns → REDACTED
 *   10. Defensive: malformed preview doesn't throw
 *   11. Format review lines (label-only)
 *   12. P0 without strong evidence → CHECK_PRIORITY_P0_SAFE fails
 */

import { reviewPatchPreviewV1 } from "../src/review/reviewer";
import { determineDecisionCandidate, CHECKLIST_ITEMS } from "../src/review/rules";
import { sanitizeLabel, formatReviewLines } from "../src/review/guards";
import { PatchPreviewReportV1 } from "../src/preview/types";

describe("PR172: Patch Review Checklist + Decision Rationale", () => {
  /**
   * Test 1: All 6 checklist items evaluate correctly
   */
  test("Test 1: All 6 checklist items run", () => {
    const preview: PatchPreviewReportV1 = {
      kind: "PATCH_PREVIEW_V1",
      proposalId: "P0_TEST",
      priority: "P0",
      status: "COMPLETE",
      patchOps: ["PATCH_GATE_ORDER"],
      sections: [],
      evidence: [
        {
          kind: "EVID_1",
          label: "STRONG_EVID",
          strength: "EVIDENCE_STRONG",
          context: "ctx1",
        },
      ],
      compareSignals: ["NO_WORSENING"],
      riskLabels: [],
      readiness: ["REVIEWABLE"],
      warnings: [],
      ts: Date.now(),
    };

    const review = reviewPatchPreviewV1(preview);

    // Should have 6 checklist items
    expect(review.checklist.length).toBe(6);

    // Verify all items passed
    const allPassed = review.checklist.every((item) => item.status === "PASS");
    expect(allPassed).toBe(true);
  });

  /**
   * Test 2: NOT_REVIEWABLE → CANDIDATE_REJECT
   */
  test("Test 2: NOT_REVIEWABLE suggests REJECT", () => {
    const preview: PatchPreviewReportV1 = {
      kind: "PATCH_PREVIEW_V1",
      proposalId: "P0_TEST",
      priority: "P0",
      status: "COMPLETE",
      patchOps: ["PATCH_GATE_ORDER"],
      sections: [],
      evidence: [],
      compareSignals: [],
      riskLabels: [],
      readiness: ["NOT_REVIEWABLE_REJECT_EXPECTED"],
      warnings: [],
      ts: Date.now(),
    };

    const review = reviewPatchPreviewV1(preview);

    expect(review.status).toBe("NOT_REVIEWABLE");
    expect(review.rationale.decisionCandidate).toBe("CANDIDATE_REJECT");
    expect(review.rationale.reasons).toContain("REASON_PREVIEW_NOT_REVIEWABLE");
  });

  /**
   * Test 3: PATCH_NOT_ALLOWED → CANDIDATE_REJECT
   */
  test("Test 3: PATCH_NOT_ALLOWED suggests REJECT", () => {
    const preview: PatchPreviewReportV1 = {
      kind: "PATCH_PREVIEW_V1",
      proposalId: "P0_TEST",
      priority: "P0",
      status: "COMPLETE",
      patchOps: ["PATCH_NOT_ALLOWED"],
      sections: [],
      evidence: [],
      compareSignals: [],
      riskLabels: ["RISK_PATCH_NOT_ALLOWED_PRESENT"],
      readiness: ["REVIEWABLE"],
      warnings: [],
      ts: Date.now(),
    };

    const review = reviewPatchPreviewV1(preview);

    expect(review.status).toBe("REVIEWABLE");

    // Should have failing check
    const notAllowedCheck = review.checklist.find(
      (item) => item.id === "CHECK_NO_NOT_ALLOWED_PATCH"
    );
    expect(notAllowedCheck?.status).toBe("FAIL");

    expect(review.rationale.decisionCandidate).toBe("CANDIDATE_REJECT");
    expect(review.rationale.reasons).toContain("REASON_PATCH_NOT_ALLOWED_PRESENT");
  });

  /**
   * Test 4: Worsening signals → CANDIDATE_REJECT
   */
  test("Test 4: Worsening signals suggest REJECT", () => {
    const preview: PatchPreviewReportV1 = {
      kind: "PATCH_PREVIEW_V1",
      proposalId: "P0_TEST",
      priority: "P0",
      status: "COMPLETE",
      patchOps: ["PATCH_GATE_ORDER"],
      sections: [],
      evidence: [
        {
          kind: "EVID_1",
          label: "STRONG_EVID",
          strength: "EVIDENCE_STRONG",
          context: "ctx1",
        },
      ],
      compareSignals: ["SIGNAL_WORSENED_PASS_RATIO"],
      riskLabels: [],
      readiness: ["REVIEWABLE"],
      warnings: [],
      ts: Date.now(),
    };

    const review = reviewPatchPreviewV1(preview);

    // Should have failing check
    const worseningCheck = review.checklist.find(
      (item) => item.id === "CHECK_NO_WORSENING_SIGNAL"
    );
    expect(worseningCheck?.status).toBe("FAIL");

    expect(review.rationale.decisionCandidate).toBe("CANDIDATE_REJECT");
    expect(review.rationale.reasons).toContain("REASON_COMPARE_SHOWS_WORSENING");
  });

  /**
   * Test 5: Weak evidence only → CANDIDATE_HOLD
   */
  test("Test 5: Weak evidence only suggests HOLD", () => {
    const preview: PatchPreviewReportV1 = {
      kind: "PATCH_PREVIEW_V1",
      proposalId: "P0_TEST",
      priority: "P0",
      status: "COMPLETE",
      patchOps: ["PATCH_GATE_ORDER"],
      sections: [],
      evidence: [
        {
          kind: "EVID_1",
          label: "WEAK_EVID",
          strength: "EVIDENCE_WEAK",
          context: "ctx1",
        },
      ],
      compareSignals: ["NO_WORSENING"],
      riskLabels: [],
      readiness: ["REVIEWABLE"],
      warnings: [],
      ts: Date.now(),
    };

    const review = reviewPatchPreviewV1(preview);

    expect(review.status).toBe("REVIEWABLE");
    expect(review.rationale.decisionCandidate).toBe("CANDIDATE_HOLD");
    expect(review.rationale.reasons).toContain("REASON_EVIDENCE_WEAK_ONLY");
  });

  /**
   * Test 6: Multi-area (>2 ops) → CANDIDATE_HOLD
   */
  test("Test 6: Multi-area change suggests HOLD", () => {
    const preview: PatchPreviewReportV1 = {
      kind: "PATCH_PREVIEW_V1",
      proposalId: "P0_TEST",
      priority: "P0",
      status: "COMPLETE",
      patchOps: ["PATCH_GATE_ORDER", "PATCH_PHASE_POLICY", "PATCH_ROUTER_TIEBREAK"],
      sections: [],
      evidence: [
        {
          kind: "EVID_1",
          label: "STRONG_EVID",
          strength: "EVIDENCE_STRONG",
          context: "ctx1",
        },
      ],
      compareSignals: ["NO_WORSENING"],
      riskLabels: [],
      readiness: ["REVIEWABLE"],
      warnings: [],
      ts: Date.now(),
    };

    const review = reviewPatchPreviewV1(preview);

    // Should have failing check
    const scopeCheck = review.checklist.find((item) => item.id === "CHECK_SCOPE_NOT_MULTI");
    expect(scopeCheck?.status).toBe("FAIL");

    expect(review.rationale.decisionCandidate).toBe("CANDIDATE_HOLD");
    expect(review.rationale.reasons).toContain("REASON_MULTI_AREA_CHANGE");
  });

  /**
   * Test 7: No evidence → CANDIDATE_HOLD
   */
  test("Test 7: No evidence suggests HOLD", () => {
    const preview: PatchPreviewReportV1 = {
      kind: "PATCH_PREVIEW_V1",
      proposalId: "P0_TEST",
      priority: "P0",
      status: "COMPLETE",
      patchOps: ["PATCH_GATE_ORDER"],
      sections: [],
      evidence: [],
      compareSignals: ["NO_WORSENING"],
      riskLabels: [],
      readiness: ["REVIEWABLE"],
      warnings: [],
      ts: Date.now(),
    };

    const review = reviewPatchPreviewV1(preview);

    // Should have failing check
    const evidenceCheck = review.checklist.find((item) => item.id === "CHECK_HAS_EVIDENCE");
    expect(evidenceCheck?.status).toBe("FAIL");

    expect(review.rationale.decisionCandidate).toBe("CANDIDATE_HOLD");
    expect(review.rationale.reasons).toContain("REASON_NO_EVIDENCE");
  });

  /**
   * Test 8: Strong evidence + no worsening → CANDIDATE_ADOPT
   */
  test("Test 8: Strong evidence and no worsening suggest ADOPT", () => {
    const preview: PatchPreviewReportV1 = {
      kind: "PATCH_PREVIEW_V1",
      proposalId: "P0_TEST",
      priority: "P0",
      status: "COMPLETE",
      patchOps: ["PATCH_GATE_ORDER"],
      sections: [],
      evidence: [
        {
          kind: "EVID_1",
          label: "STRONG_EVID",
          strength: "EVIDENCE_STRONG",
          context: "ctx1",
        },
      ],
      compareSignals: ["NO_WORSENING"],
      riskLabels: [],
      readiness: ["REVIEWABLE"],
      warnings: [],
      ts: Date.now(),
    };

    const review = reviewPatchPreviewV1(preview);

    expect(review.status).toBe("REVIEWABLE");
    expect(review.rationale.decisionCandidate).toBe("CANDIDATE_ADOPT");
    expect(review.rationale.reasons).toContain("REASON_STRONG_EVIDENCE_PRESENT");
    expect(review.rationale.reasons).toContain("REASON_NO_WORSENING_SIGNAL");
    expect(review.rationale.reasons).toContain("REASON_CHANGE_SCOPE_LIMITED");
  });

  /**
   * Test 9: Sanitization - forbidden patterns
   */
  test("Test 9: Forbidden patterns sanitized", () => {
    // Token literals
    expect(sanitizeLabel("wBTC balance")).toBe("REDACTED");
    expect(sanitizeLabel("USDC threshold")).toBe("REDACTED");

    // Trading vocab
    expect(sanitizeLabel("buy signal")).toBe("REDACTED");
    expect(sanitizeLabel("sell trigger")).toBe("REDACTED");

    // Prescriptive language
    expect(sanitizeLabel("should adopt")).toBe("REDACTED");
    expect(sanitizeLabel("must reject")).toBe("REDACTED");

    // Address
    expect(sanitizeLabel("0x1234abcd5678")).toBe("REDACTED");

    // Allowed
    expect(sanitizeLabel("CANDIDATE_ADOPT")).toBe("CANDIDATE_ADOPT");
    expect(sanitizeLabel("CHECK_NO_WORSENING_SIGNAL")).toBe("CHECK_NO_WORSENING_SIGNAL");
  });

  /**
   * Test 10: Defensive - malformed preview doesn't throw
   */
  test("Test 10: Malformed preview doesn't throw", () => {
    // Should not throw with undefined fields
    expect(() => {
      reviewPatchPreviewV1({
        kind: "PATCH_PREVIEW_V1",
        proposalId: undefined as any,
        priority: undefined as any,
        status: "COMPLETE",
        patchOps: undefined as any,
        sections: [],
        evidence: undefined as any,
        compareSignals: undefined as any,
        riskLabels: [],
        readiness: ["REVIEWABLE"],
        warnings: [],
        ts: Date.now(),
      });
    }).not.toThrow();

    // Should return ERROR status
    const review = reviewPatchPreviewV1({} as any);
    expect(review.status).toBe("ERROR");
    expect(review.rationale.decisionCandidate).toBe("CANDIDATE_REJECT");
    expect(review.rationale.reasons).toContain("REASON_REVIEW_ERROR");
  });

  /**
   * Test 11: Format review lines (label-only)
   */
  test("Test 11: Format review lines label-only", () => {
    const preview: PatchPreviewReportV1 = {
      kind: "PATCH_PREVIEW_V1",
      proposalId: "P0_TEST",
      priority: "P0",
      status: "COMPLETE",
      patchOps: ["PATCH_GATE_ORDER"],
      sections: [],
      evidence: [
        {
          kind: "EVID_1",
          label: "STRONG_EVID",
          strength: "EVIDENCE_STRONG",
          context: "ctx1",
        },
      ],
      compareSignals: ["NO_WORSENING"],
      riskLabels: [],
      readiness: ["REVIEWABLE"],
      warnings: [],
      ts: Date.now(),
    };

    const review = reviewPatchPreviewV1(preview);
    const lines = formatReviewLines(review, false);

    // Should have header
    expect(lines.some((line) => line.includes("Patch Review Report"))).toBe(true);

    // Should have checklist section
    expect(lines.some((line) => line.includes("Review Checklist"))).toBe(true);

    // Should have decision rationale section
    expect(lines.some((line) => line.includes("Decision Rationale"))).toBe(true);

    // Should show suggested decision
    expect(lines.some((line) => line.includes("CANDIDATE_ADOPT"))).toBe(true);

    // Should not contain numeric timestamps (label-only mode)
    const hasNumericTimestamp = lines.some((line) => /\d{13}/.test(line));
    expect(hasNumericTimestamp).toBe(false);
  });

  /**
   * Test 12: P0 without strong evidence → CHECK_PRIORITY_P0_SAFE fails
   */
  test("Test 12: P0 without strong evidence fails priority check", () => {
    const preview: PatchPreviewReportV1 = {
      kind: "PATCH_PREVIEW_V1",
      proposalId: "P0_TEST",
      priority: "P0",
      status: "COMPLETE",
      patchOps: ["PATCH_GATE_ORDER"],
      sections: [],
      evidence: [
        {
          kind: "EVID_1",
          label: "WEAK_EVID",
          strength: "EVIDENCE_WEAK",
          context: "ctx1",
        },
      ],
      compareSignals: ["NO_WORSENING"],
      riskLabels: [],
      readiness: ["REVIEWABLE"],
      warnings: [],
      ts: Date.now(),
    };

    const review = reviewPatchPreviewV1(preview);

    // Should have failing P0 priority check
    const p0Check = review.checklist.find((item) => item.id === "CHECK_PRIORITY_P0_SAFE");
    expect(p0Check?.status).toBe("FAIL");
    expect(p0Check?.detail).toContain("P0 priority without strong evidence");
  });
});
