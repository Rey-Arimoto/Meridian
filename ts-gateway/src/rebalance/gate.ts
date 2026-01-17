/**
 * PR153: v1.4 Quote/Safety Gate (READ-ONLY)
 * PR155: Oracle status checks added
 * PR156: Simulation checks added
 * PR158: Cooldown and Drift checks added
 *
 * Purpose:
 *   Validate rebalance plan against safety constraints.
 *   Determines if tx draft can be created (PASS) or blocked (BLOCK).
 *
 * Constitutional Constraints:
 *   - READ-ONLY: No execution, just validation
 *   - Conservative: When in doubt, BLOCK
 *   - Fixed rules: No learning, no optimization
 *   - Double guard: TS-side checks Python-side constraints
 *   - Safe defaults: Oracle/simulation unavailable → BLOCK (PR155/156)
 *   - Cooldown approach B: Unknown → WARN only, don't BLOCK (PR158)
 *
 * Gate Rules (BLOCK conditions - priority order):
 *   A) Upper-level prohibitions (from Python):
 *      - actionShape = FREEZE_STATE → BLOCK
 *      - stress = STRESSED → BLOCK
 *      - shockPhase = PHASE_DOWN_SHOCK → BLOCK
 *      - shockPhase = PHASE_UP_REVERSAL → BLOCK
 *
 *   B) Execution impossibility:
 *      - route.venue = NONE → BLOCK
 *      - oracle unavailable → BLOCK (PR155)
 *      - simulation missing/error → BLOCK (PR156)
 *
 *   C) Cooldown/Drift (PR158):
 *      - cooldown.blocked = true → BLOCK
 *      - drift.driftTooSmall = true → BLOCK (redundant with NOOP)
 *
 *   D) Trade safety:
 *      - SUI balance < minSuiBalance → BLOCK
 *      - delta < minDeltaToAct → BLOCK
 *      - notionalUsd > maxNotionalUsd (200k) → BLOCK
 *      - impact = IMPACT_HIGH → BLOCK
 *      - slippage = SLIP_HIGH → BLOCK
 *      - depth = DEPTH_THIN → BLOCK
 *
 * PASS condition:
 *   - None of the above conditions met
 *
 * IMPORTANT:
 *   PASS = "draft creation allowed"
 *   Execution still requires allowExecution=true
 */

import { RebalancePlan, RebalanceConstraints, PortfolioSnapshot } from "./types";
import { RoutePlan } from "./router";
import type { ExecutionSimulationRecord } from "../sim/types";

/**
 * Python signals (extracted from Python PR151/149/146/147 output)
 */
export interface PythonSignals {
  // Shock phase (PR149)
  shockPhase?: string;

  // Stress (PR146/150)
  stress?: string;

  // Action shape (PR147)
  actionShape?: string;

  // Template ID (PR151)
  templateId?: string;
}

/**
 * Gate result
 */
export interface GateResult {
  // Status (PASS = allowed, BLOCK = blocked, ERROR = error)
  status: "PASS" | "BLOCK" | "ERROR";

  // Block reasons (if BLOCK)
  blockReasons: string[];

  // Warnings
  warnings: string[];
}

/**
 * Run safety gate checks
 *
 * @param plan - Rebalance plan (PR152)
 * @param route - Route plan (PR153)
 * @param signals - Python signals (PR151/149/146/147)
 * @param constraints - Rebalance constraints
 * @param portfolio - Portfolio snapshot
 * @returns Gate result
 *
 * Logic: Check BLOCK conditions first-match-wins.
 * If any BLOCK condition met, return BLOCK immediately.
 * If all checks pass, return PASS.
 */
