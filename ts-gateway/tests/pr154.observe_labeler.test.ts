/**
 * PR154: v1.4 Observation Labeler - Test Suite
 *
 * Verification:
 *   - Label generation from snapshots (fixed rules)
 *   - Defensive handling of missing data
 *   - IMPULSE, THINNING, DOMINANCE, ABSORPTION labels
 *
 * Required test cases (minimum 10):
 *   1. L1 missing → UNKNOWN (no errors)
 *   2. L2 missing → T1=UNKNOWN, T2 only
 *   3. impact_not_controlled_up (A_UP: L1 break)
 *   4. impact_not_controlled_down (A_DOWN: L1 break)
 *   5. l2_min_depth_thin_up (B_UP: L2 floor break)
 *   6. ask_absorption_released = A||B (OR works)
 *   7. impulse_up/impulse_down (direction confirmation)
 *   8. agg_buy/sell_dominance (proxy conditions)
 *   9. liquidity_thinning (spread widening)
 *   10. All null snapshot → UNKNOWN (defensive)
 */

import { strict as assert } from "assert";
import {
  computeObservationLabels,
  observeAndLabel,
} from "../src/observe/labeler";
import {
  initWindowState,
  updateWindowState,
} from "../src/observe/window";
import {
  BookSnapshot,
  WindowState,
} from "../src/observe/types";
import {
  createEmptySnapshot,
  createL1OnlySnapshot,
} from "../src/observe/deepbook";
import {
  createWideSpreadSnapshot,
  createThinDepthSnapshot,
} from "../src/observe/cetus";

/**
 * Test 1: L1 missing → UNKNOWN (no errors)
 */
function test1_l1_missing_unknown() {
  console.log("\n[TEST 1] L1 missing → UNKNOWN (defensive)");

  // Create snapshot with L1 missing
  const snap = createEmptySnapshot();

  // Init state
  const state = initWindowState();

  // Compute labels (should not throw)
  const labels = computeObservationLabels(snap, state);

  // Assert: Most labels should be UNKNOWN (defensive)
  assert.strictEqual(labels.impulse_up, "UNKNOWN");
  assert.strictEqual(labels.impulse_down, "UNKNOWN");
  assert.strictEqual(labels.agg_buy_dominance, "UNKNOWN");
  assert.strictEqual(labels.agg_sell_dominance, "UNKNOWN");

  console.log("  ✓ L1 missing → UNKNOWN (no errors)");
  console.log(`  ✓ impulse_up: ${labels.impulse_up}`);
  console.log(`  ✓ impulse_down: ${labels.impulse_down}`);
}

/**
 * Test 2: L2 missing → T1=UNKNOWN, T2 only
 */
function test2_l2_missing_t2_only() {
  console.log("\n[TEST 2] L2 missing → T1=UNKNOWN, T2 only");

  // Create snapshot with L1 only (wide spread)
  const snap = createL1OnlySnapshot(44000, 46000); // Wide spread

  // Init state
  const state = initWindowState();

  // Compute labels
  const labels = computeObservationLabels(snap, state);

  // Assert: liquidity_thinning should be true (T2: spread widening)
  // T1 cannot be calculated (no L2), but T2 works
  assert.strictEqual(labels.liquidity_thinning, true);

  console.log("  ✓ L2 missing → liquidity_thinning=true (T2 only)");
  console.log(`  ✓ liquidity_thinning: ${labels.liquidity_thinning}`);
}

/**
 * Test 3: impact_not_controlled_up (A_UP: L1 break)
 */
