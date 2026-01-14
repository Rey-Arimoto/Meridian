/**
 * PR152: v1.4 TS Rebalance Executor Skeleton (READ-ONLY)
 * PR153: v1.4 Gate Integration (READ-ONLY)
 *
 * Purpose:
 *   Build transaction drafts and execute rebalances.
 *   Execution is DISABLED by default (safety first).
 *
 * PR153 Updates:
 *   - Integrate GateResult for safety checks
 *   - BLOCK → status=SKIPPED
 *   - PASS → status=EXECUTABLE_DRAFT
 *   - Execution still requires allowExecution=true
 *
 * Constitutional Constraints:
 *   - EXECUTION DISABLED BY DEFAULT
 *   - Only execute if opts.allowExecution === true
 *   - Never log private keys or sensitive data
 *   - Defensive: Handle errors gracefully
 *   - Conservative: Prefer safe defaults
 */

import {
  RebalancePlan,
  RebalanceConstraints,
  TxDraft,
  TxExecutionResult,
  SimulationResult,
} from "./types";
import { GateResult } from "./gate";
import { RoutePlan } from "./router";

/**
 * Executor options
 */
export interface ExecutorOptions {
  // Allow actual execution (default: false)
  allowExecution?: boolean;

  // Simulate-only mode (default: true)
  simulateOnly?: boolean;

  // Additional notes for debugging
  notes?: string[];
}

/**
 * Build transaction draft from rebalance plan
 *
 * @param plan - Rebalance plan
 * @param constraints - Rebalance constraints
 * @param opts - Executor options
 * @returns Transaction draft
 *
 * Draft Logic:
 *   1. If intent=NOOP, return SKIPPED draft
 *   2. If intent=INCREASE_WBTC, prepare USDC→wBTC swap
 *   3. If intent=DECREASE_WBTC, prepare wBTC→USDC swap
 *   4. Calculate amountIn from notionalUsd
 *   5. Set route (CETUS fixed for now, future PR will add routing)
 *   6. Set slippage/deadline from constraints
 */
export async function buildTxDraft(
  plan: RebalancePlan,
  constraints: RebalanceConstraints,
  opts?: ExecutorOptions
): Promise<TxDraft> {
  const notes: string[] = opts?.notes ? [...opts.notes] : [];
  const errors: string[] = [];

  // Check if NOOP
  if (plan.intent === "NOOP") {
    notes.push("Intent is NOOP, skipping transaction");

    return {
      status: "SKIPPED",
      simulateOnly: opts?.simulateOnly ?? true,
      route: "UNKNOWN",
      action: "NOOP",
      amountIn: "0",
      minOut: null,
      slippageBps: constraints.slippageBps,
      deadlineSeconds: constraints.deadlineSeconds,
      notes,
      errors,
    };
  }

  // Determine action and amountIn
  let action: "SWAP_USDC_TO_WBTC" | "SWAP_WBTC_TO_USDC";
  let amountIn: string;

  if (plan.intent === "INCREASE_WBTC") {
    action = "SWAP_USDC_TO_WBTC";
    // amountIn = notionalUsd (in USDC, since USDC = $1)
    amountIn = plan.notionalUsd.toFixed(6); // 6 decimals for USDC
    notes.push(`Action: Buy wBTC with ${amountIn} USDC`);
  } else if (plan.intent === "DECREASE_WBTC") {
    action = "SWAP_WBTC_TO_USDC";
    // amountIn = notionalUsd / wBTC price (estimate)
    // For now, use simple approximation (will be refined in future PR)
    amountIn = (plan.notionalUsd / 45000).toFixed(8); // 8 decimals for wBTC
    notes.push(`Action: Sell ${amountIn} wBTC for USDC`);
  } else {
    // Should not reach here, but defensive
    errors.push("Invalid intent (not INCREASE_WBTC or DECREASE_WBTC)");

    return {
      status: "ERROR",
      simulateOnly: opts?.simulateOnly ?? true,
      route: "UNKNOWN",
      action: "NOOP",
      amountIn: "0",
      minOut: null,
      slippageBps: constraints.slippageBps,
      deadlineSeconds: constraints.deadlineSeconds,
      notes,
      errors,
    };
  }

  // Route (fixed to CETUS for now - future PR will add routing logic)
  const route = "CETUS";
  notes.push(`Route: ${route} (fixed for PR152, routing logic in future PR)`);

  // minOut (not calculated yet - future PR will add price/slippage calculation)
  const minOut = null;
  notes.push("minOut not calculated (will be added in routing PR)");

  return {
    status: "DRAFT",
    simulateOnly: opts?.simulateOnly ?? true,
    route,
    action,
    amountIn,
    minOut,
    slippageBps: constraints.slippageBps,
    deadlineSeconds: constraints.deadlineSeconds,
    notes,
    errors,
  };
}