export function runSafetyGate(
  plan: RebalancePlan,
  route: RoutePlan,
  signals: PythonSignals,
  constraints: RebalanceConstraints,
  portfolio: PortfolioSnapshot
): GateResult {
  const blockReasons: string[] = [];
  const warnings: string[] = [];

  // ===== A) Upper-level prohibitions (from Python) =====

  // A1: FREEZE_STATE
  if (signals.actionShape === "FREEZE_STATE") {
    blockReasons.push("BLOCK_FREEZE_STATE");
  }

  // A2: STRESSED
  if (signals.stress === "STRESS_STRESSED") {
    blockReasons.push("BLOCK_STRESSED");
  }

  // A3: PHASE_DOWN_SHOCK
  if (signals.shockPhase === "PHASE_DOWN_SHOCK") {
    blockReasons.push("BLOCK_DOWN_SHOCK");
  }

  // A4: PHASE_UP_REVERSAL
  if (signals.shockPhase === "PHASE_UP_REVERSAL") {
    blockReasons.push("BLOCK_UP_REVERSAL");
  }

  // ===== B) Execution impossibility =====

  // B1: No route
  if (route.venue === "NONE") {
    blockReasons.push("BLOCK_NO_ROUTE");
  }

  // B2: Oracle unavailable (PR155)
  if (portfolio.oracleStatus === "ERROR") {
    blockReasons.push("BLOCK_ORACLE_UNAVAILABLE");
  }

  // B3: Oracle stale (PR155)
  if (portfolio.oracleStatus === "STALE") {
    blockReasons.push("BLOCK_ORACLE_STALE");
  }

  // ===== C) Trade safety =====

  // C1: Gas insufficient (SUI)
  const suiBalance = parseFloat(portfolio.balances.SUI);
  const minSui = parseFloat(constraints.minSuiBalance);
  if (suiBalance < minSui) {
    blockReasons.push("BLOCK_NO_GAS");
  }

  // C2: Delta too small (already in plan.intent=NOOP, but double-check)
  if (plan.intent === "NOOP") {
    blockReasons.push("BLOCK_DELTA_TOO_SMALL");
  }

  // C3: Notional unavailable (PR155 - oracle failed to provide valuation)
  if (
    plan.notionalUsd === undefined ||
    plan.notionalUsd === null ||
    isNaN(plan.notionalUsd)
  ) {
    blockReasons.push("BLOCK_NOTIONAL_UNAVAILABLE");
  }

  // C4: Notional cap exceeded
  // Default cap: 200,000 USD (PR153 update)
  const maxNotional = constraints.maxNotionalUsd ?? 200000;
  if (plan.notionalUsd > maxNotional) {
    blockReasons.push("BLOCK_NOTIONAL_CAP");
  }

  // C4: Impact too high
  if (route.chosenQuote && route.chosenQuote.impact === "IMPACT_HIGH") {
    blockReasons.push("BLOCK_IMPACT_HIGH");
  }

  // C5: Slippage too high
  if (route.chosenQuote && route.chosenQuote.slippage === "SLIP_HIGH") {
    blockReasons.push("BLOCK_SLIPPAGE_HIGH");
  }

  // C6: Depth too thin
  if (route.chosenQuote && route.chosenQuote.depth === "DEPTH_THIN") {
    blockReasons.push("BLOCK_DEPTH_THIN");
  }

  // ===== Determine status =====

  if (blockReasons.length > 0) {
    return { status: "BLOCK", blockReasons, warnings };
  }

  return { status: "PASS", blockReasons, warnings };
}

/**
 * Check if gate allows execution
 *
 * @param result - Gate result
 * @returns True if gate passed (status = PASS)
 */
export function isGatePassed(result: GateResult): boolean {
  return result.status === "PASS";
}

/**
 * Run safety gate with simulation (PR156)
 * PR184: Updated with observe degrade block reasons
 * PR187: Updated to use NormalizedQuoteV1
 *
 * @param plan - Rebalance plan
 * @param route - Route plan
 * @param signals - Python signals
 * @param constraints - Rebalance constraints
 * @param portfolio - Portfolio snapshot
 * @param simulation - Execution simulation record (PR156)
 * @param observeDegradeLevel - Observe degrade level (PR184, optional)
 * @param normalizedQuote - Normalized quote (PR187, optional)
 * @returns Gate result
 *
 * Adds simulation checks to existing gate logic.
 * Simulation checks run AFTER upper-level prohibitions but BEFORE trade safety.
 * Conservative: Simulation missing → BLOCK.
 *
 * PR184: Adds degrade-based tightening:
 *   - HEAVY/UNKNOWN + quote/consistency UNKNOWN → BLOCK_OBSERVE_DEGRADED_UNCERTAIN
 *   - MEDIUM + quote stale → BLOCK_OBSERVE_DEGRADED_QUOTE_REQUIRE_FRESH
 *
 * PR187: Uses NormalizedQuoteV1 for all quote-based checks.
 */
