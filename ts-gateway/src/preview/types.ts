/**
 * PR171: v1.4 Patch Preview Report v1 - Types
 *
 * Purpose:
 *   Convert PatchPlan to human-readable change previews for adoption review.
 *   Shows "what will change" before adoption (READ-ONLY).
 *
 * Constitutional Constraints:
 *   - READ-ONLY: Report generation only (no automatic adoption, no code changes)
 *   - Fixed mapping: patch op → report sections (predetermined)
 *   - Label-only: Normal mode uses labels (no numerics)
 *   - Defensive: Never throws, always returns result
 */

/**
 * Preview Status
 *
 * - AVAILABLE: Preview generated successfully
 * - PARTIAL: Preview generated with missing information
 * - ERROR: Fatal error (minimal result returned)
 */
export type PreviewStatus = "AVAILABLE" | "PARTIAL" | "ERROR";

/**
 * Time Label
 *
 * Discretized time categories (label-only, not numeric timestamps in normal mode).
 */
export type PreviewTimeLabel =
  | "T_RECENT" // < 5 minutes
  | "T_MIN" // < 60 minutes
  | "T_HOUR" // < 24 hours
  | "T_OLD" // >= 24 hours
  | "T_UNKNOWN"; // No timestamp

/**
 * Preview Section
 *
 * One section of the preview report (one patch operation's changes).
 * All fields are label-only (no numerics, no rule values).
 */
export interface PreviewSection {
  /**
   * Section title (label-only)
   *
   * Example: "SECTION_PHASE_POLICY", "SECTION_GATE_PRIORITY"
   */
  title: string;

  /**
   * Before state (label-only)
   *
   * Example: ["BEFORE_STOP_RULES_CURRENT"]
   */
  before: string[];

  /**
   * After state (label-only)
   *
   * Example: ["AFTER_STOP_RULES_TUNED"]
   */
  after: string[];

  /**
   * Notes (label-only explanations)
   *
   * Example: ["NOTE_STOP_WAIT_BALANCE_CHANGED", "NOTE_SAFETY_CONSTRAINTS_PRESERVED"]
   */
  notes: string[];
}

/**
 * Patch Preview Report v1
 *
 * Human-readable preview of PatchPlan changes.
 * All fields are label-only (no numerics in normal mode).
 */
export interface PatchPreviewReportV1 {
  /**
   * Kind (always "PATCH_PREVIEW_V1")
   */
  kind: "PATCH_PREVIEW_V1";

  /**
   * Status
   */
  status: PreviewStatus;

  /**
   * Proposal ID (if available)
   *
   * Example: "P0_REDUCE_ORACLE_STALE_BLOCKS_DEGRADE"
   */
  proposalId?: string;

  /**
   * Priority (if available)
   */
  priority?: "P0" | "P1" | "P2" | "UNKNOWN";

  /**
   * Decision candidate (if available)
   *
   * Example: "ADOPT", "HOLD", "REJECT"
   */
  decisionCandidate?: "ADOPT" | "HOLD" | "REJECT" | "UNKNOWN";

  /**
   * Patch operations (label-only op IDs)
   *
   * Example: ["PATCH_PHASE_POLICY", "PATCH_GATE_ORDER"]
   */
  patchOps: string[];

  /**
   * Sections (one per patch op)
   *
   * Generated from fixed templates based on patchOps.
   */
  sections: PreviewSection[];

  /**
   * Risk labels (label-only warnings)
   *
   * Example: ["RISK_PATCH_NOT_ALLOWED_PRESENT"]
   */
  riskLabels: string[];

  /**
   * Readiness labels (label-only status)
   *
   * Example: ["REVIEWABLE"], ["NOT_REVIEWABLE_REJECT_EXPECTED"]
   */
  readiness: string[];

  /**
   * Evidence (from PR170, sanitized, max 3)
   *
   * Strength-sorted evidence supporting the proposal.
   */
  evidence: Array<{
    kind: string; // EVID_*
    label: string; // label-only
    strength: string; // EVIDENCE_*
    context?: string[]; // label-only (debug may include more)
  }>;

  /**
   * Compare signals (from PR168, label-only)
   *
   * Example: ["IMPROVED_PASS_RATIO", "NO_WORSENING"]
   */
  compareSignals: string[];

  /**
   * Warnings (non-fatal issues)
   */
  warnings: string[];

  /**
   * Time label (discretized timestamp)
   */
  timeLabel: PreviewTimeLabel;

  /**
   * Timestamp (numeric, for storage/filtering)
   *
   * Not displayed in normal mode (only timeLabel shown).
   */
  ts: number;
}

/**
 * Preview Filter
 *
 * For reading previews from store.
 */
export interface PreviewFilter {
  /**
   * Tail N most recent previews
   */
  tail?: number;

  /**
   * Filter by proposal ID
   */
  proposalId?: string;

  /**
   * Filter by priority
   */
  priority?: "P0" | "P1" | "P2" | "UNKNOWN";

  /**
   * Filter by decision candidate
   */
  decisionCandidate?: "ADOPT" | "HOLD" | "REJECT" | "UNKNOWN";
}
