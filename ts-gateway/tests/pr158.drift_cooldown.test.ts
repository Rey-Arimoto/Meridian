/**
 * PR158: v1.4 Drift + Cooldown Gate v1 - Test Suite
 *
 * Tests for position drift monitor and cooldown gate.
 *
 * Test Cases (10):
 *   1. Drift evaluation - drift too small (< 7%)
 *   2. Drift evaluation - drift actionable (>= 7%)
 *   3. Drift evaluation - weights unavailable (UNKNOWN)
 *   4. Cooldown evaluation - no activity yet (AVAILABLE)
 *   5. Cooldown evaluation - within cooldown period (BLOCKED)
 *   6. Cooldown evaluation - cooldown expired (AVAILABLE)
 *   7. Gate integration - BLOCK_COOLDOWN_ACTIVE
 *   8. Gate integration - BLOCK_DRIFT_TOO_SMALL
 *   9. Gate integration - WARN_COOLDOWN_UNAVAILABLE (approach B)
 *   10. End-to-end - planner sets NOOP when driftTooSmall
 */

import { describe, test, expect } from "bun:test";
import {
  evaluateDriftV1,
  DriftResult,
  getDriftSummary,
} from "../src/rebalance/drift";
import {
  initCooldownStateV1,
  evaluateCooldownV1,
  markActivityV1,
  CooldownState,
  CooldownResult,
  getCooldownSummary,
} from "../src/rebalance/cooldown";
import { runSafetyGateWithSimulation } from "../src/rebalance/gate";
import { buildRebalancePlan } from "../src/rebalance/planner";
import { PortfolioSnapshot, RebalanceConstraints } from "../src/rebalance/types";

describe("PR158: Drift Evaluation", () => {
  test("Test 1: Drift too small (< 7%)", () => {
    // Current weight: 50% wBTC
    // Target weight: 55% wBTC
    // Delta: 5% (below 7% threshold)
    const snapshot: PortfolioSnapshot = {
      balances: { WBTC: "1.0", USDC: "50000", SUI: "1.0" },
      pricesUsd: { WBTC: 50000, USDC: 1.0 },
      valuesUsd: { WBTC: 50000, USDC: 50000 },
      weights: { WBTC: 0.5, USDC: 0.5 },
      totalUsd: 100000,
      oracleStatus: "AVAILABLE",
      timestamp: Date.now(),
    };

    const target = { wbtcWeight: 0.55, usdcWeight: 0.45 };

    const result: DriftResult = evaluateDriftV1(snapshot, target);

    expect(result.status).toBe("AVAILABLE");
    expect(result.driftTooSmall).toBe(true);
    expect(result.reasons).toContain("REASON_DRIFT_TOO_SMALL");
    expect(getDriftSummary(result)).toBe("DRIFT_TOO_SMALL");
  });

  test("Test 2: Drift actionable (>= 7%)", () => {
    // Current weight: 50% wBTC
    // Target weight: 60% wBTC
    // Delta: 10% (above 7% threshold)
    const snapshot: PortfolioSnapshot = {
      balances: { WBTC: "1.0", USDC: "50000", SUI: "1.0" },
      pricesUsd: { WBTC: 50000, USDC: 1.0 },
      valuesUsd: { WBTC: 50000, USDC: 50000 },
      weights: { WBTC: 0.5, USDC: 0.5 },
      totalUsd: 100000,
      oracleStatus: "AVAILABLE",
      timestamp: Date.now(),
    };

    const target = { wbtcWeight: 0.6, usdcWeight: 0.4 };

    const result: DriftResult = evaluateDriftV1(snapshot, target);

    expect(result.status).toBe("AVAILABLE");
    expect(result.driftTooSmall).toBe(false);
    expect(result.reasons).toContain("REASON_DRIFT_ACTIONABLE");
    expect(getDriftSummary(result)).toBe("DRIFT_ACTIONABLE");
  });

  test("Test 3: Drift evaluation - weights unavailable (UNKNOWN)", () => {
    // No weights available (oracle failure)
    const snapshot: PortfolioSnapshot = {
      balances: { WBTC: "1.0", USDC: "50000", SUI: "1.0" },
      pricesUsd: {}, // No prices
      timestamp: Date.now(),
    };

    const target = { wbtcWeight: 0.6, usdcWeight: 0.4 };

    const result: DriftResult = evaluateDriftV1(snapshot, target);

    expect(result.status).toBe("UNKNOWN");
    expect(result.driftTooSmall).toBeUndefined();
    expect(result.reasons).toContain("REASON_WEIGHTS_UNAVAILABLE");
    expect(result.warnings).toContain("WARN_CURRENT_WEIGHTS_MISSING");
    expect(getDriftSummary(result)).toBe("DRIFT_UNKNOWN");
  });
});

