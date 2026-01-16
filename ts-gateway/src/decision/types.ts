/**
 * PR173: v1.4 Decision Acknowledgement + Reviewer Trace v1 - Types
 *
 * Purpose:
 *   Type definitions for decision acknowledgement records.
 *   Captures "who decided what, when, and why" for audit trail.
 *
 * Constitutional Constraints:
 *   - READ-ONLY: Records decision facts only (no automatic adoption)
 *   - Label-only: All fields sanitized (no numerics in display)
 *   - Defensive: All types designed to handle missing/corrupt data
 *   - Append-only: Records are immutable audit logs
 */

/**
 * Decision Ack Status
 *
 * - AVAILABLE: Complete record with all required fields
 * - PARTIAL: Some fields missing but record valid
 * - ERROR: Record creation failed but returned safe fallback
 */
export type DecisionAckStatus = "AVAILABLE" | "PARTIAL" | "ERROR";

/**
 * Reviewer Kind
 *
 * Labels who made the decision (not what they decided).
 *
 * - HUMAN_PRIMARY: Primary human decision maker
 * - HUMAN_SECONDARY: Secondary human reviewer
 * - AUTO_ASSISTED: Human with automated assistance (e.g., PR172 checklist)
 * - POLICY_ONLY: Policy-first automated decision (PR168)
 * - UNKNOWN: Reviewer kind not specified
 */
export type ReviewerKind =
  | "HUMAN_PRIMARY"
  | "HUMAN_SECONDARY"
  | "AUTO_ASSISTED"
  | "POLICY_ONLY"
  | "UNKNOWN";

/**
 * Ack Decision
 *
 * Final decision recorded in acknowledgement.
 *
 * - ADOPT: Decision to adopt the patch
 * - HOLD: Decision to hold (defer) the patch
 * - REJECT: Decision to reject the patch
 * - UNKNOWN: Decision not available
 */
export type AckDecision = "ADOPT" | "HOLD" | "REJECT" | "UNKNOWN";

/**
 * Ack Source
 *
 * Where the acknowledgement was created.
 *
 * - CLI_ADOPT: From adopt CLI with --ack option
 * - CLI_ACK: From standalone decisions CLI
 * - UNKNOWN: Source not specified
 */
export type AckSource = "CLI_ADOPT" | "CLI_ACK" | "UNKNOWN";

/**
 * Time Label
 *
 * Discretized time representation (no raw timestamps in display).
 *
 * - T_RECENT: < 5 minutes ago
 * - T_MIN: < 60 minutes ago
 * - T_HOUR: < 24 hours ago
 * - T_OLD: >= 24 hours ago
 * - T_UNKNOWN: No timestamp available
 */
export type TimeLabel =
  | "T_RECENT"
  | "T_MIN"
  | "T_HOUR"
  | "T_OLD"
  | "T_UNKNOWN";

/**
 * Decision Ack References
 *
 * Links to related entities (proposal, preview, review, patch plan).
 * All fields are label-only (no numeric IDs).
 */
export interface DecisionAckRefs {
  /**
   * Proposal ID (e.g., "P0_REDUCE_ORACLE_STALE_BLOCKS_DEGRADE")
   */
  proposalId?: string;

  /**
   * Preview reference label (e.g., "PREVIEW_PRESENT")
   */
  previewId?: string;

  /**
   * Review reference label (e.g., "REVIEW_PRESENT")
   */
  reviewId?: string;

  /**
   * Patch plan reference label (e.g., "PATCHPLAN_PRESENT")
   */
  patchPlanId?: string;
}

/**
 * Decision Ack Rationale
 *
 * Why the decision was made (label-only summaries).
 */
export interface DecisionAckRationale {
  /**
   * Final decision (ADOPT/HOLD/REJECT/UNKNOWN)
   */
  decision: AckDecision;

  /**
   * Rationale labels (e.g., "REASON_STRONG_EVIDENCE_PRESENT")
   */
  rationaleLabels: string[];

  /**
   * Checklist summary (e.g., "CHECK_NO_NOT_ALLOWED_PATCH:PASS")
   */
  checklistSummary: string[];

  /**
   * Evidence summary (e.g., "EVIDENCE_STRONG")
   */
  evidenceSummary: string[];

  /**
   * Compare summary (e.g., "IMPROVED_BLOCK_DOMINANCE")
   */
  compareSummary: string[];
}

/**
 * Decision Acknowledgement Record v1
 *
 * Immutable audit record of a decision.
 *
 * Constitutional Constraints:
 * - READ-ONLY: Recording only (no automatic adoption)
 * - Label-only: All fields sanitized for display
 * - Defensive: Always valid, even on error
 * - Append-only: Immutable audit log
 */
export interface DecisionAckRecordV1 {
  /**
   * Record kind identifier
   */
  kind: "DECISION_ACK_V1";

  /**
   * Record status
   */
  status: DecisionAckStatus;

  /**
   * Timestamp (internal storage only, never displayed raw)
   */
  ts: number;

  /**
   * Time label (display-safe)
   */
  timeLabel: TimeLabel;

  /**
   * Who made the decision
   */
  reviewer: ReviewerKind;

  /**
   * Where the acknowledgement was created
   */
  source: AckSource;

  /**
   * References to related entities
   */
  refs: DecisionAckRefs;

  /**
   * Decision rationale
   */
  rationale: DecisionAckRationale;

  /**
   * Warnings (label-only)
   */
  warnings: string[];
}
