/**
 * PR175: v1.4 Regression Guard v1 - Detector
 *
 * Purpose:
 *   Detect regressions in patch effectiveness using fixed rules.
 *   Analyzes time-series of PR174 effect reports.
 *
 * Constitutional Constraints:
 *   - Fixed rules: Hardcoded thresholds (no learning)
 *   - READ-ONLY: Observation only
 *   - Defensive: Never throws
 */

import { PatchEffectReportV1 } from "../effect/types";
import {
  RegressionAnalysis,
  RegressionDecision,
  RegressionKind,
  RegressionStrength,
  RegressionWindowLabel,
  RegressionEvidence,
  REGRESSION_RULES,
} from "./types";

/**
 * Detect regression for a single proposal
 *
 * @param proposalId - Proposal ID
 * @param effects - Time-sorted effect reports
 * @returns Regression analysis
 */
export function detectRegressionV1(
  proposalId: string,
  effects: PatchEffectReportV1[]
): RegressionAnalysis {
  const warnings: string[] = [];

  // 1. Check minimum data requirement
  if (effects.length < REGRESSION_RULES.MIN_EFFECTS_FOR_EVAL) {
    return {
      proposalId,
      decision: "REGRESSION_UNKNOWN",
      kind: "REGRESS_UNKNOWN",
      strength: "UNKNOWN",
      windowLabel: "W_UNKNOWN",
      evidence: [],
      warnings: ["WARN_INSUFFICIENT_EFFECTS_FOR_EVAL"],
    };
  }

  // 2. Extract recent window (last N effects)
  const lookback = Math.min(
    effects.length,
    REGRESSION_RULES.STRONG_REGRESS_LOOKBACK
  );
  const recentEffects = effects.slice(-lookback);

  // 3. Extract effect decisions
  const decisions = recentEffects.map((e) => e.effectDecision);

  // 4. Apply detection rules (priority order: first-match-wins)

  // Rule 1: IMPROVED → WORSENED within IMPROVE_TO_WORSE_WITHIN
  const improvedToWorsened = detectImprovedToWorsened(
    effects,
    REGRESSION_RULES.IMPROVE_TO_WORSE_WITHIN
  );
  if (improvedToWorsened) {
    return {
      proposalId,
      decision: "REGRESSION_DETECTED",
      kind: "REGRESS_IMPROVED_TO_WORSENED",
      strength: "STRONG",
      windowLabel: "W_SHORT",
      evidence: [improvedToWorsened],
      warnings,
    };
  }

  // Rule 2: IMPROVED → BLOCK dominance re-emergence
  const blockDominance = detectDominanceReemergence(
    recentEffects,
    "BLOCK"
  );
  if (blockDominance) {
    return {
      proposalId,
      decision: "REGRESSION_DETECTED",
      kind: "REGRESS_IMPROVED_TO_BLOCK_DOMINANT",
      strength: blockDominance.strength,
      windowLabel: "W_MEDIUM",
      evidence: [blockDominance],
      warnings,
    };
  }

  // Rule 3: IMPROVED → STOP dominance re-emergence
  const stopDominance = detectDominanceReemergence(recentEffects, "STOP");
  if (stopDominance) {
    return {
      proposalId,
      decision: "REGRESSION_DETECTED",
      kind: "REGRESS_IMPROVED_TO_STOP_DOMINANT",
      strength: stopDominance.strength,
      windowLabel: "W_MEDIUM",
      evidence: [stopDominance],
      warnings,
    };
  }

  // Rule 4: Category shift worsening
  const categoryShift = detectCategoryShiftWorsened(recentEffects);
  if (categoryShift) {
    return {
      proposalId,
      decision: "REGRESSION_DETECTED",
      kind: "REGRESS_CATEGORY_SHIFT_WORSENED",
      strength: "MEDIUM",
      windowLabel: "W_MEDIUM",
      evidence: [categoryShift],
      warnings,
    };
  }

  // Rule 5: Effect flapping
  const flapping = detectFlapping(decisions, REGRESSION_RULES.FLAP_THRESHOLD);
  if (flapping) {
    return {
      proposalId,
      decision: "REGRESSION_DETECTED",
      kind: "REGRESS_EFFECT_FLAPPING",
      strength: "MEDIUM",
      windowLabel: "W_LONG",
      evidence: [flapping],
      warnings,
    };
  }

  // Rule 6: No regression (recent effects are IMPROVED/NO_CHANGE)
  const lastEffect = recentEffects[recentEffects.length - 1];
  if (
    lastEffect.effectDecision === "EFFECT_IMPROVED" ||
    lastEffect.effectDecision === "EFFECT_NO_CHANGE"
  ) {
    return {
      proposalId,
      decision: "NO_REGRESSION",
      kind: "REGRESS_UNKNOWN",
      strength: "UNKNOWN",
      windowLabel: "W_MEDIUM",
      evidence: [
        {
          kind: "EVID_EFFECT",
          label: `LAST_EFFECT_${lastEffect.effectDecision}`,
          strength: "UNKNOWN",
        },
      ],
      warnings,
    };
  }

  // Rule 7: Unknown (ambiguous data)
  return {
    proposalId,
    decision: "REGRESSION_UNKNOWN",
    kind: "REGRESS_UNKNOWN",
    strength: "UNKNOWN",
    windowLabel: "W_UNKNOWN",
    evidence: [],
    warnings: ["WARN_REGRESSION_AMBIGUOUS"],
  };
}