function test3_impact_not_controlled_up() {
  console.log("\n[TEST 3] impact_not_controlled_up (A_UP: L1 break)");

  // Create snapshots that push askBest up and mid up
  const snap1: BookSnapshot = {
    ts_ms: Date.now(),
    best_bid_px: 44900,
    best_bid_sz: 1.0,
    best_ask_px: 45100,
    best_ask_sz: 1.0,
    levels_bid: [],
    levels_ask: [],
  };

  const snap2: BookSnapshot = {
    ts_ms: Date.now(),
    best_bid_px: 44950, // bid up
    best_bid_sz: 1.0,
    best_ask_px: 45200, // ask up
    best_ask_sz: 1.0,
    levels_bid: [],
    levels_ask: [],
  };

  const snap3: BookSnapshot = {
    ts_ms: Date.now(),
    best_bid_px: 45000, // bid up again
    best_bid_sz: 1.0,
    best_ask_px: 45300, // ask up again
    best_ask_sz: 1.0,
    levels_bid: [],
    levels_ask: [],
  };

  // Update state progressively
  let state = initWindowState();
  state = updateWindowState(state, snap1);
  state = updateWindowState(state, snap2);
  state = updateWindowState(state, snap3);

  // Compute labels
  const labels = computeObservationLabels(snap3, state);

  // Assert: impact_not_controlled_up should be true
  // (askBestUpCount>=2 && midUpCount>=2)
  assert.strictEqual(labels.impact_not_controlled_up, true);

  console.log("  ✓ impact_not_controlled_up=true (A_UP)");
  console.log(`  ✓ askBestUpCount: ${state.ask_best_up_count}`);
  console.log(`  ✓ midUpCount: ${state.mid_up_count}`);
}

/**
 * Test 4: impact_not_controlled_down (A_DOWN: L1 break)
 */
function test4_impact_not_controlled_down() {
  console.log("\n[TEST 4] impact_not_controlled_down (A_DOWN: L1 break)");

  // Create snapshots that push bidBest down and mid down
  const snap1: BookSnapshot = {
    ts_ms: Date.now(),
    best_bid_px: 45100,
    best_bid_sz: 1.0,
    best_ask_px: 45300,
    best_ask_sz: 1.0,
    levels_bid: [],
    levels_ask: [],
  };

  const snap2: BookSnapshot = {
    ts_ms: Date.now(),
    best_bid_px: 45000, // bid down
    best_bid_sz: 1.0,
    best_ask_px: 45200, // ask down
    best_ask_sz: 1.0,
    levels_bid: [],
    levels_ask: [],
  };

  const snap3: BookSnapshot = {
    ts_ms: Date.now(),
    best_bid_px: 44900, // bid down again
    best_bid_sz: 1.0,
    best_ask_px: 45100, // ask down again
    best_ask_sz: 1.0,
    levels_bid: [],
    levels_ask: [],
  };

  // Update state progressively
  let state = initWindowState();
  state = updateWindowState(state, snap1);
  state = updateWindowState(state, snap2);
  state = updateWindowState(state, snap3);

  // Compute labels
  const labels = computeObservationLabels(snap3, state);

  // Assert: impact_not_controlled_down should be true
  // (bidBestDownCount>=2 && midDownCount>=2)
  assert.strictEqual(labels.impact_not_controlled_down, true);

  console.log("  ✓ impact_not_controlled_down=true (A_DOWN)");
  console.log(`  ✓ bidBestDownCount: ${state.bid_best_down_count}`);
  console.log(`  ✓ midDownCount: ${state.mid_down_count}`);
}

/**
 * Test 5: l2_min_depth_thin_up (B_UP: L2 floor break)
 */
function test5_l2_min_depth_thin_up() {
  console.log("\n[TEST 5] l2_min_depth_thin_up (B_UP: L2 floor break)");

  // Create snapshot with thin L2 depth
  const snap = createThinDepthSnapshot();

  // Init state
  const state = initWindowState();

  // Compute labels
  const labels = computeObservationLabels(snap, state);

  // Assert: l2_min_depth_thin_up should be true
  // (depthMinAsk < FLOOR_MIN_ASK or depthSumAsk < FLOOR_SUM_ASK)
  assert.strictEqual(labels.l2_min_depth_thin_up, true);

  console.log("  ✓ l2_min_depth_thin_up=true (B_UP)");
  console.log(`  ✓ L2 ask depth is thin (floor break)`);
}

