/**
 * PR158: v1.4 Position Drift Monitor (READ-ONLY)
 *
 * Purpose:
 *   Evaluate if weight drift between current and target is large enough to act.
 *   Small drift → NOOP (prevent noise trading / micro-adjustments).
 *
 * Constitutional Constraints:
 *   - READ-ONLY: Drift evaluation only, no execution
 *   - Fixed rules: No learning, no optimization
 *   - Never throws: Always returns DriftResult
 *   - Label-only output: No numbers in reasons/warnings
 *   - Conservative: Uncertain → NOOP or UNKNOWN (safe default)
 */

import { PortfolioSnapshot } from "./types";
import { TemplateWeights } from "./templates";

/**
 * Drift status
 */
export type DriftStatus = "AVAILABLE" | "UNKNOWN" | "ERROR";

/**
 * Drift configuration (fixed thresholds)
 */
export interface DriftConfig {
  // Minimum absolute delta to act (internal numeric, not in output)
  // Default: 0.07 (7%)
  minAbsDeltaToAct: number;

  // Allow asymmetry (future tuning, currently unused)
  allowAsymmetry?: boolean;
}

/**
 * Drift evaluation result
 */
export interface DriftResult {
  // Status
  status: DriftStatus;

  // Is drift too small to act? (true → NOOP is rational)
  driftTooSmall?: boolean;

  // Reasons (label-only, no numbers)
  reasons: string[];

  // Warnings (label-only, no numbers)
  warnings: string[];
}

/**
 * Fixed drift thresholds (constitutional constants)
 */
const DRIFT_THRESHOLDS = {
  // Default minimum absolute delta to act (7%)
  DEFAULT_MIN_ABS_DELTA: 0.07,
};

/**
 * Evaluate position drift (main API)
 *
 * @param snapshot - Portfolio snapshot (current weights)
 * @param target - Target weights from template
 * @param cfg - Optional drift configuration
 * @returns Drift evaluation result
 *
 * Fixed rules (never throws):
 *   1. Check if weights are available in snapshot
 *   2. Check if target weights are valid
 *   3. Calculate abs(target.WBTC - current.WBTC)
 *   4. If delta < minAbsDeltaToAct → driftTooSmall=true
 *   5. Return AVAILABLE with driftTooSmall flag
 *
 * IMPORTANT: Returns label-only reasons/warnings (no numeric values)
 */
export function evaluateDriftV1(
  snapshot: PortfolioSnapshot,
  target: TemplateWeights,
  cfg?: Partial<DriftConfig>
): DriftResult {
  const reasons: string[] = [];
  const warnings: string[] = [];

  try {
    // Merge config with defaults
    const minAbsDeltaToAct =
      cfg?.minAbsDeltaToAct ?? DRIFT_THRESHOLDS.DEFAULT_MIN_ABS_DELTA;

    // Step 1: Check if current weights are available
    if (
      !snapshot.weights ||
      typeof snapshot.weights.WBTC !== "number" ||
      typeof snapshot.weights.USDC !== "number" ||
      isNaN(snapshot.weights.WBTC) ||
      isNaN(snapshot.weights.USDC)
    ) {
      reasons.push("REASON_WEIGHTS_UNAVAILABLE");
      warnings.push("WARN_CURRENT_WEIGHTS_MISSING");

      return {
        status: "UNKNOWN",
        driftTooSmall: undefined,
        reasons,
        warnings,
      };
    }

    // Step 2: Check if target weights are valid
    if (
      !target ||
      typeof target.wbtcWeight !== "number" ||
      typeof target.usdcWeight !== "number" ||
      isNaN(target.wbtcWeight) ||
      isNaN(target.usdcWeight)
    ) {
      reasons.push("REASON_TARGET_WEIGHTS_INVALID");
      warnings.push("WARN_TARGET_WEIGHTS_INVALID");

      return {
        status: "UNKNOWN",
        driftTooSmall: undefined,
        reasons,
        warnings,
      };
    }

    // Step 3: Calculate drift (absolute difference)
    const currentWbtc = snapshot.weights.WBTC;
    const targetWbtc = target.wbtcWeight;
    const delta = Math.abs(targetWbtc - currentWbtc);

    // Step 4: Evaluate drift threshold
    if (delta < minAbsDeltaToAct) {
      // Drift is too small → NOOP is rational
      reasons.push("REASON_DRIFT_TOO_SMALL");

      return {
        status: "AVAILABLE",
        driftTooSmall: true,
        reasons,
        warnings,
      };
    } else {
      // Drift is actionable
      reasons.push("REASON_DRIFT_ACTIONABLE");

      return {
        status: "AVAILABLE",
        driftTooSmall: false,
        reasons,
        warnings,
      };
    }
  } catch (error) {
    // Defensive: Never throw, return ERROR state
    return {
      status: "ERROR",
      driftTooSmall: undefined,
      reasons: ["REASON_DRIFT_EVALUATION_ERROR"],
      warnings: ["WARN_DRIFT_EVALUATION_ERROR"],
    };
  }
}

/**
 * Get drift summary (for logging/debugging)
 *
 * @param result - Drift result
 * @returns Summary string (label-only)
 */
export function getDriftSummary(result: DriftResult): string {
  if (result.status === "UNKNOWN") {
    return "DRIFT_UNKNOWN";
  }

  if (result.status === "ERROR") {
    return "DRIFT_ERROR";
  }

  if (result.driftTooSmall) {
    return "DRIFT_TOO_SMALL";
  }

  return "DRIFT_ACTIONABLE";
}
