/**
 * PR157: v1.4 Slippage + minOut Guard (READ-ONLY)
 *
 * Purpose:
 *   Calculate slippage tolerance and minOut using fixed rules.
 *   Conservative approach: prefer execution with thick slippage over blocking.
 *
 * Constitutional Constraints:
 *   - Fixed rules: No learning, no optimization
 *   - Never throws: Always returns calculation result
 *   - Label-only output: No numbers in warnings/checks
 *   - Numeric values: Internal only (slippageBps, minOut)
 *   - Conservative: When uncertain, increase slippage (don't block unnecessarily)
 *   - Hard limit: maxSlippageBps = 1500 (15%)
 */

import { TemplateId } from "./templates";
import { ImpactLabel } from "./quotes";

/**
 * Slippage calculation input
 */
export interface SlippageInput {
  // Template ID (risk level)
  templateId: TemplateId;

  // Shock phase (from Python PR149)
  shockPhase?: string;

  // Stress level (from Python PR146/150)
  stress?: string;

  // Impact label from quote
  impactLabel: ImpactLabel;

  // Venue
  venue: "CETUS" | "DEEPBOOK";

  // Amount out from quote (internal numeric)
  amountOut: number;
}

/**
 * Slippage calculation result
 */
export interface SlippageResult {
  // Calculated slippage in basis points (internal numeric)
  slippageBps: number;

  // Calculated minOut (internal numeric, undefined if cannot calculate)
  minOut?: number;

  // Safety checks performed (label-only, no numbers)
  checks: string[];

  // Warnings (label-only, no numbers)
  warnings: string[];

  // Block reasons (if slippage exceeds limit)
  blockReasons: string[];
}

/**
 * Fixed slippage thresholds (constitutional constants)
 */
const SLIPPAGE_THRESHOLDS = {
  // Base slippage by template (basis points)
  TEMPLATE_BASE: {
    "TPL_RISK_90": 150,
    "TPL_RISK_50": 100,
    "TPL_RISK_20": 75,
    "TPL_RISK_0": 50,
    "TPL_UNKNOWN": 100, // Safe default
  } as Record<string, number>,

  // Shock phase adjustments (add to base)
  SHOCK_ADJUST: {
    PHASE_UP_SHOCK: 150,
    PHASE_DOWN_SHOCK: 150,
    PHASE_PRE_SHOCK: 100,
    PHASE_UP_REVERSAL: 200,
    PHASE_DOWN_REVERSAL: 200,
    PHASE_NORMAL: 0,
    PHASE_RECOVERY: 0,
  } as Record<string, number>,

  // Stress adjustments (add to base)
  STRESS_ADJUST: {
    STRESS_STRESSED: 200,
    STRESS_TENSE: 100,
    STRESS_CALM: 0,
  } as Record<string, number>,

  // Impact adjustments (add to base)
  IMPACT_ADJUST: {
    IMPACT_HIGH: 200,
    IMPACT_MED: 100,
    IMPACT_LOW: 0,
    IMPACT_UNKNOWN: 200, // Conservative
  } as Record<string, number>,

  // Venue adjustments (add to base)
  VENUE_ADJUST: {
    CETUS: 50, // AMM slips more
    DEEPBOOK: 0,
  } as Record<string, number>,

  // Hard limit (15%)
  MAX_SLIPPAGE_BPS: 1500,
};

/**
 * Calculate slippage tolerance and minOut (main API)
 *
 * @param input - Slippage input
 * @returns Slippage calculation result
 *
 * Fixed rules (never throws):
 *   1. Calculate base slippage from template
 *   2. Add shock phase adjustment
 *   3. Add stress adjustment
 *   4. Add impact adjustment
 *   5. Add venue adjustment
 *   6. Cap at MAX_SLIPPAGE_BPS
 *   7. If exceeds cap → BLOCK_SLIPPAGE_TOO_HIGH
 *   8. Calculate minOut = amountOut * (1 - slippageBps/10000)
 *   9. If amountOut invalid → minOut undefined + BLOCK_MINOUT_UNAVAILABLE
 */