/**
 * Test 6: ask_absorption_released = A||B (OR works)
 */
function test6_absorption_released_or() {
  console.log("\n[TEST 6] ask_absorption_released = A||B (OR works)");

  // Create snapshots that trigger A_UP (impact_not_controlled_up)
  const snap1: BookSnapshot = {
    ts_ms: Date.now(),
    best_bid_px: 44900,
    best_bid_sz: 1.0,
    best_ask_px: 45100,
    best_ask_sz: 1.0,
    levels_bid: [{ px: 44800, sz: 10.0 }], // Good depth
    levels_ask: [{ px: 45200, sz: 10.0 }], // Good depth
  };

  const snap2: BookSnapshot = {
    ts_ms: Date.now(),
    best_bid_px: 44950,
    best_bid_sz: 1.0,
    best_ask_px: 45200, // ask up
    best_ask_sz: 1.0,
    levels_bid: [{ px: 44850, sz: 10.0 }],
    levels_ask: [{ px: 45300, sz: 10.0 }],
  };

  const snap3: BookSnapshot = {
    ts_ms: Date.now(),
    best_bid_px: 45000,
    best_bid_sz: 1.0,
    best_ask_px: 45300, // ask up again
    best_ask_sz: 1.0,
    levels_bid: [{ px: 44900, sz: 10.0 }],
    levels_ask: [{ px: 45400, sz: 10.0 }],
  };

  // Update state progressively
  let state = initWindowState();
  state = updateWindowState(state, snap1);
  state = updateWindowState(state, snap2);
  state = updateWindowState(state, snap3);

  // Compute labels
  const labels = computeObservationLabels(snap3, state);

  // Assert: ask_absorption_released should be true
  // (A_UP is true, B_UP is false, A||B = true)
  assert.strictEqual(labels.ask_absorption_released, true);
  assert.strictEqual(labels.impact_not_controlled_up, true);

  console.log("  ✓ ask_absorption_released=true (A||B OR works)");
  console.log(`  ✓ impact_not_controlled_up: ${labels.impact_not_controlled_up}`);
  console.log(`  ✓ l2_min_depth_thin_up: ${labels.l2_min_depth_thin_up}`);
}

/**
 * Test 7: impulse_up/impulse_down (direction confirmation)
 */
function test7_impulse_direction() {
  console.log("\n[TEST 7] impulse_up/impulse_down (direction confirmation)");

  // Create snapshots for impulse_up
  const snap1: BookSnapshot = {
    ts_ms: Date.now(),
    best_bid_px: 44900,
    best_bid_sz: 1.0,
    best_ask_px: 45100,
    best_ask_sz: 1.0,
    levels_bid: [],
    levels_ask: [],
  };

  const snap2: BookSnapshot = {
    ts_ms: Date.now(),
    best_bid_px: 44950, // bid up (L1 following)
    best_bid_sz: 1.0,
    best_ask_px: 45150, // mid up
    best_ask_sz: 1.0,
    levels_bid: [],
    levels_ask: [],
  };

  const snap3: BookSnapshot = {
    ts_ms: Date.now(),
    best_bid_px: 45000, // bid up again
    best_bid_sz: 1.0,
    best_ask_px: 45200, // mid up again
    best_ask_sz: 1.0,
    levels_bid: [],
    levels_ask: [],
  };

  // Update state progressively
  let state = initWindowState();
  state = updateWindowState(state, snap1);
  state = updateWindowState(state, snap2);
  state = updateWindowState(state, snap3);

  // Compute labels
  const labels = computeObservationLabels(snap3, state);

  // Assert: impulse_up should be true
  // (midUpCount>=2 && (askBestUp OR bidBestUp))
  assert.strictEqual(labels.impulse_up, true);

  console.log("  ✓ impulse_up=true (direction confirmed)");
  console.log(`  ✓ midUpCount: ${state.mid_up_count}`);
  console.log(`  ✓ bidBestUpCount: ${state.bid_best_up_count}`);
}