export function runSafetyGateWithSimulation(
  plan: RebalancePlan,
  route: RoutePlan,
  signals: PythonSignals,
  constraints: RebalanceConstraints,
  portfolio: PortfolioSnapshot,
  simulation?: ExecutionSimulationRecord,
  observeDegradeLevel?: string,
  normalizedQuote?: any // PR187: NormalizedQuoteV1 (imported type)
): GateResult {
  const blockReasons: string[] = [];
  const warnings: string[] = [];

  // ===== A) Upper-level prohibitions (from Python) =====
  // Same as runSafetyGate

  if (signals.actionShape === "FREEZE_STATE") {
    blockReasons.push("BLOCK_FREEZE_STATE");
  }

  if (signals.stress === "STRESS_STRESSED") {
    blockReasons.push("BLOCK_STRESSED");
  }

  if (signals.shockPhase === "PHASE_DOWN_SHOCK") {
    blockReasons.push("BLOCK_DOWN_SHOCK");
  }

  if (signals.shockPhase === "PHASE_UP_REVERSAL") {
    blockReasons.push("BLOCK_UP_REVERSAL");
  }

  // ===== B) Execution impossibility =====

  if (route.venue === "NONE") {
    blockReasons.push("BLOCK_NO_ROUTE");
  }

  if (portfolio.oracleStatus === "ERROR") {
    blockReasons.push("BLOCK_ORACLE_UNAVAILABLE");
  }

  if (portfolio.oracleStatus === "STALE") {
    blockReasons.push("BLOCK_ORACLE_STALE");
  }

  // ===== B-SIM) Simulation checks (PR156) =====

  // SIM1: Simulation missing (conservative)
  if (!simulation) {
    blockReasons.push("BLOCK_SIMULATION_MISSING");
  } else {
    // SIM2: Simulation ERROR
    if (simulation.status === "ERROR") {
      blockReasons.push("BLOCK_SIMULATION_ERROR");
    }

    // SIM3: Simulation BLOCK (high risk)
    if (simulation.status === "BLOCK") {
      blockReasons.push("BLOCK_SIMULATION_RISK_HIGH");

      // Add specific reasons from simulation
      if (simulation.reasons.includes("REASON_ORACLE_UNAVAILABLE")) {
        blockReasons.push("BLOCK_SIMULATION_ORACLE");
      }
      if (simulation.reasons.includes("REASON_MISSING_QUOTE")) {
        blockReasons.push("BLOCK_SIMULATION_NO_QUOTE");
      }
    }

    // Add simulation warnings (if any)
    if (simulation.warnings.length > 0) {
      warnings.push(...simulation.warnings);
    }
  }

  // ===== B-DEGRADE) Observe degrade checks (PR184) =====

  // DEGRADE1: HEAVY/UNKNOWN + quote unavailable → BLOCK
  if (
    observeDegradeLevel === "DEGRADED_HEAVY" ||
    observeDegradeLevel === "DEGRADED_UNKNOWN"
  ) {
    // Check if quote is unavailable (PR187: use normalizedQuote)
    const quoteUnavailable =
      !normalizedQuote ||
      normalizedQuote.status === "UNAVAILABLE" ||
      normalizedQuote.status === "ERROR";

    if (quoteUnavailable) {
      blockReasons.push("BLOCK_OBSERVE_DEGRADED_UNCERTAIN");
      warnings.push("WARN_OBSERVE_DEGRADED_QUOTE_UNAVAILABLE");
    }
  }

  // DEGRADE2: MEDIUM + quote stale → BLOCK
  // Note: "Stale" is determined by timestamp freshness (>30s old)
  if (observeDegradeLevel === "DEGRADED_MEDIUM") {
    // Check if quote is stale (older than 30 seconds) (PR187: use normalizedQuote)
    const nowMs = Date.now();
    const quoteStale =
      normalizedQuote &&
      normalizedQuote.status === "AVAILABLE" &&
      nowMs - normalizedQuote.ts > 30000; // 30 seconds

    if (quoteStale) {
      blockReasons.push("BLOCK_OBSERVE_DEGRADED_QUOTE_REQUIRE_FRESH");
      warnings.push("WARN_OBSERVE_DEGRADED_QUOTE_STALE");
    }
  }

  // DEGRADE3: LIGHT → WARN only (no block)
  if (observeDegradeLevel === "DEGRADED_LIGHT") {
    warnings.push("WARN_OBSERVE_DEGRADED_LIGHT");
  }

  // ===== C) Cooldown/Drift checks (PR158) =====

  // C1: Cooldown check
  if (plan.cooldown) {
    if (plan.cooldown.blocked === true) {
      blockReasons.push("BLOCK_COOLDOWN_ACTIVE");
    } else if (
      plan.cooldown.status === "UNKNOWN" ||
      plan.cooldown.status === "ERROR"
    ) {
      // Approach B: Don't block, just warn
      warnings.push("WARN_COOLDOWN_UNAVAILABLE");
    }

    // Add cooldown warnings
    if (plan.cooldown.warnings.length > 0) {
      warnings.push(...plan.cooldown.warnings);
    }
  }

  // C2: Drift check (redundant with plan.intent=NOOP, but explicit)
  if (plan.drift) {
    if (plan.drift.driftTooSmall === true) {
      blockReasons.push("BLOCK_DRIFT_TOO_SMALL");
    }

    // Add drift warnings
    if (plan.drift.warnings.length > 0) {
      warnings.push(...plan.drift.warnings);
    }
  }

  // ===== D) Trade safety =====

  const suiBalance = parseFloat(portfolio.balances.SUI);
  const minSui = parseFloat(constraints.minSuiBalance);
  if (suiBalance < minSui) {
    blockReasons.push("BLOCK_NO_GAS");
  }

  if (plan.intent === "NOOP") {
    blockReasons.push("BLOCK_DELTA_TOO_SMALL");
  }

  if (
    plan.notionalUsd === undefined ||
    plan.notionalUsd === null ||
    isNaN(plan.notionalUsd)
  ) {
    blockReasons.push("BLOCK_NOTIONAL_UNAVAILABLE");
  }

  const maxNotional = constraints.maxNotionalUsd ?? 200000;
  if (plan.notionalUsd > maxNotional) {
    blockReasons.push("BLOCK_NOTIONAL_CAP");
  }

  // PR187: Use normalizedQuote for impact/depth checks
  if (normalizedQuote && normalizedQuote.impactLabel === "IMPACT_HIGH") {
    blockReasons.push("BLOCK_IMPACT_HIGH");
  }

  // Note: Old "slippage" label check removed (PR187)
  // Slippage is now computed dynamically via computeSlippageBps

  if (normalizedQuote && normalizedQuote.depthLabel === "DEPTH_THIN") {
    blockReasons.push("BLOCK_DEPTH_THIN");
  }

  // D7: MinOut unavailable (PR186/PR187 - slippage protection)
  // Conservative: If we can't compute minOut, BLOCK execution
  if (plan.intent !== "NOOP") {
    const canComputeMinOut =
      normalizedQuote &&
      normalizedQuote.status === "AVAILABLE" &&
      typeof normalizedQuote.amountOut === "number" &&
      !isNaN(normalizedQuote.amountOut) &&
      normalizedQuote.amountOut > 0;

    if (!canComputeMinOut) {
      blockReasons.push("BLOCK_MINOUT_UNAVAILABLE");
    }
  }

  // ===== Determine status =====

  if (blockReasons.length > 0) {
    return { status: "BLOCK", blockReasons, warnings };
  }

  return { status: "PASS", blockReasons, warnings };
}