describe("PR158: Cooldown Evaluation", () => {
  test("Test 4: No activity yet (AVAILABLE)", () => {
    // Fresh cooldown state (no previous activity)
    const state: CooldownState = initCooldownStateV1();
    const nowTs = Date.now();

    const result: CooldownResult = evaluateCooldownV1(state, nowTs);

    expect(result.status).toBe("AVAILABLE");
    expect(result.blocked).toBe(false);
    expect(result.reasons).toContain("REASON_NO_ACTIVITY_YET");
    expect(getCooldownSummary(result)).toBe("COOLDOWN_AVAILABLE");
  });

  test("Test 5: Within cooldown period (BLOCKED)", () => {
    // Activity 5 minutes ago (within 10-minute cooldown)
    const nowTs = Date.now();
    const lastActivityTs = nowTs - 5 * 60 * 1000; // 5 minutes ago

    const state: CooldownState = {
      lastActivityTs,
      lastActivityKind: "EXECUTED",
    };

    const result: CooldownResult = evaluateCooldownV1(state, nowTs);

    expect(result.status).toBe("BLOCKED");
    expect(result.blocked).toBe(true);
    expect(result.reasons).toContain("REASON_COOLDOWN_ACTIVE");
    expect(getCooldownSummary(result)).toBe("COOLDOWN_ACTIVE");
  });

  test("Test 6: Cooldown expired (AVAILABLE)", () => {
    // Activity 15 minutes ago (beyond 10-minute cooldown)
    const nowTs = Date.now();
    const lastActivityTs = nowTs - 15 * 60 * 1000; // 15 minutes ago

    const state: CooldownState = {
      lastActivityTs,
      lastActivityKind: "EXECUTED",
    };

    const result: CooldownResult = evaluateCooldownV1(state, nowTs);

    expect(result.status).toBe("AVAILABLE");
    expect(result.blocked).toBe(false);
    expect(result.reasons).toContain("REASON_COOLDOWN_EXPIRED");
    expect(getCooldownSummary(result)).toBe("COOLDOWN_AVAILABLE");
  });
});

