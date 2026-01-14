/**
 * PR152: v1.4 TS Rebalance Template Resolver + Executor Skeleton - Tests
 *
 * Test Coverage:
 *   1. resolveTemplate("TPL_RISK_90") returns 0.9/0.1
 *   2. Planner: current 0.5 → target 0.9 = INCREASE_WBTC
 *   3. Planner: delta below threshold = NOOP
 *   4. Executor: allowExecution=false = EXECUTION_DISABLED
 *   5. buildTxDraft: NOOP intent = SKIPPED status
 */

import assert from "assert";
import { resolveTemplate } from "../src/rebalance/templates";
import {
  buildRebalancePlan,
  createDefaultConstraints,
} from "../src/rebalance/planner";
import { buildTxDraft, executeTx } from "../src/rebalance/executor";
import { getPortfolioSnapshot, createStubPortfolioDeps } from "../src/rebalance/portfolio";
import { extractTemplateIdFromPython } from "../src/bridge/pythonSignals";

/**
 * Test 1: resolveTemplate("TPL_RISK_90") returns 0.9/0.1
 */
function test1_resolveTemplate() {
  console.log("Test 1: resolveTemplate('TPL_RISK_90') returns 0.9/0.1");

  const weights = resolveTemplate("TPL_RISK_90");

  assert.strictEqual(weights.wbtcWeight, 0.9, "wBTC weight should be 0.9");
  assert.strictEqual(weights.usdcWeight, 0.1, "USDC weight should be 0.1");

  console.log("✓ Test 1 passed");
}

/**
 * Test 2: Planner: current 0.5 → target 0.9 = INCREASE_WBTC
 */
async function test2_planner_increase() {
  console.log("Test 2: Planner: current 0.5 → target 0.9 = INCREASE_WBTC");

  // Create portfolio with 50/50 weights
  const snapshot = await getPortfolioSnapshot(
    createStubPortfolioDeps({
      getBalance: async (symbol) => {
        if (symbol === "WBTC") return "0.01"; // 0.01 wBTC
        if (symbol === "USDC") return "450.0"; // 450 USDC
        if (symbol === "SUI") return "1.0"; // 1 SUI
        return "0.0";
      },
      getPriceUsd: async (symbol) => {
        if (symbol === "WBTC") return 45000.0; // $45k per wBTC
        if (symbol === "USDC") return 1.0;
        return 0.0;
      },
    })
  );

  // Verify current weight is ~0.5
  assert.ok(snapshot.weights, "Weights should be present");
  assert.ok(
    Math.abs(snapshot.weights.WBTC - 0.5) < 0.01,
    "Current wBTC weight should be ~0.5"
  );

  // Build rebalance plan for TPL_RISK_90 (target 0.9)
  const constraints = createDefaultConstraints();
  const plan = buildRebalancePlan(snapshot, "TPL_RISK_90", constraints);

  assert.strictEqual(plan.intent, "INCREASE_WBTC", "Intent should be INCREASE_WBTC");
  assert.ok(plan.notionalUsd > 0, "Notional USD should be > 0");

  console.log("✓ Test 2 passed");
}

/**
 * Test 3: Planner: delta below threshold = NOOP
 */
async function test3_planner_noop_delta() {
  console.log("Test 3: Planner: delta below threshold = NOOP");

  // Create portfolio with ~0.9 wBTC weight (close to TPL_RISK_90 target)
  const snapshot = await getPortfolioSnapshot(
    createStubPortfolioDeps({
      getBalance: async (symbol) => {
        if (symbol === "WBTC") return "0.018"; // 0.018 wBTC
        if (symbol === "USDC") return "90.0"; // 90 USDC
        if (symbol === "SUI") return "1.0"; // 1 SUI
        return "0.0";
      },
      getPriceUsd: async (symbol) => {
        if (symbol === "WBTC") return 45000.0; // $45k per wBTC
        if (symbol === "USDC") return 1.0;
        return 0.0;
      },
    })
  );

  // Verify current weight is ~0.9
  assert.ok(snapshot.weights, "Weights should be present");
  assert.ok(
    Math.abs(snapshot.weights.WBTC - 0.9) < 0.05,
    "Current wBTC weight should be ~0.9"
  );

  // Build rebalance plan for TPL_RISK_90 (target 0.9, delta < threshold)
  const constraints = createDefaultConstraints();
  const plan = buildRebalancePlan(snapshot, "TPL_RISK_90", constraints);

  assert.strictEqual(plan.intent, "NOOP", "Intent should be NOOP (delta below threshold)");
  assert.strictEqual(plan.notionalUsd, 0, "Notional USD should be 0");

  console.log("✓ Test 3 passed");
}

/**
 * Test 4: Executor: allowExecution=false = EXECUTION_DISABLED
 */
