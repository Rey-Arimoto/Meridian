/**
 * PR152: v1.4 TS Rebalance Executor Skeleton (READ-ONLY)
 * PR153: v1.4 Gate Integration (READ-ONLY)
 * PR156: v1.4 Simulation Pipeline Integration (READ-ONLY)
 * PR156: v1.4 Auto Execution Policy Integration (READ-ONLY)
 * PR158: v1.4 Cooldown Integration (READ-ONLY)
 *
 * Purpose:
 *   Build transaction drafts and execute rebalances.
 *   Execution controlled by double-key policy (env + HardStop).
 *
 * PR153 Updates:
 *   - Integrate GateResult for safety checks
 *   - BLOCK → status=SKIPPED
 *   - PASS → status=EXECUTABLE_DRAFT
 *   - Execution still requires allowExecution=true
 *
 * PR156 Updates (Simulation):
 *   - Integrate execution simulation into pipeline
 *   - Pipeline: planner → router → quote → simulation → gate → txDraft
 *   - Execution still disabled (allowExecution=false)
 *
 * PR156 Updates (Policy):
 *   - Delegate allowExecution to policy system
 *   - Double-key: env (MERIDIAN_EXECUTION_ENABLED) + policy (HardStop)
 *   - Aggressive + HardStop: Stop only when truly broken
 *
 * PR158 Updates (Cooldown):
 *   - Cooldown state should be evaluated by caller and added to plan.cooldown
 *   - After successful execution, use updateCooldownAfterExecution() helper
 *   - Cooldown blocks execution if within cooldown period
 *
 * Constitutional Constraints:
 *   - EXECUTION DISABLED BY DEFAULT
 *   - Only execute if policy allows (env key + policy key)
 *   - Never log private keys or sensitive data
 *   - Defensive: Handle errors gracefully
 *   - Conservative: Prefer safe defaults
 */

import {
  RebalancePlan,
  RebalanceConstraints,
  TxDraft,
  TxDraftStatus,
  RouteProtocol,
  SwapAction,
  TxExecutionResult,
  SimulationResult,
  PortfolioSnapshot,
} from "./types";
import { GateResult, PythonSignals, runSafetyGateWithSimulation } from "./gate";
import { RoutePlan } from "./router";
import {
  runExecutionSimulationV1,
  SimulationInput,
  ExecutionSimulationRecord,
} from "../sim";
import {
  evaluateExecutionPolicy,
  isExecutionAllowed,
  PolicyInput,
  PolicyResult,
  HardStopState,
} from "../policy";
import {
  evaluateCooldownV1,
  markActivityV1,
  CooldownState,
  CooldownResult,
} from "./cooldown";
import { evaluateSpecLockV1, SpecLockResultV1 } from "../spec";

/**
 * Executor options
 */
export interface ExecutorOptions {
  // Allow actual execution (default: false)
  // NOTE: This is now delegated to policy system (PR156)
  allowExecution?: boolean;

  // Simulate-only mode (default: true)
  simulateOnly?: boolean;

  // HardStop state (for policy evaluation, optional)
  hardStopState?: HardStopState;

  // Additional notes for debugging
  notes?: string[];
}

/**
 * Compute minOut floor (PR186)
 *
 * @param amountOut - Expected amount out (numeric)
 * @param slippageBps - Slippage tolerance in basis points
 * @returns Minimum acceptable amount out (as string)
 *
 * Formula: minOut = floor(amountOut * (1 - slippageBps/10000))
 *
 * Defensive: Returns "0" on error (safe side - will cause BLOCK)
 */
export function computeMinOutFloor(
  amountOut: number,
  slippageBps: number
): string {
  try {
    // Validate inputs
    if (
      typeof amountOut !== "number" ||
      typeof slippageBps !== "number" ||
      isNaN(amountOut) ||
      isNaN(slippageBps) ||
      amountOut <= 0 ||
      slippageBps < 0
    ) {
      return "0"; // Invalid input → safe default
    }

    // minOut = amountOut * (1 - slippageBps/10000)
    const slippageFactor = 1 - slippageBps / 10000;
    const minOut = Math.floor(amountOut * slippageFactor);

    // Return as string (internal numeric, but stored as string)
    return minOut.toString();
  } catch (error) {
    // Defensive: Return "0" on error (safe side)
    return "0";
  }
}

