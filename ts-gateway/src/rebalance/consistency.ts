/**
 * PR157: v1.4 Quote Consistency Check (READ-ONLY)
 *
 * Purpose:
 *   Validate quote integrity before creating transaction draft.
 *   Prevent broken/inconsistent quotes from reaching execution.
 *
 * Constitutional Constraints:
 *   - Fixed rules: No learning, no optimization
 *   - Never throws: Always returns consistency result
 *   - Label-only output: No numbers in warnings/checks
 *   - Conservative: When uncertain (oracle unavailable), block
 *   - Oracle-dependent: Consistency check requires oracle pricing
 */

import { QuoteResult, SwapSide } from "./quotes";

/**
 * Consistency check input
 */
export interface ConsistencyInput {
  // Quote to check
  quote: QuoteResult;

  // Oracle prices (for consistency validation)
  oraclePrices?: {
    wbtcUsd?: number; // wBTC price in USD (internal)
    usdcUsd?: number; // USDC price in USD (typically 1.0)
  };

  // Oracle status
  oracleStatus?: "AVAILABLE" | "STALE" | "ERROR";

  // Current timestamp (for staleness check)
  now?: number;
}

/**
 * Consistency check result
 */
export interface ConsistencyResult {
  // Is quote consistent?
  consistent: boolean;

  // Safety checks performed (label-only)
  checks: string[];

  // Warnings (label-only)
  warnings: string[];

  // Block reasons (if inconsistent)
  blockReasons: string[];
}

/**
 * Fixed consistency thresholds (constitutional constants)
 */
const CONSISTENCY_THRESHOLDS = {
  // Max quote age (60 seconds, same as oracle)
  MAX_QUOTE_AGE_MS: 60 * 1000,

  // Price deviation tolerance (±5%)
  MAX_PRICE_DEVIATION_PCT: 5.0,
};

/**
 * Check quote consistency (main API)
 *
 * @param input - Consistency input
 * @returns Consistency result
 *
 * Fixed rules (never throws):
 *   1. Check basic validity: amountIn > 0 && amountOut > 0
 *   2. Check staleness: quote.ts within maxAgeMs
 *   3. Check oracle availability
 *   4. Calculate impliedPrice from quote
 *   5. Compare impliedPrice with oracle price
 *   6. If deviation > ±5% → BLOCK_QUOTE_INCONSISTENT
 *
 * IMPORTANT: Requires oracle for consistency check.
 * If oracle unavailable → BLOCK_QUOTE_CONSISTENCY_UNAVAILABLE (safe default)
 */
export function checkQuoteConsistency(
  input: ConsistencyInput
): ConsistencyResult {
  const checks: string[] = [];
  const warnings: string[] = [];
  const blockReasons: string[] = [];

  try {
    const quote = input.quote;
    const now = input.now ?? Date.now();

    // Step 1: Basic validity check
    if (
      !quote.amountIn ||
      !quote.amountOut ||
      quote.amountIn <= 0 ||
      quote.amountOut <= 0 ||
      isNaN(quote.amountIn) ||
      isNaN(quote.amountOut)
    ) {
      blockReasons.push("BLOCK_QUOTE_AMOUNTS_INVALID");
      warnings.push("WARN_QUOTE_AMOUNTS_INVALID");

      return {
        consistent: false,
        checks,
        warnings,
        blockReasons,
      };
    }

    checks.push("CHECK_QUOTE_AMOUNTS_VALID");

    // Step 2: Staleness check
    if (!quote.ts || isNaN(quote.ts)) {
      blockReasons.push("BLOCK_QUOTE_TIMESTAMP_MISSING");
      warnings.push("WARN_QUOTE_TIMESTAMP_MISSING");

      return {
        consistent: false,
        checks,
        warnings,
        blockReasons,
      };
    }

    const quoteAge = now - quote.ts;
    if (quoteAge > CONSISTENCY_THRESHOLDS.MAX_QUOTE_AGE_MS) {
      blockReasons.push("BLOCK_QUOTE_STALE");
      warnings.push("WARN_QUOTE_STALE");

      return {
        consistent: false,
        checks,
        warnings,
        blockReasons,
      };
    }

    checks.push("CHECK_QUOTE_FRESH");

    // Step 3: Oracle availability check
    if (
      !input.oracleStatus ||
      input.oracleStatus === "ERROR" ||
      input.oracleStatus === "STALE"
    ) {
      blockReasons.push("BLOCK_QUOTE_CONSISTENCY_UNAVAILABLE");
      warnings.push("WARN_ORACLE_UNAVAILABLE_FOR_CONSISTENCY");

      return {
        consistent: false,
        checks,
        warnings,
        blockReasons,
      };
    }

    if (
      !input.oraclePrices ||
      !input.oraclePrices.wbtcUsd ||
      !input.oraclePrices.usdcUsd
    ) {
      blockReasons.push("BLOCK_QUOTE_CONSISTENCY_UNAVAILABLE");
      warnings.push("WARN_ORACLE_PRICES_MISSING");

      return {
        consistent: false,
        checks,
        warnings,
        blockReasons,
      };
    }

    checks.push("CHECK_ORACLE_AVAILABLE");

    // Step 4: Calculate implied price from quote
    let impliedWbtcPrice: number;

    if (quote.side === "USDC_TO_WBTC") {
      // Buying wBTC with USDC
      // impliedWbtcPrice = amountIn (USDC) / amountOut (wBTC)
      impliedWbtcPrice = quote.amountIn / quote.amountOut;
    } else {
      // Selling wBTC for USDC
      // impliedWbtcPrice = amountOut (USDC) / amountIn (wBTC)
      impliedWbtcPrice = quote.amountOut / quote.amountIn;
    }

    checks.push("CHECK_IMPLIED_PRICE_CALCULATED");

    // Step 5: Compare with oracle price
    const oracleWbtcPrice = input.oraclePrices.wbtcUsd!;

    // Calculate deviation percentage
    const deviation =
      Math.abs(impliedWbtcPrice - oracleWbtcPrice) / oracleWbtcPrice;
    const deviationPct = deviation * 100;

    // Step 6: Check deviation threshold
    if (deviationPct > CONSISTENCY_THRESHOLDS.MAX_PRICE_DEVIATION_PCT) {
      blockReasons.push("BLOCK_QUOTE_INCONSISTENT");
      warnings.push("WARN_QUOTE_PRICE_DEVIATION");

      return {
        consistent: false,
        checks,
        warnings,
        blockReasons,
      };
    }

    checks.push("CHECK_QUOTE_PRICE_CONSISTENT");

    // All checks passed
    return {
      consistent: true,
      checks,
      warnings,
      blockReasons,
    };
  } catch (error) {
    // Defensive: Never throw, return error state
    return {
      consistent: false,
      checks,
      warnings: ["WARN_CONSISTENCY_CHECK_ERROR"],
      blockReasons: ["BLOCK_CONSISTENCY_CHECK_ERROR"],
    };
  }
}

/**
 * Get consistency summary (for logging/debugging)
 *
 * @param result - Consistency result
 * @returns Summary string (label-only)
 */
export function getConsistencySummary(result: ConsistencyResult): string {
  if (result.consistent) {
    return "CONSISTENCY_OK";
  }

  if (result.blockReasons.length > 0) {
    return `CONSISTENCY_BLOCKED_${result.blockReasons[0]}`;
  }

  return "CONSISTENCY_UNKNOWN";
}
