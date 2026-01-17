/**
 * PR187: v1.4 Routing + Quote Normalization v1 - Router (READ-ONLY)
 *
 * Purpose:
 *   Select and normalize quotes with deterministic priority routing.
 *   Unifies all quote sources into NormalizedQuoteV1.
 *
 * Constitutional Constraints:
 *   - READ-ONLY: No learning, optimization, or prediction
 *   - Fixed rules: Deterministic priority routing
 *   - Priority: DeepBook WS → HTTP → Cetus → UNAVAILABLE
 *   - Defensive: Never throws, always returns valid model
 */

import type {
  NormalizedQuoteV1,
  QuoteSources,
  TradeSide,
} from "./types";
import { normalizeDeepBookQuote } from "./deepbookNormalizer";
import { normalizeCetusQuote } from "./cetusNormalizer";
import { isQuoteUsable } from "./guards";

/**
 * Select and normalize quote with priority routing
 *
 * Fixed priority rules:
 *   1. DeepBook WS (primary)
 *   2. DeepBook HTTP (fallback)
 *   3. Cetus pool (last resort)
 *   4. UNAVAILABLE (if all fail)
 *
 * @param args - Arguments
 * @param args.quoteSources - Available quote sources
 * @param args.side - Trade side
 * @param args.amountIn - Input amount for quote
 * @returns NormalizedQuoteV1
 *
 * Defensive: Never throws, always returns valid NormalizedQuoteV1.
 * If all sources unavailable, returns UNAVAILABLE quote.
 */
export function selectAndNormalizeQuote(args: {
  quoteSources: QuoteSources;
  side: TradeSide;
  amountIn: number;
}): NormalizedQuoteV1 {
  try {
    const { quoteSources, side, amountIn } = args;

    // Priority 1: DeepBook WS
    if (quoteSources.deepbookWs) {
      const quote = normalizeDeepBookQuote(
        quoteSources.deepbookWs,
        "DEEPBOOK_WS",
        side,
        amountIn
      );

      if (isQuoteUsable(quote)) {
        return quote;
      }
    }

    // Priority 2: DeepBook HTTP (fallback)
    if (quoteSources.deepbookHttp) {
      const quote = normalizeDeepBookQuote(
        quoteSources.deepbookHttp,
        "DEEPBOOK_HTTP",
        side,
        amountIn
      );

      if (isQuoteUsable(quote)) {
        return quote;
      }
    }

    // Priority 3: Cetus pool (last resort)
    if (quoteSources.cetusPool) {
      const quote = normalizeCetusQuote(
        quoteSources.cetusPool,
        side,
        amountIn
      );

      if (isQuoteUsable(quote)) {
        return quote;
      }
    }

    // Priority 4: All sources unavailable
    return createNoneQuote(side, "ALL_SOURCES_UNAVAILABLE");
  } catch (error) {
    // Defensive: Return UNAVAILABLE on error
    return createNoneQuote(args.side, "ROUTER_ERROR");
  }
}

/**
 * Create NONE/UNAVAILABLE quote (helper)
 *
 * Returns a safe UNAVAILABLE quote when no sources are available.
 *
 * @param side - Trade side
 * @param reason - Reason for unavailability
 * @returns NormalizedQuoteV1 with venue "NONE" and status "UNAVAILABLE"
 */
function createNoneQuote(side: TradeSide, reason: string): NormalizedQuoteV1 {
  return {
    venue: "NONE",
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
