/**
 * PR156: v1.4 Execution Simulation + Slippage Envelope v1 - Test Suite
 *
 * Verification:
 *   - Simulation: Label mapping (LOW/MEDIUM/HIGH/UNKNOWN)
 *   - Simulation: Status determination (PASS/RISKY/BLOCK/ERROR)
 *   - Gate: Simulation integration (BLOCK conditions)
 *   - Guards: Output validation (no numbers/tokens/vocab)
 *
 * Required test cases (minimum 10):
 *   1. Simulation: intent=NOOP → PASS
 *   2. Simulation: oracleStatus=ERROR → BLOCK + REASON_ORACLE_UNAVAILABLE
 *   3. Simulation: quote missing → BLOCK + REASON_MISSING_QUOTE
 *   4. Simulation: slippageBps=200 → BLOCK (SLIPPAGE_HIGH)
 *   5. Simulation: impactBps=200 → BLOCK (IMPACT_HIGH)
 *   6. Simulation: depthUsd too thin → RISKY (LIQUIDITY_THIN)
 *   7. Simulation: all low + ok → PASS
 *   8. Gate: simulation missing → BLOCK_SIMULATION_MISSING
 *   9. Gate: simulation BLOCK → BLOCK_SIMULATION_RISK_HIGH
 *  10. Guards: defensive validation (no forbidden content in output)
 */

import { strict as assert } from "assert";
import {
  runExecutionSimulationV1,
  SimulationInput,
  ExecutionSimulationRecord,
  validateSimulationOutput,
  containsNumericLike,
  containsForbiddenVocab,
  containsTokenLiteral,
} from "../src/sim";
import {
  runSafetyGateWithSimulation,
  isGatePassed,
  PythonSignals,
} from "../src/rebalance/gate";
import {
  PortfolioSnapshot,
  RebalancePlan,
  RebalanceConstraints,
} from "../src/rebalance/types";
import { RoutePlan } from "../src/rebalance/router";
import { createDefaultConstraints } from "../src/rebalance/planner";

/**
 * Test 1: Simulation - intent=NOOP → PASS
 */
async function test1_simulation_noop_pass() {
  console.log("\n[TEST 1] Simulation: intent=NOOP → PASS");

  const input: SimulationInput = {
    notionalUsd: 0,
    deltaWbtc: 0,
    intent: "NOOP",
    oracleStatus: "AVAILABLE",
  };

  const result = runExecutionSimulationV1(input);

  // Assert: status should be PASS
  assert.strictEqual(result.status, "PASS");
  assert.strictEqual(result.reasons.length, 0);
  assert.ok(result.warnings.includes("SIM_NOOP"));

  console.log("  ✓ NOOP → status=PASS");
  console.log(`  ✓ Warnings: ${result.warnings.join(", ")}`);
}

/**
 * Test 2: Simulation - oracleStatus=ERROR → BLOCK + REASON_ORACLE_UNAVAILABLE
 */
async function test2_simulation_oracle_error() {
  console.log("\n[TEST 2] Simulation: oracleStatus=ERROR → BLOCK");

  const input: SimulationInput = {
    notionalUsd: 10000,
    deltaWbtc: 0.1,
    intent: "INCREASE_WBTC",
    oracleStatus: "ERROR", // Oracle unavailable
    quote: {
      venue: "CETUS",
      status: "AVAILABLE",
      slippageBps: 30,
      impactBps: 40,
      depthUsd: 100000,
    },
  };

  const result = runExecutionSimulationV1(input);

  // Assert: status should be BLOCK
  assert.strictEqual(result.status, "BLOCK");
  assert.ok(result.reasons.includes("REASON_ORACLE_UNAVAILABLE"));
  assert.ok(result.warnings.includes("SIM_ORACLE_UNAVAILABLE"));

  console.log("  ✓ Oracle ERROR → status=BLOCK");
  console.log(`  ✓ Reasons: ${result.reasons.join(", ")}`);
}

/**
 * Test 3: Simulation - quote missing → BLOCK + REASON_MISSING_QUOTE
 */
