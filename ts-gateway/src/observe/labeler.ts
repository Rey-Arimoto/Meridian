/**
 * PR154: v1.4 Observation Labeler - Fixed Rule Engine (READ-ONLY)
 *
 * Purpose:
 *   Generate observation labels from snapshots using fixed rules.
 *   All rules are first-match-wins, no learning, no optimization.
 *
 * Constitutional Constraints:
 *   - READ-ONLY: No execution, just labeling
 *   - Fixed rules: No learning, no optimization
 *   - Label-only output: boolean | "UNKNOWN"
 *   - Defensive: UNKNOWN on data absence
 *   - No prescriptive vocabulary in output
 */

import {
  BookSnapshot,
  WindowState,
  ObservationLabels,
  ObservationDiagnostics,
  ObservationResult,
  VenueSource,
  WindowLabel,
  ProfileRef,
} from "./types";
import {
  initWindowState,
  updateWindowState,
  hasValidPrevValues,
} from "./window";
import { fetchDeepBookTopK } from "./deepbook";
import { fetchCetusPseudoTopK } from "./cetus";

/**
 * Fixed thresholds (constitutional constants)
 *
 * These are the ONLY location with numeric thresholds.
 * Output labels are boolean | "UNKNOWN" only.
 */
const THRESHOLDS = {
  // THINNING: L2 floor break (T1)
  THIN_MIN_FLOOR: 0.05, // Minimum L2 level size

  // THINNING: Spread widening (T2)
  THIN_SPREAD_BPS_FLOOR: 200, // 2.00% spread = wide

  // ABSORPTION: L2 floor break (B)
  FLOOR_SUM_ASK: 5.0, // Minimum total L2 ask depth
  FLOOR_SUM_BID: 5.0, // Minimum total L2 bid depth
  FLOOR_MIN_ASK: 0.1, // Minimum single L2 ask level
  FLOOR_MIN_BID: 0.1, // Minimum single L2 bid level

  // Counters: Direction confirmation (fixed at 2)
  MIN_COUNT_DIRECTION: 2, // Minimum count for directional confirmation
};

/**
 * Calculate diagnostics from snapshot
 *
 * @param snap - Book snapshot
 * @returns Diagnostics (presence flags only, no numbers)
 */
function calculateDiagnostics(snap: BookSnapshot): ObservationDiagnostics {
  const has_l1 =
    snap.best_bid_px !== null &&
    snap.best_ask_px !== null &&
    snap.best_bid_sz !== null &&
    snap.best_ask_sz !== null;

  const has_l2 = snap.levels_bid.length > 0 || snap.levels_ask.length > 0;

  const has_mid = snap.best_bid_px !== null && snap.best_ask_px !== null;

  const has_valid_snapshot = has_l1 || has_l2 || has_mid;

  return {
    has_l1,
    has_l2,
    has_mid,
    has_valid_snapshot,
  };
}

/**
 * Calculate spread in basis points
 *
 * @param snap - Book snapshot
 * @returns Spread in bps or null if L1 incomplete
 */
function calculateSpreadBps(snap: BookSnapshot): number | null {
  if (snap.best_bid_px === null || snap.best_ask_px === null) {
    return null;
  }

  const mid = (snap.best_bid_px + snap.best_ask_px) / 2;
  if (mid === 0) return null;

  const spread = snap.best_ask_px - snap.best_bid_px;
  const spread_bps = (spread / mid) * 10000;

  return spread_bps;
}

/**
 * Calculate L2 depth statistics
 *
 * @param levels - L2 levels
 * @returns Depth stats (sum, min, count)
 */
function calculateL2Depth(levels: { px: number; sz: number }[]): {
  sum: number;
  min: number | null;
  count: number;
} {
  if (levels.length === 0) {
    return { sum: 0, min: null, count: 0 };
  }

  let sum = 0;
  let min = Infinity;

  for (const level of levels) {
    sum += level.sz;
    if (level.sz < min) {
      min = level.sz;
    }
  }

  return {
    sum,
    min: min === Infinity ? null : min,
    count: levels.length,
  };
}

/**
 * Compute IMPULSE labels (fixed 2 conditions)
 *
 * @param snap - Book snapshot
 * @param state - Window state
 * @returns impulse_up, impulse_down
 *
 * impulse_up (fixed 2 conditions):
 *   I1: midUpCount >= 2
 *   I2: askBestUp OR bidBestUp (L1 following)
 *
 * impulse_down (fixed 2 conditions):
 *   I1: midDownCount >= 2
 *   I2: bidBestDown OR askBestDown (L1 following)
 *
 * UNKNOWN: If L1 or mid missing, or if no prev values yet
 */
