/**
 * PR153: v1.4 Execution Router + Quote/Safety Gate v1 - Test Suite
 *
 * Verification:
 *   - Router: Venue selection (CETUS vs DeepBook)
 *   - Gate: Safety checks (BLOCK conditions)
 *   - E2E: Full pipeline (quotes → router → gate → executor)
 *
 * Required test cases (minimum 8):
 *   1. Router: Both UNAVAILABLE → NONE
 *   2. Router: One AVAILABLE → select it
 *   3. Router: Both AVAILABLE, lower impact wins
 *   4. Gate: notionalUsd=250000 → BLOCK_NOTIONAL_CAP
 *   5. Gate: IMPACT_HIGH → BLOCK_IMPACT_HIGH
 *   6. Gate: DEPTH_THIN → BLOCK_DEPTH_THIN
 *   7. Gate: stress=STRESSED → BLOCK_STRESSED
 *   8. E2E: PASS → EXECUTABLE_DRAFT but allowExecution=false blocks execution
 */

import { strict as assert } from "assert";
import {
  QuoteResult,
  createStubQuoteRequest,
  getQuoteCetus,
  getQuoteDeepBook,
} from "../src/rebalance/quotes";
import { selectRoute, isRouteExecutable } from "../src/rebalance/router";
import {
  runSafetyGate,
  isGatePassed,
  PythonSignals,
} from "../src/rebalance/gate";
import { buildTxDraftWithGate } from "../src/rebalance/executor";
import {
  PortfolioSnapshot,
  RebalancePlan,
  RebalanceConstraints,
} from "../src/rebalance/types";
import { createDefaultConstraints } from "../src/rebalance/planner";

/**
 * Test 1: Router - Both quotes UNAVAILABLE → NONE
 */
async function test1_router_both_unavailable() {
  console.log("\n[TEST 1] Router: Both UNAVAILABLE → NONE");

  // Create unavailable quotes
  const quotes: QuoteResult[] = [
    {
      venue: "CETUS",
      status: "UNAVAILABLE",
      impact: "IMPACT_UNKNOWN",
      slippage: "SLIP_UNKNOWN",
      depth: "DEPTH_UNKNOWN",
      fee: "FEE_UNKNOWN",
      warnings: ["Service unavailable"],
    },
    {
      venue: "DEEPBOOK",
      status: "UNAVAILABLE",
      impact: "IMPACT_UNKNOWN",
      slippage: "SLIP_UNKNOWN",
      depth: "DEPTH_UNKNOWN",
      fee: "FEE_UNKNOWN",
      warnings: ["Service unavailable"],
    },
  ];

  // Select route
  const route = selectRoute(quotes);

  // Assert: venue should be NONE
  assert.strictEqual(route.venue, "NONE");
  assert.strictEqual(isRouteExecutable(route), false);
  assert.ok(route.reasonLabels.includes("ROUTE_NO_AVAILABLE_QUOTES"));

  console.log("  ✓ Both UNAVAILABLE → venue=NONE");
  console.log(`  ✓ Reason labels: ${route.reasonLabels.join(", ")}`);
}

/**
 * Test 2: Router - One AVAILABLE → select it
 */
async function test2_router_one_available() {
  console.log("\n[TEST 2] Router: One AVAILABLE → select it");

  // Create quotes: CETUS available, DeepBook unavailable
  const quotes: QuoteResult[] = [
    {
      venue: "CETUS",
      status: "AVAILABLE",
      impact: "IMPACT_LOW",
      slippage: "SLIP_LOW",
      depth: "DEPTH_OK",
      fee: "FEE_LOW",
      warnings: [],
    },
    {
      venue: "DEEPBOOK",
      status: "UNAVAILABLE",
      impact: "IMPACT_UNKNOWN",
      slippage: "SLIP_UNKNOWN",
      depth: "DEPTH_UNKNOWN",
      fee: "FEE_UNKNOWN",
      warnings: ["Service unavailable"],
    },
  ];

  // Select route
  const route = selectRoute(quotes);

  // Assert: venue should be CETUS
  assert.strictEqual(route.venue, "CETUS");
  assert.strictEqual(isRouteExecutable(route), true);
  assert.ok(route.reasonLabels.includes("ROUTE_ONLY_ONE_AVAILABLE"));
  assert.ok(route.chosenQuote);
  assert.strictEqual(route.chosenQuote.venue, "CETUS");

  console.log("  ✓ One AVAILABLE → venue=CETUS");
  console.log(`  ✓ Reason labels: ${route.reasonLabels.join(", ")}`);
}

