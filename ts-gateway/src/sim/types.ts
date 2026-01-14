/**
 * PR156: v1.4 Execution Simulation + Slippage Envelope - Type Definitions (READ-ONLY)
 *
 * Purpose:
 *   Define types for execution simulation and slippage envelope.
 *   Provides pre-trade safety labeling for slippage/impact/liquidity.
 *
 * Constitutional Constraints:
 *   - READ-ONLY: Simulation only, no execution
 *   - Label-only output (no numbers in warnings/reasons)
 *   - Fixed rules (no learning, no optimization)
 *   - Conservative: Unknown/missing → RISKY or BLOCK
 */

/**
 * Simulation status
 *
 * - PASS: All checks passed, safe to proceed
 * - RISKY: Some checks uncertain or thin liquidity
 * - BLOCK: High risk detected, execution blocked
 * - ERROR: Simulation failed (missing data, invalid input)
 */
export type SimStatus = "PASS" | "RISKY" | "BLOCK" | "ERROR";

/**
 * Simulation labels (slippage/impact/liquidity)
 *
 * All labels are LOW/MEDIUM/HIGH/UNKNOWN (or OK/THIN for liquidity).
 * No numeric values in output.
 */
export type SlippageLabel =
  | "SLIPPAGE_LOW"
  | "SLIPPAGE_MEDIUM"
  | "SLIPPAGE_HIGH"
  | "SLIPPAGE_UNKNOWN";

export type ImpactLabel =
  | "IMPACT_LOW"
  | "IMPACT_MEDIUM"
  | "IMPACT_HIGH"
  | "IMPACT_UNKNOWN";

export type LiquidityLabel =
  | "LIQUIDITY_OK"
  | "LIQUIDITY_THIN"
  | "LIQUIDITY_UNKNOWN";

/**
 * Simulation reasons (label-only, no numbers)
 *
 * These explain why simulation returned specific status.
 */
export type SimReason =
  | "REASON_MISSING_QUOTE"
  | "REASON_ORACLE_UNAVAILABLE"
  | "REASON_INVALID_INPUT"
  | "REASON_GUARD_TRIGGERED"
  | "REASON_RISK_THRESHOLD"
  | "REASON_UNKNOWN";

/**
 * Simulation input (from planner, router, oracle)
 */
export interface SimulationInput {
  // From planner (numeric values internal only)
  notionalUsd?: number; // USD amount to move
  deltaWbtc?: number; // Weight delta (target - current)
  intent: "INCREASE_WBTC" | "DECREASE_WBTC" | "NOOP";

  // From router/quotes (numeric values internal only)
  quote?: {
    venue: "CETUS" | "DEEPBOOK" | "NONE";
    status: "AVAILABLE" | "UNAVAILABLE" | "ERROR";
    slippageBps?: number; // Slippage in basis points (internal)
    impactBps?: number; // Price impact in basis points (internal)
    depthUsd?: number; // Liquidity depth in USD (internal)
  };

  // From oracle (optional)
  oracleStatus?: "AVAILABLE" | "STALE" | "ERROR";
}

/**
 * Execution simulation record (output)
 *
 * All fields are label-only (no numbers in warnings/reasons).
 */
export interface ExecutionSimulationRecord {
  // Status (PASS/RISKY/BLOCK/ERROR)
  status: SimStatus;

  // Labels (slippage/impact/liquidity)
  labels: {
    slippage: SlippageLabel;
    impact: ImpactLabel;
    liquidity: LiquidityLabel;
  };

  // Reasons (label-only, no numbers)
  reasons: SimReason[];

  // Warnings (label-only, no numbers)
  warnings: string[];
}