async function test3_simulation_quote_missing() {
  console.log("\n[TEST 3] Simulation: quote missing → BLOCK");

  const input: SimulationInput = {
    notionalUsd: 10000,
    deltaWbtc: 0.1,
    intent: "INCREASE_WBTC",
    oracleStatus: "AVAILABLE",
    quote: undefined, // No quote available
  };

  const result = runExecutionSimulationV1(input);

  // Assert: status should be BLOCK
  assert.strictEqual(result.status, "BLOCK");
  assert.ok(result.reasons.includes("REASON_MISSING_QUOTE"));
  assert.ok(result.warnings.includes("SIM_MISSING_QUOTE"));

  console.log("  ✓ Quote missing → status=BLOCK");
  console.log(`  ✓ Reasons: ${result.reasons.join(", ")}`);
}

/**
 * Test 4: Simulation - slippageBps=200 → BLOCK (SLIPPAGE_HIGH)
 */
async function test4_simulation_slippage_high() {
  console.log("\n[TEST 4] Simulation: slippageBps=200 → BLOCK");

  const input: SimulationInput = {
    notionalUsd: 10000,
    deltaWbtc: 0.1,
    intent: "INCREASE_WBTC",
    oracleStatus: "AVAILABLE",
    quote: {
      venue: "CETUS",
      status: "AVAILABLE",
      slippageBps: 200, // HIGH (threshold: 150)
      impactBps: 30,
      depthUsd: 100000,
    },
  };

  const result = runExecutionSimulationV1(input);

  // Assert: status should be BLOCK
  assert.strictEqual(result.status, "BLOCK");
  assert.strictEqual(result.labels.slippage, "SLIPPAGE_HIGH");
  assert.ok(result.reasons.includes("REASON_RISK_THRESHOLD"));

  console.log("  ✓ Slippage 200bps → SLIPPAGE_HIGH → BLOCK");
  console.log(`  ✓ Labels: ${JSON.stringify(result.labels)}`);
}

/**
 * Test 5: Simulation - impactBps=200 → BLOCK (IMPACT_HIGH)
 */
async function test5_simulation_impact_high() {
  console.log("\n[TEST 5] Simulation: impactBps=200 → BLOCK");

  const input: SimulationInput = {
    notionalUsd: 10000,
    deltaWbtc: 0.1,
    intent: "INCREASE_WBTC",
    oracleStatus: "AVAILABLE",
    quote: {
      venue: "CETUS",
      status: "AVAILABLE",
      slippageBps: 30,
      impactBps: 200, // HIGH (threshold: 150)
      depthUsd: 100000,
    },
  };

  const result = runExecutionSimulationV1(input);

  // Assert: status should be BLOCK
  assert.strictEqual(result.status, "BLOCK");
  assert.strictEqual(result.labels.impact, "IMPACT_HIGH");
  assert.ok(result.reasons.includes("REASON_RISK_THRESHOLD"));

  console.log("  ✓ Impact 200bps → IMPACT_HIGH → BLOCK");
  console.log(`  ✓ Labels: ${JSON.stringify(result.labels)}`);
}

/**
 * Test 6: Simulation - depthUsd too thin → RISKY (LIQUIDITY_THIN)
 */
async function test6_simulation_liquidity_thin() {
  console.log("\n[TEST 6] Simulation: depthUsd too thin → RISKY");

  const input: SimulationInput = {
    notionalUsd: 10000,
    deltaWbtc: 0.1,
    intent: "INCREASE_WBTC",
    oracleStatus: "AVAILABLE",
    quote: {
      venue: "CETUS",
      status: "AVAILABLE",
      slippageBps: 30,
      impactBps: 40,
      depthUsd: 20000, // THIN (threshold: notional * 5 = 50000)
    },
  };

  const result = runExecutionSimulationV1(input);

  // Assert: status should be RISKY
  assert.strictEqual(result.status, "RISKY");
  assert.strictEqual(result.labels.liquidity, "LIQUIDITY_THIN");

  console.log("  ✓ Depth 20k < (10k * 5) → LIQUIDITY_THIN → RISKY");
  console.log(`  ✓ Labels: ${JSON.stringify(result.labels)}`);
}

/**
 * Test 7: Simulation - all low + ok → PASS
 */