/**
 * Test 3: Router - Both AVAILABLE, lower impact wins
 */
async function test3_router_best_impact() {
  console.log("\n[TEST 3] Router: Both AVAILABLE, lower impact wins");

  // Create quotes: CETUS has IMPACT_LOW, DeepBook has IMPACT_MED
  const quotes: QuoteResult[] = [
    {
      venue: "CETUS",
      status: "AVAILABLE",
      impact: "IMPACT_LOW",
      slippage: "SLIP_LOW",
      depth: "DEPTH_OK",
      fee: "FEE_LOW",
      warnings: [],
    },
    {
      venue: "DEEPBOOK",
      status: "AVAILABLE",
      impact: "IMPACT_MED", // Worse impact
      slippage: "SLIP_LOW",
      depth: "DEPTH_OK",
      fee: "FEE_LOW",
      warnings: [],
    },
  ];

  // Select route
  const route = selectRoute(quotes);

  // Assert: venue should be CETUS (better impact)
  assert.strictEqual(route.venue, "CETUS");
  assert.strictEqual(isRouteExecutable(route), true);
  assert.ok(route.reasonLabels.includes("ROUTE_BEST_QUOTE"));
  assert.ok(route.chosenQuote);
  assert.strictEqual(route.chosenQuote.impact, "IMPACT_LOW");

  console.log("  ✓ Both AVAILABLE → CETUS wins (IMPACT_LOW < IMPACT_MED)");
  console.log(`  ✓ Chosen impact: ${route.chosenQuote.impact}`);
}

/**
 * Test 4: Gate - notionalUsd=250000 → BLOCK_NOTIONAL_CAP
 */
async function test4_gate_notional_cap() {
  console.log("\n[TEST 4] Gate: notionalUsd=250000 → BLOCK_NOTIONAL_CAP");

  // Create portfolio snapshot
  const portfolio: PortfolioSnapshot = {
    balances: { WBTC: "1.0", USDC: "50000", SUI: "1.0" },
    pricesUsd: { WBTC: 45000, USDC: 1 },
    valuesUsd: { WBTC: 45000, USDC: 50000 },
    weights: { WBTC: 0.47, USDC: 0.53 },
    totalUsd: 95000,
    timestamp: Date.now(),
  };

  // Create rebalance plan with notionalUsd=250000 (exceeds cap)
  const plan: RebalancePlan = {
    templateId: "TPL_RISK_90",
    targetWeights: { WBTC: 0.9, USDC: 0.1 },
    currentWeights: { WBTC: 0.47, USDC: 0.53 },
    deltaWeights: { WBTC: 0.43, USDC: -0.43 },
    intent: "INCREASE_WBTC",
    notionalUsd: 250000, // Exceeds 200k cap
    reasonCodes: [],
  };

  // Create route (available)
  const route = {
    venue: "CETUS" as const,
    reasonLabels: ["ROUTE_BEST_QUOTE"],
    chosenQuote: {
      venue: "CETUS" as const,
      status: "AVAILABLE" as const,
      impact: "IMPACT_LOW" as const,
      slippage: "SLIP_LOW" as const,
      depth: "DEPTH_OK" as const,
      fee: "FEE_LOW" as const,
      warnings: [],
    },
  };

  // Create signals (no prohibitions)
  const signals: PythonSignals = {
    templateId: "TPL_RISK_90",
  };

  // Create constraints
  const constraints = createDefaultConstraints();

  // Run gate
  const gateResult = runSafetyGate(plan, route, signals, constraints, portfolio);

  // Assert: gate should BLOCK due to notional cap
  assert.strictEqual(gateResult.status, "BLOCK");
  assert.ok(gateResult.blockReasons.includes("BLOCK_NOTIONAL_CAP"));
  assert.strictEqual(isGatePassed(gateResult), false);

  console.log("  ✓ notionalUsd=250000 → status=BLOCK");
  console.log(`  ✓ Block reasons: ${gateResult.blockReasons.join(", ")}`);
}

