/**
 * PR187: v1.4 Routing + Quote Normalization v1 - Cetus Normalizer (READ-ONLY)
 *
 * Purpose:
 *   Normalize Cetus pool snapshots to NormalizedQuoteV1.
 *   Creates conservative pseudo-quote from sqrtPrice + liquidity.
 *
 * Constitutional Constraints:
 *   - READ-ONLY: No learning, optimization, or prediction
 *   - Fixed rules: Deterministic pseudo-quote generation
 *   - Conservative: MEDIUM impact, cautious depth estimation
 *   - Unknown → conservative: Missing data → conservative labels
 *   - Defensive: Never throws, always returns valid model
 */

import type {
  NormalizedQuoteV1,
  CetusPoolSnapshot,
  TradeSide,
  QuoteDepthLabel,
} from "./types";

/**
 * Fixed thresholds for Cetus depth classification (PR187)
 * Based on liquidity (conservative estimates)
 */
const CETUS_DEPTH_THRESHOLDS = {
  THIN_MAX_LIQUIDITY: 100000, // < 100k liquidity → THIN
  // ≥ 100k liquidity → OK
};

/**
 * Normalize Cetus pool snapshot to NormalizedQuoteV1
 *
 * Fixed rules:
 *   1. price = (sqrtPrice / 2^64)^2 (Cetus sqrtPriceX64 format)
 *   2. mid = price (no orderbook, spot price only)
 *   3. spread = 0 (no orderbook spread)
 *   4. Impact: MEDIUM (conservative, no orderbook visibility)
 *   5. Depth: Based on liquidity thresholds
 *   6. amountOut: Estimated from spot price (no slippage simulation)
 *
 * IMPORTANT: This is a FALLBACK pseudo-quote.
 * Always prefer DeepBook quotes when available.
 *
 * @param pool - Cetus pool snapshot
 * @param side - Trade side
 * @param amountIn - Input amount for quote
 * @returns NormalizedQuoteV1
 *
 * Defensive: Never throws, returns UNAVAILABLE on error.
 */
export function normalizeCetusQuote(
  pool: CetusPoolSnapshot | null | undefined,
  side: TradeSide,
  amountIn: number
): NormalizedQuoteV1 {
  try {
    // Validate inputs
    if (!pool) {
      return createCetusUnavailableQuote(side, "POOL_MISSING");
    }

    if (
      typeof pool.sqrtPrice !== "number" ||
      isNaN(pool.sqrtPrice) ||
      pool.sqrtPrice <= 0
    ) {
      return createCetusUnavailableQuote(side, "INVALID_SQRT_PRICE");
    }

    if (
      typeof pool.liquidity !== "number" ||
      isNaN(pool.liquidity) ||
      pool.liquidity < 0
    ) {
      return createCetusUnavailableQuote(side, "INVALID_LIQUIDITY");
    }

    // Compute price from sqrtPrice
    // Note: Assuming sqrtPriceX64 format (common in Cetus/Uniswap v3)
    // price = (sqrtPrice / 2^64)^2
    const Q64 = Math.pow(2, 64);
    const price = Math.pow(pool.sqrtPrice / Q64, 2);

    if (price <= 0 || !isFinite(price)) {
      return createCetusUnavailableQuote(side, "INVALID_COMPUTED_PRICE");
    }

    // Compute amountOut (simple spot price, no slippage simulation)
    let amountOut: number;

    if (side === "BUY_WBTC_WITH_USDC") {
      // Buying WBTC with USDC
      amountOut = amountIn / price;
    } else if (side === "SELL_WBTC_FOR_USDC") {
      // Selling WBTC for USDC
      amountOut = amountIn * price;
    } else {
      return createCetusUnavailableQuote(side, "SIDE_UNKNOWN");
    }

    // Classify depth based on liquidity
    const depthLabel = classifyCetusDepth(pool.liquidity);

    // Return normalized quote
    // CONSERVATIVE: Use MEDIUM impact (no orderbook visibility)
    return {
      venue: "CETUS",
      status: "AVAILABLE",
      side,
      amountIn,
      amountOut,
      price,
      mid: price, // No orderbook, mid = spot price
      spread: 0,  // No orderbook spread
      impactLabel: "IMPACT_MEDIUM", // Conservative: assume medium impact
      depthLabel,
      ts: pool.ts,
      reasons: ["NORMALIZED_FROM_CETUS_POOL", "PSEUDO_QUOTE_CONSERVATIVE"],
    };
  } catch (error) {
    // Defensive: Return UNAVAILABLE on error
    return createCetusUnavailableQuote(side, "NORMALIZE_ERROR");
  }
}

/**
 * Classify Cetus depth based on liquidity
 *
 * Fixed rules (conservative):
 *   - liquidity < 100k → DEPTH_THIN
 *   - liquidity ≥ 100k → DEPTH_OK
 *   - Invalid liquidity → DEPTH_UNKNOWN
 *
 * @param liquidity - Pool liquidity
 * @returns Depth label
 */
function classifyCetusDepth(liquidity: number): QuoteDepthLabel {
  try {
    if (typeof liquidity !== "number" || isNaN(liquidity) || liquidity < 0) {
      return "DEPTH_UNKNOWN";
    }

    if (liquidity < CETUS_DEPTH_THRESHOLDS.THIN_MAX_LIQUIDITY) {
      return "DEPTH_THIN";
    } else {
      return "DEPTH_OK";
    }
  } catch (error) {
    return "DEPTH_UNKNOWN";
  }
}

/**
 * Create UNAVAILABLE quote (helper)
 *
 * Returns a safe UNAVAILABLE quote with all fields populated.
 *
 * @param side - Trade side
 * @param reason - Reason for unavailability
 * @returns NormalizedQuoteV1 with status "UNAVAILABLE"
 */
function createCetusUnavailableQuote(
  side: TradeSide,
  reason: string
): NormalizedQuoteV1 {
  return {
    venue: "CETUS",
    status: "UNAVAILABLE",
    side,
    amountIn: 0,
    amountOut: 0,
    price: 0,
    mid: 0,
    spread: 0,
    impactLabel: "IMPACT_UNKNOWN",
    depthLabel: "DEPTH_UNKNOWN",
    ts: Date.now(),
    reasons: [reason],
  };
}
