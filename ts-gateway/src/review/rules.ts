/**
 * PR172: v1.4 Patch Review Checklist + Decision Rationale v1 - Fixed Rules
 *
 * Purpose:
 *   Fixed checklist items and decision rationale rules.
 *   All rules are predetermined (no learning, no optimization).
 *
 * Constitutional Constraints:
 *   - Fixed rules: All checks and rationale are predetermined
 *   - Deterministic: Same preview → same review result
 *   - Safety-first: NOT_REVIEWABLE checks have highest priority
 *   - Label-only: All outputs are labels
 */

import { PatchPreviewReportV1 } from "../preview/types";
import { ReviewChecklistItem, ChecklistItemStatus, DecisionCandidate } from "./types";

/**
 * Checklist Check Definition
 *
 * Fixed definition for one checklist item.
 */
export interface ChecklistCheckDef {
  /**
   * Check ID (fixed identifier)
   */
  id: string;

  /**
   * Human-readable label
   */
  label: string;

  /**
   * Evaluation function
   *
   * @param preview - Patch preview report
   * @returns Check status
   */
  evaluate: (preview: PatchPreviewReportV1) => {
    status: ChecklistItemStatus;
    detail?: string;
  };
}

/**
 * Fixed Checklist Items
 *
 * All checklist items are defined here (predetermined).
 */
export const CHECKLIST_ITEMS: ChecklistCheckDef[] = [
  // CHECK 1: No PATCH_NOT_ALLOWED
  {
    id: "CHECK_NO_NOT_ALLOWED_PATCH",
    label: "No safety-reducing patches present",
    evaluate: (preview) => {
      const hasNotAllowed = preview.patchOps.some((op) =>
        op.includes("NOT_ALLOWED")
      );

      if (hasNotAllowed) {
        return {
          status: "FAIL",
          detail: "PATCH_NOT_ALLOWED found in patchOps",
        };
      }

      return { status: "PASS" };
    },
  },

  // CHECK 2: Preview readiness is REVIEWABLE
  {
    id: "CHECK_PREVIEW_REVIEWABLE",
    label: "Preview marked as reviewable",
    evaluate: (preview) => {
      const isReviewable = preview.readiness.includes("REVIEWABLE");

      if (!isReviewable) {
        return {
          status: "FAIL",
          detail: "Preview readiness is NOT_REVIEWABLE",
        };
      }

      return { status: "PASS" };
    },
  },

  // CHECK 3: Has evidence
  {
    id: "CHECK_HAS_EVIDENCE",
    label: "Supporting evidence present",
    evaluate: (preview) => {
      if (preview.evidence.length === 0) {
        return {
          status: "FAIL",
          detail: "No evidence available",
        };
      }

      return { status: "PASS" };
    },
  },

  // CHECK 4: No worsening signals
  {
    id: "CHECK_NO_WORSENING_SIGNAL",
    label: "No worsening signals in comparison",
    evaluate: (preview) => {
      const hasWorsening = preview.compareSignals.some((signal) =>
        signal.includes("WORSENED")
      );

      if (hasWorsening) {
        return {
          status: "FAIL",
          detail: "WORSENED signal found in compareSignals",
        };
      }

      return { status: "PASS" };
    },
  },

  // CHECK 5: Change scope is not multi-area
  {
    id: "CHECK_SCOPE_NOT_MULTI",
    label: "Change scope limited to single area",
    evaluate: (preview) => {
      // Multi-area if more than 2 patch ops
      if (preview.patchOps.length > 2) {
        return {
          status: "FAIL",
          detail: "Multiple patch operations (> 2)",
        };
      }

      return { status: "PASS" };
    },
  },

  // CHECK 6: P0 priority has strong evidence
  {
    id: "CHECK_PRIORITY_P0_SAFE",
    label: "P0 priority has strong evidence",
    evaluate: (preview) => {
      if (preview.priority === "P0") {
        const hasStrongEvidence = preview.evidence.some((evid) =>
          evid.strength.includes("STRONG")
        );

        if (!hasStrongEvidence) {
          return {
            status: "FAIL",
            detail: "P0 priority without strong evidence",
          };
        }
      }

      return { status: "PASS" };
    },
  },
];