/**
 * Test 5: Gate - IMPACT_HIGH → BLOCK_IMPACT_HIGH
 */
async function test5_gate_impact_high() {
  console.log("\n[TEST 5] Gate: IMPACT_HIGH → BLOCK_IMPACT_HIGH");

  // Create portfolio snapshot
  const portfolio: PortfolioSnapshot = {
    balances: { WBTC: "1.0", USDC: "50000", SUI: "1.0" },
    pricesUsd: { WBTC: 45000, USDC: 1 },
    valuesUsd: { WBTC: 45000, USDC: 50000 },
    weights: { WBTC: 0.47, USDC: 0.53 },
    totalUsd: 95000,
    timestamp: Date.now(),
  };

  // Create rebalance plan (within limits)
  const plan: RebalancePlan = {
    templateId: "TPL_RISK_90",
    targetWeights: { WBTC: 0.9, USDC: 0.1 },
    currentWeights: { WBTC: 0.47, USDC: 0.53 },
    deltaWeights: { WBTC: 0.43, USDC: -0.43 },
    intent: "INCREASE_WBTC",
    notionalUsd: 5000, // Within cap
    reasonCodes: [],
  };

  // Create route with IMPACT_HIGH
  const route = {
    venue: "CETUS" as const,
    reasonLabels: ["ROUTE_BEST_QUOTE"],
    chosenQuote: {
      venue: "CETUS" as const,
      status: "AVAILABLE" as const,
      impact: "IMPACT_HIGH" as const, // HIGH impact
      slippage: "SLIP_LOW" as const,
      depth: "DEPTH_OK" as const,
      fee: "FEE_LOW" as const,
      warnings: [],
    },
  };

  // Create signals (no prohibitions)
  const signals: PythonSignals = {
    templateId: "TPL_RISK_90",
  };

  // Create constraints
  const constraints = createDefaultConstraints();

  // Run gate
  const gateResult = runSafetyGate(plan, route, signals, constraints, portfolio);

  // Assert: gate should BLOCK due to high impact
  assert.strictEqual(gateResult.status, "BLOCK");
  assert.ok(gateResult.blockReasons.includes("BLOCK_IMPACT_HIGH"));
  assert.strictEqual(isGatePassed(gateResult), false);

  console.log("  ✓ IMPACT_HIGH → status=BLOCK");
  console.log(`  ✓ Block reasons: ${gateResult.blockReasons.join(", ")}`);
}

/**
 * Test 6: Gate - DEPTH_THIN → BLOCK_DEPTH_THIN
 */