/**
 * PR191/PR191e: Derive execution reason codes for TxDraft (label-only)
 *
 * @param args - Draft context
 * @returns Array of reason code strings (label-only, no numerics)
 *
 * Constitutional: READ-ONLY, fixed rules, defensive (never throws)
 *
 * PR191e: slippageLabel source of truth is draft.slippageLabel only
 */
export function deriveExecutionReasonCodesV1(args: {
  draft: TxDraft;
  intent?: string;
  gateStatus?: "PASS" | "BLOCK" | "ERROR";
  policyStatus?: "ALLOW" | "SIM_ONLY" | "BLOCKED" | "ERROR";
}): string[] {
  const codes = new Set<string>();

  try {
    // 1) Draft basic status
    if (args.draft.status === "SKIPPED") {
      codes.add("REASON_INTENT_NOOP");
    } else if (args.draft.status === "ERROR") {
      codes.add("REASON_DRAFT_ERROR");
    } else if (args.draft.status === "DRAFT") {
      codes.add("REASON_DRAFT_OK");
    }

    // 2) Simulate-only / execution mode
    if (args.draft.simulateOnly === true) {
      codes.add("REASON_SIMULATE_ONLY");
    } else {
      codes.add("REASON_EXECUTION_ALLOWED");
    }

    // 3) Route
    if (args.draft.route === "CETUS") {
      codes.add("REASON_ROUTE_CETUS_SELECTED");
    } else if (args.draft.route === "DEEPBOOK") {
      codes.add("REASON_ROUTE_DEEPBOOK_SELECTED");
    } else {
      codes.add("REASON_ROUTE_UNKNOWN");
    }

    // 4) Slippage / MinOut
    // PR191e: slippageLabel source of truth is draft.slippageLabel only
    if (args.draft.slippageLabel) {
      codes.add(`REASON_SLIPPAGE_${args.draft.slippageLabel}`);
    }

    if (args.draft.minOut === null || args.draft.minOut === undefined) {
      codes.add("REASON_MINOUT_UNAVAILABLE");
    } else if (args.draft.minOut === "0") {
      codes.add("REASON_MINOUT_ZERO");
    } else {
      codes.add("REASON_MINOUT_OK");
    }

    // 5) Gate / Policy (if provided)
    if (args.gateStatus === "BLOCK") {
      codes.add("REASON_GATE_BLOCKED");
    }

    if (args.policyStatus === "SIM_ONLY") {
      codes.add("REASON_POLICY_SIM_ONLY");
    } else if (args.policyStatus === "BLOCKED") {
      codes.add("REASON_POLICY_BLOCKED");
    } else if (args.policyStatus === "ALLOW") {
      codes.add("REASON_POLICY_ALLOW");
    }
  } catch (error) {
    // Defensive: Never throw, return what we have
  }

  return Array.from(codes);
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

    const draft: TxDraft = {
      status: "SKIPPED" as TxDraftStatus,
      simulateOnly: opts?.simulateOnly ?? true,
      route: "UNKNOWN" as RouteProtocol,
      action: "NOOP" as SwapAction,
      amountIn: "0",
      minOut: null,
      slippageBps: constraints.slippageBps,
      deadlineSeconds: constraints.deadlineSeconds,
      checks: [],
      notes,
      errors,
    };

    // PR191e: Add execution reason codes (draft is source of truth)
    const executionReasonCodes = deriveExecutionReasonCodesV1({
      draft,
      intent: plan.intent,
    });

    return { ...draft, executionReasonCodes };
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

    const draft: TxDraft = {
      status: "ERROR" as TxDraftStatus,
      simulateOnly: opts?.simulateOnly ?? true,
      route: "UNKNOWN" as RouteProtocol,
      action: "NOOP" as SwapAction,
      amountIn: "0",
      minOut: null,
      slippageBps: constraints.slippageBps,
      deadlineSeconds: constraints.deadlineSeconds,
      checks: [],
      notes,
      errors,
    };

    // PR191e: Add execution reason codes (draft is source of truth)
    const executionReasonCodes = deriveExecutionReasonCodesV1({
      draft,
      intent: plan.intent,
    });

    return { ...draft, executionReasonCodes };
  }

  // Route (fixed to CETUS for now - future PR will add routing logic)
  const route: RouteProtocol = "CETUS";
  notes.push(`Route: ${route} (fixed for PR152, routing logic in future PR)`);

  // minOut (not calculated yet - future PR will add price/slippage calculation)
  const minOut = null;
  notes.push("minOut not calculated (will be added in routing PR)");

  const draft: TxDraft = {
    status: "DRAFT" as TxDraftStatus,
    simulateOnly: opts?.simulateOnly ?? true,
    route,
    action,
    amountIn,
    minOut,
    slippageBps: constraints.slippageBps,
    deadlineSeconds: constraints.deadlineSeconds,
    checks: [],
    notes,
    errors,
  };

  // PR191e: Add execution reason codes (draft is source of truth)
  const executionReasonCodes = deriveExecutionReasonCodesV1({
    draft,
    intent: plan.intent,
  });

  return { ...draft, executionReasonCodes };
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
 * Execute transaction (PR156: Policy-based execution control)
 *
 * @param draft - Transaction draft
 * @param policyResult - Policy evaluation result (PR156)
 * @param opts - Executor options
 * @returns Execution result
 *
 * IMPORTANT: Execution is controlled by policy system (PR156).
 * Double-key: env (MERIDIAN_EXECUTION_ENABLED) + policy (HardStop).
 *
 * Logic:
 *   1. Check policy status (ALLOW/SIM_ONLY/BLOCKED/ERROR)
 *   2. If not ALLOW → execution disabled
 *   3. Else → proceed with execution (stub for now)
 */