function computeImpulse(
  snap: BookSnapshot,
  state: WindowState
): {
  impulse_up: boolean | "UNKNOWN";
  impulse_down: boolean | "UNKNOWN";
} {
  // Defensive: Check if we have prev values
  if (!hasValidPrevValues(state)) {
    return { impulse_up: "UNKNOWN", impulse_down: "UNKNOWN" };
  }

  // Defensive: Check L1 availability
  const has_l1 = snap.best_bid_px !== null && snap.best_ask_px !== null;
  if (!has_l1) {
    return { impulse_up: "UNKNOWN", impulse_down: "UNKNOWN" };
  }

  // impulse_up: I1 (midUpCount>=2) && I2 (L1 following)
  const i1_up = state.mid_up_count >= THRESHOLDS.MIN_COUNT_DIRECTION;
  const i2_up =
    state.ask_best_up_count >= 1 || state.bid_best_up_count >= 1;
  const impulse_up = i1_up && i2_up;

  // impulse_down: I1 (midDownCount>=2) && I2 (L1 following)
  const i1_down = state.mid_down_count >= THRESHOLDS.MIN_COUNT_DIRECTION;
  const i2_down =
    state.bid_best_down_count >= 1 || state.ask_best_down_count >= 1;
  const impulse_down = i1_down && i2_down;

  return { impulse_up, impulse_down };
}

/**
 * Compute THINNING label (fixed 2 conditions)
 *
 * @param snap - Book snapshot
 * @returns liquidity_thinning
 *
 * liquidity_thinning (fixed 2 conditions):
 *   T1: min(depthMinBid, depthMinAsk) < THIN_MIN_FLOOR (L2 floor break)
 *   T2: spread_bps > THIN_SPREAD_BPS_FLOOR (spread widening)
 *   Result: T1 OR T2
 *
 * UNKNOWN: If both T1 and T2 cannot be calculated
 */
function computeThinning(snap: BookSnapshot): boolean | "UNKNOWN" {
  // T1: L2 floor break
  const bid_depth = calculateL2Depth(snap.levels_bid);
  const ask_depth = calculateL2Depth(snap.levels_ask);

  let t1: boolean | null = null;
  if (bid_depth.min !== null && ask_depth.min !== null) {
    const min_depth = Math.min(bid_depth.min, ask_depth.min);
    t1 = min_depth < THRESHOLDS.THIN_MIN_FLOOR;
  } else if (bid_depth.min !== null) {
    t1 = bid_depth.min < THRESHOLDS.THIN_MIN_FLOOR;
  } else if (ask_depth.min !== null) {
    t1 = ask_depth.min < THRESHOLDS.THIN_MIN_FLOOR;
  }

  // T2: Spread widening
  const spread_bps = calculateSpreadBps(snap);
  let t2: boolean | null = null;
  if (spread_bps !== null) {
    t2 = spread_bps > THRESHOLDS.THIN_SPREAD_BPS_FLOOR;
  }

  // Result: T1 OR T2
  if (t1 !== null || t2 !== null) {
    return (t1 === true) || (t2 === true);
  }

  // Neither T1 nor T2 calculable → UNKNOWN
  return "UNKNOWN";
}

/**
 * Compute DOMINANCE labels (fixed 2 conditions, proxy)
 *
 * @param state - Window state
 * @returns agg_buy_dominance, agg_sell_dominance
 *
 * agg_buy_dominance (fixed 2 conditions):
 *   D1: askBestUpCount >= 2 (ask pushed up)
 *   D2: midUpCount >= 2 (mid moved up)
 *
 * agg_sell_dominance (fixed 2 conditions):
 *   D1: bidBestDownCount >= 2 (bid pushed down)
 *   D2: midDownCount >= 2 (mid moved down)
 *
 * UNKNOWN: If no prev values yet (no comparison)
 */
function computeDominance(state: WindowState): {
  agg_buy_dominance: boolean | "UNKNOWN";
  agg_sell_dominance: boolean | "UNKNOWN";
} {
  // Defensive: Check if we have prev values
  if (!hasValidPrevValues(state)) {
    return { agg_buy_dominance: "UNKNOWN", agg_sell_dominance: "UNKNOWN" };
  }

  // BUY dominance: D1 (askBestUpCount>=2) && D2 (midUpCount>=2)
  const d1_buy = state.ask_best_up_count >= THRESHOLDS.MIN_COUNT_DIRECTION;
  const d2_buy = state.mid_up_count >= THRESHOLDS.MIN_COUNT_DIRECTION;
  const agg_buy_dominance = d1_buy && d2_buy;

  // SELL dominance: D1 (bidBestDownCount>=2) && D2 (midDownCount>=2)
  const d1_sell = state.bid_best_down_count >= THRESHOLDS.MIN_COUNT_DIRECTION;
  const d2_sell = state.mid_down_count >= THRESHOLDS.MIN_COUNT_DIRECTION;
  const agg_sell_dominance = d1_sell && d2_sell;

  return { agg_buy_dominance, agg_sell_dominance };
}