/**
 * Test 8: agg_buy/sell_dominance (proxy conditions)
 */
function test8_dominance_proxy() {
  console.log("\n[TEST 8] agg_buy/sell_dominance (proxy conditions)");

  // Create snapshots for buy dominance
  const snap1: BookSnapshot = {
    ts_ms: Date.now(),
    best_bid_px: 44900,
    best_bid_sz: 1.0,
    best_ask_px: 45100,
    best_ask_sz: 1.0,
    levels_bid: [],
    levels_ask: [],
  };

  const snap2: BookSnapshot = {
    ts_ms: Date.now(),
    best_bid_px: 44950,
    best_bid_sz: 1.0,
    best_ask_px: 45200, // ask up
    best_ask_sz: 1.0,
    levels_bid: [],
    levels_ask: [],
  };

  const snap3: BookSnapshot = {
    ts_ms: Date.now(),
    best_bid_px: 45000,
    best_bid_sz: 1.0,
    best_ask_px: 45300, // ask up again
    best_ask_sz: 1.0,
    levels_bid: [],
    levels_ask: [],
  };

  // Update state progressively
  let state = initWindowState();
  state = updateWindowState(state, snap1);
  state = updateWindowState(state, snap2);
  state = updateWindowState(state, snap3);

  // Compute labels
  const labels = computeObservationLabels(snap3, state);

  // Assert: agg_buy_dominance should be true
  // (askBestUpCount>=2 && midUpCount>=2)
  assert.strictEqual(labels.agg_buy_dominance, true);

  console.log("  ✓ agg_buy_dominance=true (proxy conditions)");
  console.log(`  ✓ askBestUpCount: ${state.ask_best_up_count}`);
  console.log(`  ✓ midUpCount: ${state.mid_up_count}`);
}

/**
 * Test 9: liquidity_thinning (spread widening)
 */
function test9_thinning_spread() {
  console.log("\n[TEST 9] liquidity_thinning (spread widening)");

  // Create snapshot with wide spread
  const snap = createWideSpreadSnapshot();

  // Init state
  const state = initWindowState();

  // Compute labels
  const labels = computeObservationLabels(snap, state);

  // Assert: liquidity_thinning should be true (T2: spread widening)
  assert.strictEqual(labels.liquidity_thinning, true);

  console.log("  ✓ liquidity_thinning=true (spread widening)");
  console.log(`  ✓ Wide spread detected`);
}

/**
 * Test 10: All null snapshot → UNKNOWN (defensive)
 */
function test10_all_null_defensive() {
  console.log("\n[TEST 10] All null snapshot → UNKNOWN (defensive)");

  // Create empty snapshot (all null)
  const snap = createEmptySnapshot();

  // Init state
  const state = initWindowState();

  // Compute labels (should not throw)
  const labels = computeObservationLabels(snap, state);

  // Assert: All labels should be UNKNOWN (defensive)
  assert.strictEqual(labels.impulse_up, "UNKNOWN");
  assert.strictEqual(labels.impulse_down, "UNKNOWN");
  assert.strictEqual(labels.agg_buy_dominance, "UNKNOWN");
  assert.strictEqual(labels.agg_sell_dominance, "UNKNOWN");
  // liquidity_thinning might be calculable if L1 exists, but here it's all null
  assert.strictEqual(labels.liquidity_thinning, "UNKNOWN");

  console.log("  ✓ All null snapshot → UNKNOWN (no errors)");
  console.log("  ✓ Defensive handling works");
}

/**
 * Bonus Test 11: E2E observeAndLabel API
 */
