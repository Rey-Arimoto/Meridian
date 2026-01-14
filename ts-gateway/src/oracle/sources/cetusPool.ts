/**
 * PR155: v1.4 Price Oracle Integration - Cetus Pool Price Source (STUB)
 *
 * Purpose:
 *   Fetch implied price from Cetus AMM pool.
 *   This is a STUB implementation for PR155.
 *   Future PR will replace with actual Cetus SDK calls.
 *
 * Constitutional Constraints:
 *   - STUB ONLY: Returns deterministic test data
 *   - Interface fixed for future implementation
 *   - READ-ONLY: No execution, just price observation
 */

import { PricePoint } from "../types";

/**
 * Fetch wBTC/USDC implied price from Cetus pool (STUB)
 *
 * @returns Price point or null if unavailable
 *
 * STUB behavior (deterministic for testing):
 *   - Returns fixed wBTC price: $44,950 (slightly different from DeepBook)
 *   - Always AVAILABLE (stub)
 *   - Source: CETUS_POOL
 *
 * Future PR will replace this with:
 *   - Cetus SDK calls
 *   - Real-time pool sqrtPrice → price conversion
 *   - Error handling for API failures
 *   - Pool address parameter
 */
export async function fetchCetusPoolPrice(): Promise<PricePoint | null> {
  // STUB: Return fixed price (slightly different from DeepBook for testing)
  return {
    priceUsd: 44950, // $44,950 per wBTC
    source: "CETUS_POOL",
    ts: Date.now(),
  };
}

/**
 * Create unavailable price point (for testing)
 *
 * @returns Null (simulates unavailable price)
 */
export function createUnavailablePrice(): PricePoint | null {
  return null;
}