/**
 * Decision Rationale Rules
 *
 * Fixed rules for determining decision candidate.
 */

/**
 * Determine decision candidate
 *
 * Uses fixed rules to suggest decision based on checklist results.
 *
 * Priority:
 * 1. REJECT if safety issues (NOT_ALLOWED, worsening, not reviewable)
 * 2. HOLD if weak evidence or multi-area or unknown checks
 * 3. ADOPT if all checks pass with strong evidence
 *
 * @param preview - Patch preview report
 * @param checklist - Evaluated checklist
 * @returns Decision candidate and reasons
 */
export function determineDecisionCandidate(
  preview: PatchPreviewReportV1,
  checklist: ReviewChecklistItem[]
): { candidate: DecisionCandidate; reasons: string[] } {
  const reasons: string[] = [];

  // REJECT conditions (highest priority)

  // 1. NOT_REVIEWABLE
  if (!preview.readiness.includes("REVIEWABLE")) {
    reasons.push("REASON_PREVIEW_NOT_REVIEWABLE");
    return { candidate: "CANDIDATE_REJECT", reasons };
  }

  // 2. PATCH_NOT_ALLOWED present
  if (preview.patchOps.some((op) => op.includes("NOT_ALLOWED"))) {
    reasons.push("REASON_PATCH_NOT_ALLOWED_PRESENT");
    return { candidate: "CANDIDATE_REJECT", reasons };
  }

  // 3. Worsening signals
  if (preview.compareSignals.some((signal) => signal.includes("WORSENED"))) {
    reasons.push("REASON_COMPARE_SHOWS_WORSENING");
    return { candidate: "CANDIDATE_REJECT", reasons };
  }

  // HOLD conditions (medium priority)

  // 1. Has FAIL checks (other than already handled above)
  const hasFailChecks = checklist.some((item) => item.status === "FAIL");
  if (hasFailChecks) {
    reasons.push("REASON_CHECKLIST_FAILURES");
    return { candidate: "CANDIDATE_HOLD", reasons };
  }

  // 2. Has UNKNOWN checks
  const hasUnknownChecks = checklist.some((item) => item.status === "UNKNOWN");
  if (hasUnknownChecks) {
    reasons.push("REASON_INSUFFICIENT_CONFIRMATION");
    return { candidate: "CANDIDATE_HOLD", reasons };
  }

  // 3. Weak evidence only
  const hasStrongOrMediumEvidence = preview.evidence.some(
    (evid) => evid.strength.includes("STRONG") || evid.strength.includes("MEDIUM")
  );

  if (!hasStrongOrMediumEvidence && preview.evidence.length > 0) {
    reasons.push("REASON_EVIDENCE_WEAK_ONLY");
    return { candidate: "CANDIDATE_HOLD", reasons };
  }

  // 4. No evidence
  if (preview.evidence.length === 0) {
    reasons.push("REASON_NO_EVIDENCE");
    return { candidate: "CANDIDATE_HOLD", reasons };
  }

  // 5. Multi-area change
  if (preview.patchOps.length > 2) {
    reasons.push("REASON_MULTI_AREA_CHANGE");
    return { candidate: "CANDIDATE_HOLD", reasons };
  }

  // ADOPT conditions (all checks passed)

  // Strong or medium evidence present
  if (hasStrongOrMediumEvidence) {
    reasons.push("REASON_STRONG_EVIDENCE_PRESENT");
  }

  // No worsening signals
  if (!preview.compareSignals.some((signal) => signal.includes("WORSENED"))) {
    reasons.push("REASON_NO_WORSENING_SIGNAL");
  }

  // Limited scope
  if (preview.patchOps.length <= 2) {
    reasons.push("REASON_CHANGE_SCOPE_LIMITED");
  }

  return { candidate: "CANDIDATE_ADOPT", reasons };
}
