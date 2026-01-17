/**
 * PR184: v1.4 Observe Degraded → Safety Tightening Bridge v1 (READ-ONLY)
 *
 * Purpose:
 *   Bridge observeDegraded status from PR183 into execution pipeline.
 *   Tighten safety checks when observation is degraded, WITHOUT adding new STOP conditions.
 *
 * Constitutional Constraints:
 *   - READ-ONLY: No learning, optimization, or prediction
 *   - STOP conditions NOT increased (observeDegraded is NOT a STOP reason)
 *   - Label-only: All adjustments/modes are labels, not numbers (test comparisons OK)
 *   - Never throws: Always returns result
 *   - Double-key maintained: Execution enable = env + policy only
 *
 * Fixed Rules:
 *   - observeDegraded !== true → DEGRADED_NONE
 *   - observeDegraded === true + tier → DEGRADED_LIGHT/MEDIUM/HEAVY
 *   - tier unknown → DEGRADED_UNKNOWN (safe side)
 *
 * Behavior Changes:
 *   - Gate: BLOCK more easily when quote/consistency UNKNOWN (HEAVY/UNKNOWN only)
 *   - Slippage: Add conservative bps based on degrade level
 *   - Quote Consistency: Tighten band (±%) based on degrade level
 */

/**
 * Observe degrade level (label-only)
 */
export type ObserveDegradeLevel =
  | "DEGRADED_NONE"
  | "DEGRADED_LIGHT"
  | "DEGRADED_MEDIUM"
  | "DEGRADED_HEAVY"
  | "DEGRADED_UNKNOWN";

/**
 * Observe degrade adjustments (fixed table)
 */
export interface ObserveDegradeAdjustments {
  // Slippage add (internal numeric only, never displayed as number)
  slippageAddBps: number;

  // Quote freshness mode (label-only)
  quoteFreshnessMode: "STRICT" | "MEDIUM" | "NORMAL";

  // Consistency band mode (label-only)
  consistencyBandMode: "TIGHTER" | "TIGHT" | "NORMAL";

  // Gate sensitivity mode (label-only)
  gateSensitivityMode: "STRICT" | "NORMAL";
}

/**
 * Derive observe degrade level from observeState (PR183)
 *
 * Fixed rules:
 *   - observeDegraded !== true → DEGRADED_NONE
 *   - observeDegraded === true:
 *     - tier = TIER_2S → DEGRADED_LIGHT
 *     - tier = TIER_5S → DEGRADED_MEDIUM
 *     - tier = TIER_10S → DEGRADED_HEAVY
 *     - tier unknown → DEGRADED_UNKNOWN (safe side)
 *
 * @param observeState - Observe state from PR181+PR183 (optional)
 * @returns Observe degrade level
 *
 * Defensive: Never throws, returns DEGRADED_UNKNOWN on error.
 */
export function deriveObserveDegradeLevel(
  observeState?: any
): ObserveDegradeLevel {
  try {
    // No observe state → UNKNOWN (safe side)
    if (!observeState) {
      return "DEGRADED_UNKNOWN";
    }

    // observeDegraded field check
    const observeDegraded = observeState.observeDegraded;
    const observeTier = observeState.observeTier;

    // observeDegraded !== "YES" → NONE
    if (observeDegraded !== "YES") {
      return "DEGRADED_NONE";
    }

    // observeDegraded === "YES" → check tier
    if (observeTier === "TIER_2S") {
      return "DEGRADED_LIGHT";
    } else if (observeTier === "TIER_5S") {
      return "DEGRADED_MEDIUM";
    } else if (observeTier === "TIER_10S") {
      return "DEGRADED_HEAVY";
    }

    // Tier unknown → UNKNOWN (safe side)
    return "DEGRADED_UNKNOWN";
  } catch (error) {
    // Defensive: Return UNKNOWN on error
    return "DEGRADED_UNKNOWN";
  }
}

/**
 * Get observe degrade adjustments (fixed table)
 *
 * Fixed rules:
 *   - NONE: +0 bps, NORMAL mode
 *   - LIGHT: +50 bps, MEDIUM freshness, TIGHT band, NORMAL gate
 *   - MEDIUM: +150 bps, STRICT freshness, TIGHTER band, NORMAL gate
 *   - HEAVY: +300 bps, STRICT freshness, TIGHTER band, STRICT gate
 *   - UNKNOWN: +300 bps (safe side), STRICT freshness, TIGHTER band, STRICT gate
 *
 * @param level - Observe degrade level
 * @returns Observe degrade adjustments
 *
 * Defensive: Never throws.
 */
export function getObserveDegradeAdjustments(
  level: ObserveDegradeLevel
): ObserveDegradeAdjustments {
  try {
    switch (level) {
      case "DEGRADED_NONE":
        return {
          slippageAddBps: 0,
          quoteFreshnessMode: "NORMAL",
          consistencyBandMode: "NORMAL",
          gateSensitivityMode: "NORMAL",
        };

      case "DEGRADED_LIGHT":
        return {
          slippageAddBps: 50,
          quoteFreshnessMode: "MEDIUM",
          consistencyBandMode: "TIGHT",
          gateSensitivityMode: "NORMAL",
        };

      case "DEGRADED_MEDIUM":
        return {
          slippageAddBps: 150,
          quoteFreshnessMode: "STRICT",
          consistencyBandMode: "TIGHTER",
          gateSensitivityMode: "NORMAL",
        };

      case "DEGRADED_HEAVY":
        return {
          slippageAddBps: 300,
          quoteFreshnessMode: "STRICT",
          consistencyBandMode: "TIGHTER",
          gateSensitivityMode: "STRICT",
        };

      case "DEGRADED_UNKNOWN":
        return {
          slippageAddBps: 300,
          quoteFreshnessMode: "STRICT",
          consistencyBandMode: "TIGHTER",
          gateSensitivityMode: "STRICT",
        };

      default:
        // Defensive: Unknown level → treat as UNKNOWN (safe side)
        return {
          slippageAddBps: 300,
          quoteFreshnessMode: "STRICT",
          consistencyBandMode: "TIGHTER",
          gateSensitivityMode: "STRICT",
        };
    }
  } catch (error) {
    // Defensive: Return safest settings on error
    return {
      slippageAddBps: 300,
      quoteFreshnessMode: "STRICT",
      consistencyBandMode: "TIGHTER",
      gateSensitivityMode: "STRICT",
    };
  }
}