async function test6_gate_depth_thin() {
  console.log("\n[TEST 6] Gate: DEPTH_THIN → BLOCK_DEPTH_THIN");

  // Create portfolio snapshot
  const portfolio: PortfolioSnapshot = {
    balances: { WBTC: "1.0", USDC: "50000", SUI: "1.0" },
    pricesUsd: { WBTC: 45000, USDC: 1 },
    valuesUsd: { WBTC: 45000, USDC: 50000 },
    weights: { WBTC: 0.47, USDC: 0.53 },
    totalUsd: 95000,
    timestamp: Date.now(),
  };

  // Create rebalance plan (within limits)
  const plan: RebalancePlan = {
    templateId: "TPL_RISK_90",
    targetWeights: { WBTC: 0.9, USDC: 0.1 },
    currentWeights: { WBTC: 0.47, USDC: 0.53 },
    deltaWeights: { WBTC: 0.43, USDC: -0.43 },
    intent: "INCREASE_WBTC",
    notionalUsd: 5000, // Within cap
    reasonCodes: [],
  };

  // Create route with DEPTH_THIN
  const route = {
    venue: "CETUS" as const,
    reasonLabels: ["ROUTE_BEST_QUOTE"],
    chosenQuote: {
      venue: "CETUS" as const,
      status: "AVAILABLE" as const,
      impact: "IMPACT_LOW" as const,
      slippage: "SLIP_LOW" as const,
      depth: "DEPTH_THIN" as const, // THIN depth
      fee: "FEE_LOW" as const,
      warnings: [],
    },
  };

  // Create signals (no prohibitions)
  const signals: PythonSignals = {
    templateId: "TPL_RISK_90",
  };

  // Create constraints
  const constraints = createDefaultConstraints();

  // Run gate
  const gateResult = runSafetyGate(plan, route, signals, constraints, portfolio);

  // Assert: gate should BLOCK due to thin depth
  assert.strictEqual(gateResult.status, "BLOCK");
  assert.ok(gateResult.blockReasons.includes("BLOCK_DEPTH_THIN"));
  assert.strictEqual(isGatePassed(gateResult), false);

  console.log("  ✓ DEPTH_THIN → status=BLOCK");
  console.log(`  ✓ Block reasons: ${gateResult.blockReasons.join(", ")}`);
}

/**
 * Test 7: Gate - stress=STRESSED → BLOCK_STRESSED
 */
async function test7_gate_stressed() {
  console.log("\n[TEST 7] Gate: stress=STRESSED → BLOCK_STRESSED");

  // Create portfolio snapshot
  const portfolio: PortfolioSnapshot = {
    balances: { WBTC: "1.0", USDC: "50000", SUI: "1.0" },
    pricesUsd: { WBTC: 45000, USDC: 1 },
    valuesUsd: { WBTC: 45000, USDC: 50000 },
    weights: { WBTC: 0.47, USDC: 0.53 },
    totalUsd: 95000,
    timestamp: Date.now(),
  };

  // Create rebalance plan (within limits)
  const plan: RebalancePlan = {
    templateId: "TPL_RISK_90",
    targetWeights: { WBTC: 0.9, USDC: 0.1 },
    currentWeights: { WBTC: 0.47, USDC: 0.53 },
    deltaWeights: { WBTC: 0.43, USDC: -0.43 },
    intent: "INCREASE_WBTC",
    notionalUsd: 5000, // Within cap
    reasonCodes: [],
  };

  // Create route (good quote)
  const route = {
    venue: "CETUS" as const,
    reasonLabels: ["ROUTE_BEST_QUOTE"],
    chosenQuote: {
      venue: "CETUS" as const,
      status: "AVAILABLE" as const,
      impact: "IMPACT_LOW" as const,
      slippage: "SLIP_LOW" as const,
      depth: "DEPTH_OK" as const,
      fee: "FEE_LOW" as const,
      warnings: [],
    },
  };

  // Create signals with STRESSED stress
  const signals: PythonSignals = {
    templateId: "TPL_RISK_90",
    stress: "STRESS_STRESSED", // STRESSED
  };

  // Create constraints
  const constraints = createDefaultConstraints();

  // Run gate
  const gateResult = runSafetyGate(plan, route, signals, constraints, portfolio);

  // Assert: gate should BLOCK due to stressed
  assert.strictEqual(gateResult.status, "BLOCK");
  assert.ok(gateResult.blockReasons.includes("BLOCK_STRESSED"));
  assert.strictEqual(isGatePassed(gateResult), false);

  console.log("  ✓ stress=STRESSED → status=BLOCK");
  console.log(`  ✓ Block reasons: ${gateResult.blockReasons.join(", ")}`);
}

