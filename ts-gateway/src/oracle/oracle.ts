/**
 * PR155: v1.4 Price Oracle Integration - Main Oracle (READ-ONLY)
 *
 * Purpose:
 *   Aggregate prices from multiple sources with fixed priority.
 *   Provides USD valuation for notional cap safety checks.
 *
 * Constitutional Constraints:
 *   - READ-ONLY: Price observation only, no execution
 *   - No exceptions: Always returns OracleResult
 *   - Safe defaults: Missing prices → ERROR status
 *   - Label-only warnings (no numbers)
 *   - Fixed priority: DeepBook → Cetus → Fallback
 */

import {
  OracleConfig,
  OracleResult,
  OracleStatus,
  PricePoint,
  DEFAULT_ORACLE_CONFIG,
} from "./types";
import {
  fetchDeepBookMidPrice,
  fetchUsdcPrice,
} from "./sources/deepbookMid";
import { fetchCetusPoolPrice } from "./sources/cetusPool";
import { sanitizeWarning } from "./guards";

/**
 * Check if price point is fresh (within maxAge)
 *
 * @param price - Price point
 * @param maxAgeMs - Maximum age in milliseconds
 * @returns True if fresh
 */
function isFresh(price: PricePoint | null | undefined, maxAgeMs: number): boolean {
  if (!price) return false;

  const age = Date.now() - price.ts;
  return age <= maxAgeMs;
}

/**
 * Fetch wBTC price with fallback priority
 *
 * @param cfg - Oracle config
 * @returns Price point or null
 *
 * Priority:
 *   1. DeepBook mid price
 *   2. Cetus pool price
 *   3. Fallback (if enabled): null (no hardcoded fallback for wBTC)
 */
async function fetchWbtcPrice(cfg: OracleConfig): Promise<PricePoint | null> {
  try {
    // Priority 1: DeepBook
    const deepbookPrice = await fetchDeepBookMidPrice();
    if (deepbookPrice && isFresh(deepbookPrice, cfg.maxAgeMs)) {
      return deepbookPrice;
    }

    // Priority 2: Cetus
    const cetusPrice = await fetchCetusPoolPrice();
    if (cetusPrice && isFresh(cetusPrice, cfg.maxAgeMs)) {
      return cetusPrice;
    }

    // Priority 3: Fallback (not available for wBTC)
    if (cfg.allowFallback) {
      // No hardcoded fallback for wBTC (too volatile)
      return null;
    }

    return null;
  } catch (error) {
    // Defensive: catch all errors, return null
    return null;
  }
}

/**
 * Fetch USDC price with fallback
 *
 * @param cfg - Oracle config
 * @returns Price point (never null, fallback to 1.0)
 *
 * Priority:
 *   1. DeepBook price feed (future)
 *   2. Fallback: 1.0 (stablecoin assumption)
 */
async function fetchUsdcPriceWithFallback(
  cfg: OracleConfig
): Promise<PricePoint> {
  try {
    // Priority 1: DeepBook (stub returns 1.0)
    const price = await fetchUsdcPrice();
    if (price && isFresh(price, cfg.maxAgeMs)) {
      return price;
    }

    // Priority 2: Fallback (stablecoin assumption)
    if (cfg.allowFallback) {
      return {
        priceUsd: 1.0,
        source: "FALLBACK",
        ts: Date.now(),
      };
    }

    // Should not reach here (USDC always has fallback)
    return {
      priceUsd: 1.0,
      source: "FALLBACK",
      ts: Date.now(),
    };
  } catch (error) {
    // Defensive: fallback to 1.0 (stablecoin)
    return {
      priceUsd: 1.0,
      source: "FALLBACK",
      ts: Date.now(),
    };
  }
}

/**
 * Determine oracle status from price points
 *
 * @param wbtcUsd - wBTC price point (optional)
 * @param usdcUsd - USDC price point (optional)
 * @param cfg - Oracle config
 * @returns Status and warnings
 *
 * Status logic:
 *   - AVAILABLE: Both prices present and fresh
 *   - STALE: Prices present but old, or one missing
 *   - ERROR: wBTC price missing (critical for valuation)
 */
function determineStatus(
  wbtcUsd: PricePoint | null | undefined,
  usdcUsd: PricePoint | null | undefined,
  cfg: OracleConfig
): { status: OracleStatus; warnings: string[] } {
  const warnings: string[] = [];

  // Check if wBTC price available
  if (!wbtcUsd) {
    warnings.push("ORACLE_WBTC_UNAVAILABLE");
    return { status: "ERROR", warnings };
  }

  // Check if wBTC price fresh
  if (!isFresh(wbtcUsd, cfg.maxAgeMs)) {
    warnings.push("ORACLE_WBTC_STALE");
    return { status: "STALE", warnings };
  }

  // Check if USDC price available (should always be, due to fallback)
  if (!usdcUsd) {
    warnings.push("ORACLE_USDC_UNAVAILABLE");
    return { status: "STALE", warnings };
  }

  // Check if USDC price fresh
  if (!isFresh(usdcUsd, cfg.maxAgeMs)) {
    warnings.push("ORACLE_USDC_STALE");
    return { status: "STALE", warnings };
  }

  // All prices present and fresh
  return { status: "AVAILABLE", warnings };
}

/**
 * Fetch oracle prices (main API)
 *
 * @param cfg - Oracle config (optional, uses defaults)
 * @returns Oracle result
 *
 * This is the main entry point for price oracle.
 * Aggregates prices from multiple sources with fixed priority.
 *
 * IMPORTANT: Never throws exceptions. Always returns OracleResult.
 */
export async function fetchOracleV1(
  cfg?: Partial<OracleConfig>
): Promise<OracleResult> {
  // Merge with defaults
  const config: OracleConfig = {
    ...DEFAULT_ORACLE_CONFIG,
    ...cfg,
  };

  try {
    // Fetch prices
    const wbtcUsd = await fetchWbtcPrice(config);
    const usdcUsd = await fetchUsdcPriceWithFallback(config);

    // Determine status
    const { status, warnings } = determineStatus(wbtcUsd, usdcUsd, config);

    // Sanitize warnings (defensive)
    const sanitizedWarnings = warnings.map(sanitizeWarning);

    return {
      status,
      wbtcUsd: wbtcUsd || undefined,
      usdcUsd: usdcUsd || undefined,
      warnings: sanitizedWarnings,
    };
  } catch (error) {
    // Defensive: catch all errors, return ERROR status
    return {
      status: "ERROR",
      warnings: [sanitizeWarning("ORACLE_FETCH_FAILED")],
    };
  }
}

/**
 * Create fallback oracle result (for testing)
 *
 * @returns Oracle result with fallback prices
 */
export function createFallbackOracleResult(): OracleResult {
  return {
    status: "AVAILABLE",
    wbtcUsd: {
      priceUsd: 45000,
      source: "FALLBACK",
      ts: Date.now(),
    },
    usdcUsd: {
      priceUsd: 1.0,
      source: "FALLBACK",
      ts: Date.now(),
    },
    warnings: ["ORACLE_FALLBACK_USED"],
  };
}

/**
 * Create error oracle result (for testing)
 *
 * @returns Oracle result with ERROR status
 */
export function createErrorOracleResult(): OracleResult {
  return {
    status: "ERROR",
    warnings: ["ORACLE_WBTC_UNAVAILABLE"],
  };
}
