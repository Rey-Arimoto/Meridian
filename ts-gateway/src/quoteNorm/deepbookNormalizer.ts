/**
 * PR187: v1.4 Routing + Quote Normalization v1 - DeepBook Normalizer (READ-ONLY)
 *
 * Purpose:
 *   Normalize DeepBook orderbook snapshots (WS/HTTP) to NormalizedQuoteV1.
 *
 * Constitutional Constraints:
 *   - READ-ONLY: No learning, optimization, or prediction
 *   - Fixed rules: Deterministic spread/depth thresholds
 *   - Unknown → conservative: Missing data → UNKNOWN labels
 *   - Defensive: Never throws, always returns valid model
 */

import type {
  NormalizedQuoteV1,
  DeepBookOrderbookSnapshot,
  QuoteSourceVenue,
  TradeSide,
  QuoteImpactLabel,
  QuoteDepthLabel,
} from "./types";

/**
 * Fixed thresholds for impact classification (PR187)
 */
const IMPACT_THRESHOLDS = {
  NORMAL_MAX_BPS: 30,   // < 0.3% → NORMAL
  MEDIUM_MAX_BPS: 100,  // 0.3% - 1% → MEDIUM
  // ≥ 1% → HIGH
};

/**
 * Fixed thresholds for depth classification (PR187)
 * Based on volume at best levels (in USD notional)
 */
const DEPTH_THRESHOLDS = {
  THIN_MAX_USD: 5000,   // < $5k → THIN
  // ≥ $5k → OK
};

/**
 * Normalize DeepBook orderbook snapshot to NormalizedQuoteV1
 *
 * Fixed rules:
 *   1. mid = (bestBid + bestAsk) / 2
 *   2. spread = ((bestAsk - bestBid) / mid) * 10000 (bps)
 *   3. Impact: spread < 30 bps → NORMAL, 30-100 bps → MEDIUM, ≥ 100 bps → HIGH
 *   4. Depth: volume < $5k → THIN, ≥ $5k → OK
 *   5. Missing data → UNKNOWN labels
 *
 * @param orderbook - DeepBook orderbook snapshot
 * @param venue - Quote source ("DEEPBOOK_WS" | "DEEPBOOK_HTTP")
 * @param side - Trade side
 * @param amountIn - Input amount for quote
 * @returns NormalizedQuoteV1
 *
 * Defensive: Never throws, returns UNAVAILABLE on error.
 */
export function normalizeDeepBookQuote(
  orderbook: DeepBookOrderbookSnapshot | null | undefined,
  venue: QuoteSourceVenue,
  side: TradeSide,
  amountIn: number
): NormalizedQuoteV1 {
  try {
    // Validate inputs
    if (!orderbook || !orderbook.bids || !orderbook.asks) {
      return createUnavailableQuote(venue, side, "ORDERBOOK_MISSING");
    }

    if (orderbook.bids.length === 0 || orderbook.asks.length === 0) {
      return createUnavailableQuote(venue, side, "ORDERBOOK_EMPTY");
    }

    // Get best bid and ask
    const bestBid = orderbook.bids[0];
    const bestAsk = orderbook.asks[0];

    if (!bestBid || !bestAsk) {
      return createUnavailableQuote(venue, side, "BEST_LEVELS_MISSING");
    }

    // Validate best levels
    if (
      typeof bestBid.price !== "number" ||
      typeof bestAsk.price !== "number" ||
      bestBid.price <= 0 ||
      bestAsk.price <= 0
    ) {
      return createUnavailableQuote(venue, side, "INVALID_PRICES");
    }

    // Compute mid price
    const mid = (bestBid.price + bestAsk.price) / 2;

    // Compute spread (bps)
    const spreadBps = ((bestAsk.price - bestBid.price) / mid) * 10000;

    // Classify impact based on spread
    const impactLabel = classifyImpact(spreadBps);

    // Classify depth based on volume
    const depthLabel = classifyDepth(bestBid.volume, bestAsk.volume, mid);

    // Compute execution price based on side
    let price: number;
    let amountOut: number;

    if (side === "BUY_WBTC_WITH_USDC") {
      // Buying WBTC: pay bestAsk price
      price = bestAsk.price;
      amountOut = amountIn / price;
    } else if (side === "SELL_WBTC_FOR_USDC") {
      // Selling WBTC: receive bestBid price
      price = bestBid.price;
      amountOut = amountIn * price;
    } else {
      // Unknown side
      return createUnavailableQuote(venue, side, "SIDE_UNKNOWN");
    }

    // Return normalized quote
    return {
      venue,
      status: "AVAILABLE",
      side,
      amountIn,
      amountOut,
      price,
      mid,
      spread: spreadBps,
      impactLabel,
      depthLabel,
      ts: orderbook.ts,
      reasons: ["NORMALIZED_FROM_ORDERBOOK"],
    };
  } catch (error) {
    // Defensive: Return UNAVAILABLE on error
    return createUnavailableQuote(venue, side, "NORMALIZE_ERROR");
  }
}

/**
 * Classify impact based on spread
 *
 * Fixed rules:
 *   - spread < 30 bps → IMPACT_NORMAL
 *   - 30 ≤ spread < 100 bps → IMPACT_MEDIUM
 *   - spread ≥ 100 bps → IMPACT_HIGH
 *   - Invalid spread → IMPACT_UNKNOWN
 *
 * @param spreadBps - Spread in basis points
 * @returns Impact label
 */
function classifyImpact(spreadBps: number): QuoteImpactLabel {
  if (typeof spreadBps !== "number" || isNaN(spreadBps) || spreadBps < 0) {
    return "IMPACT_UNKNOWN";
  }

  if (spreadBps < IMPACT_THRESHOLDS.NORMAL_MAX_BPS) {
    return "IMPACT_NORMAL";
  } else if (spreadBps < IMPACT_THRESHOLDS.MEDIUM_MAX_BPS) {
    return "IMPACT_MEDIUM";
  } else {
    return "IMPACT_HIGH";
  }
}

/**
 * Classify depth based on volume
 *
 * Fixed rules:
 *   - min(bidVolume, askVolume) * mid < $5k → DEPTH_THIN
 *   - min(bidVolume, askVolume) * mid ≥ $5k → DEPTH_OK
 *   - Invalid volume → DEPTH_UNKNOWN
 *
 * @param bidVolume - Best bid volume (in base currency)
 * @param askVolume - Best ask volume (in base currency)
 * @param mid - Mid price (USD)
 * @returns Depth label
 */
function classifyDepth(
  bidVolume: number,
  askVolume: number,
  mid: number
): QuoteDepthLabel {
  try {
    // Validate inputs
    if (
      typeof bidVolume !== "number" ||
      typeof askVolume !== "number" ||
      typeof mid !== "number" ||
      isNaN(bidVolume) ||
      isNaN(askVolume) ||
      isNaN(mid) ||
      bidVolume < 0 ||
      askVolume < 0 ||
      mid <= 0
    ) {
      return "DEPTH_UNKNOWN";
    }

    // Compute minimum volume in USD
    const minVolume = Math.min(bidVolume, askVolume);
    const minVolumeUsd = minVolume * mid;

    // Classify
    if (minVolumeUsd < DEPTH_THRESHOLDS.THIN_MAX_USD) {
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
 * @param venue - Quote source venue
 * @param side - Trade side
 * @param reason - Reason for unavailability
 * @returns NormalizedQuoteV1 with status "UNAVAILABLE"
 */
function createUnavailableQuote(
  venue: QuoteSourceVenue,
  side: TradeSide,
  reason: string
): NormalizedQuoteV1 {
  return {
    venue,
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