/**
 * Simulate transaction
 *
 * @param draft - Transaction draft
 * @param opts - Executor options
 * @returns Simulation result
 *
 * Note: This is a stub - actual simulation will be added in future PR
 */
export async function simulateTx(
  draft: TxDraft,
  opts?: ExecutorOptions
): Promise<SimulationResult> {
  const notes: string[] = [];

  // Check if draft is skipped
  if (draft.status === "SKIPPED") {
    notes.push("Draft status is SKIPPED, no simulation needed");
    return { ok: true, notes };
  }

  // Check if draft has errors
  if (draft.status === "ERROR" || draft.errors.length > 0) {
    notes.push("Draft has errors, cannot simulate");
    return { ok: false, notes };
  }

  // Stub simulation (future PR will add actual SUI SDK simulation)
  notes.push("Simulation stub (actual simulation in future PR)");
  notes.push(`Would simulate: ${draft.action} ${draft.amountIn} on ${draft.route}`);

  return { ok: true, notes };
}

/**
 * Execute transaction
 *
 * @param draft - Transaction draft
 * @param opts - Executor options
 * @returns Execution result
 *
 * IMPORTANT: Execution is DISABLED by default.
 * Only executes if opts.allowExecution === true.
 */
export async function executeTx(
  draft: TxDraft,
  opts?: ExecutorOptions
): Promise<TxExecutionResult> {
  const notes: string[] = [];
  const errors: string[] = [];

  // Check if execution is allowed
  if (!opts?.allowExecution) {
    errors.push("EXECUTION_DISABLED");
    notes.push("Execution is disabled by default (set allowExecution=true to enable)");

    return { ok: false, errors, notes };
  }

  // Check if draft is skipped
  if (draft.status === "SKIPPED") {
    notes.push("Draft status is SKIPPED, no execution needed");
    return { ok: true, notes };
  }

  // Check if draft has errors
  if (draft.status === "ERROR" || draft.errors.length > 0) {
    errors.push("DRAFT_HAS_ERRORS");
    notes.push("Draft has errors, cannot execute");
    return { ok: false, errors, notes };
  }

  // Check if simulateOnly mode
  if (draft.simulateOnly) {
    notes.push("Draft is in simulateOnly mode, skipping execution");
    return { ok: true, notes };
  }

  // Stub execution (future PR will add actual SUI SDK transaction)
  errors.push("EXECUTION_NOT_IMPLEMENTED");
  notes.push("Execution stub (actual execution in future PR)");
  notes.push(`Would execute: ${draft.action} ${draft.amountIn} on ${draft.route}`);

  return { ok: false, errors, notes };
}

/**
 * Build transaction draft with gate integration (PR153)
 *
 * @param plan - Rebalance plan
 * @param route - Route plan
 * @param gate - Gate result
 * @param constraints - Rebalance constraints
 * @param opts - Executor options
 * @returns Transaction draft
 *
 * Logic:
 *   1. If gate.status = BLOCK → return SKIPPED draft with block reasons
 *   2. If gate.status = PASS → build draft with status=EXECUTABLE_DRAFT
 *   3. Use route.venue for routing
 */