async function test4_executor_disabled() {
  console.log("Test 4: Executor: allowExecution=false = EXECUTION_DISABLED");

  // Create a valid plan
  const snapshot = await getPortfolioSnapshot(createStubPortfolioDeps());
  const constraints = createDefaultConstraints();
  const plan = buildRebalancePlan(snapshot, "TPL_RISK_90", constraints);

  // Build draft
  const draft = await buildTxDraft(plan, constraints);

  // PR156: Create policy result with env disabled (SIM_ONLY)
  const { evaluateExecutionPolicy } = await import("../src/policy");

  // Save original env
  const originalEnv = process.env.MERIDIAN_EXECUTION_ENABLED;
  delete process.env.MERIDIAN_EXECUTION_ENABLED;

  const policyResult = evaluateExecutionPolicy({
    oracleStatus: "AVAILABLE",
    simulationStatus: "PASS",
    routeStatus: "AVAILABLE",
  });

  // Restore env
  if (originalEnv !== undefined) {
    process.env.MERIDIAN_EXECUTION_ENABLED = originalEnv;
  }

  // Try to execute with env disabled
  const result = await executeTx(draft, policyResult);

  assert.strictEqual(result.ok, false, "Execution should fail");
  assert.ok(
    result.errors?.includes("EXECUTION_ENV_DISABLED"),
    "Should have EXECUTION_ENV_DISABLED error"
  );

  console.log("✓ Test 4 passed");
}

/**
 * Test 5: buildTxDraft: NOOP intent = SKIPPED status
 */
async function test5_draft_noop() {
  console.log("Test 5: buildTxDraft: NOOP intent = SKIPPED status");

  // Create portfolio with weight matching target (NOOP)
  const snapshot = await getPortfolioSnapshot(
    createStubPortfolioDeps({
      getBalance: async (symbol) => {
        if (symbol === "WBTC") return "0.018"; // ~0.9 weight
        if (symbol === "USDC") return "90.0"; // ~0.1 weight
        if (symbol === "SUI") return "1.0";
        return "0.0";
      },
    })
  );

  const constraints = createDefaultConstraints();
  const plan = buildRebalancePlan(snapshot, "TPL_RISK_90", constraints);

  // Plan should be NOOP
  assert.strictEqual(plan.intent, "NOOP", "Intent should be NOOP");

  // Build draft
  const draft = await buildTxDraft(plan, constraints);

  assert.strictEqual(draft.status, "SKIPPED", "Draft status should be SKIPPED");
  assert.strictEqual(draft.action, "NOOP", "Draft action should be NOOP");

  console.log("✓ Test 5 passed");
}

/**
 * Test 6: Python bridge extracts template ID
 */
function test6_python_bridge() {
  console.log("Test 6: Python bridge extracts template ID");

  // Test direct field
  const json1 = { v14_rebalance_template_id: "TPL_RISK_90" };
  const templateId1 = extractTemplateIdFromPython(json1);
  assert.strictEqual(templateId1, "TPL_RISK_90", "Should extract direct field");

  // Test nested in rebalance_record
  const json2 = {
    rebalance_record: { v14_rebalance_template_id: "TPL_RISK_50" },
  };
  const templateId2 = extractTemplateIdFromPython(json2);
  assert.strictEqual(templateId2, "TPL_RISK_50", "Should extract from rebalance_record");

  // Test nested in artifacts.rebalance_record
  const json3 = {
    artifacts: {
      rebalance_record: { v14_rebalance_template_id: "TPL_RISK_20" },
    },
  };
  const templateId3 = extractTemplateIdFromPython(json3);
  assert.strictEqual(
    templateId3,
    "TPL_RISK_20",
    "Should extract from artifacts.rebalance_record"
  );

  // Test fallback to UNKNOWN
  const json4 = {};
  const templateId4 = extractTemplateIdFromPython(json4);
  assert.strictEqual(templateId4, "TPL_UNKNOWN", "Should fallback to TPL_UNKNOWN");

  console.log("✓ Test 6 passed");
}

/**
 * Run all tests
 */
async function runAllTests() {
  console.log("=".repeat(60));
  console.log("PR152: v1.4 TS Rebalance Template Resolver + Executor Skeleton - Tests");
  console.log("=".repeat(60));
  console.log();

  try {
    test1_resolveTemplate();
    await test2_planner_increase();
    await test3_planner_noop_delta();
    await test4_executor_disabled();
    await test5_draft_noop();
    test6_python_bridge();

    console.log();
    console.log("=".repeat(60));
    console.log("All tests passed! ✓");
    console.log("=".repeat(60));

    process.exit(0);
  } catch (error) {
    console.error();
    console.error("✗ Test failed:", error);
    console.error();

    process.exit(1);
  }
}

// Run tests
runAllTests();
