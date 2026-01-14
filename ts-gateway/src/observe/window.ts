/**
 * PR154: v1.4 Observation Labeler - Window State Management (READ-ONLY)
 *
 * Purpose:
 *   Initialize and update window state for observation labeling.
 *   Tracks directional moves within SHORT window bucket.
 *
 * Constitutional Constraints:
 *   - READ-ONLY: No execution, just state tracking
 *   - Defensive: Handle null/missing data gracefully
 *   - No prescriptive output
 */

import { WindowState, BookSnapshot } from "./types";

/**
 * Initialize empty window state
 *
 * @returns Initial window state (all counters zero)
 */
export function initWindowState(): WindowState {
  return {
    prev_mid_px: null,
    prev_best_bid_px: null,
    prev_best_ask_px: null,
    mid_up_count: 0,
    mid_down_count: 0,
    ask_best_up_count: 0,
    bid_best_down_count: 0,
    ask_best_down_count: 0,
    bid_best_up_count: 0,
  };
}

/**
 * Calculate mid price from snapshot
 *
 * @param snap - Book snapshot
 * @returns Mid price or null if L1 incomplete
 */
function calculateMid(snap: BookSnapshot): number | null {
  if (snap.best_bid_px === null || snap.best_ask_px === null) {
    return null;
  }

  return (snap.best_bid_px + snap.best_ask_px) / 2;
}

/**
 * Update window state with new snapshot
 *
 * @param prev - Previous window state
 * @param snap - New book snapshot
 * @returns Updated window state
 *
 * Logic:
 *   1. Calculate current mid/L1 from snapshot
 *   2. Compare with prev values to detect directional moves
 *   3. Increment counters if direction detected
 *   4. Update prev values for next comparison
 *
 * Defensive:
 *   - Null prev values on first snapshot (no comparison)
 *   - Null current values → no comparison (counters unchanged)
 *   - Equal values → no direction (counters unchanged)
 */
export function updateWindowState(
  prev: WindowState,
  snap: BookSnapshot
): WindowState {
  const newState = { ...prev };

  // Calculate current values
  const curr_mid = calculateMid(snap);
  const curr_best_bid = snap.best_bid_px;
  const curr_best_ask = snap.best_ask_px;

  // Update mid counters (if mid available and prev exists)
  if (curr_mid !== null && prev.prev_mid_px !== null) {
    if (curr_mid > prev.prev_mid_px) {
      newState.mid_up_count++;
    } else if (curr_mid < prev.prev_mid_px) {
      newState.mid_down_count++;
    }
  }

  // Update bid counters (if bid available and prev exists)
  if (curr_best_bid !== null && prev.prev_best_bid_px !== null) {
    if (curr_best_bid > prev.prev_best_bid_px) {
      newState.bid_best_up_count++;
    } else if (curr_best_bid < prev.prev_best_bid_px) {
      newState.bid_best_down_count++;
    }
  }

  // Update ask counters (if ask available and prev exists)
  if (curr_best_ask !== null && prev.prev_best_ask_px !== null) {
    if (curr_best_ask > prev.prev_best_ask_px) {
      newState.ask_best_up_count++;
    } else if (curr_best_ask < prev.prev_best_ask_px) {
      newState.ask_best_down_count++;
    }
  }

  // Update prev values for next comparison
  newState.prev_mid_px = curr_mid;
  newState.prev_best_bid_px = curr_best_bid;
  newState.prev_best_ask_px = curr_best_ask;

  return newState;
}

/**
 * Reset window counters (keep prev values)
 *
 * @param state - Current window state
 * @returns State with counters reset to zero
 *
 * Use this when transitioning to a new window bucket.
 * Prev values are kept for continuity across buckets.
 */
export function resetWindowCounters(state: WindowState): WindowState {
  return {
    ...state,
    mid_up_count: 0,
    mid_down_count: 0,
    ask_best_up_count: 0,
    bid_best_down_count: 0,
    ask_best_down_count: 0,
    bid_best_up_count: 0,
  };
}

/**
 * Check if window state has valid prev values
 *
 * @param state - Window state
 * @returns True if prev values are set (not first snapshot)
 */
export function hasValidPrevValues(state: WindowState): boolean {
  return (
    state.prev_mid_px !== null ||
    state.prev_best_bid_px !== null ||
    state.prev_best_ask_px !== null
  );
}
