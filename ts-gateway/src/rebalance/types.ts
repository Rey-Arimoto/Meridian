/**
 * PR152: v1.4 TS Rebalance Type Definitions (READ-ONLY)
 *
 * Purpose:
 *   Define types for rebalance template resolution and execution.
 *
 * Token Scope:
 *   - wBTC: Risk asset (target of rebalancing)
 *   - USDC: Stable asset (safe haven)
 *   - SUI: Gas only (not rebalanced, minimum balance reserved)
 */

import { TemplateId } from "./templates";

/**
 * Token symbols supported in Meridian TS Gateway
 */
export type TokenSymbol = "WBTC" | "USDC" | "SUI";

/**
 * Portfolio snapshot (wallet balances + prices + weights)
 */
export interface PortfolioSnapshot {
  // Token balances (as strings to avoid precision loss)
  balances: {
    WBTC: string;
    USDC: string;
    SUI: string;
  };

  // Token prices in USD
  pricesUsd: {
    WBTC: number;
    USDC: number; // Always 1.0 for stablecoin
  };

  // Token values in USD
  valuesUsd: {
    WBTC: number;
    USDC: number;
  };

  // Current weights (normalized to 1.0, excluding SUI)
  weights: {
    WBTC: number; // wBTC weight (0.0 - 1.0)
    USDC: number; // USDC weight (0.0 - 1.0)
  };

  // Total portfolio value in USD (wBTC + USDC, excluding SUI)
  totalUsd: number;

  // Timestamp of snapshot
  timestamp: number;
}

/**
 * Rebalance constraints (safety limits and execution parameters)
 */
export interface RebalanceConstraints {
  // Minimum SUI balance to reserve for gas (as string)
  minSuiBalance: string; // e.g., "0.05" SUI

  // Minimum weight delta to trigger action (e.g., 0.05 = 5%)
  minDeltaToAct: number;

  // Maximum notional USD to move in single rebalance
  maxNotionalUsd: number; // e.g., 200 USD

  // Cooldown period between rebalances (seconds)
  cooldownSeconds: number; // e.g., 900 (15 minutes)

  // Slippage tolerance in basis points (e.g., 50 = 0.50%)
  slippageBps: number;

  // Transaction deadline (seconds from now)
  deadlineSeconds: number; // e.g., 120 (2 minutes)
}

/**
 * Rebalance intent (what needs to be done)
 */
export type RebalanceIntent = "INCREASE_WBTC" | "DECREASE_WBTC" | "NOOP";

/**
 * Rebalance plan (target weights + delta + intent)
 */
export interface RebalancePlan {
  // Template ID from Python PR151
  templateId: TemplateId;

  // Target weights from template
  targetWeights: {
    WBTC: number;
    USDC: number;
  };

  // Current weights from portfolio
  currentWeights: {
    WBTC: number;
    USDC: number;
  };

  // Weight deltas (target - current)
  deltaWeights: {
    WBTC: number;
    USDC: number;
  };

  // Rebalance intent
  intent: RebalanceIntent;

  // Notional USD to move (capped by maxNotionalUsd)
  notionalUsd: number;

  // Reason codes (debugging/logging)
  reasonCodes: string[];
}

/**
 * Transaction draft status (PR153 update)
 */
export type TxDraftStatus =
  | "DRAFT"
  | "EXECUTABLE_DRAFT" // PR153: Gate passed, ready for execution
  | "SIMULATION_ONLY" // PR153: Simulation only, no execution
  | "SKIPPED"
  | "ERROR";

/**
 * Routing protocol
 */
export type RouteProtocol = "CETUS" | "DEEPBOOK" | "UNKNOWN";

/**
 * Swap action
 */
export type SwapAction = "SWAP_USDC_TO_WBTC" | "SWAP_WBTC_TO_USDC" | "NOOP";

/**
 * Transaction draft (ready for simulate/execute)
 */
export interface TxDraft {
  // Draft status
  status: TxDraftStatus;

  // Simulate-only mode (true = do not execute)
  simulateOnly: boolean;

  // Routing protocol
  route: RouteProtocol;

  // Swap action
  action: SwapAction;

  // Amount in (as string)
  amountIn: string;

  // Minimum amount out (as string, null if not calculated)
  minOut: string | null;

  // Slippage tolerance in basis points
  slippageBps: number;

  // Transaction deadline (seconds from now)
  deadlineSeconds: number;

  // Notes (debugging/logging)
  notes: string[];

  // Errors (if any)
  errors: string[];
}

/**
 * Transaction execution result
 */
export interface TxExecutionResult {
  // Success flag
  ok: boolean;

  // Transaction digest (if executed)
  txDigest?: string;

  // Errors (if any)
  errors?: string[];

  // Notes (debugging/logging)
  notes?: string[];
}

/**
 * Simulation result
 */
export interface SimulationResult {
  // Success flag
  ok: boolean;

  // Notes (debugging/logging)
  notes: string[];
}

/**
 * Re-export TemplateId for convenience
 */
export type { TemplateId };