/**
 * Compute ABSORPTION components (A: impact control, B: depth floor)
 *
 * @param snap - Book snapshot
 * @param state - Window state
 * @returns All absorption components
 *
 * A (IMPACT_NOT_CONTROLLED): L1 break (fixed 2 conditions)
 *   UP: askBestUpCount>=2 && midUpCount>=2
 *   DOWN: bidBestDownCount>=2 && midDownCount>=2
 *
 * B (L2_MIN_DEPTH_THIN): L2 floor break (fixed 2 conditions)
 *   UP: (depthSumAsk < FLOOR_SUM) OR (depthMinAsk < FLOOR_MIN)
 *   DOWN: (depthSumBid < FLOOR_SUM) OR (depthMinBid < FLOOR_MIN)
 *
 * released: A OR B
 * present (fixed 2 conditions): impulse && !impact_not_controlled
 */
function computeAbsorption(
  snap: BookSnapshot,
  state: WindowState
): {
  impact_not_controlled_up: boolean | "UNKNOWN";
  impact_not_controlled_down: boolean | "UNKNOWN";
  l2_min_depth_thin_up: boolean | "UNKNOWN";
  l2_min_depth_thin_down: boolean | "UNKNOWN";
  ask_absorption_released: boolean | "UNKNOWN";
  bid_absorption_released: boolean | "UNKNOWN";
  ask_absorption_present: boolean | "UNKNOWN";
  bid_absorption_present: boolean | "UNKNOWN";
} {
  // Defensive defaults
  let impact_not_controlled_up: boolean | "UNKNOWN" = "UNKNOWN";
  let impact_not_controlled_down: boolean | "UNKNOWN" = "UNKNOWN";
  let l2_min_depth_thin_up: boolean | "UNKNOWN" = "UNKNOWN";
  let l2_min_depth_thin_down: boolean | "UNKNOWN" = "UNKNOWN";

  // A (IMPACT_NOT_CONTROLLED): L1 break
  if (hasValidPrevValues(state)) {
    // UP: askBestUpCount>=2 && midUpCount>=2
    const a1_up = state.ask_best_up_count >= THRESHOLDS.MIN_COUNT_DIRECTION;
    const a2_up = state.mid_up_count >= THRESHOLDS.MIN_COUNT_DIRECTION;
    impact_not_controlled_up = a1_up && a2_up;

    // DOWN: bidBestDownCount>=2 && midDownCount>=2
    const a1_down = state.bid_best_down_count >= THRESHOLDS.MIN_COUNT_DIRECTION;
    const a2_down = state.mid_down_count >= THRESHOLDS.MIN_COUNT_DIRECTION;
    impact_not_controlled_down = a1_down && a2_down;
  }

  // B (L2_MIN_DEPTH_THIN): L2 floor break
  const bid_depth = calculateL2Depth(snap.levels_bid);
  const ask_depth = calculateL2Depth(snap.levels_ask);

  // UP: (depthSumAsk < FLOOR_SUM) OR (depthMinAsk < FLOOR_MIN)
  if (ask_depth.count > 0) {
    const b1_up = ask_depth.sum < THRESHOLDS.FLOOR_SUM_ASK;
    const b2_up =
      ask_depth.min !== null && ask_depth.min < THRESHOLDS.FLOOR_MIN_ASK;
    l2_min_depth_thin_up = b1_up || b2_up;
  }

  // DOWN: (depthSumBid < FLOOR_SUM) OR (depthMinBid < FLOOR_MIN)
  if (bid_depth.count > 0) {
    const b1_down = bid_depth.sum < THRESHOLDS.FLOOR_SUM_BID;
    const b2_down =
      bid_depth.min !== null && bid_depth.min < THRESHOLDS.FLOOR_MIN_BID;
    l2_min_depth_thin_down = b1_down || b2_down;
  }

  // released: A OR B
  let ask_absorption_released: boolean | "UNKNOWN" = "UNKNOWN";
  let bid_absorption_released: boolean | "UNKNOWN" = "UNKNOWN";

  if (
    impact_not_controlled_up !== "UNKNOWN" ||
    l2_min_depth_thin_up !== "UNKNOWN"
  ) {
    ask_absorption_released =
      impact_not_controlled_up === true || l2_min_depth_thin_up === true;
  }

  if (
    impact_not_controlled_down !== "UNKNOWN" ||
    l2_min_depth_thin_down !== "UNKNOWN"
  ) {
    bid_absorption_released =
      impact_not_controlled_down === true || l2_min_depth_thin_down === true;
  }

  // present: impulse && !impact_not_controlled (fixed 2 conditions)
  const impulse = computeImpulse(snap, state);

  let ask_absorption_present: boolean | "UNKNOWN" = "UNKNOWN";
  let bid_absorption_present: boolean | "UNKNOWN" = "UNKNOWN";

  // UP present: P1 (impulse_up) && P2 (!impact_not_controlled_up)
  if (impulse.impulse_up !== "UNKNOWN" && impact_not_controlled_up !== "UNKNOWN") {
    const p1_up = impulse.impulse_up === true;
    const p2_up = impact_not_controlled_up === false;
    ask_absorption_present = p1_up && p2_up;
  }

  // DOWN present: P1 (impulse_down) && P2 (!impact_not_controlled_down)
  if (
    impulse.impulse_down !== "UNKNOWN" &&
    impact_not_controlled_down !== "UNKNOWN"
  ) {
    const p1_down = impulse.impulse_down === true;
    const p2_down = impact_not_controlled_down === false;
    bid_absorption_present = p1_down && p2_down;
  }

  return {
    impact_not_controlled_up,
    impact_not_controlled_down,
    l2_min_depth_thin_up,
    l2_min_depth_thin_down,
    ask_absorption_released,
    bid_absorption_released,
    ask_absorption_present,
    bid_absorption_present,
  };
}

