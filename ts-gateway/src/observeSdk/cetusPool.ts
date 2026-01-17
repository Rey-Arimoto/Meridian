/**
 * PR182: v1.4 Real Observation SDK Connectors v1 - Cetus Pool
 *
 * Purpose:
 *   Fetch Cetus pool state and generate pseudo-TopK orderbook.
 *   Maintains existing pseudo-TopK approach with real pool data.
 *
 * Constitutional Constraints:
 *   - READ-ONLY: Observation only
 *   - Defensive: Never throws, returns PARTIAL/ERROR on failure
 *   - Safe defaults: Missing pool → PARTIAL or ERROR
 *   - Pseudo-TopK: Generate orderbook from pool sqrtPrice and liquidity
 */

import {
  NumericBookSnapshot,
  CetusPoolResult,
  FetchStatus,
  SdkHealthLabel,
} from "./types";
import { sanitizeStringArray } from "./guards";

/**
 * Cetus pool state (internal)
 */
interface CetusPoolState {
  sqrtPrice: number; // Internal numeric
  liquidity: number; // Internal numeric
  timestamp: number; // Internal numeric
}

/**
 * Fetch Cetus pool state
 *
 * NOTE: This is a stub for v1. Real Cetus SDK integration in future PR.
 *
 * @returns Pool fetch result (defensive)
 */
export async function fetchCetusPool(): Promise<CetusPoolResult> {
  const warnings: string[] = [];

  try {
    // TODO: Real Cetus pool fetch logic
    // For now, return stub data to simulate unavailable pool
    warnings.push("CETUS_SDK_NOT_INTEGRATED");

    return {
      status: "ERROR",
      healthLabel: "UNKNOWN",
      warnings: sanitizeStringArray(warnings),
    };
  } catch (error) {
    // Defensive: Never throw
    warnings.push("CETUS_FETCH_ERROR");

    return {
      status: "ERROR",
      healthLabel: "UNKNOWN",
      warnings: sanitizeStringArray(warnings),
    };
  }
}

/**
 * Generate pseudo-TopK from pool state
 *
 * Existing approach: Create synthetic orderbook from pool sqrtPrice and liquidity.
 *
 * @param poolState - Pool state (internal)
 * @returns Numeric book snapshot
 */
function generatePseudoTopK(poolState: CetusPoolState): NumericBookSnapshot {
  try {
    // Convert sqrtPrice to price
    const price = Math.pow(poolState.sqrtPrice, 2);

    // Generate synthetic bids/asks around current price
    // This is a simplified version - real logic would use liquidity distribution
    const spread = price * 0.001; // 0.1% spread

    const bids = [
      { price: price - spread, quantity: 1000 },
      { price: price - spread * 2, quantity: 2000 },
      { price: price - spread * 3, quantity: 3000 },
    ];

    const asks = [
      { price: price + spread, quantity: 1000 },
      { price: price + spread * 2, quantity: 2000 },
      { price: price + spread * 3, quantity: 3000 },
    ];

    return {
      bids,
      asks,
      timestamp: poolState.timestamp,
      source: "CETUS_POOL",
    };
  } catch (error) {
    // Defensive: Return empty book on error
    return {
      bids: [],
      asks: [],
      timestamp: Date.now(),
      source: "CETUS_POOL",
    };
  }
}

/**
 * Simulate Cetus pool success (for testing)
 *
 * @param poolState - Pool state to inject
 * @returns Pool result with pseudo-TopK
 */
export async function simulateCetusSuccess(
  poolState: CetusPoolState
): Promise<CetusPoolResult> {
  const snapshot = generatePseudoTopK(poolState);

  return {
    status: "AVAILABLE",
    snapshot,
    healthLabel: "HTTP_OK",
    warnings: [],
  };
}

/**
 * Simulate Cetus pool unavailable (for testing)
 *
 * @returns Pool result with error
 */
export async function simulateCetusUnavailable(): Promise<CetusPoolResult> {
  return {
    status: "ERROR",
    healthLabel: "UNKNOWN",
    warnings: ["CETUS_POOL_UNAVAILABLE"],
  };
}

/**
 * Create stub pool state (for testing)
 *
 * @param price - Target price
 * @param liquidity - Liquidity amount
 * @returns Pool state
 */
export function createStubPoolState(
  price: number = 1.0,
  liquidity: number = 100000
): CetusPoolState {
  return {
    sqrtPrice: Math.sqrt(price),
    liquidity,
    timestamp: Date.now(),
  };
}
