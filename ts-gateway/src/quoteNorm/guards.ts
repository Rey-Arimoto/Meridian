/**
 * PR187: v1.4 Routing + Quote Normalization v1 - Guards (READ-ONLY)
 *
 * Purpose:
 *   Sanitization and validation for NormalizedQuoteV1.
 *   Ensures numeric fields never leak to logs/telemetry.
 *
 * Constitutional Constraints:
 *   - READ-ONLY: No learning, optimization, or prediction
 *   - Fixed rules: Deterministic validation
 *   - Numeric never logged: sanitizeQuoteForLogs() removes all numerics
 *   - Defensive: Never throws, always returns safe values
 */

import type {
  NormalizedQuoteV1,
  SanitizedQuote,
  QuoteStatus,
} from "./types";

/**
 * Sanitize quote for logging/telemetry
 *
 * Removes ALL numeric fields (amountIn, amountOut, price, mid, spread).
 * Returns only labels and metadata safe for logging.
 *
 * CRITICAL: Always use this before logging quotes.
 *
 * @param quote - NormalizedQuoteV1
 * @returns SanitizedQuote (numeric fields removed)
 *
 * Fixed rules:
 *   - Remove: amountIn, amountOut, price, mid, spread
 *   - Keep: venue, status, side, impactLabel, depthLabel, ts, reasons
 *   - Defensive: Returns safe defaults on error
 */
export function sanitizeQuoteForLogs(
  quote: NormalizedQuoteV1 | null | undefined
): SanitizedQuote {
  try {
    if (!quote) {
      return {
        venue: "NONE",
        status: "UNAVAILABLE",
        side: "UNKNOWN",
        impactLabel: "IMPACT_UNKNOWN",
        depthLabel: "DEPTH_UNKNOWN",
        ts: Date.now(),
        reasons: ["QUOTE_MISSING"],
      };
    }

    // Return only label-safe fields
    return {
      venue: quote.venue,
      status: quote.status,
      side: quote.side,
      impactLabel: quote.impactLabel,
      depthLabel: quote.depthLabel,
      ts: quote.ts,
      reasons: [...quote.reasons], // Clone array
    };
  } catch (error) {
    // Defensive: Return safe defaults on error
    return {
      venue: "NONE",
      status: "ERROR",
      side: "UNKNOWN",
      impactLabel: "IMPACT_UNKNOWN",
      depthLabel: "DEPTH_UNKNOWN",
      ts: Date.now(),
      reasons: ["SANITIZE_ERROR"],
    };
  }
}

/**
 * Check if quote is usable for execution
 *
 * Fixed rules:
 *   - status must be "AVAILABLE"
 *   - amountOut must be > 0
 *   - amountIn must be > 0
 *   - price must be > 0
 *   - venue must not be "NONE"
 *
 * @param quote - NormalizedQuoteV1
 * @returns true if quote can be used for execution
 *
 * Defensive: Returns false on error or missing fields.
 */
export function isQuoteUsable(
  quote: NormalizedQuoteV1 | null | undefined
): boolean {
  try {
    if (!quote) {
      return false;
    }

    // Check status
    if (quote.status !== "AVAILABLE") {
      return false;
    }

    // Check venue
    if (quote.venue === "NONE") {
      return false;
    }

    // Check numeric fields (must be valid positive numbers)
    if (
      typeof quote.amountOut !== "number" ||
      isNaN(quote.amountOut) ||
      quote.amountOut <= 0
    ) {
      return false;
    }

    if (
      typeof quote.amountIn !== "number" ||
      isNaN(quote.amountIn) ||
      quote.amountIn <= 0
    ) {
      return false;
    }

    if (
      typeof quote.price !== "number" ||
      isNaN(quote.price) ||
      quote.price <= 0
    ) {
      return false;
    }

    return true;
  } catch (error) {
    // Defensive: Return false on error
    return false;
  }
}

/**
 * Check if quote is stale
 *
 * Fixed rules:
 *   - Fresh: age < 30 seconds
 *   - Stale: age ≥ 30 seconds
 *
 * @param quote - NormalizedQuoteV1
 * @param nowMs - Current timestamp (ms), defaults to Date.now()
 * @returns true if quote is stale
 *
 * Defensive: Returns true (stale) on error.
 */
export function isQuoteStale(
  quote: NormalizedQuoteV1 | null | undefined,
  nowMs?: number
): boolean {
  try {
    if (!quote) {
      return true; // Missing quote is considered stale
    }

    const now = nowMs ?? Date.now();
    const ageMs = now - quote.ts;

    // Stale if older than 30 seconds
    return ageMs >= 30000;
  } catch (error) {
    // Defensive: Return true (stale) on error
    return true;
  }
}

/**
 * Get quote status with staleness check
 *
 * Updates status to "STALE" if quote is old.
 *
 * @param quote - NormalizedQuoteV1
 * @param nowMs - Current timestamp (ms), defaults to Date.now()
 * @returns Updated status
 *
 * Fixed rules:
 *   - If status is "AVAILABLE" and age ≥ 30s → "STALE"
 *   - Otherwise, return original status
 */
export function getQuoteStatusWithStalenessCheck(
  quote: NormalizedQuoteV1 | null | undefined,
  nowMs?: number
): QuoteStatus {
  try {
    if (!quote) {
      return "UNAVAILABLE";
    }

    // If already not available, return original status
    if (quote.status !== "AVAILABLE") {
      return quote.status;
    }

    // Check staleness
    if (isQuoteStale(quote, nowMs)) {
      return "STALE";
    }

    return quote.status;
  } catch (error) {
    // Defensive: Return ERROR on exception
    return "ERROR";
  }
}