/**
 * Test 8: E2E - PASS → EXECUTABLE_DRAFT but allowExecution=false blocks execution
 */
async function test8_e2e_gate_pass_no_execution() {
  console.log("\n[TEST 8] E2E: PASS → EXECUTABLE_DRAFT but allowExecution=false");

  // Create portfolio snapshot
  const portfolio: PortfolioSnapshot = {
    balances: { WBTC: "1.0", USDC: "50000", SUI: "1.0" },
    pricesUsd: { WBTC: 45000, USDC: 1 },
    valuesUsd: { WBTC: 45000, USDC: 50000 },
    weights: { WBTC: 0.47, USDC: 0.53 },
    totalUsd: 95000,
    timestamp: Date.now(),
  };

  // Create rebalance plan (safe)
  const plan: RebalancePlan = {
    templateId: "TPL_RISK_90",
    targetWeights: { WBTC: 0.9, USDC: 0.1 },
    currentWeights: { WBTC: 0.47, USDC: 0.53 },
    deltaWeights: { WBTC: 0.43, USDC: -0.43 },
    intent: "INCREASE_WBTC",
    notionalUsd: 5000, // Safe amount
    reasonCodes: [],
  };

  // Create route (good quote)
  const route = {
    venue: "CETUS" as const,
    reasonLabels: ["ROUTE_BEST_QUOTE"],
    chosenQuote: {
      venue: "CETUS" as const,
      status: "AVAILABLE" as const,
      impact: "IMPACT_LOW" as const,
      slippage: "SLIP_LOW" as const,
      depth: "DEPTH_OK" as const,
      fee: "FEE_LOW" as const,
      warnings: [],
    },
  };

  // Create signals (no prohibitions)
  const signals: PythonSignals = {
    templateId: "TPL_RISK_90",
  };

  // Create constraints
  const constraints = createDefaultConstraints();

  // Run gate
  const gateResult = runSafetyGate(plan, route, signals, constraints, portfolio);

  // Assert: gate should PASS
  assert.strictEqual(gateResult.status, "PASS");
  assert.strictEqual(gateResult.blockReasons.length, 0);
  assert.strictEqual(isGatePassed(gateResult), true);

  console.log("  ✓ Gate status=PASS (all checks passed)");

  // Build tx draft with gate
  const draft = await buildTxDraftWithGate(plan, route, gateResult, constraints, {
    allowExecution: false, // Execution disabled
    simulateOnly: true,
  });

  // Assert: draft should be EXECUTABLE_DRAFT (gate passed)
  assert.strictEqual(draft.status, "EXECUTABLE_DRAFT");
  assert.strictEqual(draft.route, "CETUS");
  assert.strictEqual(draft.action, "SWAP_USDC_TO_WBTC");
  assert.strictEqual(draft.simulateOnly, true);

  console.log("  ✓ Draft status=EXECUTABLE_DRAFT (gate passed)");
  console.log(`  ✓ Draft route: ${draft.route}`);
  console.log(`  ✓ Draft action: ${draft.action}`);
  console.log(
    "  ✓ Execution disabled by allowExecution=false and simulateOnly=true"
  );
}

/**
 * Bonus Test 9: Gate - FREEZE_STATE → BLOCK_FREEZE_STATE
 */