export async function buildTxDraftWithGate(
  plan: RebalancePlan,
  route: RoutePlan,
  gate: GateResult,
  constraints: RebalanceConstraints,
  opts?: ExecutorOptions
): Promise<TxDraft> {
  const notes: string[] = opts?.notes ? [...opts.notes] : [];
  const errors: string[] = [];

  // Check gate status
  if (gate.status === "BLOCK") {
    notes.push("Gate status is BLOCK, skipping transaction");
    notes.push(`Block reasons: ${gate.blockReasons.join(", ")}`);

    return {
      status: "SKIPPED",
      simulateOnly: opts?.simulateOnly ?? true,
      route: route.venue === "NONE" ? "UNKNOWN" : route.venue,
      action: "NOOP",
      amountIn: "0",
      minOut: null,
      slippageBps: constraints.slippageBps,
      deadlineSeconds: constraints.deadlineSeconds,
      notes,
      errors: gate.blockReasons, // Block reasons as errors
    };
  }

  if (gate.status === "ERROR") {
    errors.push("Gate returned ERROR status");

    return {
      status: "ERROR",
      simulateOnly: opts?.simulateOnly ?? true,
      route: "UNKNOWN",
      action: "NOOP",
      amountIn: "0",
      minOut: null,
      slippageBps: constraints.slippageBps,
      deadlineSeconds: constraints.deadlineSeconds,
      notes,
      errors,
    };
  }

  // Gate PASS → build executable draft
  // Check if NOOP (should have been caught by gate, but defensive)
  if (plan.intent === "NOOP") {
    notes.push("Intent is NOOP (defensive check)");

    return {
      status: "SKIPPED",
      simulateOnly: opts?.simulateOnly ?? true,
      route: route.venue === "NONE" ? "UNKNOWN" : route.venue,
      action: "NOOP",
      amountIn: "0",
      minOut: null,
      slippageBps: constraints.slippageBps,
      deadlineSeconds: constraints.deadlineSeconds,
      notes,
      errors,
    };
  }

  // Determine action and amountIn
  let action: "SWAP_USDC_TO_WBTC" | "SWAP_WBTC_TO_USDC";
  let amountIn: string;

  if (plan.intent === "INCREASE_WBTC") {
    action = "SWAP_USDC_TO_WBTC";
    amountIn = plan.notionalUsd.toFixed(6); // 6 decimals for USDC
    notes.push(`Action: Buy wBTC with ${amountIn} USDC`);
  } else if (plan.intent === "DECREASE_WBTC") {
    action = "SWAP_WBTC_TO_USDC";
    amountIn = (plan.notionalUsd / 45000).toFixed(8); // 8 decimals for wBTC
    notes.push(`Action: Sell ${amountIn} wBTC for USDC`);
  } else {
    errors.push("Invalid intent (not INCREASE_WBTC or DECREASE_WBTC)");

    return {
      status: "ERROR",
      simulateOnly: opts?.simulateOnly ?? true,
      route: "UNKNOWN",
      action: "NOOP",
      amountIn: "0",
      minOut: null,
      slippageBps: constraints.slippageBps,
      deadlineSeconds: constraints.deadlineSeconds,
      notes,
      errors,
    };
  }

  // Use route.venue
  const routeVenue = route.venue === "NONE" ? "UNKNOWN" : route.venue;
  notes.push(`Route: ${routeVenue}`);

  // Add gate warnings
  if (gate.warnings.length > 0) {
    notes.push(`Gate warnings: ${gate.warnings.join(", ")}`);
  }

  // minOut (not calculated yet - future PR will add price/slippage calculation)
  const minOut = null;
  notes.push("minOut not calculated (will be added in routing PR)");

  return {
    status: "EXECUTABLE_DRAFT", // Gate passed
    simulateOnly: opts?.simulateOnly ?? true,
    route: routeVenue,
    action,
    amountIn,
    minOut,
    slippageBps: constraints.slippageBps,
    deadlineSeconds: constraints.deadlineSeconds,
    notes,
    errors,
  };
}
