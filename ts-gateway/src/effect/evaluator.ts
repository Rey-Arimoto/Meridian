/**
 * PR174: v1.4 Patch Effectiveness Tracker v1 - Evaluator
 *
 * Purpose:
 *   Evaluate patch effectiveness by comparing Before/After windows.
 *   Uses fixed thresholds (10% point change) to determine improvement/worsening.
 *
 * Constitutional Constraints:
 *   - READ-ONLY: Evaluation only (no automatic adoption)
 *   - Fixed rules: Fixed thresholds (no learning/optimization)
 *   - Defensive: Never throws, handles missing data gracefully
 */

import {
  EffectWindowSummary,
  EffectDecision,
  EffectCompareSignals,
} from "./types";

/**
 * Fixed threshold for significant change (10% points)
 */
const SIGNIFICANT_CHANGE_THRESHOLD = 0.1;

/**
 * Evaluate Effect Result
 */
export interface EvaluateEffectResult {
  /**
   * Overall effect decision
   */
  decision: EffectDecision;

  /**
   * Compare signals (label-only)
   */
  compare: EffectCompareSignals;

  /**
   * Rationale (label-only)
   */
  rationale: string[];

  /**
   * Warnings (label-only)
   */
  warnings: string[];
}

/**
 * Evaluate effect v1
 *
 * Compares Before and After windows to determine effectiveness.
 *
 * Fixed thresholds:
 * - 10% point decrease in blockRate → IMPROVED_BLOCK_RATE
 * - 10% point decrease in stopRate → IMPROVED_STOP_RATE
 * - 10% point increase in passRate → IMPROVED_PASS_RATE
 * - Confusion signals removed → IMPROVED_CONFUSION_RESOLVED
 * - Opposite changes → WORSENED
 *
 * Decision priority:
 * 1. No afterShort → EFFECT_UNKNOWN
 * 2. Improved only (no worsening) → EFFECT_IMPROVED
 * 3. Worsened only (no improvement) → EFFECT_WORSENED
 * 4. Both improved and worsened → EFFECT_MIXED
 * 5. No significant change → EFFECT_NO_CHANGE
 *
 * @param before - Before window summary
 * @param afterShort - Short-term after window summary
 * @param afterMedium - Medium-term after window summary (optional)
 * @param afterLong - Long-term after window summary (optional)
 * @returns Evaluation result
 */