async function test7_simulation_all_pass() {
  console.log("\n[TEST 7] Simulation: all low + ok → PASS");

  const input: SimulationInput = {
    notionalUsd: 10000,
    deltaWbtc: 0.1,
    intent: "INCREASE_WBTC",
    oracleStatus: "AVAILABLE",
    quote: {
      venue: "CETUS",
      status: "AVAILABLE",
      slippageBps: 30, // LOW (threshold: 50)
      impactBps: 40, // LOW (threshold: 50)
      depthUsd: 100000, // OK (threshold: 50000)
    },
  };

  const result = runExecutionSimulationV1(input);

  // Assert: status should be PASS
  assert.strictEqual(result.status, "PASS");
  assert.strictEqual(result.labels.slippage, "SLIPPAGE_LOW");
  assert.strictEqual(result.labels.impact, "IMPACT_LOW");
  assert.strictEqual(result.labels.liquidity, "LIQUIDITY_OK");

  console.log("  ✓ All LOW/OK → status=PASS");
  console.log(`  ✓ Labels: ${JSON.stringify(result.labels)}`);
}

/**
 * Test 8: Gate - simulation missing → BLOCK_SIMULATION_MISSING
 */
async function test8_gate_simulation_missing() {
  console.log("\n[TEST 8] Gate: simulation missing → BLOCK_SIMULATION_MISSING");

  // Create minimal test inputs
  const plan: RebalancePlan = {
    templateId: "T01-CALM-50/50" as any,
    targetWeights: { WBTC: 0.6, USDC: 0.4 },
    currentWeights: { WBTC: 0.5, USDC: 0.5 },
    deltaWeights: { WBTC: 0.1, USDC: -0.1 },
    intent: "INCREASE_WBTC",
    notionalUsd: 10000,
    reasonCodes: [],
  };

  const route: RoutePlan = {
    venue: "CETUS",
    chosenQuote: {
      venue: "CETUS",
      status: "AVAILABLE",
      impact: "IMPACT_LOW",
      slippage: "SLIP_LOW",
      depth: "DEPTH_OK",
      fee: "FEE_LOW",
      warnings: [],
    },
    reasonLabels: [],
  };

  const signals: PythonSignals = {
    shockPhase: "PHASE_NORMAL",
    stress: "STRESS_NORMAL",
    actionShape: "SHAPED_NORMAL",
  };

  const constraints: RebalanceConstraints = createDefaultConstraints();

  const portfolio: PortfolioSnapshot = {
    balances: {
      SUI: "10.0",
      USDC: "50000.0",
      WBTC: "0.5",
    },
    pricesUsd: {
      WBTC: 45000,
      USDC: 1.0,
    },
    weights: {
      WBTC: 0.5,
      USDC: 0.5,
    },
    totalUsd: 100000,
    oracleStatus: "AVAILABLE",
    timestamp: Date.now(),
  };

  // Run gate WITHOUT simulation (undefined)
  const gateResult = runSafetyGateWithSimulation(
    plan,
    route,
    signals,
    constraints,
    portfolio,
    undefined // Simulation missing
  );

  // Assert: gate should BLOCK
  assert.strictEqual(gateResult.status, "BLOCK");
  assert.ok(gateResult.blockReasons.includes("BLOCK_SIMULATION_MISSING"));

  console.log("  ✓ Simulation missing → gate=BLOCK");
  console.log(`  ✓ Block reasons: ${gateResult.blockReasons.join(", ")}`);
}

/**
 * Test 9: Gate - simulation BLOCK → BLOCK_SIMULATION_RISK_HIGH
 */
