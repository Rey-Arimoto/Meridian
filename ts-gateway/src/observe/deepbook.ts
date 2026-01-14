/**
 * PR154: v1.4 Observation Labeler - DeepBook Data Fetcher (STUB)
 *
 * Purpose:
 *   Fetch TopK levels from DeepBook order book.
 *   This is a STUB implementation for PR154.
 *   Future PR will replace with actual DeepBook SDK calls.
 *
 * Constitutional Constraints:
 *   - STUB ONLY: Returns deterministic test data
 *   - Interface fixed for future implementation
 *   - No execution, read-only
 */

import { BookSnapshot, L2Level } from "./types";

/**
 * Fetch DeepBook TopK levels (STUB)
 *
 * @param pair_ref - Pair reference (e.g., "PAIR_WBTC_USDC")
 * @param k - Number of levels to fetch (including L1)
 * @returns Book snapshot
 *
 * STUB behavior (deterministic for testing):
 *   - Returns fixed snapshot with L1 + L2..Lk
 *   - L1: bid=44900, ask=45100 (mid=45000)
 *   - L2+ levels: 5 levels each side
 *   - All sizes are 1.0 (simplified)
 *
 * Future PR will replace this with:
 *   - DeepBook SDK calls
 *   - Real-time order book queries
 *   - Error handling for API failures
 */
export async function fetchDeepBookTopK(
  pair_ref: string,
  k: number
): Promise<BookSnapshot> {
  // STUB: Return fixed snapshot
  const ts_ms = Date.now();

  // L1 (best bid/ask)
  const best_bid_px = 44900;
  const best_bid_sz = 2.0;
  const best_ask_px = 45100;
  const best_ask_sz = 2.0;

  // L2..Lk levels (k-1 levels, since L1 is separate)
  const levels_bid: L2Level[] = [];
  const levels_ask: L2Level[] = [];

  for (let i = 1; i < k; i++) {
    // Bid side: descending price
    levels_bid.push({
      px: best_bid_px - i * 100,
      sz: 1.0,
    });

    // Ask side: ascending price
    levels_ask.push({
      px: best_ask_px + i * 100,
      sz: 1.0,
    });
  }

  return {
    ts_ms,
    best_bid_px,
    best_bid_sz,
    best_ask_px,
    best_ask_sz,
    levels_bid,
    levels_ask,
  };
}

/**
 * Create empty snapshot (for testing data absence)
 *
 * @returns Empty snapshot (all null)
 */
export function createEmptySnapshot(): BookSnapshot {
  return {
    ts_ms: Date.now(),
    best_bid_px: null,
    best_bid_sz: null,
    best_ask_px: null,
    best_ask_sz: null,
    levels_bid: [],
    levels_ask: [],
  };
}

/**
 * Create partial snapshot (L1 only, no L2+)
 *
 * @param bid_px - Best bid price
 * @param ask_px - Best ask price
 * @returns Snapshot with L1 only
 */
export function createL1OnlySnapshot(
  bid_px: number,
  ask_px: number
): BookSnapshot {
  return {
    ts_ms: Date.now(),
    best_bid_px: bid_px,
    best_bid_sz: 1.0,
    best_ask_px: ask_px,
    best_ask_sz: 1.0,
    levels_bid: [],
    levels_ask: [],
  };
}