export function evaluateEffectV1(
  before: EffectWindowSummary,
  afterShort: EffectWindowSummary,
  afterMedium?: EffectWindowSummary,
  afterLong?: EffectWindowSummary
): EvaluateEffectResult {
  const warnings: string[] = [];
  const rationale: string[] = [];
  const improved: string[] = [];
  const worsened: string[] = [];
  const unchanged: string[] = [];
  const unavailable: string[] = [];

  try {
    // 1. Check if afterShort is available
    if (afterShort.status === "ERROR" || afterShort.counts.nSnapshots === 0) {
      warnings.push("WARN_AFTER_SHORT_UNAVAILABLE");
      rationale.push("REASON_AFTER_SHORT_UNAVAILABLE");

      return {
        decision: "EFFECT_UNKNOWN",
        compare: { improved, worsened, unchanged, unavailable },
        rationale,
        warnings,
      };
    }

    // 2. Compare blockRate
    const beforeBlockRate = before.rates.blockRate;
    const afterBlockRate = afterShort.rates.blockRate;

    if (beforeBlockRate !== undefined && afterBlockRate !== undefined) {
      const blockRateChange = afterBlockRate - beforeBlockRate;

      if (blockRateChange <= -SIGNIFICANT_CHANGE_THRESHOLD) {
        improved.push("IMPROVED_BLOCK_RATE");
        rationale.push("REASON_BLOCK_RATE_DECREASED");
      } else if (blockRateChange >= SIGNIFICANT_CHANGE_THRESHOLD) {
        worsened.push("WORSENED_BLOCK_RATE");
        rationale.push("REASON_BLOCK_RATE_INCREASED");
      } else {
        unchanged.push("UNCHANGED_BLOCK_RATE");
      }
    } else {
      unavailable.push("UNAVAILABLE_BLOCK_RATE");
    }

    // 3. Compare stopRate
    const beforeStopRate = before.rates.stopRate;
    const afterStopRate = afterShort.rates.stopRate;

    if (beforeStopRate !== undefined && afterStopRate !== undefined) {
      const stopRateChange = afterStopRate - beforeStopRate;

      if (stopRateChange <= -SIGNIFICANT_CHANGE_THRESHOLD) {
        improved.push("IMPROVED_STOP_RATE");
        rationale.push("REASON_STOP_RATE_DECREASED");
      } else if (stopRateChange >= SIGNIFICANT_CHANGE_THRESHOLD) {
        worsened.push("WORSENED_STOP_RATE");
        rationale.push("REASON_STOP_RATE_INCREASED");
      } else {
        unchanged.push("UNCHANGED_STOP_RATE");
      }
    } else {
      unavailable.push("UNAVAILABLE_STOP_RATE");
    }

    // 4. Compare passRate
    const beforePassRate = before.rates.passRate;
    const afterPassRate = afterShort.rates.passRate;

    if (beforePassRate !== undefined && afterPassRate !== undefined) {
      const passRateChange = afterPassRate - beforePassRate;

      if (passRateChange >= SIGNIFICANT_CHANGE_THRESHOLD) {
        improved.push("IMPROVED_PASS_RATE");
        rationale.push("REASON_PASS_RATE_INCREASED");
      } else if (passRateChange <= -SIGNIFICANT_CHANGE_THRESHOLD) {
        worsened.push("WORSENED_PASS_RATE");
        rationale.push("REASON_PASS_RATE_DECREASED");
      } else {
        unchanged.push("UNCHANGED_PASS_RATE");
      }
    } else {
      unavailable.push("UNAVAILABLE_PASS_RATE");
    }

    // 5. Compare confusion signals
    const beforeConfusion = new Set(before.confusionSignals);
    const afterConfusion = new Set(afterShort.confusionSignals);

    // Confusion resolved
    for (const signal of beforeConfusion) {
      if (!afterConfusion.has(signal)) {
        if (signal === "CONFUSION_GATE_BLOCK_DOMINATES") {
          improved.push("IMPROVED_CONFUSION_BLOCK_DOMINATES_RESOLVED");
          rationale.push("REASON_CONFUSION_BLOCK_RESOLVED");
        } else if (signal === "CONFUSION_STOP_FREQUENT") {
          improved.push("IMPROVED_CONFUSION_STOP_RESOLVED");
          rationale.push("REASON_CONFUSION_STOP_RESOLVED");
        }
      }
    }

    // New confusion appeared
    for (const signal of afterConfusion) {
      if (!beforeConfusion.has(signal)) {
        worsened.push(`WORSENED_NEW_CONFUSION_${signal}`);
        rationale.push("REASON_NEW_CONFUSION_APPEARED");
      }
    }

    // 6. Compare bottlenecks
    const beforeBottlenecks = new Set(before.bottlenecks);
    const afterBottlenecks = new Set(afterShort.bottlenecks);

    // Bottleneck resolved
    for (const bottleneck of beforeBottlenecks) {
      if (!afterBottlenecks.has(bottleneck)) {
        improved.push(`IMPROVED_BOTTLENECK_RESOLVED_${bottleneck}`);
        rationale.push("REASON_BOTTLENECK_RESOLVED");
      }
    }

    // New bottleneck appeared
    for (const bottleneck of afterBottlenecks) {
      if (!beforeBottlenecks.has(bottleneck)) {
        worsened.push(`WORSENED_NEW_BOTTLENECK_${bottleneck}`);
        rationale.push("REASON_NEW_BOTTLENECK_APPEARED");
      }
    }

    // 7. Determine overall decision
    let decision: EffectDecision;

    if (improved.length > 0 && worsened.length === 0) {
      // Improved only
      decision = "EFFECT_IMPROVED";
      rationale.push("REASON_OVERALL_IMPROVED");
    } else if (worsened.length > 0 && improved.length === 0) {
      // Worsened only
      decision = "EFFECT_WORSENED";
      rationale.push("REASON_OVERALL_WORSENED");
    } else if (improved.length > 0 && worsened.length > 0) {
      // Mixed
      decision = "EFFECT_MIXED";
      rationale.push("REASON_OVERALL_MIXED");
    } else if (unchanged.length > 0) {
      // No significant change
      decision = "EFFECT_NO_CHANGE";
      rationale.push("REASON_NO_SIGNIFICANT_CHANGE");
    } else {
      // Unknown (all unavailable)
      decision = "EFFECT_UNKNOWN";
      rationale.push("REASON_METRICS_UNAVAILABLE");
    }

    return {
      decision,
      compare: { improved, worsened, unchanged, unavailable },
      rationale,
      warnings,
    };
  } catch (error) {
    // Defensive: Return UNKNOWN with error
    warnings.push("WARN_EFFECT_EVALUATION_ERROR");
    rationale.push("REASON_EVALUATION_ERROR");

    return {
      decision: "EFFECT_UNKNOWN",
      compare: { improved, worsened, unchanged, unavailable },
      rationale,
      warnings,
    };
  }
}