describe("PR158: Gate Integration", () => {
  test("Test 7: Gate blocks when cooldown active (BLOCK_COOLDOWN_ACTIVE)", () => {
    // Setup: Plan with active cooldown
    const plan = {
      templateId: "TPL_RISK_50" as const,
      targetWeights: { WBTC: 0.5, USDC: 0.5 },
      currentWeights: { WBTC: 0.4, USDC: 0.6 },
      deltaWeights: { WBTC: 0.1, USDC: -0.1 },
      intent: "INCREASE_WBTC" as const,
      notionalUsd: 10000,
      reasonCodes: [],
      cooldown: {
        status: "BLOCKED" as const,
        blocked: true,
        reasons: ["REASON_COOLDOWN_ACTIVE"],
        warnings: [],
      },
    };

    const route = {
      venue: "CETUS" as const,
      venueConfig: {},
      chosenQuote: {
        venue: "CETUS" as const,
        status: "AVAILABLE" as const,
        slippage: "SLIP_LOW" as const,
        impact: "IMPACT_LOW" as const,
        depth: "DEPTH_SUFFICIENT" as const,
      },
      errors: [],
    };

    const signals = {
      shockPhase: "PHASE_NORMAL",
      stress: "STRESS_CALM",
      actionShape: "ADJUST_WEIGHTS",
    };

    const constraints: RebalanceConstraints = {
      minSuiBalance: "0.05",
      minDeltaToAct: 0.05,
      maxNotionalUsd: 200000,
      cooldownSeconds: 600,
      slippageBps: 50,
      deadlineSeconds: 120,
    };

    const portfolio: PortfolioSnapshot = {
      balances: { WBTC: "1.0", USDC: "50000", SUI: "1.0" },
      pricesUsd: { WBTC: 50000, USDC: 1.0 },
      valuesUsd: { WBTC: 50000, USDC: 50000 },
      weights: { WBTC: 0.5, USDC: 0.5 },
      totalUsd: 100000,
      oracleStatus: "AVAILABLE",
      timestamp: Date.now(),
    };

    const simulation = {
      status: "PASS" as const,
      reasons: [],
      warnings: [],
    };

    const gateResult = runSafetyGateWithSimulation(
      plan,
      route,
      signals,
      constraints,
      portfolio,
      simulation
    );

    expect(gateResult.status).toBe("BLOCK");
    expect(gateResult.blockReasons).toContain("BLOCK_COOLDOWN_ACTIVE");
  });

  test("Test 8: Gate blocks when drift too small (BLOCK_DRIFT_TOO_SMALL)", () => {
    // Setup: Plan with driftTooSmall=true
    const plan = {
      templateId: "TPL_RISK_50" as const,
      targetWeights: { WBTC: 0.5, USDC: 0.5 },
      currentWeights: { WBTC: 0.48, USDC: 0.52 },
      deltaWeights: { WBTC: 0.02, USDC: -0.02 },
      intent: "INCREASE_WBTC" as const,
      notionalUsd: 2000,
      reasonCodes: [],
      drift: {
        status: "AVAILABLE" as const,
        driftTooSmall: true,
        reasons: ["REASON_DRIFT_TOO_SMALL"],
        warnings: [],
      },
    };

    const route = {
      venue: "CETUS" as const,
      venueConfig: {},
      chosenQuote: {
        venue: "CETUS" as const,
        status: "AVAILABLE" as const,
        slippage: "SLIP_LOW" as const,
        impact: "IMPACT_LOW" as const,
        depth: "DEPTH_SUFFICIENT" as const,
      },
      errors: [],
    };

    const signals = {
      shockPhase: "PHASE_NORMAL",
      stress: "STRESS_CALM",
      actionShape: "ADJUST_WEIGHTS",
    };

    const constraints: RebalanceConstraints = {
      minSuiBalance: "0.05",
      minDeltaToAct: 0.05,
      maxNotionalUsd: 200000,
      cooldownSeconds: 600,
      slippageBps: 50,
      deadlineSeconds: 120,
    };

    const portfolio: PortfolioSnapshot = {
      balances: { WBTC: "1.0", USDC: "50000", SUI: "1.0" },
      pricesUsd: { WBTC: 50000, USDC: 1.0 },
      valuesUsd: { WBTC: 50000, USDC: 50000 },
      weights: { WBTC: 0.5, USDC: 0.5 },
      totalUsd: 100000,
      oracleStatus: "AVAILABLE",
      timestamp: Date.now(),
    };

    const simulation = {
      status: "PASS" as const,
      reasons: [],
      warnings: [],
    };

    const gateResult = runSafetyGateWithSimulation(
      plan,
      route,
      signals,
      constraints,
      portfolio,
      simulation
    );

    expect(gateResult.status).toBe("BLOCK");
    expect(gateResult.blockReasons).toContain("BLOCK_DRIFT_TOO_SMALL");
  });

  test("Test 9: Gate warns when cooldown unavailable (WARN_COOLDOWN_UNAVAILABLE)", () => {
    // Approach B: Unknown cooldown → WARN only, don't BLOCK
    const plan = {
      templateId: "TPL_RISK_50" as const,
      targetWeights: { WBTC: 0.5, USDC: 0.5 },
      currentWeights: { WBTC: 0.4, USDC: 0.6 },
      deltaWeights: { WBTC: 0.1, USDC: -0.1 },
      intent: "INCREASE_WBTC" as const,
      notionalUsd: 10000,
      reasonCodes: [],
      cooldown: {
        status: "UNKNOWN" as const,
        blocked: undefined,
        reasons: [],
        warnings: ["WARN_COOLDOWN_STATE_UNKNOWN"],
      },
    };

    const route = {
      venue: "CETUS" as const,
      venueConfig: {},
      chosenQuote: {
        venue: "CETUS" as const,
        status: "AVAILABLE" as const,
        slippage: "SLIP_LOW" as const,
        impact: "IMPACT_LOW" as const,
        depth: "DEPTH_SUFFICIENT" as const,
      },
      errors: [],
    };

    const signals = {
      shockPhase: "PHASE_NORMAL",
      stress: "STRESS_CALM",
      actionShape: "ADJUST_WEIGHTS",
    };

    const constraints: RebalanceConstraints = {
      minSuiBalance: "0.05",
      minDeltaToAct: 0.05,
      maxNotionalUsd: 200000,
      cooldownSeconds: 600,
      slippageBps: 50,
      deadlineSeconds: 120,
    };

    const portfolio: PortfolioSnapshot = {
      balances: { WBTC: "1.0", USDC: "50000", SUI: "1.0" },
      pricesUsd: { WBTC: 50000, USDC: 1.0 },
      valuesUsd: { WBTC: 50000, USDC: 50000 },
      weights: { WBTC: 0.5, USDC: 0.5 },
      totalUsd: 100000,
      oracleStatus: "AVAILABLE",
      timestamp: Date.now(),
    };

    const simulation = {
      status: "PASS" as const,
      reasons: [],
      warnings: [],
    };

    const gateResult = runSafetyGateWithSimulation(
      plan,
      route,
      signals,
      constraints,
      portfolio,
      simulation
    );

    // Approach B: Don't block, just warn
    expect(gateResult.status).toBe("PASS");
    expect(gateResult.warnings).toContain("WARN_COOLDOWN_UNAVAILABLE");
  });
});

