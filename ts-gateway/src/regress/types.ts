/**
 * PR175: v1.4 Regression Guard v1 - Types
 *
 * Purpose:
 *   Monitor patch effectiveness persistence - detect when improvements regress.
 *   Reads PR174 effects.log to identify patterns like IMPROVED→WORSENED.
 *
 * Constitutional Constraints:
 *   - READ-ONLY: Observation only (no automatic revert)
 *   - Fixed rules: Hardcoded thresholds and detection logic
 *   - Label-only: Normal mode uses labels (no counts)
 *   - Defensive: Never throws, handles missing data gracefully
 *   - Append-only: Audit trail in ~/.meridian/regressions.log
 */

import { PatchEffectReportV1 } from "../effect/types";
import { DecisionAckRecordV1 } from "../decision/types";

/**
 * Regression status
 */
export type RegressionStatus = "AVAILABLE" | "PARTIAL" | "ERROR";

/**
 * Regression kind (type of regression detected)
 */
export type RegressionKind =
  | "REGRESS_IMPROVED_TO_WORSENED"
  | "REGRESS_IMPROVED_TO_BLOCK_DOMINANT"
  | "REGRESS_IMPROVED_TO_STOP_DOMINANT"
  | "REGRESS_CATEGORY_SHIFT_WORSENED"
  | "REGRESS_EFFECT_FLAPPING"
  | "REGRESS_UNKNOWN";

/**
 * Regression strength
 */
export type RegressionStrength = "STRONG" | "MEDIUM" | "WEAK" | "UNKNOWN";

/**
 * Regression window label (time period)
 */
export type RegressionWindowLabel =
  | "W_SHORT"
  | "W_MEDIUM"
  | "W_LONG"
  | "W_UNKNOWN";

/**
 * Regression decision
 */
export type RegressionDecision =
  | "REGRESSION_DETECTED"
  | "NO_REGRESSION"
  | "REGRESSION_UNKNOWN";

/**
 * Regression evidence (label-only)
 */
export interface RegressionEvidence {
  kind: "EVID_EFFECT" | "EVID_DECISION" | "EVID_NONE";
  label: string; // no numbers/tokens
  strength: RegressionStrength;
}

/**
 * Regression analysis for a single proposal
 */
export interface RegressionAnalysis {
  proposalId: string;
  decision: RegressionDecision;
  kind: RegressionKind;
  strength: RegressionStrength;
  windowLabel: RegressionWindowLabel;
  evidence: RegressionEvidence[];
  warnings: string[];
}

/**
 * Regression report v1
 */
export interface RegressionReportV1 {
  kind: "REGRESSION_REPORT_V1";
  status: RegressionStatus;
  analysis: RegressionAnalysis;
  ts: number;
  warnings: string[];
}

/**
 * Fixed detection rules (constants)
 */
export const REGRESSION_RULES = {
  MIN_EFFECTS_FOR_EVAL: 3,
  STRONG_REGRESS_LOOKBACK: 5,
  FLAP_THRESHOLD: 3,
  DOMINANCE_THRESHOLD: 0.5,
  IMPROVE_TO_WORSE_WITHIN: 2,
} as const;
