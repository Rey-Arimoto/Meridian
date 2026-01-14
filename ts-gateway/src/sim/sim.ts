/**
 * PR156: v1.4 Execution Simulation - Main Logic (READ-ONLY)
 *
 * Purpose:
 *   Run execution simulation with fixed rules.
 *   Label slippage/impact/liquidity based on thresholds.
 *   Conservative: Unknown → RISKY, High → BLOCK.
 *
 * Constitutional Constraints:
 *   - READ-ONLY: Simulation only, no execution
 *   - Fixed rules: First-match-wins, no learning
 *   - Never throws: Always returns ExecutionSimulationRecord
 *   - Label-only output: No numbers in warnings/reasons
 *   - Conservative: Missing data → BLOCK/RISKY
 */

import {
  SimulationInput,
  ExecutionSimulationRecord,
  SimStatus,
  SlippageLabel,
  ImpactLabel,
  LiquidityLabel,
  SimReason,
} from "./types";
import { sanitizeWarnings } from "./guards";

/**
 * Fixed thresholds (constitutional constants)
 *
 * These are the ONLY location with numeric thresholds.
 * Output labels are LOW/MEDIUM/HIGH/UNKNOWN only.
 */
const THRESHOLDS = {
  // Slippage thresholds (basis points)
  SLIPPAGE_LOW_BPS: 50, // <= 50 bps (0.50%) = LOW
  SLIPPAGE_MEDIUM_BPS: 150, // <= 150 bps (1.50%) = MEDIUM
  // > 150 bps = HIGH

  // Impact thresholds (basis points)
  IMPACT_LOW_BPS: 50, // <= 50 bps (0.50%) = LOW
  IMPACT_MEDIUM_BPS: 150, // <= 150 bps (1.50%) = MEDIUM
  // > 150 bps = HIGH

  // Liquidity threshold (depth multiplier)
  LIQUIDITY_DEPTH_MULTIPLIER: 5, // depth >= notional * 5 = OK
  // depth < notional * 5 = THIN
};

/**
 * Map slippage bps to label
 *
 * @param slippageBps - Slippage in basis points (internal)
 * @returns Slippage label
 */
function mapSlippageLabel(slippageBps: number | undefined): SlippageLabel {
  if (slippageBps === undefined || slippageBps === null || isNaN(slippageBps)) {
    return "SLIPPAGE_UNKNOWN";
  }

  if (slippageBps <= THRESHOLDS.SLIPPAGE_LOW_BPS) {
    return "SLIPPAGE_LOW";
  }

  if (slippageBps <= THRESHOLDS.SLIPPAGE_MEDIUM_BPS) {
    return "SLIPPAGE_MEDIUM";
  }

  return "SLIPPAGE_HIGH";
}

/**
 * Map impact bps to label
 *
 * @param impactBps - Impact in basis points (internal)
 * @returns Impact label
 */
function mapImpactLabel(impactBps: number | undefined): ImpactLabel {
  if (impactBps === undefined || impactBps === null || isNaN(impactBps)) {
    return "IMPACT_UNKNOWN";
  }

  if (impactBps <= THRESHOLDS.IMPACT_LOW_BPS) {
    return "IMPACT_LOW";
  }

  if (impactBps <= THRESHOLDS.IMPACT_MEDIUM_BPS) {
    return "IMPACT_MEDIUM";
  }

  return "IMPACT_HIGH";
}

/**
 * Map liquidity depth to label
 *
 * @param depthUsd - Liquidity depth in USD (internal)
 * @param notionalUsd - Notional USD amount (internal)
 * @returns Liquidity label
 */
function mapLiquidityLabel(
  depthUsd: number | undefined,
  notionalUsd: number | undefined
): LiquidityLabel {
  if (
    depthUsd === undefined ||
    depthUsd === null ||
    isNaN(depthUsd) ||
    notionalUsd === undefined ||
    notionalUsd === null ||
    isNaN(notionalUsd)
  ) {
    return "LIQUIDITY_UNKNOWN";
  }

  const minDepth = notionalUsd * THRESHOLDS.LIQUIDITY_DEPTH_MULTIPLIER;

  if (depthUsd >= minDepth) {
    return "LIQUIDITY_OK";
  }

  return "LIQUIDITY_THIN";
}

/**
 * Determine simulation status from labels
 *
 * @param labels - Slippage/impact/liquidity labels
 * @param reasons - Accumulated reasons
 * @returns Final status
 *
 * Decision logic (first-match-wins):
 *   1. Any *_HIGH label → BLOCK + REASON_RISK_THRESHOLD
 *   2. Any *_UNKNOWN or LIQUIDITY_THIN → RISKY
 *   3. All OK → PASS
 */
function determineStatus(
  labels: {
    slippage: SlippageLabel;
    impact: ImpactLabel;
    liquidity: LiquidityLabel;
  },
  reasons: SimReason[]
): { status: SimStatus; reasons: SimReason[] } {
  const updatedReasons = [...reasons];

  // Check for HIGH risk
  if (
    labels.slippage === "SLIPPAGE_HIGH" ||
    labels.impact === "IMPACT_HIGH"
  ) {
    updatedReasons.push("REASON_RISK_THRESHOLD");
    return { status: "BLOCK", reasons: updatedReasons };
  }

  // Check for UNKNOWN or THIN
  if (
    labels.slippage === "SLIPPAGE_UNKNOWN" ||
    labels.impact === "IMPACT_UNKNOWN" ||
    labels.liquidity === "LIQUIDITY_UNKNOWN" ||
    labels.liquidity === "LIQUIDITY_THIN"
  ) {
    return { status: "RISKY", reasons: updatedReasons };
  }

  // All checks passed
  return { status: "PASS", reasons: updatedReasons };
}