export async function executeTx(
  draft: TxDraft,
  policyResult: PolicyResult,
  opts?: ExecutorOptions
): Promise<TxExecutionResult> {
  const notes: string[] = [];
  const errors: string[] = [];

  // PR156: Check policy status
  if (!isExecutionAllowed(policyResult)) {
    if (policyResult.status === "SIM_ONLY") {
      errors.push("EXECUTION_ENV_DISABLED");
      notes.push("Execution disabled by env (MERIDIAN_EXECUTION_ENABLED not true)");
    } else if (policyResult.status === "BLOCKED") {
      errors.push("EXECUTION_HARDSTOP_ACTIVE");
      notes.push(
        `Execution blocked by HardStop (${policyResult.hardStopState.reason})`
      );
    } else {
      errors.push("EXECUTION_POLICY_ERROR");
      notes.push("Execution disabled by policy error");
    }

    // Add policy warnings to notes
    if (policyResult.warnings.length > 0) {
      notes.push(...policyResult.warnings);
    }

    return { ok: false, errors, notes };
  }

  // Policy allows execution
  notes.push("PR156: Policy allows execution (double-key passed)");

  // PR179: Check spec lock status
  const specLockResult = await evaluateSpecLockV1();

  // Add spec lock info to draft checks (as label-only string)
  draft.checks.push(`SPEC_LOCK_${specLockResult.status}`);

  // Block execution if spec lock has issues
  if (specLockResult.status === "ERROR") {
    errors.push("BLOCK_SPEC_LOCK_ERROR");
    notes.push("Execution blocked by spec lock error");
    notes.push(...specLockResult.warnings);
    return { ok: false, errors, notes };
  }

  if (specLockResult.status === "LOCKED_PENDING_ACK" && !specLockResult.activeSpec) {
    errors.push("BLOCK_SPEC_ACK_REQUIRED");
    notes.push("Execution blocked: Latest spec requires human ACK");
    notes.push(...specLockResult.warnings);
    return { ok: false, errors, notes };
  }

  // Allow execution with old spec if activeSpec exists
  if (specLockResult.activeSpec) {
    notes.push(`PR179: Using ACKed spec: ${specLockResult.activeSpec}`);
  }

  if (specLockResult.status === "LOCKED_EXPIRED") {
    notes.push("WARN_SPEC_TTL_EXPIRED (execution continues with old ACKed spec)");
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

    const draft: TxDraft = {
      status: "SKIPPED" as TxDraftStatus,
      simulateOnly: opts?.simulateOnly ?? true,
      route: (route.venue === "NONE" ? "UNKNOWN" : route.venue) as RouteProtocol,
      action: "NOOP" as SwapAction,
      amountIn: "0",
      minOut: null,
      slippageBps: constraints.slippageBps,
      deadlineSeconds: constraints.deadlineSeconds,
      checks: [],
      notes,
      errors: gate.blockReasons, // Block reasons as errors
    };

    // PR191e: Add execution reason codes (draft is source of truth)
    const executionReasonCodes = deriveExecutionReasonCodesV1({
      draft,
      intent: plan.intent,
      gateStatus: gate.status,
    });

    return { ...draft, executionReasonCodes };
  }

  if (gate.status === "ERROR") {
    errors.push("Gate returned ERROR status");

    const draft: TxDraft = {
      status: "ERROR" as TxDraftStatus,
      simulateOnly: opts?.simulateOnly ?? true,
      route: "UNKNOWN" as RouteProtocol,
      action: "NOOP" as SwapAction,
      amountIn: "0",
      minOut: null,
      slippageBps: constraints.slippageBps,
      deadlineSeconds: constraints.deadlineSeconds,
      checks: [],
      notes,
      errors,
    };

    // PR191e: Add execution reason codes (draft is source of truth)
    const executionReasonCodes = deriveExecutionReasonCodesV1({
      draft,
      intent: plan.intent,
      gateStatus: gate.status,
    });

    return { ...draft, executionReasonCodes };
  }

  // Gate PASS → build executable draft
  // Check if NOOP (should have been caught by gate, but defensive)
  if (plan.intent === "NOOP") {
    notes.push("Intent is NOOP (defensive check)");

    const draft: TxDraft = {
      status: "SKIPPED" as TxDraftStatus,
      simulateOnly: opts?.simulateOnly ?? true,
      route: (route.venue === "NONE" ? "UNKNOWN" : route.venue) as RouteProtocol,
      action: "NOOP" as SwapAction,
      amountIn: "0",
      minOut: null,
      slippageBps: constraints.slippageBps,
      deadlineSeconds: constraints.deadlineSeconds,
      checks: [],
      notes,
      errors,
    };

    // PR191e: Add execution reason codes (draft is source of truth)
    const executionReasonCodes = deriveExecutionReasonCodesV1({
      draft,
      intent: plan.intent,
      gateStatus: gate.status,
    });

    return { ...draft, executionReasonCodes };
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

    const draft: TxDraft = {
      status: "ERROR" as TxDraftStatus,
      simulateOnly: opts?.simulateOnly ?? true,
      route: "UNKNOWN" as RouteProtocol,
      action: "NOOP" as SwapAction,
      amountIn: "0",
      minOut: null,
      slippageBps: constraints.slippageBps,
      deadlineSeconds: constraints.deadlineSeconds,
      checks: [],
      notes,
      errors,
    };

    // PR191e: Add execution reason codes (draft is source of truth)
    const executionReasonCodes = deriveExecutionReasonCodesV1({
      draft,
      intent: plan.intent,
      gateStatus: gate.status,
    });

    return { ...draft, executionReasonCodes };
  }

  // Use route.venue
  const routeVenue = (route.venue === "NONE" ? "UNKNOWN" : route.venue) as RouteProtocol;
  notes.push(`Route: ${routeVenue}`);

  // Add gate warnings
  if (gate.warnings.length > 0) {
    notes.push(`Gate warnings: ${gate.warnings.join(", ")}`);
  }

  // minOut (not calculated yet - future PR will add price/slippage calculation)
  const minOut = null;
  notes.push("minOut not calculated (will be added in routing PR)");

  const draft: TxDraft = {
    status: "EXECUTABLE_DRAFT" as TxDraftStatus, // Gate passed
    simulateOnly: opts?.simulateOnly ?? true,
    route: routeVenue,
    action,
    amountIn,
    minOut,
    slippageBps: constraints.slippageBps,
    deadlineSeconds: constraints.deadlineSeconds,
    checks: [],
    notes,
    errors,
  };

  // PR191e: Add execution reason codes (draft is source of truth)
  const executionReasonCodes = deriveExecutionReasonCodesV1({
    draft,
    intent: plan.intent,
    gateStatus: gate.status,
  });

  return { ...draft, executionReasonCodes };
}