async function test9_gate_simulation_block() {
  console.log("\n[TEST 9] Gate: simulation BLOCK → BLOCK_SIMULATION_RISK_HIGH");

  // Create minimal test inputs
  const plan: RebalancePlan = {
    templateId: "T01-CALM-50/50" as any,
    targetWeights: { WBTC: 0.6, USDC: 0.4 },
    currentWeights: { WBTC: 0.5, USDC: 0.5 },
    deltaWeights: { WBTC: 0.1, USDC: -0.1 },
    intent: "INCREASE_WBTC",
    notionalUsd: 10000,
    reasonCodes: [],
  };

  const route: RoutePlan = {
    venue: "CETUS",
    chosenQuote: {
      venue: "CETUS",
      status: "AVAILABLE",
      impact: "IMPACT_LOW",
      slippage: "SLIP_LOW",
      depth: "DEPTH_OK",
      fee: "FEE_LOW",
      warnings: [],
    },
    reasonLabels: [],
  };

  const signals: PythonSignals = {
    shockPhase: "PHASE_NORMAL",
    stress: "STRESS_NORMAL",
    actionShape: "SHAPED_NORMAL",
  };

  const constraints: RebalanceConstraints = createDefaultConstraints();

  const portfolio: PortfolioSnapshot = {
    balances: {
      SUI: "10.0",
      USDC: "50000.0",
      WBTC: "0.5",
    },
    pricesUsd: {
      WBTC: 45000,
      USDC: 1.0,
    },
    weights: {
      WBTC: 0.5,
      USDC: 0.5,
    },
    totalUsd: 100000,
    oracleStatus: "AVAILABLE",
    timestamp: Date.now(),
  };

  // Create BLOCK simulation record
  const simulationRecord: ExecutionSimulationRecord = {
    status: "BLOCK",
    labels: {
      slippage: "SLIPPAGE_HIGH",
      impact: "IMPACT_HIGH",
      liquidity: "LIQUIDITY_UNKNOWN",
    },
    reasons: ["REASON_RISK_THRESHOLD"],
    warnings: [],
  };

  // Run gate with BLOCK simulation
  const gateResult = runSafetyGateWithSimulation(
    plan,
    route,
    signals,
    constraints,
    portfolio,
    simulationRecord
  );

  // Assert: gate should BLOCK
  assert.strictEqual(gateResult.status, "BLOCK");
  assert.ok(gateResult.blockReasons.includes("BLOCK_SIMULATION_RISK_HIGH"));

  console.log("  ✓ Simulation BLOCK → gate=BLOCK");
  console.log(`  ✓ Block reasons: ${gateResult.blockReasons.join(", ")}`);
}

/**
 * Test 10: Guards - defensive validation (no forbidden content)
 */
async function test10_guards_validation() {
  console.log("\n[TEST 10] Guards: defensive validation");

  // Test 10a: Numeric values should be detected
  assert.strictEqual(containsNumericLike("Value is 123"), true);
  assert.strictEqual(containsNumericLike("SLIPPAGE_LOW"), false);
  console.log("  ✓ Numeric detection works");

  // Test 10b: Forbidden vocab should be detected
  assert.strictEqual(containsForbiddenVocab("You should buy now"), true);
  assert.strictEqual(containsForbiddenVocab("REASON_ORACLE_UNAVAILABLE"), false);
  console.log("  ✓ Forbidden vocab detection works");

  // Test 10c: Token literals should be detected
  assert.strictEqual(containsTokenLiteral("Swap USDC for wBTC"), true);
  assert.strictEqual(containsTokenLiteral("REASON_MISSING_QUOTE"), false);
  console.log("  ✓ Token literal detection works");

  // Test 10d: Validate clean simulation output
  const cleanOutput = validateSimulationOutput(
    ["SIM_NOOP", "WARN_ORACLE_STALE"],
    ["REASON_ORACLE_UNAVAILABLE"]
  );
  assert.strictEqual(cleanOutput.valid, true);
  assert.strictEqual(cleanOutput.violations.length, 0);
  console.log("  ✓ Clean output validation passes");

  // Test 10e: Validate dirty output (with numeric)
  const dirtyOutput = validateSimulationOutput(
    ["Slippage is 123 bps"],
    ["REASON_ORACLE_UNAVAILABLE"]
  );
  assert.strictEqual(dirtyOutput.valid, false);
  assert.ok(dirtyOutput.violations.includes("NUMERIC_IN_WARNING"));
  console.log("  ✓ Dirty output validation catches violations");
}

/**
 * Main test runner
 */
async function main() {
  console.log("=".repeat(60));
  console.log("PR156: Execution Simulation + Slippage Envelope - Test Suite");
  console.log("=".repeat(60));

  try {
    await test1_simulation_noop_pass();
    await test2_simulation_oracle_error();
    await test3_simulation_quote_missing();
    await test4_simulation_slippage_high();
    await test5_simulation_impact_high();
    await test6_simulation_liquidity_thin();
    await test7_simulation_all_pass();
    await test8_gate_simulation_missing();
    await test9_gate_simulation_block();
    await test10_guards_validation();

    console.log("\n" + "=".repeat(60));
    console.log("✓ All PR156 tests passed!");
    console.log("=".repeat(60));
  } catch (error) {
    console.error("\n" + "=".repeat(60));
    console.error("✗ Test failed:");
    console.error(error);
    console.error("=".repeat(60));
    process.exit(1);
  }
}

// Run tests
main();
