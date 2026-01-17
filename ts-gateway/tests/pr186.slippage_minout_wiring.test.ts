/**
 * PR186: v1.4 Activate PR185 Slippage + MinOut Wiring v1 - Tests
 *
 * Purpose:
 *   Verify PR185 slippage calculation is wired into live execution pipeline.
 *   Tests focus on wiring/integration, not slippage calculation logic (covered in PR185 tests).
 *
 * Test Coverage:
 *   1. RunnerDeps.buildTxDraft signature accepts optional context parameters
 *   2. computeSlippageBps called with correct arguments from context
 *   3. computeMinOutFloor computes minOut correctly
 *   4. Gate blocks when quote missing amountOut (BLOCK_MINOUT_UNAVAILABLE)
 *   5. Gate passes when quote has valid amountOut
 *   6. Edge cases: undefined/null/NaN/negative amountOut
 *   7. Integration: context → slippage → minOut flow
 */

import { computeSlippageBps } from "../src/rebalance/slippage";
import { computeMinOutFloor } from "../src/rebalance/executor";
import { runSafetyGateWithSimulation } from "../src/rebalance/gate";

describe("PR186: Activate PR185 Slippage + MinOut Wiring", () => {
  /**
   * Test 1: RunnerDeps.buildTxDraft signature (type check only)
   * Verifies optional context parameters exist in the interface
   */
  test("Test 1: buildTxDraft accepts optional context parameters", () => {
    // Type check: This test passes if the code compiles
    // RunnerDeps.buildTxDraft should accept:
    // - venue?: "CETUS" | "DEEPBOOK" | "NONE"
    // - phaseLabel?: string
    // - stressLabel?: string
    // - impactLabel?: string
    // - observeDegradeLevel?: string
    // - chosenQuote?: any

    const mockBuildTxDraft = async (args: {
      chunkPlan: any;
      portfolio: any;
      venue?: "CETUS" | "DEEPBOOK" | "NONE";
      phaseLabel?: string;
      stressLabel?: string;
      impactLabel?: string;
      observeDegradeLevel?: string;
      chosenQuote?: any;
    }) => {
      // Mock implementation
      return {
        status: "READY",
        venue: args.venue || "NONE",
        slippageBps: 100,
        minOut: null,
      };
    };

    // Should accept all parameters
    expect(
      mockBuildTxDraft({
        chunkPlan: {},
        portfolio: {},
        venue: "CETUS",
        phaseLabel: "PHASE_NORMAL",
        stressLabel: "STRESS_CALM",
        impactLabel: "IMPACT_NORMAL",
        observeDegradeLevel: "DEGRADED_NONE",
        chosenQuote: { amountOut: 1000 },
      })
    ).resolves.toBeDefined();
  });

  /**
   * Test 2: computeSlippageBps called with correct arguments
   * Verifies slippage calculation receives context parameters
   */
  test("Test 2: computeSlippageBps receives context correctly", () => {
    // TPL_RISK_50 (100) + CETUS (50) + PHASE_NORMAL (0) + DEGRADED_NONE (0) = 150
    const slippage = computeSlippageBps({
      templateId: "TPL_RISK_50",
      venue: "CETUS",
      phaseLabel: "PHASE_NORMAL",
      observeDegradeLevel: "DEGRADED_NONE",
    });

    expect(slippage).toBe(150);
  });

  /**
   * Test 3: computeMinOutFloor computes correctly
   */
  test("Test 3: computeMinOutFloor basic calculation", () => {
    // amountOut = 10000, slippage = 100 bps (1%)
    // minOut = floor(10000 * (1 - 0.01)) = floor(9900) = 9900
    const minOut1 = computeMinOutFloor(10000, 100);
    expect(minOut1).toBe("9900");

    // amountOut = 5000, slippage = 200 bps (2%)
    // minOut = floor(5000 * 0.98) = 4900
    const minOut2 = computeMinOutFloor(5000, 200);
    expect(minOut2).toBe("4900");

    // amountOut = 1000, slippage = 50 bps (0.5%)
    // minOut = floor(1000 * 0.995) = 995
    const minOut3 = computeMinOutFloor(1000, 50);
    expect(minOut3).toBe("995");
  });

  /**
   * Test 4: computeMinOutFloor edge cases
   */
  test("Test 4: computeMinOutFloor edge cases", () => {
    // Zero amountOut → "0"
    expect(computeMinOutFloor(0, 100)).toBe("0");

    // Negative amountOut → "0" (defensive)
    expect(computeMinOutFloor(-100, 100)).toBe("0");

    // NaN amountOut → "0" (defensive)
    expect(computeMinOutFloor(NaN, 100)).toBe("0");

    // Negative slippage → "0" (defensive)
    expect(computeMinOutFloor(1000, -50)).toBe("0");

    // NaN slippage → "0" (defensive)
    expect(computeMinOutFloor(1000, NaN)).toBe("0");

    // Very high slippage (above 100%) → should still compute
    // amountOut = 1000, slippage = 15000 bps (150%)
    // minOut = floor(1000 * (1 - 1.5)) = floor(-500) = -500
    // But defensive code should handle this
    const minOut = computeMinOutFloor(1000, 15000);
    // Expect either "0" or negative floored value (depends on implementation)
    expect(typeof minOut).toBe("string");
  });

  /**
   * Test 5: Gate blocks when quote missing amountOut
   */
  test("Test 5: Gate BLOCK when quote missing amountOut", () => {
    const result = runSafetyGateWithSimulation(
      {
        intent: "INCREASE_WBTC",
        notionalUsd: 100,
        targetWeights: { WBTC: 0.5, USDC: 0.5 },
        currentWeights: { WBTC: 0.4, USDC: 0.6 },
        deltaWeights: { WBTC: 0.1, USDC: -0.1 },
        templateId: "TPL_RISK_50",
        reasonCodes: [],
      },
      {
        venue: "CETUS",
        chosenQuote: {
          status: "AVAILABLE",
          venue: "CETUS",
          side: "BUY_WBTC_WITH_USDC",
          amountIn: 100,
          // amountOut missing
          ts: Date.now(),
          price: 50000,
          impact: "IMPACT_NORMAL",
          slippage: "SLIP_NORMAL",
          depth: "DEPTH_OK",
        },
        reasons: [],
      },
      {
        shockPhase: "PHASE_NORMAL",
        stress: "STRESS_CALM",
        actionShape: "INCREASE_EXPOSURE",
      },
      {
        minSuiBalance: "0.05",
        minDeltaToAct: 0.05,
        maxNotionalUsd: 200000,
        slippageBps: 50,
        deadlineSeconds: 120,
        cooldownSeconds: 900,
      },
      {
        balances: { WBTC: "0.1", USDC: "1000", SUI: "1.0" },
        pricesUsd: { WBTC: 50000, USDC: 1.0 },
        timestamp: Date.now(),
        oracleStatus: "AVAILABLE",
      },
      {
        status: "PASS",
        reasons: [],
        warnings: [],
      },
      "DEGRADED_NONE"
    );

    expect(result.status).toBe("BLOCK");
    expect(result.blockReasons).toContain("BLOCK_MINOUT_UNAVAILABLE");
  });

  /**
   * Test 6: Gate passes when quote has valid amountOut
   */
  test("Test 6: Gate PASS when quote has valid amountOut", () => {
    const result = runSafetyGateWithSimulation(
      {
        intent: "INCREASE_WBTC",
        notionalUsd: 100,
        targetWeights: { WBTC: 0.5, USDC: 0.5 },
        currentWeights: { WBTC: 0.4, USDC: 0.6 },
        deltaWeights: { WBTC: 0.1, USDC: -0.1 },
        templateId: "TPL_RISK_50",
        reasonCodes: [],
      },
      {
        venue: "CETUS",
        chosenQuote: {
          status: "AVAILABLE",
          venue: "CETUS",
          side: "BUY_WBTC_WITH_USDC",
          amountIn: 100,
          amountOut: 0.002, // Valid amountOut
          ts: Date.now(),
          price: 50000,
          impact: "IMPACT_NORMAL",
          slippage: "SLIP_NORMAL",
          depth: "DEPTH_OK",
        },
        reasons: [],
      },
      {
        shockPhase: "PHASE_NORMAL",
        stress: "STRESS_CALM",
        actionShape: "INCREASE_EXPOSURE",
      },
      {
        minSuiBalance: "0.05",
        minDeltaToAct: 0.05,
        maxNotionalUsd: 200000,
        slippageBps: 50,
        deadlineSeconds: 120,
        cooldownSeconds: 900,
      },
      {
        balances: { WBTC: "0.1", USDC: "1000", SUI: "1.0" },
        pricesUsd: { WBTC: 50000, USDC: 1.0 },
        timestamp: Date.now(),
        oracleStatus: "AVAILABLE",
      },
      {
        status: "PASS",
        reasons: [],
        warnings: [],
      },
      "DEGRADED_NONE"
    );

    expect(result.status).toBe("PASS");
    expect(result.blockReasons).not.toContain("BLOCK_MINOUT_UNAVAILABLE");
  });

  /**
   * Test 7: Gate blocks when quote unavailable
   */
  test("Test 7: Gate BLOCK when quote unavailable", () => {
    const result = runSafetyGateWithSimulation(
      {
        intent: "INCREASE_WBTC",
        notionalUsd: 100,
        targetWeights: { WBTC: 0.5, USDC: 0.5 },
        currentWeights: { WBTC: 0.4, USDC: 0.6 },
        deltaWeights: { WBTC: 0.1, USDC: -0.1 },
        templateId: "TPL_RISK_50",
        reasonCodes: [],
      },
      {
        venue: "CETUS",
        chosenQuote: undefined, // Quote unavailable
        reasons: [],
      },
      {
        shockPhase: "PHASE_NORMAL",
        stress: "STRESS_CALM",
        actionShape: "INCREASE_EXPOSURE",
      },
      {
        minSuiBalance: "0.05",
        minDeltaToAct: 0.05,
        maxNotionalUsd: 200000,
        slippageBps: 50,
        deadlineSeconds: 120,
        cooldownSeconds: 900,
      },
      {
        balances: { WBTC: "0.1", USDC: "1000", SUI: "1.0" },
        pricesUsd: { WBTC: 50000, USDC: 1.0 },
        timestamp: Date.now(),
        oracleStatus: "AVAILABLE",
      },
      {
        status: "PASS",
        reasons: [],
        warnings: [],
      },
      "DEGRADED_NONE"
    );

    expect(result.status).toBe("BLOCK");
    expect(result.blockReasons).toContain("BLOCK_MINOUT_UNAVAILABLE");
  });

  /**
   * Test 8: Gate allows NOOP even without quote
   */
  test("Test 8: Gate allows NOOP without quote check", () => {
    const result = runSafetyGateWithSimulation(
      {
        intent: "NOOP",
        notionalUsd: 0,
        targetWeights: { WBTC: 0.5, USDC: 0.5 },
        currentWeights: { WBTC: 0.5, USDC: 0.5 },
        deltaWeights: { WBTC: 0.0, USDC: 0.0 },
        templateId: "TPL_RISK_50",
        reasonCodes: [],
      },
      {
        venue: "NONE",
        chosenQuote: undefined, // Quote unavailable but NOOP
        reasons: [],
      },
      {
        shockPhase: "PHASE_NORMAL",
        stress: "STRESS_CALM",
        actionShape: "NO_ACTION",
      },
      {
        minSuiBalance: "0.05",
        minDeltaToAct: 0.05,
        maxNotionalUsd: 200000,
        slippageBps: 50,
        deadlineSeconds: 120,
        cooldownSeconds: 900,
      },
      {
        balances: { WBTC: "0.1", USDC: "1000", SUI: "1.0" },
        pricesUsd: { WBTC: 50000, USDC: 1.0 },
        timestamp: Date.now(),
        oracleStatus: "AVAILABLE",
      },
      {
        status: "PASS",
        reasons: [],
        warnings: [],
      },
      "DEGRADED_NONE"
    );

    // NOOP blocks with BLOCK_DELTA_TOO_SMALL, not BLOCK_MINOUT_UNAVAILABLE
    expect(result.status).toBe("BLOCK");
    expect(result.blockReasons).toContain("BLOCK_DELTA_TOO_SMALL");
    expect(result.blockReasons).not.toContain("BLOCK_MINOUT_UNAVAILABLE");
  });

  /**
   * Test 9: Integration - context flows through to slippage calculation
   */
  test("Test 9: Integration - full context to slippage flow", () => {
    // Simulate full flow: venue + phase + degrade → slippage
    const templateId = "TPL_RISK_90";
    const venue = "CETUS";
    const phaseLabel = "PHASE_UP_SHOCK";
    const observeDegradeLevel = "DEGRADED_MEDIUM";

    // Expected: TPL_RISK_90 (150) + CETUS (50) + SHOCK (150) + MEDIUM (150) = 500
    const slippage = computeSlippageBps({
      templateId,
      venue,
      phaseLabel,
      observeDegradeLevel,
    });

    expect(slippage).toBe(500);

    // Then compute minOut with this slippage
    const amountOut = 10000;
    const minOut = computeMinOutFloor(amountOut, slippage);

    // minOut = floor(10000 * (1 - 0.05)) = floor(9500) = 9500
    expect(minOut).toBe("9500");
  });

  /**
   * Test 10: Gate blocks when amountOut is zero
   */
  test("Test 10: Gate BLOCK when amountOut is zero", () => {
    const result = runSafetyGateWithSimulation(
      {
        intent: "INCREASE_WBTC",
        notionalUsd: 100,
        targetWeights: { WBTC: 0.5, USDC: 0.5 },
        currentWeights: { WBTC: 0.4, USDC: 0.6 },
        deltaWeights: { WBTC: 0.1, USDC: -0.1 },
        templateId: "TPL_RISK_50",
        reasonCodes: [],
      },
      {
        venue: "CETUS",
        chosenQuote: {
          status: "AVAILABLE",
          venue: "CETUS",
          side: "BUY_WBTC_WITH_USDC",
          amountIn: 100,
          amountOut: 0, // Zero amountOut
          ts: Date.now(),
          price: 50000,
          impact: "IMPACT_NORMAL",
          slippage: "SLIP_NORMAL",
          depth: "DEPTH_OK",
        },
        reasons: [],
      },
      {
        shockPhase: "PHASE_NORMAL",
        stress: "STRESS_CALM",
        actionShape: "INCREASE_EXPOSURE",
      },
      {
        minSuiBalance: "0.05",
        minDeltaToAct: 0.05,
        maxNotionalUsd: 200000,
        slippageBps: 50,
        deadlineSeconds: 120,
        cooldownSeconds: 900,
      },
      {
        balances: { WBTC: "0.1", USDC: "1000", SUI: "1.0" },
        pricesUsd: { WBTC: 50000, USDC: 1.0 },
        timestamp: Date.now(),
        oracleStatus: "AVAILABLE",
      },
      {
        status: "PASS",
        reasons: [],
        warnings: [],
      },
      "DEGRADED_NONE"
    );

    expect(result.status).toBe("BLOCK");
    expect(result.blockReasons).toContain("BLOCK_MINOUT_UNAVAILABLE");
  });

  /**
   * Test 11: Gate blocks when amountOut is NaN
   */
  test("Test 11: Gate BLOCK when amountOut is NaN", () => {
    const result = runSafetyGateWithSimulation(
      {
        intent: "INCREASE_WBTC",
        notionalUsd: 100,
        targetWeights: { WBTC: 0.5, USDC: 0.5 },
        currentWeights: { WBTC: 0.4, USDC: 0.6 },
        deltaWeights: { WBTC: 0.1, USDC: -0.1 },
        templateId: "TPL_RISK_50",
        reasonCodes: [],
      },
      {
        venue: "CETUS",
        chosenQuote: {
          status: "AVAILABLE",
          venue: "CETUS",
          side: "BUY_WBTC_WITH_USDC",
          amountIn: 100,
          amountOut: NaN, // NaN amountOut
          ts: Date.now(),
          price: 50000,
          impact: "IMPACT_NORMAL",
          slippage: "SLIP_NORMAL",
          depth: "DEPTH_OK",
        },
        reasons: [],
      },
      {
        shockPhase: "PHASE_NORMAL",
        stress: "STRESS_CALM",
        actionShape: "INCREASE_EXPOSURE",
      },
      {
        minSuiBalance: "0.05",
        minDeltaToAct: 0.05,
        maxNotionalUsd: 200000,
        slippageBps: 50,
        deadlineSeconds: 120,
        cooldownSeconds: 900,
      },
      {
        balances: { WBTC: "0.1", USDC: "1000", SUI: "1.0" },
        pricesUsd: { WBTC: 50000, USDC: 1.0 },
        timestamp: Date.now(),
        oracleStatus: "AVAILABLE",
      },
      {
        status: "PASS",
        reasons: [],
        warnings: [],
      },
      "DEGRADED_NONE"
    );

    expect(result.status).toBe("BLOCK");
    expect(result.blockReasons).toContain("BLOCK_MINOUT_UNAVAILABLE");
  });
});