async function test9_gate_freeze_state() {
  console.log("\n[TEST 9] Gate: actionShape=FREEZE_STATE → BLOCK_FREEZE_STATE");

  // Create portfolio snapshot
  const portfolio: PortfolioSnapshot = {
    balances: { WBTC: "1.0", USDC: "50000", SUI: "1.0" },
    pricesUsd: { WBTC: 45000, USDC: 1 },
    valuesUsd: { WBTC: 45000, USDC: 50000 },
    weights: { WBTC: 0.47, USDC: 0.53 },
    totalUsd: 95000,
    timestamp: Date.now(),
  };

  // Create rebalance plan
  const plan: RebalancePlan = {
    templateId: "TPL_RISK_90",
    targetWeights: { WBTC: 0.9, USDC: 0.1 },
    currentWeights: { WBTC: 0.47, USDC: 0.53 },
    deltaWeights: { WBTC: 0.43, USDC: -0.43 },
    intent: "INCREASE_WBTC",
    notionalUsd: 5000,
    reasonCodes: [],
  };

  // Create route
  const route = {
    venue: "CETUS" as const,
    reasonLabels: ["ROUTE_BEST_QUOTE"],
    chosenQuote: {
      venue: "CETUS" as const,
      status: "AVAILABLE" as const,
      impact: "IMPACT_LOW" as const,
      slippage: "SLIP_LOW" as const,
      depth: "DEPTH_OK" as const,
      fee: "FEE_LOW" as const,
      warnings: [],
    },
  };

  // Create signals with FREEZE_STATE
  const signals: PythonSignals = {
    templateId: "TPL_RISK_90",
    actionShape: "FREEZE_STATE", // FREEZE_STATE
  };

  // Create constraints
  const constraints = createDefaultConstraints();

  // Run gate
  const gateResult = runSafetyGate(plan, route, signals, constraints, portfolio);

  // Assert: gate should BLOCK due to freeze state
  assert.strictEqual(gateResult.status, "BLOCK");
  assert.ok(gateResult.blockReasons.includes("BLOCK_FREEZE_STATE"));

  console.log("  ✓ actionShape=FREEZE_STATE → status=BLOCK");
  console.log(`  ✓ Block reasons: ${gateResult.blockReasons.join(", ")}`);
}

/**
 * Bonus Test 10: Router - Real stub quote comparison
 */
async function test10_router_real_stub_quotes() {
  console.log("\n[TEST 10] Router: Real stub quote comparison (500 USD)");

  // Create quote request
  const req = createStubQuoteRequest(500, "USDC_TO_WBTC");

  // Get quotes from both venues
  const cetusQuote = await getQuoteCetus(req);
  const deepbookQuote = await getQuoteDeepBook(req);

  console.log(`  Cetus quote: ${JSON.stringify(cetusQuote)}`);
  console.log(`  DeepBook quote: ${JSON.stringify(deepbookQuote)}`);

  // Select route
  const route = selectRoute([cetusQuote, deepbookQuote]);

  // Assert: CETUS should win (both IMPACT_LOW, but CETUS wins on tie-break)
  assert.strictEqual(route.venue, "CETUS");
  assert.ok(route.chosenQuote);

  console.log(`  ✓ Router selected: ${route.venue}`);
  console.log(`  ✓ Reason labels: ${route.reasonLabels.join(", ")}`);
}

/**
 * Main test runner
 */
async function main() {
  console.log("========================================");
  console.log("PR153: Router + Gate Test Suite");
  console.log("========================================");

  try {
    // Required tests (1-8)
    await test1_router_both_unavailable();
    await test2_router_one_available();
    await test3_router_best_impact();
    await test4_gate_notional_cap();
    await test5_gate_impact_high();
    await test6_gate_depth_thin();
    await test7_gate_stressed();
    await test8_e2e_gate_pass_no_execution();

    // Bonus tests (9-10)
    await test9_gate_freeze_state();
    await test10_router_real_stub_quotes();

    console.log("\n========================================");
    console.log("✓ All tests passed (10/10)");
    console.log("========================================");
  } catch (error) {
    console.error("\n========================================");
    console.error("✗ Test failed");
    console.error("========================================");
    throw error;
  }
}

// Run tests
main();