/**
 * Build transaction draft with simulation + gate integration (PR156)
 *
 * @param plan - Rebalance plan
 * @param route - Route plan
 * @param signals - Python signals
 * @param constraints - Rebalance constraints
 * @param portfolio - Portfolio snapshot
 * @param opts - Executor options
 * @returns Transaction draft
 *
 * Pipeline: planner → router → quote → simulation → gate → txDraft
 *
 * Logic:
 *   1. Build SimulationInput from plan and route.chosenQuote
 *   2. Run runExecutionSimulationV1() to get ExecutionSimulationRecord
 *   3. Run runSafetyGateWithSimulation() with simulation record
 *   4. Build tx draft using gate result
 *
 * Note: Execution still disabled (allowExecution=false)
 */
export async function buildTxDraftWithSimulationGate(
  plan: RebalancePlan,
  route: RoutePlan,
  signals: PythonSignals,
  constraints: RebalanceConstraints,
  portfolio: PortfolioSnapshot,
  opts?: ExecutorOptions
): Promise<TxDraft> {
  const notes: string[] = opts?.notes ? [...opts.notes] : [];

  // Step 1: Build SimulationInput
  // Note: QuoteResult only provides labels, not numeric values (PR153)
  // Simulation will return UNKNOWN labels when numeric values unavailable
  const simulationInput: SimulationInput = {
    notionalUsd: plan.notionalUsd,
    deltaWbtc: plan.deltaWeights.WBTC,
    intent: plan.intent,
    quote: route.chosenQuote
      ? {
          venue: route.venue,
          status: "AVAILABLE",
          // PR153 quotes are label-only, no numeric values available
          slippageBps: undefined,
          impactBps: undefined,
          depthUsd: undefined,
        }
      : undefined,
    oracleStatus: portfolio.oracleStatus,
  };

  notes.push("PR156: Running execution simulation pipeline");

  // Step 2: Run execution simulation
  const simulationRecord: ExecutionSimulationRecord =
    runExecutionSimulationV1(simulationInput);

  notes.push(`Simulation status: ${simulationRecord.status}`);
  if (simulationRecord.warnings.length > 0) {
    notes.push(`Simulation warnings: ${simulationRecord.warnings.join(", ")}`);
  }

  // Step 3: Run safety gate with simulation
  const gateResult: GateResult = runSafetyGateWithSimulation(
    plan,
    route,
    signals,
    constraints,
    portfolio,
    simulationRecord
  );

  notes.push(`Gate status: ${gateResult.status}`);
  if (gateResult.blockReasons.length > 0) {
    notes.push(`Gate block reasons: ${gateResult.blockReasons.join(", ")}`);
  }

  // Step 4: Build tx draft using gate result
  return buildTxDraftWithGate(plan, route, gateResult, constraints, {
    ...opts,
    notes,
  });
}

