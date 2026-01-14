/**
 * PR154: v1.4 Observation Labeler - Cetus Data Fetcher (STUB)
 *
 * Purpose:
 *   Fetch pseudo TopK levels from Cetus AMM.
 *   Cetus is an AMM, so "levels" are constructed from tick liquidity.
 *   This is a STUB implementation for PR154.
 *   Future PR will replace with actual Cetus SDK calls.
 *
 * Constitutional Constraints:
 *   - STUB ONLY: Returns deterministic test data
 *   - Interface fixed for future implementation
 *   - No execution, read-only
 *
 * Note: Cetus uses concentrated liquidity (tick-based).
 * "Pseudo book" is constructed by:
 *   1. Get current tick
 *   2. Get liquidity distribution around current tick
 *   3. Convert tick liquidity to price-size levels
 */

import { BookSnapshot, L2Level } from "./types";

/**
 * Fetch Cetus pseudo TopK levels (STUB)
 *
 * @param pair_ref - Pair reference (e.g., "PAIR_WBTC_USDC")
 * @param k - Number of levels to construct (including L1)
 * @returns Book snapshot (pseudo book from AMM ticks)
 *
 * STUB behavior (deterministic for testing):
 *   - Returns fixed snapshot with L1 + L2..Lk
 *   - L1: bid=44950, ask=45050 (mid=45000, tighter spread than DeepBook)
 *   - L2+ levels: 5 levels each side (pseudo from tick liquidity)
 *   - All sizes are 1.5 (slightly different from DeepBook for testing)
 *
 * Future PR will replace this with:
 *   - Cetus SDK calls
 *   - Real-time tick/liquidity queries
 *   - Tick-to-price-level conversion
 *   - Error handling for API failures
 */
export async function fetchCetusPseudoTopK(
  pair_ref: string,
  k: number
): Promise<BookSnapshot> {
  // STUB: Return fixed pseudo snapshot
  const ts_ms = Date.now();

  // L1 (best bid/ask, tighter spread than DeepBook)
  const best_bid_px = 44950;
  const best_bid_sz = 1.5;
  const best_ask_px = 45050;
  const best_ask_sz = 1.5;

  // L2..Lk pseudo levels (constructed from tick liquidity)
  const levels_bid: L2Level[] = [];
  const levels_ask: L2Level[] = [];

  for (let i = 1; i < k; i++) {
    // Bid side: descending price
    levels_bid.push({
      px: best_bid_px - i * 50,
      sz: 1.5,
    });

    // Ask side: ascending price
    levels_ask.push({
      px: best_ask_px + i * 50,
      sz: 1.5,
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
 * Create Cetus snapshot with wide spread (for thinning tests)
 *
 * @returns Snapshot with wide spread
 */
export function createWideSpreadSnapshot(): BookSnapshot {
  return {
    ts_ms: Date.now(),
    best_bid_px: 44500,
    best_bid_sz: 1.0,
    best_ask_px: 45500, // Spread = 1000 bps (~2.2%)
    best_ask_sz: 1.0,
    levels_bid: [
      { px: 44400, sz: 0.5 },
      { px: 44300, sz: 0.5 },
    ],
    levels_ask: [
      { px: 45600, sz: 0.5 },
      { px: 45700, sz: 0.5 },
    ],
  };
}

/**
 * Create Cetus snapshot with thin L2 depth (for floor break tests)
 *
 * @returns Snapshot with thin L2 depth
 */
export function createThinDepthSnapshot(): BookSnapshot {
  return {
    ts_ms: Date.now(),
    best_bid_px: 44900,
    best_bid_sz: 2.0,
    best_ask_px: 45100,
    best_ask_sz: 2.0,
    levels_bid: [
      { px: 44800, sz: 0.01 }, // Very thin
      { px: 44700, sz: 0.01 },
    ],
    levels_ask: [
      { px: 45200, sz: 0.01 }, // Very thin
      { px: 45300, sz: 0.01 },
    ],
  };
}