async function test11_e2e_observe_and_label() {
  console.log("\n[TEST 11] E2E: observeAndLabel API");

  // Call observeAndLabel with DEEPBOOK source
  const result = await observeAndLabel(
    "PAIR_WBTC_USDC",
    "DEEPBOOK",
    "CORE_3W",
    "SHORT",
    null
  );

  // Assert: Result should have labels, state, diagnostics
  assert.ok(result.labels);
  assert.ok(result.state);
  assert.ok(result.diagnostics);

  // Diagnostics should show has_l1, has_mid (stub returns valid snapshot)
  assert.strictEqual(result.diagnostics.has_l1, true);
  assert.strictEqual(result.diagnostics.has_mid, true);
  assert.strictEqual(result.diagnostics.has_valid_snapshot, true);

  console.log("  ✓ observeAndLabel API works");
  console.log(`  ✓ has_l1: ${result.diagnostics.has_l1}`);
  console.log(`  ✓ has_mid: ${result.diagnostics.has_mid}`);
  console.log(`  ✓ has_valid_snapshot: ${result.diagnostics.has_valid_snapshot}`);
}

/**
 * Bonus Test 12: absorption_present (holding)
 */
function test12_absorption_present() {
  console.log("\n[TEST 12] absorption_present (holding)");

  // Create snapshots for impulse_up but impact controlled
  // Key: bid moves up (mid up), but ask stays flat (impact controlled)
  const snap1: BookSnapshot = {
    ts_ms: Date.now(),
    best_bid_px: 44900,
    best_bid_sz: 1.0,
    best_ask_px: 45100,
    best_ask_sz: 1.0,
    levels_bid: [],
    levels_ask: [],
  };

  const snap2: BookSnapshot = {
    ts_ms: Date.now(),
    best_bid_px: 44950, // bid up (L1 following)
    best_bid_sz: 1.0,
    best_ask_px: 45100, // ask stays flat (impact controlled)
    best_ask_sz: 1.0,
    levels_bid: [],
    levels_ask: [],
  };

  const snap3: BookSnapshot = {
    ts_ms: Date.now(),
    best_bid_px: 45000, // bid up again
    best_bid_sz: 1.0,
    best_ask_px: 45100, // ask still flat (impact controlled)
    best_ask_sz: 1.0,
    levels_bid: [],
    levels_ask: [],
  };

  // Update state progressively
  let state = initWindowState();
  state = updateWindowState(state, snap1);
  state = updateWindowState(state, snap2);
  state = updateWindowState(state, snap3);

  // Compute labels
  const labels = computeObservationLabels(snap3, state);

  // Assert: impulse_up=true, impact_not_controlled_up=false
  // → ask_absorption_present=true (holding)
  // Note: impulse_up requires midUpCount>=2 and L1 following
  // Here mid goes up (bid up), and bid follows, so impulse_up=true
  // askBestUpCount=0 (ask flat), so impact_not_controlled_up=false
  assert.strictEqual(labels.impulse_up, true);
  assert.strictEqual(labels.impact_not_controlled_up, false);
  assert.strictEqual(labels.ask_absorption_present, true);

  console.log("  ✓ ask_absorption_present=true (holding)");
  console.log(`  ✓ impulse_up: ${labels.impulse_up}`);
  console.log(`  ✓ impact_not_controlled_up: ${labels.impact_not_controlled_up}`);
}

/**
 * Main test runner
 */
async function main() {
  console.log("========================================");
  console.log("PR154: Observation Labeler Test Suite");
  console.log("========================================");

  try {
    // Required tests (1-10)
    test1_l1_missing_unknown();
    test2_l2_missing_t2_only();
    test3_impact_not_controlled_up();
    test4_impact_not_controlled_down();
    test5_l2_min_depth_thin_up();
    test6_absorption_released_or();
    test7_impulse_direction();
    test8_dominance_proxy();
    test9_thinning_spread();
    test10_all_null_defensive();

    // Bonus tests (11-12)
    await test11_e2e_observe_and_label();
    test12_absorption_present();

    console.log("\n========================================");
    console.log("✓ All tests passed (12/12)");
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
