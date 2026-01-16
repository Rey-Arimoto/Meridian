/**
 * PR177: v1.4 Pre-Adoption Risk Overlay v1 - Types
 *
 * Purpose:
 *   Inject known risk information (from PR175 regressions and PR176 interactions)
 *   into PR171 preview and PR172 review flows.
 *
 * Constitutional Constraints:
 *   - READ-ONLY: Observation only (no automatic adoption/revert)
 *   - Fixed rules: Hardcoded risk assessment logic (no learning)
 *   - Label-only: Normal mode uses labels (no counts/scores)
 *   - Defensive: Never throws, handles missing data gracefully
 *   - No modification: Reads existing logs, doesn't append/modify them
 */

/**
 * Overlay status
 */
export type OverlayStatus = "AVAILABLE" | "PARTIAL" | "ERROR";

/**
 * Overlay risk level
 */
export type OverlayRiskLevel =
  | "RISK_HIGH"
  | "RISK_MEDIUM"
  | "RISK_LOW"
  | "RISK_UNKNOWN";

/**
 * Overlay risk kind
 */
export type OverlayRiskKind =
  | "RISK_REGRESSION_HISTORY"
  | "RISK_INTERACTION_COUPLING"
  | "RISK_EVIDENCE_WEAK"
  | "RISK_UNKNOWN";

/**
 * Overlay evidence (label-only)
 */
export interface OverlayEvidence {
  kind: "EVID_REGRESSION" | "EVID_INTERACTION" | "EVID_NONE";
  label: string; // Label-only (no numbers/tokens)
  strength: "STRONG" | "MEDIUM" | "WEAK" | "UNKNOWN";
}

/**
 * Risk overlay v1
 */
export interface RiskOverlayV1 {
  status: OverlayStatus;

  proposalId: string;
  priority?: "P0" | "P1" | "P2" | "UNKNOWN";

  riskLevel: OverlayRiskLevel;
  risks: { kind: OverlayRiskKind; label: string }[]; // Max 5, label-only
  evidence: OverlayEvidence[]; // Max 3

  warnings: string[]; // Label-only
}

/**
 * Fixed overlay parameters (constants)
 */
export const OVERLAY_PARAMS = {
  MAX_RISKS: 5,
  MAX_EVIDENCE: 3,
  RECENT_TAIL: 100, // How many recent records to read
} as const;
