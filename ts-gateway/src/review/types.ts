/**
 * PR172: v1.4 Patch Review Checklist + Decision Rationale v1 - Types
 *
 * Purpose:
 *   Structured review checklist and decision rationale to support human judgment.
 *   Standardizes the review process before adoption (READ-ONLY).
 *
 * Constitutional Constraints:
 *   - READ-ONLY: No automatic adoption (judgment and application are manual)
 *   - Fixed rules: All checklist items and rationale rules are predetermined
 *   - Label-only: All output is sanitized (no numerics)
 *   - Defensive: Never throws, always returns result
 *   - Safety-first: NOT_REVIEWABLE is highest priority
 */

/**
 * Review Status
 *
 * Indicates whether the patch preview can be reviewed.
 */
export type ReviewStatus =
  | "REVIEWABLE" // Can be reviewed (all checks can be evaluated)
  | "NOT_REVIEWABLE" // Cannot be reviewed (safety issues, missing data)
  | "ERROR"; // Fatal error during review

/**
 * Checklist Item Status
 *
 * Status of individual checklist item.
 */
export type ChecklistItemStatus =
  | "PASS" // Check passed
  | "FAIL" // Check failed
  | "UNKNOWN"; // Check could not be evaluated

/**
 * Review Checklist Item
 *
 * One item in the review checklist (label-only).
 */
export interface ReviewChecklistItem {
  /**
   * Check ID (fixed identifier)
   *
   * Example: "CHECK_NO_NOT_ALLOWED_PATCH"
   */
  id: string;

  /**
   * Human-readable label (label-only)
   *
   * Example: "No safety-reducing patches present"
   */
  label: string;

  /**
   * Check status
   */
  status: ChecklistItemStatus;

  /**
   * Optional detail (label-only)
   *
   * Example: "PATCH_NOT_ALLOWED found in patchOps"
   */
  detail?: string;
}

/**
 * Decision Candidate
 *
 * Suggested decision based on review (not automatic).
 */
export type DecisionCandidate =
  | "CANDIDATE_ADOPT" // Suggests adoption (strong evidence, no issues)
  | "CANDIDATE_HOLD" // Suggests holding (weak evidence, multiple areas)
  | "CANDIDATE_REJECT"; // Suggests rejection (safety issues, worsening)

/**
 * Decision Rationale
 *
 * Explanation for decision candidate (label-only).
 */
export interface DecisionRationale {
  /**
   * Decision candidate (suggested, not automatic)
   */
  decisionCandidate: DecisionCandidate;

  /**
   * Reasons for decision (label-only)
   *
   * Example: ["REASON_STRONG_EVIDENCE_PRESENT", "REASON_NO_WORSENING_SIGNAL"]
   */
  reasons: string[];
}

/**
 * Patch Review Report v1
 *
 * Complete review report including checklist and decision rationale.
 */
export interface PatchReviewReportV1 {
  /**
   * Kind (always "PATCH_REVIEW_V1")
   */
  kind: "PATCH_REVIEW_V1";

  /**
   * Review status
   */
  status: ReviewStatus;

  /**
   * Review checklist (fixed items)
   */
  checklist: ReviewChecklistItem[];

  /**
   * Decision rationale (suggested decision + reasons)
   */
  rationale: DecisionRationale;

  /**
   * Warnings (non-fatal issues)
   */
  warnings: string[];

  /**
   * Timestamp
   */
  ts: number;
}
