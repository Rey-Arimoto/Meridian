/**
 * PR157: v1.4 Slippage Management (READ-ONLY)
 * PR184: Updated with observe degrade adjustments
 * PR185: Restored template-based slippage calculation
 *
 * Purpose:
 *   Compute slippage tolerance in basis points with fixed rules.
 *   PR157: Template-based base + phase/stress/impact/venue adjustments.
 *   PR184: Add conservative slippage based on observe degrade level.
 *   PR185: Restore PR157 tables while maintaining PR184 degrade adjustment.
 *
 * Constitutional Constraints:
 *   - READ-ONLY: No learning, optimization, or prediction
 *   - Fixed rules: Slippage = baseByTemplate + phaseAdj + stressAdj + impactAdj + venueAdj + degradeAdj
 *   - Hard cap: 1500 bps (15%) maximum
 *   - Label-only output: No numbers in warnings/reasons
 */

import { ObserveDegradeLevel, getObserveDegradeAdjustments } from "./observeDegrade";

/**
 * Slippage parameters (constitutional constants - PR157/PR185)
 */
const SLIPPAGE_PARAMS = {
  // Template-based base slippage (PR157/PR185)
  BASE_BY_TEMPLATE: {
    TPL_RISK_90: 150,
    TPL_RISK_50: 100,
    TPL_RISK_20: 75,
    TPL_RISK_0: 50,
    UNKNOWN: 200, // Safe side
  },

  // Phase adjustments (PR157/PR185)
  PHASE_ADJ: {
    PHASE_UP_SHOCK: 150,
    PHASE_DOWN_SHOCK: 150,
    PHASE_PRE_SHOCK: 100,
    PHASE_UP_REVERSAL: 200,
    PHASE_DOWN_REVERSAL: 200,
    DEFAULT: 0,
  },

  // Stress adjustments (PR157/PR185)
  STRESS_ADJ: {
    STRESS_STRESSED: 200,
    STRESS_TENSE: 100,
    DEFAULT: 0,
  },

  // Impact adjustments (PR157/PR185)
  IMPACT_ADJ: {
    IMPACT_HIGH: 200,
    IMPACT_MEDIUM: 100,
    IMPACT_UNKNOWN: 200, // Safe side
    DEFAULT: 0,
  },

  // Venue adjustments (PR157/PR185)
  VENUE_ADJ: {
    CETUS: 50,
    DEEPBOOK: 0,
    DEFAULT: 0,
  },

  // Hard cap (never exceed this)
  HARD_CAP_BPS: 1500, // 15.00%
};

/**
 * Compute slippage tolerance in basis points
 *
 * Fixed rules (PR157 + PR184 + PR185):
 *   - Base by template: TPL_RISK_90(150) / TPL_RISK_50(100) / TPL_RISK_20(75) / TPL_RISK_0(50) / unknown(200)
 *   - Phase adjustment: SHOCK(+150) / PRE_SHOCK(+100) / REVERSAL(+200) / other(+0)
 *   - Stress adjustment: STRESSED(+200) / TENSE(+100) / other(+0)
 *   - Impact adjustment: HIGH(+200) / MEDIUM(+100) / UNKNOWN(+200) / other(+0)
 *   - Venue adjustment: CETUS(+50) / DEEPBOOK(+0) / other(+0)
 *   - Degrade adjustment (PR184): NONE(+0) / LIGHT(+50) / MEDIUM(+150) / HEAVY/UNKNOWN(+300)
 *   - Hard cap: 1500 bps
 *
 * @param args - Arguments
 * @param args.templateId - Template ID (optional, PR157/PR185)
 * @param args.phaseLabel - Phase label (optional, PR157/PR185)
 * @param args.stressLabel - Stress label (optional, PR157/PR185)
 * @param args.impactLabel - Impact label (optional, PR157/PR185)
 * @param args.venue - Venue (optional, PR157/PR185)
 * @param args.observeDegradeLevel - Observe degrade level (optional, PR184)
 * @returns Slippage in basis points
 *
 * Defensive: Never throws, returns capped value.
 */
export function computeSlippageBps(args: {
  templateId?: string;
  phaseLabel?: string;
  stressLabel?: string;
  impactLabel?: string;
  venue?: string;
  observeDegradeLevel?: ObserveDegradeLevel;
}): number {
  try {
    // 1. Base by template (PR157/PR185)
    let slippageBps = 0;
    if (args.templateId) {
      const tpl = args.templateId as keyof typeof SLIPPAGE_PARAMS.BASE_BY_TEMPLATE;
      slippageBps = SLIPPAGE_PARAMS.BASE_BY_TEMPLATE[tpl] || SLIPPAGE_PARAMS.BASE_BY_TEMPLATE.UNKNOWN;
    } else {
      // No template → use UNKNOWN (safe side)
      slippageBps = SLIPPAGE_PARAMS.BASE_BY_TEMPLATE.UNKNOWN;
    }

    // 2. Phase adjustment (PR157/PR185)
    if (args.phaseLabel) {
      const phase = args.phaseLabel as keyof typeof SLIPPAGE_PARAMS.PHASE_ADJ;
      slippageBps += SLIPPAGE_PARAMS.PHASE_ADJ[phase] || SLIPPAGE_PARAMS.PHASE_ADJ.DEFAULT;
    }

    // 3. Stress adjustment (PR157/PR185)
    if (args.stressLabel) {
      const stress = args.stressLabel as keyof typeof SLIPPAGE_PARAMS.STRESS_ADJ;
      slippageBps += SLIPPAGE_PARAMS.STRESS_ADJ[stress] || SLIPPAGE_PARAMS.STRESS_ADJ.DEFAULT;
    }

    // 4. Impact adjustment (PR157/PR185)
    if (args.impactLabel) {
      const impact = args.impactLabel as keyof typeof SLIPPAGE_PARAMS.IMPACT_ADJ;
      slippageBps += SLIPPAGE_PARAMS.IMPACT_ADJ[impact] || SLIPPAGE_PARAMS.IMPACT_ADJ.DEFAULT;
    }

    // 5. Venue adjustment (PR157/PR185)
    if (args.venue) {
      const venue = args.venue as keyof typeof SLIPPAGE_PARAMS.VENUE_ADJ;
      slippageBps += SLIPPAGE_PARAMS.VENUE_ADJ[venue] || SLIPPAGE_PARAMS.VENUE_ADJ.DEFAULT;
    }

    // 6. PR184: Add degrade adjustment
    if (args.observeDegradeLevel) {
      const adjustments = getObserveDegradeAdjustments(args.observeDegradeLevel);
      slippageBps += adjustments.slippageAddBps;
    }

    // 7. Apply hard cap
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
