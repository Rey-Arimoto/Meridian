/**
 * PR172: v1.4 Patch Review Checklist + Decision Rationale v1 - Reviewer Engine
 *
 * Purpose:
 *   Main review engine that evaluates patch previews and generates
 *   structured checklist and decision rationale.
 *
 * Constitutional Constraints:
 *   - READ-ONLY: No automatic adoption (only suggests decision)
 *   - Fixed rules: Deterministic evaluation
 *   - Label-only: All output is sanitized
 *   - Defensive: Never throws, always returns result
 *   - Safety-first: NOT_REVIEWABLE checks have highest priority
 */

import { PatchPreviewReportV1 } from "../preview/types";
import {
  PatchReviewReportV1,
  ReviewStatus,
  ReviewChecklistItem,
} from "./types";
import { CHECKLIST_ITEMS, determineDecisionCandidate } from "./rules";
import { sanitizeLabel, sanitizeLines } from "./guards";

/**
 * Review patch preview v1
 *
 * Main review function that evaluates preview and generates checklist + rationale.
 *
 * @param preview - Patch preview report from PR171
 * @returns Review report (never throws)
 */
export function reviewPatchPreviewV1(
  preview: PatchPreviewReportV1
): PatchReviewReportV1 {
  const warnings: string[] = [];

  try {
    // 1. Check if preview is reviewable (safety-first)
    if (!preview.readiness.includes("REVIEWABLE")) {
      // NOT_REVIEWABLE: Skip detailed checks, suggest REJECT
      const checklist: ReviewChecklistItem[] = [
        {
          id: "CHECK_PREVIEW_REVIEWABLE",
          label: "Preview marked as reviewable",
          status: "FAIL",
          detail: "Preview readiness is NOT_REVIEWABLE",
        },
      ];

      return {
        kind: "PATCH_REVIEW_V1",
        status: "NOT_REVIEWABLE",
        checklist,
        rationale: {
          decisionCandidate: "CANDIDATE_REJECT",
          reasons: ["REASON_PREVIEW_NOT_REVIEWABLE"],
        },
        warnings: sanitizeLines(warnings),
        ts: Date.now(),
      };
    }

    // 2. Evaluate all checklist items
    const checklist: ReviewChecklistItem[] = [];

    for (const checkDef of CHECKLIST_ITEMS) {
      try {
        const result = checkDef.evaluate(preview);

        checklist.push({
          id: sanitizeLabel(checkDef.id),
          label: sanitizeLabel(checkDef.label),
          status: result.status,
          detail: result.detail ? sanitizeLabel(result.detail) : undefined,
        });
      } catch (error) {
        // Defensive: Skip failed check evaluation
        checklist.push({
          id: sanitizeLabel(checkDef.id),
          label: sanitizeLabel(checkDef.label),
          status: "UNKNOWN",
          detail: "Check evaluation failed",
        });

        warnings.push(`WARN_CHECK_EVAL_FAILED_${checkDef.id}`);
      }
    }

    // 3. Determine decision candidate and rationale
    const { candidate, reasons } = determineDecisionCandidate(
      preview,
      checklist
    );

    // 4. Determine review status
    const status: ReviewStatus = "REVIEWABLE";

    return {
      kind: "PATCH_REVIEW_V1",
      status,
      checklist,
      rationale: {
        decisionCandidate: candidate,
        reasons: sanitizeLines(reasons),
      },
      warnings: sanitizeLines(warnings),
      ts: Date.now(),
    };
  } catch (error) {
    // Defensive: Return minimal ERROR result
    warnings.push("WARN_REVIEW_ERROR");

    return {
      kind: "PATCH_REVIEW_V1",
      status: "ERROR",
      checklist: [],
      rationale: {
        decisionCandidate: "CANDIDATE_REJECT",
        reasons: ["REASON_REVIEW_ERROR"],
      },
      warnings: sanitizeLines(warnings),
      ts: Date.now(),
    };
  }
}
