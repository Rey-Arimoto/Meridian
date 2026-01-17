/**
 * PR157: v1.4 Quote Consistency Checks (READ-ONLY)
 * PR184: Updated with observe degrade band tightening
 *
 * Purpose:
 *   Check quote consistency with oracle price using fixed tolerance bands.
 *   PR184: Tighten band when observation is degraded.
 *
 * Constitutional Constraints:
 *   - READ-ONLY: No learning, optimization, or prediction
 *   - Fixed rules: Tolerance band depends on degrade level
 *   - Label-only output: No numbers in warnings/reasons
 */

import { ObserveDegradeLevel, getObserveDegradeAdjustments } from "./observeDegrade";

/**
 * Consistency parameters (constitutional constants)
 */
const CONSISTENCY_PARAMS = {
  // Base tolerance band (±%)
  BASE_BAND_PCT: 5.0, // ±5%

  // PR184: Degrade level bands
  LIGHT_BAND_PCT: 4.0, // ±4%
  MEDIUM_BAND_PCT: 3.0, // ±3%
  HEAVY_BAND_PCT: 2.0, // ±2%
};

/**
 * Quote consistency result
 */
export interface QuoteConsistencyResult {
  // Status
  status: "CONSISTENT" | "INCONSISTENT" | "UNKNOWN";

  // Reasons (label-only)
  reasons: string[];

  // Warnings (label-only)
  warnings: string[];
}

/**
 * Get tolerance band percentage based on degrade level
 *
 * Fixed rules (PR184):
 *   - NONE: ±5%
 *   - LIGHT: ±4%
 *   - MEDIUM: ±3%
 *   - HEAVY/UNKNOWN: ±2%
 *
 * @param observeDegradeLevel - Observe degrade level (optional)
 * @returns Tolerance band percentage
 */
export function getToleranceBandPct(
  observeDegradeLevel?: ObserveDegradeLevel
): number {
  try {
    if (!observeDegradeLevel || observeDegradeLevel === "DEGRADED_NONE") {
      return CONSISTENCY_PARAMS.BASE_BAND_PCT;
    }

    const adjustments = getObserveDegradeAdjustments(observeDegradeLevel);

    switch (adjustments.consistencyBandMode) {
      case "NORMAL":
        return CONSISTENCY_PARAMS.BASE_BAND_PCT;
      case "TIGHT":
        return CONSISTENCY_PARAMS.LIGHT_BAND_PCT;
      case "TIGHTER":
        return observeDegradeLevel === "DEGRADED_MEDIUM"
          ? CONSISTENCY_PARAMS.MEDIUM_BAND_PCT
          : CONSISTENCY_PARAMS.HEAVY_BAND_PCT;
      default:
        return CONSISTENCY_PARAMS.BASE_BAND_PCT;
    }
  } catch (error) {
    // Defensive: Return safest (tightest) band on error
    return CONSISTENCY_PARAMS.HEAVY_BAND_PCT;
  }
}

/**
 * Check quote consistency with oracle price
 *
 * Fixed rules:
 *   - Quote price must be within ±X% of oracle price
 *   - X depends on observe degrade level (PR184)
 *   - Missing quote or oracle → UNKNOWN
 *
 * @param args - Arguments
 * @param args.quotePrice - Quote price (optional)
 * @param args.oraclePrice - Oracle price (optional)
 * @param args.observeDegradeLevel - Observe degrade level (optional, PR184)
 * @returns Quote consistency result
 *
 * Defensive: Never throws, returns result.
 */
export function checkQuoteConsistency(args: {
  quotePrice?: number;
  oraclePrice?: number;
  observeDegradeLevel?: ObserveDegradeLevel;
}): QuoteConsistencyResult {
  const reasons: string[] = [];
  const warnings: string[] = [];

  try {
    // Missing quote or oracle → UNKNOWN
    if (
      args.quotePrice === undefined ||
      args.quotePrice === null ||
      args.oraclePrice === undefined ||
      args.oraclePrice === null
    ) {
      reasons.push("REASON_QUOTE_OR_ORACLE_MISSING");
      return { status: "UNKNOWN", reasons, warnings };
    }

    // Get tolerance band
    const bandPct = getToleranceBandPct(args.observeDegradeLevel);
    const lowerBound = args.oraclePrice * (1 - bandPct / 100);
    const upperBound = args.oraclePrice * (1 + bandPct / 100);

    // Check consistency
    if (args.quotePrice < lowerBound || args.quotePrice > upperBound) {
      reasons.push("REASON_QUOTE_INCONSISTENT_WITH_ORACLE");
      return { status: "INCONSISTENT", reasons, warnings };
    }

    // Consistent
    reasons.push("REASON_QUOTE_CONSISTENT");
    return { status: "CONSISTENT", reasons, warnings };
  } catch (error) {
    // Defensive: Return UNKNOWN on error
    reasons.push("REASON_CONSISTENCY_CHECK_ERROR");
    return { status: "UNKNOWN", reasons, warnings };
  }
}