describe("PR158: End-to-End Integration", () => {
  test("Test 10: Planner sets NOOP when driftTooSmall", () => {
    // Setup: Small drift (5%), below 7% threshold
    const snapshot: PortfolioSnapshot = {
      balances: { WBTC: "1.0", USDC: "50000", SUI: "1.0" },
      pricesUsd: { WBTC: 50000, USDC: 1.0 },
      valuesUsd: { WBTC: 50000, USDC: 50000 },
      weights: { WBTC: 0.5, USDC: 0.5 },
      totalUsd: 100000,
      oracleStatus: "AVAILABLE",
      timestamp: Date.now(),
    };

    const constraints: RebalanceConstraints = {
      minSuiBalance: "0.05",
      minDeltaToAct: 0.05, // 5% (drift check is separate)
      maxNotionalUsd: 200000,
      cooldownSeconds: 600,
      slippageBps: 50,
      deadlineSeconds: 120,
    };

    // Target: 55% wBTC (5% drift, below 7% threshold)
    const plan = buildRebalancePlan(snapshot, "TPL_RISK_50", constraints);

    // Verify drift was evaluated
    expect(plan.drift).toBeDefined();
    expect(plan.drift?.status).toBe("AVAILABLE");
    expect(plan.drift?.driftTooSmall).toBe(true);

    // Verify intent was overridden to NOOP
    expect(plan.intent).toBe("NOOP");
    expect(plan.reasonCodes).toContain("DRIFT_TOO_SMALL");
  });
});

describe("PR158: Cooldown State Management", () => {
  test("Mark activity updates cooldown state", () => {
    // Initial state: no activity
    const initialState = initCooldownStateV1();
    expect(initialState.lastActivityTs).toBeUndefined();
    expect(initialState.lastActivityKind).toBeUndefined();

    // Mark execution
    const nowTs = Date.now();
    const afterExecution = markActivityV1(initialState, nowTs, "EXECUTED");

    expect(afterExecution.lastActivityTs).toBe(nowTs);
    expect(afterExecution.lastActivityKind).toBe("EXECUTED");

    // Mark simulation
    const afterSimulation = markActivityV1(afterExecution, nowTs + 1000, "SIMULATED");

    expect(afterSimulation.lastActivityTs).toBe(nowTs + 1000);
    expect(afterSimulation.lastActivityKind).toBe("SIMULATED");
  });
});
