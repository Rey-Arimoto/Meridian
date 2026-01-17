/**
 * PR157: v1.4 Slippage Management (READ-ONLY)
 * PR184: Updated with observe degrade adjustments
 *
 * Purpose:
 *   Compute slippage tolerance in basis points with fixed rules.
 *   PR184: Add conservative slippage based on observe degrade level.
 *
 * Constitutional Constraints:
 *   - READ-ONLY: No learning, optimization, or prediction
 *   - Fixed rules: Slippage = base + shock adjustment + degrade adjustment
 *   - Hard cap: 1500 bps (15%) maximum
 *   - Label-only output: No numbers in warnings/reasons
 */

import { ObserveDegradeLevel, getObserveDegradeAdjustments } from "./observeDegrade";

/**
 * Slippage parameters (constitutional constants)
 */
const SLIPPAGE_PARAMS = {
  // Base slippage (normal conditions)
  BASE_BPS: 50, // 0.50%

  // Shock phase adjustments
  SHOCK_ADD_BPS: 100, // +1.00% for shock phases

  // Hard cap (never exceed this)
  HARD_CAP_BPS: 1500, // 15.00%
};

/**
 * Compute slippage tolerance in basis points
 *
 * Fixed rules:
 *   - Base: 50 bps
 *   - Shock phase: +100 bps
 *   - Degrade level (PR184):
 *     - NONE: +0 bps
 *     - LIGHT: +50 bps
 *     - MEDIUM: +150 bps
 *     - HEAVY/UNKNOWN: +300 bps
 *   - Hard cap: 1500 bps
 *
 * @param args - Arguments
 * @param args.phaseLabel - Phase label (optional)
 * @param args.observeDegradeLevel - Observe degrade level (optional, PR184)
 * @returns Slippage in basis points
 *
 * Defensive: Never throws, returns capped value.
 */
export function computeSlippageBps(args: {
  phaseLabel?: string;
  observeDegradeLevel?: ObserveDegradeLevel;
}): number {
  try {
    let slippageBps = SLIPPAGE_PARAMS.BASE_BPS;

    // Add shock adjustment
    const isShockPhase =
      args.phaseLabel === "PHASE_PRE_SHOCK" ||
      args.phaseLabel === "PHASE_UP_SHOCK" ||
      args.phaseLabel === "PHASE_DOWN_SHOCK";

    if (isShockPhase) {
      slippageBps += SLIPPAGE_PARAMS.SHOCK_ADD_BPS;
    }

    // PR184: Add degrade adjustment
    if (args.observeDegradeLevel) {
      const adjustments = getObserveDegradeAdjustments(args.observeDegradeLevel);
      slippageBps += adjustments.slippageAddBps;
    }

    // Apply hard cap
    if (slippageBps > SLIPPAGE_PARAMS.HARD_CAP_BPS) {
      slippageBps = SLIPPAGE_PARAMS.HARD_CAP_BPS;
    }

    return slippageBps;
  } catch (error) {
    // Defensive: Return hard cap on error (safest)
    return SLIPPAGE_PARAMS.HARD_CAP_BPS;
  }
}

/**
 * Get slippage label (for telemetry/logging)
 *
 * @param slippageBps - Slippage in basis points
 * @returns Slippage label (label-only)
 */
export function getSlippageLabel(slippageBps: number): string {
  if (slippageBps <= 50) {
    return "SLIPPAGE_NORMAL";
  } else if (slippageBps <= 150) {
    return "SLIPPAGE_ELEVATED";
  } else if (slippageBps <= 500) {
    return "SLIPPAGE_HIGH";
  } else {
    return "SLIPPAGE_VERY_HIGH";
  }
}