/**
 * Compute observation labels from snapshot and window state
 *
 * @param snap - Book snapshot
 * @param state - Window state
 * @returns Observation labels (all boolean | "UNKNOWN")
 *
 * Main labeling function. Calls all sub-functions to compute labels.
 */
export function computeObservationLabels(
  snap: BookSnapshot,
  state: WindowState
): ObservationLabels {
  // Compute IMPULSE
  const impulse = computeImpulse(snap, state);

  // Compute THINNING
  const liquidity_thinning = computeThinning(snap);

  // Compute DOMINANCE
  const dominance = computeDominance(state);

  // Compute ABSORPTION (all components)
  const absorption = computeAbsorption(snap, state);

  return {
    impulse_up: impulse.impulse_up,
    impulse_down: impulse.impulse_down,
    liquidity_thinning,
    agg_buy_dominance: dominance.agg_buy_dominance,
    agg_sell_dominance: dominance.agg_sell_dominance,
    ask_absorption_present: absorption.ask_absorption_present,
    bid_absorption_present: absorption.bid_absorption_present,
    impact_not_controlled_up: absorption.impact_not_controlled_up,
    impact_not_controlled_down: absorption.impact_not_controlled_down,
    l2_min_depth_thin_up: absorption.l2_min_depth_thin_up,
    l2_min_depth_thin_down: absorption.l2_min_depth_thin_down,
    ask_absorption_released: absorption.ask_absorption_released,
    bid_absorption_released: absorption.bid_absorption_released,
  };
}

/**
 * Observe and label (main API)
 *
 * @param pair_ref - Pair reference (e.g., "PAIR_WBTC_USDC")
 * @param source - Venue source (DEEPBOOK/CETUS)
 * @param profile_ref - Profile reference (PR148)
 * @param window - Window label (SHORT/MEDIUM/LONG)
 * @param state - Current window state (or null to init)
 * @returns Observation result (labels + state + diagnostics)
 *
 * This is the main entry point for observation labeling.
 * Fetches snapshot, updates state, computes labels.
 */
export async function observeAndLabel(
  pair_ref: string,
  source: VenueSource,
  profile_ref: ProfileRef,
  window: WindowLabel,
  state: WindowState | null
): Promise<ObservationResult> {
  // Initialize state if needed
  const currentState = state || initWindowState();

  // Fetch snapshot (k=6 for L1 + L2..L5)
  const k = 6;
  let snap: BookSnapshot;

  if (source === "DEEPBOOK") {
    snap = await fetchDeepBookTopK(pair_ref, k);
  } else if (source === "CETUS") {
    snap = await fetchCetusPseudoTopK(pair_ref, k);
  } else {
    // Should not happen (TypeScript guards this), but defensive
    throw new Error(`Unknown source: ${source}`);
  }

  // Update window state
  const newState = updateWindowState(currentState, snap);

  // Compute labels
  const labels = computeObservationLabels(snap, newState);

  // Calculate diagnostics
  const diagnostics = calculateDiagnostics(snap);

  return {
    labels,
    state: newState,
    diagnostics,
  };
}