export function calculateSlippageAndMinOut(
  input: SlippageInput
): SlippageResult {
  const checks: string[] = [];
  const warnings: string[] = [];
  const blockReasons: string[] = [];

  try {
    // Step 1: Base slippage from template
    const templateKey = String(input.templateId);
    let slippageBps =
      SLIPPAGE_THRESHOLDS.TEMPLATE_BASE[templateKey] ??
      SLIPPAGE_THRESHOLDS.TEMPLATE_BASE["TPL_UNKNOWN"];

    checks.push("CHECK_SLIPPAGE_BASE_CALCULATED");

    // Step 2: Shock phase adjustment
    if (input.shockPhase) {
      const shockAdjust =
        SLIPPAGE_THRESHOLDS.SHOCK_ADJUST[input.shockPhase] ?? 0;
      slippageBps += shockAdjust;

      if (shockAdjust > 0) {
        checks.push("CHECK_SLIPPAGE_SHOCK_ADJUSTED");
      }
    }

    // Step 3: Stress adjustment
    if (input.stress) {
      const stressAdjust =
        SLIPPAGE_THRESHOLDS.STRESS_ADJUST[input.stress] ?? 0;
      slippageBps += stressAdjust;

      if (stressAdjust > 0) {
        checks.push("CHECK_SLIPPAGE_STRESS_ADJUSTED");
      }

      // UNKNOWN stress → warning (calculation still possible)
      if (
        input.stress === "STRESS_UNKNOWN" ||
        input.stress === "UNKNOWN" ||
        !SLIPPAGE_THRESHOLDS.STRESS_ADJUST[input.stress]
      ) {
        warnings.push("WARN_STRESS_UNKNOWN");
      }
    }

    // Step 4: Impact adjustment
    const impactAdjust =
      SLIPPAGE_THRESHOLDS.IMPACT_ADJUST[input.impactLabel] ?? 200;
    slippageBps += impactAdjust;

    if (impactAdjust > 0) {
      checks.push("CHECK_SLIPPAGE_IMPACT_ADJUSTED");
    }

    // Step 5: Venue adjustment
    const venueAdjust = SLIPPAGE_THRESHOLDS.VENUE_ADJUST[input.venue] ?? 0;
    slippageBps += venueAdjust;

    if (venueAdjust > 0) {
      checks.push("CHECK_SLIPPAGE_VENUE_ADJUSTED");
    }

    // Step 6: Cap at MAX_SLIPPAGE_BPS
    if (slippageBps > SLIPPAGE_THRESHOLDS.MAX_SLIPPAGE_BPS) {
      blockReasons.push("BLOCK_SLIPPAGE_TOO_HIGH");
      warnings.push("WARN_SLIPPAGE_CAP_EXCEEDED");

      // Still return capped value for debugging
      slippageBps = SLIPPAGE_THRESHOLDS.MAX_SLIPPAGE_BPS;
    }

    // Step 7: Calculate minOut
    let minOut: number | undefined;

    if (
      input.amountOut &&
      typeof input.amountOut === "number" &&
      input.amountOut > 0 &&
      !isNaN(input.amountOut)
    ) {
      // minOut = amountOut * (1 - slippageBps/10000)
      const slippageFactor = 1 - slippageBps / 10000;
      minOut = Math.floor(input.amountOut * slippageFactor); // Floor for safety

      checks.push("CHECK_MINOUT_CALCULATED");
    } else {
      // amountOut invalid → cannot calculate minOut
      blockReasons.push("BLOCK_MINOUT_UNAVAILABLE");
      warnings.push("WARN_AMOUNTOUT_INVALID");
    }

    return {
      slippageBps,
      minOut,
      checks,
      warnings,
      blockReasons,
    };
  } catch (error) {
    // Defensive: Never throw, return error state
    return {
      slippageBps: SLIPPAGE_THRESHOLDS.MAX_SLIPPAGE_BPS, // Safe default
      minOut: undefined,
      checks: [],
      warnings: ["WARN_SLIPPAGE_CALCULATION_ERROR"],
      blockReasons: ["BLOCK_SLIPPAGE_CALCULATION_ERROR"],
    };
  }
}

/**
 * Get slippage summary (for logging/debugging)
 *
 * @param result - Slippage result
 * @returns Summary string (label-only)
 */
export function getSlippageSummary(result: SlippageResult): string {
  if (result.blockReasons.length > 0) {
    return `SLIPPAGE_BLOCKED_${result.blockReasons[0]}`;
  }

  if (result.minOut !== undefined) {
    return "SLIPPAGE_MINOUT_OK";
  }

  return "SLIPPAGE_MINOUT_UNAVAILABLE";
}