/**
 * Evaluate cooldown and add to plan (PR158)
 *
 * @param plan - Rebalance plan
 * @param cooldownState - Current cooldown state
 * @param nowTs - Current timestamp (optional, defaults to Date.now())
 * @returns Updated plan with cooldown metadata
 *
 * Helper function to evaluate cooldown and add result to plan.
 * Call this before passing plan to gate/executor functions.
 */
export function evaluateCooldownForPlan(
  plan: RebalancePlan,
  cooldownState: CooldownState,
  nowTs?: number
): RebalancePlan {
  const timestamp = nowTs ?? Date.now();
  const cooldownResult: CooldownResult = evaluateCooldownV1(
    cooldownState,
    timestamp
  );

  return {
    ...plan,
    cooldown: {
      status: cooldownResult.status,
      blocked: cooldownResult.blocked,
      reasons: cooldownResult.reasons,
      warnings: cooldownResult.warnings,
    },
  };
}

/**
 * Update cooldown state after activity (PR158)
 *
 * @param cooldownState - Current cooldown state
 * @param activityKind - Activity kind (EXECUTED or SIMULATED)
 * @param nowTs - Activity timestamp (optional, defaults to Date.now())
 * @returns Updated cooldown state
 *
 * Call this after successful execution or simulation to update cooldown state.
 * The returned state should be persisted for future cooldown evaluations.
 */
export function updateCooldownAfterActivity(
  cooldownState: CooldownState,
  activityKind: "EXECUTED" | "SIMULATED",
  nowTs?: number
): CooldownState {
  const timestamp = nowTs ?? Date.now();
  return markActivityV1(cooldownState, timestamp, activityKind);
}
