/**
 * PR176: v1.4 Change Interaction Detector v1 - Types
 *
 * Purpose:
 *   Detect patch coupling/interaction risks when multiple patches are adopted close together.
 *   "Individual patches are good, but combination breaks things."
 *
 * Constitutional Constraints:
 *   - READ-ONLY: Observation only (no automatic adoption/revert)
 *   - Fixed rules: Hardcoded detection logic (no learning)
 *   - Label-only: Normal mode uses labels (no counts/scores)
 *   - Defensive: Never throws, handles missing data gracefully
 *   - Append-only: Audit trail in ~/.meridian/interactions.log
 */

/**
 * Interaction status
 */
export type InteractionStatus = "AVAILABLE" | "PARTIAL" | "ERROR";

/**
 * Interaction kind (type of coupling/interaction detected)
 */
export type InteractionKind =
  | "INT_MULTIPLE_ADOPTS_SAME_WINDOW"
  | "INT_PATCH_PAIR_REGRESSION"
  | "INT_PATCH_FOLLOWS_WORSENING"
  | "INT_PATCH_PRECEDES_REGRESSION"
  | "INT_COUPLING_RISK_HIGH"
  | "INT_UNKNOWN";

/**
 * Interaction strength
 */
export type InteractionStrength = "STRONG" | "MEDIUM" | "WEAK" | "UNKNOWN";

/**
 * Interaction window label (time period)
 */
export type InteractionWindowLabel =
  | "W_TIGHT"
  | "W_NORMAL"
  | "W_WIDE"
  | "W_UNKNOWN";

/**
 * Time label (coarse time classification)
 */
export type InteractionTimeLabel =
  | "T_RECENT"
  | "T_MIN"
  | "T_HOUR"
  | "T_OLD"
  | "T_UNKNOWN";

/**
 * Interaction decision
 */
export type InteractionDecision =
  | "INTERACTION_DETECTED"
  | "NO_INTERACTION"
  | "UNKNOWN";

/**
 * Interaction evidence (label-only)
 */
export interface InteractionEvidence {
  kind: "EVID_DECISION" | "EVID_EFFECT" | "EVID_REGRESSION" | "EVID_NONE";
  label: string; // no numbers/tokens
  strength: InteractionStrength;
}

/**
 * Interaction report v1
 */
export interface InteractionReportV1 {
  kind: "INTERACTION_REPORT_V1";
  status: InteractionStatus;

  // Main identity
  primaryProposalId?: string;
  secondaryProposalId?: string;

  // Relationship context
  primaryDecision?: "ADOPT" | "HOLD" | "REJECT" | "UNKNOWN";
  secondaryDecision?: "ADOPT" | "HOLD" | "REJECT" | "UNKNOWN";

  // Interaction analysis
  interaction: InteractionDecision;
  interactionKind: InteractionKind;
  strength: InteractionStrength;

  // Time labels only
  window: InteractionWindowLabel;
  timeLabel: InteractionTimeLabel;

  // Explainability
  evidence: InteractionEvidence[]; // max 3
  warnings: string[];

  ts: number; // Internal storage only
}

/**
 * Fixed detection parameters (constants)
 */
export const INTERACTION_PARAMS = {
  MAX_EVIDENCE: 3,

  // Time windows (minutes/hours)
  WINDOW_TIGHT_MAX_MINUTES: 30,
  WINDOW_NORMAL_MAX_HOURS: 6,
  WINDOW_WIDE_MAX_HOURS: 24,

  // Minimal data requirements
  MIN_DECISIONS_FOR_EVAL: 2,

  // Scoring (internal only, not displayed)
  STRONG_SCORE: 3,
  MEDIUM_SCORE: 2,
  WEAK_SCORE: 1,

  // Risk threshold (internal)
  COUPLING_RISK_SCORE_THRESHOLD: 4,
} as const;
