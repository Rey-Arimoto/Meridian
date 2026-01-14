/**
 * PR154: v1.4 Observation Labeler - Type Definitions (READ-ONLY)
 *
 * Purpose:
 *   Define types for observation snapshots and labels.
 *   Labels are boolean | "UNKNOWN" only (no numbers, no token names).
 *
 * Constitutional Constraints:
 *   - Label-only output (no numbers, no token names, no instructions)
 *   - UNKNOWN on data absence (defensive)
 *   - No prescriptive/trading vocab in output
 */

/**
 * Venue source
 */
export type VenueSource = "DEEPBOOK" | "CETUS";

/**
 * Window label (PR148 profiles)
 */
export type WindowLabel = "SHORT" | "MEDIUM" | "LONG";

/**
 * Profile reference (PR148)
 */
export type ProfileRef = "CORE_3W" | "CORE_2W" | "ALERT_ONLY" | "RESEARCH";

/**
 * L2 level (price-size pair)
 */
export interface L2Level {
  px: number;
  sz: number;
}

/**
 * Book snapshot (minimal observation)
 *
 * Represents the order book state at a point in time.
 * Includes L1 (best bid/ask) and L2+ levels for depth analysis.
 */
export interface BookSnapshot {
  // Timestamp (milliseconds)
  ts_ms: number;

  // L1 (best bid)
  best_bid_px: number | null;
  best_bid_sz: number | null;

  // L1 (best ask)
  best_ask_px: number | null;
  best_ask_sz: number | null;

  // L2..Lk levels (bid side, descending price)
  levels_bid: L2Level[];

  // L2..Lk levels (ask side, ascending price)
  levels_ask: L2Level[];
}

/**
 * Window state (accumulates observations within a window)
 *
 * Tracks previous snapshot values and counts directional moves
 * within the current SHORT window bucket.
 */
export interface WindowState {
  // Previous snapshot values (for delta detection)
  prev_mid_px: number | null;
  prev_best_bid_px: number | null;
  prev_best_ask_px: number | null;

  // Counters in current SHORT window bucket
  mid_up_count: number; // Mid price moved up
  mid_down_count: number; // Mid price moved down
  ask_best_up_count: number; // Best ask moved up
  bid_best_down_count: number; // Best bid moved down
  ask_best_down_count: number; // Best ask moved down (for future use)
  bid_best_up_count: number; // Best bid moved up (for future use)
}

/**
 * Observation labels (label-only output)
 *
 * All labels are boolean | "UNKNOWN".
 * No numbers, no token names, no instructions in output.
 *
 * Label categories:
 *   - IMPULSE: Mid price direction (impulse_up/impulse_down)
 *   - THINNING: Liquidity thinning (liquidity_thinning)
 *   - DOMINANCE: Flow dominance proxy (agg_buy/sell_dominance)
 *   - ABSORPTION: Absorption present/released (ask/bid variants)
 */
export interface ObservationLabels {
  // IMPULSE (mid price direction)
  impulse_up: boolean | "UNKNOWN";
  impulse_down: boolean | "UNKNOWN";

  // THINNING (liquidity)
  liquidity_thinning: boolean | "UNKNOWN";

  // DOMINANCE (flow proxy)
  agg_buy_dominance: boolean | "UNKNOWN";
  agg_sell_dominance: boolean | "UNKNOWN";

  // ABSORPTION (present = holding, released = broken)
  ask_absorption_present: boolean | "UNKNOWN"; // UP side absorption
  bid_absorption_present: boolean | "UNKNOWN"; // DOWN side absorption

  // ABSORPTION components (impact control)
  impact_not_controlled_up: boolean | "UNKNOWN"; // A_UP: L1 break
  impact_not_controlled_down: boolean | "UNKNOWN"; // A_DOWN: L1 break

  // ABSORPTION components (depth floor)
  l2_min_depth_thin_up: boolean | "UNKNOWN"; // B_UP: L2 floor break
  l2_min_depth_thin_down: boolean | "UNKNOWN"; // B_DOWN: L2 floor break

  // ABSORPTION released (A || B)
  ask_absorption_released: boolean | "UNKNOWN"; // UP released
  bid_absorption_released: boolean | "UNKNOWN"; // DOWN released
}

/**
 * Observation diagnostics (presence flags only, no numbers)
 *
 * Used for debugging/logging. Does not contain numeric values.
 */
export interface ObservationDiagnostics {
  has_l1: boolean; // L1 (best bid/ask) present
  has_l2: boolean; // L2+ levels present
  has_mid: boolean; // Mid price calculable
  has_valid_snapshot: boolean; // Snapshot is valid (not all null)
}

/**
 * Observation result (labels + state + diagnostics)
 */
export interface ObservationResult {
  labels: ObservationLabels;
  state: WindowState;
  diagnostics: ObservationDiagnostics;
}
