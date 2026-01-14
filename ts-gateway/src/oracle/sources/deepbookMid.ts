/**
 * PR155: v1.4 Price Oracle Integration - DeepBook Mid Price Source (STUB)
 *
 * Purpose:
 *   Fetch mid price from DeepBook order book.
 *   This is a STUB implementation for PR155.
 *   Future PR will replace with actual DeepBook SDK calls.
 *
 * Constitutional Constraints:
 *   - STUB ONLY: Returns deterministic test data
 *   - Interface fixed for future implementation
 *   - READ-ONLY: No execution, just price observation
 */

import { PricePoint } from "../types";

/**
 * Fetch wBTC/USDC mid price from DeepBook (STUB)
 *
 * @returns Price point or null if unavailable
 *
 * STUB behavior (deterministic for testing):
 *   - Returns fixed wBTC price: $45,000
 *   - Always AVAILABLE (stub)
 *   - Source: DEEPBOOK_MID
 *
 * Future PR will replace this with:
 *   - DeepBook SDK calls
 *   - Real-time order book mid price
 *   - Error handling for API failures
 *   - Pair reference parameter (e.g., "WBTC_USDC")
 */
export async function fetchDeepBookMidPrice(): Promise<PricePoint | null> {
  // STUB: Return fixed price
  return {
    priceUsd: 45000, // $45,000 per wBTC
    source: "DEEPBOOK_MID",
    ts: Date.now(),
  };
}

/**
 * Fetch USDC price from DeepBook (STUB)
 *
 * @returns Price point (always 1.0 for stablecoin)
 *
 * STUB behavior:
 *   - Returns fixed USDC price: $1.00
 *   - Always AVAILABLE
 *   - Source: DEEPBOOK_MID
 *
 * Note: USDC is a stablecoin, so price is always ~1.0.
 * Future PR may add actual price feed for de-peg detection.
 */
export async function fetchUsdcPrice(): Promise<PricePoint | null> {
  // STUB: Return fixed price (stablecoin)
  return {
    priceUsd: 1.0, // $1.00 per USDC
    source: "DEEPBOOK_MID",
    ts: Date.now(),
  };
}

/**
 * Create stale price point (for testing)
 *
 * @param priceUsd - Price in USD
 * @param ageMs - Age in milliseconds
 * @returns Stale price point
 */
export function createStalePricePoint(
  priceUsd: number,
  ageMs: number
): PricePoint {
  return {
    priceUsd,
    source: "DEEPBOOK_MID",
    ts: Date.now() - ageMs,
  };
}
