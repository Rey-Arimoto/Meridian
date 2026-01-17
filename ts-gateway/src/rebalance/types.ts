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
 *
 * PR155: Oracle-based pricing support added.
 * Prices now come from oracle, and may be unavailable.
 */
export interface PortfolioSnapshot {
  // Token balances (as strings to avoid precision loss)
  balances: {
    WBTC: string;
    USDC: string;
    SUI: string;
  };

  // Token prices in USD (PR155: now optional, from oracle)
  pricesUsd: {
    WBTC?: number; // Optional: may be unavailable if oracle fails
    USDC?: number; // Optional: typically 1.0 (stablecoin)
  };

  // Token values in USD (optional if prices unavailable)
  valuesUsd?: {
    WBTC: number;
    USDC: number;
  };

  // Current weights (optional if prices unavailable)
  weights?: {
    WBTC: number; // wBTC weight (0.0 - 1.0)
    USDC: number; // USDC weight (0.0 - 1.0)
  };

  // Total portfolio value in USD (optional if prices unavailable)
  totalUsd?: number;

  // Oracle status (PR155)
  oracleStatus?: "AVAILABLE" | "STALE" | "ERROR";

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

  // PR158: Drift evaluation result (optional)
  drift?: {
    status: "AVAILABLE" | "UNKNOWN" | "ERROR";
    driftTooSmall?: boolean;
    reasons: string[];
    warnings: string[];
  };

  // PR158: Cooldown evaluation result (optional)
  cooldown?: {
    status: "AVAILABLE" | "BLOCKED" | "UNKNOWN" | "ERROR";
    blocked?: boolean;
    reasons: string[];
    warnings: string[];
  };
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
 *
 * PR157: Enhanced with minOut guard and consistency checks
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

  // Minimum amount out (PR157: Required for execution safety, string format)
  minOut: string | null;

  // Slippage tolerance in basis points (PR157: Calculated from fixed rules)
  slippageBps: number;

  // Transaction deadline (seconds from now)
  deadlineSeconds: number;

  // Safety checks performed (PR157: Label-only, no numbers)
  checks: string[];

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

/**
 * PR159: Chunked Execution / TWAP-lite v1
 */

/**
 * Chunk status
 */
export type ChunkStatus =
  | "PLANNED"
  | "SKIPPED"
  | "BLOCKED"
  | "SIMULATED"
  | "EXECUTED"
  | "STOPPED"
  | "ERROR";

/**
 * Run status
 */
export type RunStatus =
  | "PLANNED"
  | "RUNNING"
  | "COMPLETED"
  | "STOPPED"
  | "ERROR";

/**
 * Chunk plan (single chunk in a run)
 */
export interface ChunkPlan {
  // Chunk identifier
  chunkId: string;

  // Notional USD for this chunk (internal numeric only)
  notionalUsd: number;

  // Intent for this chunk
  intent: "INCREASE_WBTC" | "DECREASE_WBTC" | "NOOP";

  // Template ID (inherited from rebalance plan)
  templateId: string;

  // Venue hint (optional)
  venueHint?: "CETUS" | "DEEPBOOK" | "NONE";
}

/**
 * Chunk result (execution outcome of single chunk)
 */
export interface ChunkResult {
  // Chunk identifier
  chunkId: string;

  // Execution status
  status: ChunkStatus;

  // Reasons (label-only)
  reasons: string[];

  // Transaction draft (if created)
  txDraft?: TxDraft;

  // Venue used (if executed)
  venue?: "CETUS" | "DEEPBOOK" | "NONE";

  // Creation timestamp
  createdAtMs: number;

  // PR161: Phase diagnostics (label-only)
  phaseLabel?: string;

  // PR161: Route selection diagnostics (label-only)
  routeSelected?: "CETUS" | "DEEPBOOK" | "NONE";
  routeChanged?: boolean;

  // PR184: Observe degrade level diagnostics (label-only)
  observeDegradeLevel?: string;
}

/**
 * Run plan (chunked execution plan)
 */
export interface RunPlan {
  // Run identifier
  runId: string;

  // Run status
  status: RunStatus;

  // Creation timestamp
  createdAtMs: number;

  // Template ID
  templateId: string;

  // Total notional USD (internal numeric only)
  totalNotionalUsd: number;

  // Chunk plans
  chunks: ChunkPlan[];

  // Reasons (label-only)
  reasons: string[];
}

/**
 * Run result (chunked execution outcome)
 */
export interface RunResult {
  // Run identifier
  runId: string;

  // Run status
  status: RunStatus;

  // Reasons (label-only)
  reasons: string[];

  // Chunk results
  chunkResults: ChunkResult[];

  // Start timestamp
  startedAtMs: number;

  // Finish timestamp (if completed/stopped)
  finishedAtMs?: number;

  // PR162: Resume state (if stopped with resume possibility)
  resumeState?: ResumeState;
}

/**
 * PR162: Partial Resume Policy v1
 */

/**
 * Resume status
 */
export type ResumeStatus = "RESUMABLE" | "WAIT" | "ABANDON" | "UNKNOWN";

/**
 * Stop reason (label-only)
 */
export type StopReason =
  | "STOP_PHASE_POLICY"
  | "STOP_NO_ROUTE"
  | "STOP_ORACLE_STALE"
  | "STOP_ORACLE_ERROR"
  | "STOP_QUOTE_STALE"
  | "STOP_QUOTE_INCONSISTENT"
  | "STOP_IMPACT_HIGH"
  | "STOP_SLIPPAGE_HIGH"
  | "STOP_DEPTH_THIN"
  | "STOP_POLICY_DENY"
  | "STOP_HARDSTOP_ACTIVE"
  | "STOP_DURATION_EXCEEDED"
  | "STOP_BLOCKED_STREAK"
  | "STOP_ERROR"
  | "STOP_UNKNOWN";

/**
 * Resume state (stopped run state for resume evaluation)
 */
export interface ResumeState {
  // Status (constant "STOPPED")
  status: "STOPPED";

  // Stop reason (label-only)
  stopReason: StopReason;

  // Stop timestamp (internal numeric only)
  stopAtTs: number;

  // Resume after timestamp (internal numeric only, optional)
  resumeAfterTs?: number;

  // Last phase label (label-only, for observability)
  lastPhaseLabel?: string;

  // Last route (label-only, for observability)
  lastRoute?: string;

  // Last template ID (label-only, for observability)
  lastTemplateId?: string;

  // Last intent (label-only, for observability)
  lastIntent?: string;

  // Warnings (label-only)
  warnings: string[];
}