/**
 * Run execution simulation (main API)
 *
 * @param input - Simulation input
 * @returns Execution simulation record
 *
 * Fixed rules (first-match-wins):
 *   (A) Defensive: Invalid input → ERROR
 *   (B) NOOP → PASS
 *   (C) Missing dependencies → BLOCK
 *   (D) Label mapping → LOW/MEDIUM/HIGH/UNKNOWN
 *   (E) Final decision → PASS/RISKY/BLOCK
 *
 * IMPORTANT: Never throws exceptions. Always returns record.
 */
export function runExecutionSimulationV1(
  input: SimulationInput
): ExecutionSimulationRecord {
  const warnings: string[] = [];
  const reasons: SimReason[] = [];

  try {
    // (A) Defensive: Invalid input
    if (!input || typeof input !== "object") {
      reasons.push("REASON_INVALID_INPUT");
      return {
        status: "ERROR",
        labels: {
          slippage: "SLIPPAGE_UNKNOWN",
          impact: "IMPACT_UNKNOWN",
          liquidity: "LIQUIDITY_UNKNOWN",
        },
        reasons,
        warnings: sanitizeWarnings(["SIM_INVALID_INPUT"]),
      };
    }

    // (B) NOOP → PASS (no risk, no action)
    if (input.intent === "NOOP") {
      return {
        status: "PASS",
        labels: {
          slippage: "SLIPPAGE_UNKNOWN",
          impact: "IMPACT_UNKNOWN",
          liquidity: "LIQUIDITY_UNKNOWN",
        },
        reasons: [],
        warnings: sanitizeWarnings(["SIM_NOOP"]),
      };
    }

    // (C) Missing dependencies → BLOCK

    // C1: Oracle unavailable
    if (input.oracleStatus && input.oracleStatus !== "AVAILABLE") {
      reasons.push("REASON_ORACLE_UNAVAILABLE");
      warnings.push("SIM_ORACLE_UNAVAILABLE");

      return {
        status: "BLOCK",
        labels: {
          slippage: "SLIPPAGE_UNKNOWN",
          impact: "IMPACT_UNKNOWN",
          liquidity: "LIQUIDITY_UNKNOWN",
        },
        reasons,
        warnings: sanitizeWarnings(warnings),
      };
    }

    // C2: Quote missing or unavailable
    if (
      !input.quote ||
      input.quote.status !== "AVAILABLE" ||
      input.quote.venue === "NONE"
    ) {
      reasons.push("REASON_MISSING_QUOTE");
      warnings.push("SIM_MISSING_QUOTE");

      return {
        status: "BLOCK",
        labels: {
          slippage: "SLIPPAGE_UNKNOWN",
          impact: "IMPACT_UNKNOWN",
          liquidity: "LIQUIDITY_UNKNOWN",
        },
        reasons,
        warnings: sanitizeWarnings(warnings),
      };
    }

    // (D) Label mapping
    const slippageLabel = mapSlippageLabel(input.quote.slippageBps);
    const impactLabel = mapImpactLabel(input.quote.impactBps);
    const liquidityLabel = mapLiquidityLabel(
      input.quote.depthUsd,
      input.notionalUsd
    );

    const labels = {
      slippage: slippageLabel,
      impact: impactLabel,
      liquidity: liquidityLabel,
    };

    // (E) Final decision
    const { status, reasons: finalReasons } = determineStatus(labels, reasons);

    return {
      status,
      labels,
      reasons: finalReasons,
      warnings: sanitizeWarnings(warnings),
    };
  } catch (error) {
    // Defensive: catch all errors, return ERROR record
    return {
      status: "ERROR",
      labels: {
        slippage: "SLIPPAGE_UNKNOWN",
        impact: "IMPACT_UNKNOWN",
        liquidity: "LIQUIDITY_UNKNOWN",
      },
      reasons: ["REASON_UNKNOWN"],
      warnings: sanitizeWarnings(["SIM_ERROR"]),
    };
  }
}

/**
 * Create error simulation record (for testing)
 *
 * @returns Simulation record with ERROR status
 */
export function createErrorSimulationRecord(): ExecutionSimulationRecord {
  return {
    status: "ERROR",
    labels: {
      slippage: "SLIPPAGE_UNKNOWN",
      impact: "IMPACT_UNKNOWN",
      liquidity: "LIQUIDITY_UNKNOWN",
    },
    reasons: ["REASON_UNKNOWN"],
    warnings: ["SIM_ERROR"],
  };
}

/**
 * Create PASS simulation record (for testing)
 *
 * @returns Simulation record with PASS status
 */
export function createPassSimulationRecord(): ExecutionSimulationRecord {
  return {
    status: "PASS",
    labels: {
      slippage: "SLIPPAGE_LOW",
      impact: "IMPACT_LOW",
      liquidity: "LIQUIDITY_OK",
    },
    reasons: [],
    warnings: [],
  };
}
