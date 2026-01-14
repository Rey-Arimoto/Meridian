/**
 * PR155: v1.4 Price Oracle Integration - Type Definitions (READ-ONLY)
 *
 * Purpose:
 *   Define types for price oracle integration.
 *   Provides USD valuation for notional cap safety checks.
 *
 * Constitutional Constraints:
 *   - READ-ONLY: Price observation only, no execution
 *   - Numeric values internal only (no numbers in warnings/logs)
 *   - Safe defaults: Oracle unavailable → BLOCK
 *   - No trading instructions in output
 */

/**
 * Oracle status
 */
export type OracleStatus = "AVAILABLE" | "STALE" | "ERROR";

/**
 * Price oracle source (fixed priority)
 *
 * Priority order:
 *   1. DEEPBOOK_MID - DeepBook mid price
 *   2. CETUS_POOL - Cetus pool implied price
 *   3. FALLBACK - Hardcoded fallback (USDC=1.0)
 */
export type PriceOracleSource = "DEEPBOOK_MID" | "CETUS_POOL" | "FALLBACK";

/**
 * Price point (single asset price)
 */
export interface PricePoint {
  // Price in USD (internal numeric, not exposed in warnings)
  priceUsd: number;

  // Source of price
  source: PriceOracleSource;

  // Timestamp (epoch ms)
  ts: number;
}

/**
 * Oracle result (aggregated prices for portfolio)
 */
export interface OracleResult {
  // Status (AVAILABLE if all prices fresh, STALE if old, ERROR if missing)
  status: OracleStatus;

  // wBTC price point (optional if unavailable)
  wbtcUsd?: PricePoint;

  // USDC price point (optional if unavailable)
  usdcUsd?: PricePoint;

  // Warnings (label-only, no numbers)
  warnings: string[];
}

/**
 * Oracle configuration
 */
export interface OracleConfig {
  // Maximum age for prices (milliseconds)
  // Default: 60_000 (1 minute)
  maxAgeMs: number;

  // Allow fallback to hardcoded prices
  // Default: true
  allowFallback: boolean;
}

/**
 * Default oracle configuration
 */
export const DEFAULT_ORACLE_CONFIG: OracleConfig = {
  maxAgeMs: 60_000, // 1 minute
  allowFallback: true,
};