/**
 * Detect IMPROVED → WORSENED within N effects
 *
 * @param effects - All effects
 * @param within - Max distance
 * @returns Evidence if detected
 */
function detectImprovedToWorsened(
  effects: PatchEffectReportV1[],
  within: number
): RegressionEvidence | null {
  for (let i = 0; i < effects.length; i++) {
    if (effects[i].effectDecision === "EFFECT_IMPROVED") {
      // Check next N effects
      for (let j = i + 1; j <= Math.min(i + within, effects.length - 1); j++) {
        if (effects[j].effectDecision === "EFFECT_WORSENED") {
          return {
            kind: "EVID_EFFECT",
            label: `IMPROVED_AT_${i}_WORSENED_AT_${j}_WITHIN_${j - i}`,
            strength: "STRONG",
          };
        }
      }
    }
  }
  return null;
}

/**
 * Detect dominance re-emergence (BLOCK or STOP)
 *
 * @param effects - Recent effects
 * @param category - "BLOCK" or "STOP"
 * @returns Evidence if detected
 */
function detectDominanceReemergence(
  effects: PatchEffectReportV1[],
  category: "BLOCK" | "STOP"
): RegressionEvidence | null {
  // Look for worsened signals with dominance pattern
  for (const effect of effects) {
    if (effect.effectDecision === "EFFECT_WORSENED") {
      // Check compare signals for dominance
      const dominancePattern =
        category === "BLOCK" ? "BLOCK" : "STOP";

      // Check worsened array for dominance signals
      const hasDominance = effect.compare.worsened.some((signal) =>
        signal.includes(dominancePattern)
      );

      if (hasDominance) {
        // Determine strength based on number of worsened signals
        const strength: RegressionStrength =
          effect.compare.worsened.length >= 3
            ? "STRONG"
            : effect.compare.worsened.length >= 2
            ? "MEDIUM"
            : "WEAK";

        return {
          kind: "EVID_EFFECT",
          label: `${category}_DOMINANCE_REEMERGED`,
          strength,
        };
      }
    }
  }

  return null;
}

/**
 * Detect category shift worsening
 *
 * @param effects - Recent effects
 * @returns Evidence if detected
 */
function detectCategoryShiftWorsened(
  effects: PatchEffectReportV1[]
): RegressionEvidence | null {
  // Look for pattern: improved in one category, worsened in another
  let hasImproved = false;
  let hasWorsened = false;

  for (const effect of effects) {
    if (effect.compare.improved.length > 0) {
      hasImproved = true;
    }
    if (effect.compare.worsened.length > 0) {
      hasWorsened = true;
    }
  }

  if (hasImproved && hasWorsened) {
    return {
      kind: "EVID_EFFECT",
      label: "CATEGORY_SHIFT_MIXED_SIGNALS",
      strength: "MEDIUM",
    };
  }

  return null;
}

/**
 * Detect effect flapping (oscillation)
 *
 * @param decisions - Effect decisions
 * @param threshold - Min oscillations
 * @returns Evidence if detected
 */
function detectFlapping(
  decisions: string[],
  threshold: number
): RegressionEvidence | null {
  let oscillations = 0;

  for (let i = 1; i < decisions.length; i++) {
    const prev = decisions[i - 1];
    const curr = decisions[i];

    // Count transitions between IMPROVED/NO_CHANGE and WORSENED
    const isPositive = (d: string) =>
      d === "EFFECT_IMPROVED" || d === "EFFECT_NO_CHANGE";
    const isNegative = (d: string) => d === "EFFECT_WORSENED";

    if (
      (isPositive(prev) && isNegative(curr)) ||
      (isNegative(prev) && isPositive(curr))
    ) {
      oscillations++;
    }
  }

  if (oscillations >= threshold) {
    return {
      kind: "EVID_EFFECT",
      label: `FLAPPING_DETECTED_OSCILLATIONS_GT_${threshold}`,
      strength: "MEDIUM",
    };
  }

  return null;
}
