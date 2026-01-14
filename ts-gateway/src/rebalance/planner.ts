/**
 * PR152: v1.4 TS Rebalance Planner (READ-ONLY)
 * PR158: v1.4 Drift Monitor Integration
 *
 * Purpose:
 *   Calculate rebalance plan: target weights → delta → intent → notional.
 *   First-match-wins logic with safety constraints.
 *
 * Constitutional Constraints:
 *   - READ-ONLY: No execution, just planning
 *   - Defensive: Handle edge cases gracefully
 *   - Conservative: Prefer NOOP when uncertain
 */

import { resolveTemplate } from "./templates";
import {
  PortfolioSnapshot,
  RebalanceConstraints,
  RebalancePlan,
  RebalanceIntent,
  TemplateId,
} from "./types";
import { evaluateDriftV1, DriftResult } from "./drift";

/**
 * Build rebalance plan
 *
 * @param snapshot - Portfolio snapshot
 * @param templateId - Template ID from Python PR151
 * @param constraints - Rebalance constraints
 * @returns Rebalance plan
 *
 * Logic:
 *   1. Resolve template to target weights
 *   2. Calculate delta (target - current)
 *   3. Determine intent (INCREASE_WBTC, DECREASE_WBTC, NOOP)
 *   4. Calculate notional USD to move (capped by maxNotionalUsd)
 *   5. Apply safety checks (SUI balance, delta threshold)
 */
export function buildRebalancePlan(
  snapshot: PortfolioSnapshot,
  templateId: TemplateId,
  constraints: RebalanceConstraints
): RebalancePlan {
  const reasonCodes: string[] = [];

  // Step 1: Resolve template to target weights
  const targetWeights = resolveTemplate(templateId);

  // Step 1.5: Check if weights/totalUsd available (PR155 - oracle-based)
  if (!snapshot.weights || snapshot.totalUsd === undefined) {
    reasonCodes.push("ORACLE_VALUATION_UNAVAILABLE");

    return {
      templateId,
      targetWeights: {
        WBTC: targetWeights.wbtcWeight,
        USDC: targetWeights.usdcWeight,
      },
      currentWeights: {
        WBTC: 0,
        USDC: 0,
      },
      deltaWeights: {
        WBTC: 0,
        USDC: 0,
      },
      intent: "NOOP",
      notionalUsd: 0,
      reasonCodes,
    };
  }

  // Step 2: Calculate weight deltas (target - current)
  const deltaWbtc = targetWeights.wbtcWeight - snapshot.weights.WBTC;
  const deltaUsdc = targetWeights.usdcWeight - snapshot.weights.USDC;

  // Step 3: Check SUI balance (gas safety)
  const suiBalance = parseFloat(snapshot.balances.SUI);
  const minSui = parseFloat(constraints.minSuiBalance);

  if (suiBalance < minSui) {
    reasonCodes.push(
      `INSUFFICIENT_SUI_FOR_GAS (have: ${suiBalance.toFixed(
        4
      )}, need: ${minSui.toFixed(4)})`
    );

    return {
      templateId,
      targetWeights: {
        WBTC: targetWeights.wbtcWeight,
        USDC: targetWeights.usdcWeight,
      },
      currentWeights: {
        WBTC: snapshot.weights.WBTC,
        USDC: snapshot.weights.USDC,
      },
      deltaWeights: {
        WBTC: deltaWbtc,
        USDC: deltaUsdc,
      },
      intent: "NOOP",
      notionalUsd: 0,
      reasonCodes,
    };
  }

  // Step 4: Check delta threshold
  const absDeltaWbtc = Math.abs(deltaWbtc);

  if (absDeltaWbtc < constraints.minDeltaToAct) {
    reasonCodes.push(
      `DELTA_BELOW_THRESHOLD (abs: ${absDeltaWbtc.toFixed(
        4
      )}, min: ${constraints.minDeltaToAct.toFixed(4)})`
    );

    return {
      templateId,
      targetWeights: {
        WBTC: targetWeights.wbtcWeight,
        USDC: targetWeights.usdcWeight,
      },
      currentWeights: {
        WBTC: snapshot.weights.WBTC,
        USDC: snapshot.weights.USDC,
      },
      deltaWeights: {
        WBTC: deltaWbtc,
        USDC: deltaUsdc,
      },
      intent: "NOOP",
      notionalUsd: 0,
      reasonCodes,
    };
  }

  // Step 5: Determine intent
  let intent: RebalanceIntent;

  if (deltaWbtc > 0) {
    intent = "INCREASE_WBTC"; // Need more wBTC (sell USDC → buy wBTC)
    reasonCodes.push("INCREASE_WBTC");
  } else if (deltaWbtc < 0) {
    intent = "DECREASE_WBTC"; // Need less wBTC (sell wBTC → buy USDC)
    reasonCodes.push("DECREASE_WBTC");
  } else {
    intent = "NOOP"; // No change needed
    reasonCodes.push("DELTA_ZERO");
  }

  // Step 5.5: PR158 - Evaluate drift (only if intent is not already NOOP)
  let driftResult: DriftResult | undefined;

  if (intent !== "NOOP") {
    driftResult = evaluateDriftV1(snapshot, targetWeights);

    // If drift is too small, override intent to NOOP
    if (driftResult.driftTooSmall) {
      intent = "NOOP";
      reasonCodes.push("DRIFT_TOO_SMALL");
    }
  }

  // Step 6: Calculate notional USD to move
  // notionalUsd = min(maxNotionalUsd, totalUsd * abs(delta))
  const uncappedNotional = snapshot.totalUsd * absDeltaWbtc;
  const notionalUsd = Math.min(constraints.maxNotionalUsd, uncappedNotional);

  if (notionalUsd < uncappedNotional) {
    reasonCodes.push(
      `NOTIONAL_CAPPED (uncapped: ${uncappedNotional.toFixed(
        2
      )}, capped: ${notionalUsd.toFixed(2)})`
    );
  }

  return {
    templateId,
    targetWeights: {
      WBTC: targetWeights.wbtcWeight,
      USDC: targetWeights.usdcWeight,
    },
    currentWeights: {
      WBTC: snapshot.weights.WBTC,
      USDC: snapshot.weights.USDC,
    },
    deltaWeights: {
      WBTC: deltaWbtc,
      USDC: deltaUsdc,
    },
    intent,
    notionalUsd,
    reasonCodes,
    // PR158: Include drift evaluation result
    drift: driftResult
      ? {
          status: driftResult.status,
          driftTooSmall: driftResult.driftTooSmall,
          reasons: driftResult.reasons,
          warnings: driftResult.warnings,
        }
      : undefined,
  };
}

/**
 * Create default rebalance constraints (for testing)
 *
 * @returns Default constraints
 */
export function createDefaultConstraints(): RebalanceConstraints {
  return {
    minSuiBalance: "0.05", // 0.05 SUI minimum for gas
    minDeltaToAct: 0.05, // 5% minimum delta to trigger action
    maxNotionalUsd: 200000, // $200,000 max per rebalance (PR153 update)
    cooldownSeconds: 900, // 15 minutes cooldown
    slippageBps: 50, // 0.50% slippage tolerance
    deadlineSeconds: 120, // 2 minutes deadline
  };
}
