/**
 * PR187: v1.4 Routing + Quote Normalization v1 (READ-ONLY)
 *
 * Purpose:
 *   Unified quote model for all sources (DeepBook WS/HTTP, Cetus pool).
 *   Deterministic routing with fixed rules.
 *
 * Constitutional Constraints:
 *   - READ-ONLY: No learning, optimization, or prediction
 *   - Fixed rules: Deterministic normalization and routing
 *   - Numeric never logged: Internal fields only, sanitized for telemetry
 *   - Unknown → conservative: Missing data uses safe defaults
 *   - Defensive: Never throws, always returns valid model
 */

/**
 * Quote source venue (PR187)
 */
export type QuoteSourceVenue =
  | "DEEPBOOK_WS"    // DeepBook WebSocket (primary)
  | "DEEPBOOK_HTTP"  // DeepBook HTTP API (fallback)
  | "CETUS"          // Cetus pool (last resort)
  | "NONE";          // No source available

/**
 * Quote status (PR187)
 */
export type QuoteStatus =
  | "AVAILABLE"    // Quote available and fresh
  | "UNAVAILABLE"  // Quote not available
  | "ERROR"        // Quote fetch error
  | "STALE";       // Quote available but stale

/**
 * Quote impact label (PR187)
 * Derived from spread or slippage thresholds
 */
export type QuoteImpactLabel =
  | "IMPACT_NORMAL"   // Low impact (spread < 0.3%)
  | "IMPACT_MEDIUM"   // Medium impact (0.3% ≤ spread < 1%)
  | "IMPACT_HIGH"     // High impact (spread ≥ 1%)
  | "IMPACT_UNKNOWN"; // Impact cannot be determined

/**
 * Quote depth label (PR187)
 * Derived from volume thresholds
 */
export type QuoteDepthLabel =
  | "DEPTH_OK"       // Sufficient depth
  | "DEPTH_THIN"     // Thin depth (low volume)
  | "DEPTH_UNKNOWN"; // Depth cannot be determined

/**
 * Trade side (PR187)
 */
export type TradeSide =
  | "BUY_WBTC_WITH_USDC"   // Buy WBTC with USDC
  | "SELL_WBTC_FOR_USDC"   // Sell WBTC for USDC
  | "UNKNOWN";             // Side unknown

/**
 * NormalizedQuoteV1 (PR187)
 *
 * Unified quote model for all sources.
 * CRITICAL: Internal numeric fields MUST NOT be logged.
 * Use guards.sanitizeQuoteForLogs() before logging.
 *
 * Fields:
 *   - venue: Quote source
 *   - status: Quote status
 *   - side: Trade direction
 *   - amountIn: Input amount (NUMERIC, never log)
 *   - amountOut: Output amount (NUMERIC, never log)
 *   - price: Execution price (NUMERIC, never log)
 *   - mid: Mid price from orderbook (NUMERIC, never log)
 *   - spread: Bid-ask spread (NUMERIC, never log)
 *   - impactLabel: Impact classification (LABEL-ONLY)
 *   - depthLabel: Depth classification (LABEL-ONLY)
 *   - ts: Timestamp (ms)
 *   - reasons: Derivation reasons (LABEL-ONLY)
 */
export interface NormalizedQuoteV1 {
  // Source and status
  venue: QuoteSourceVenue;
  status: QuoteStatus;

  // Trade details
  side: TradeSide;

  // NUMERIC FIELDS (NEVER LOG - use sanitizeQuoteForLogs())
  amountIn: number;     // Input amount (e.g., USDC)
  amountOut: number;    // Output amount (e.g., WBTC)
  price: number;        // Execution price
  mid: number;          // Mid price (best bid + ask) / 2
  spread: number;       // Bid-ask spread (bps)

  // LABEL-ONLY FIELDS (safe to log)
  impactLabel: QuoteImpactLabel;
  depthLabel: QuoteDepthLabel;

  // Metadata
  ts: number;           // Timestamp (ms)
  reasons: string[];    // Derivation reasons (LABEL-ONLY)
}

/**
 * Sanitized quote (safe for logging)
 * All numeric fields removed, only labels remain
 */
export interface SanitizedQuote {
  venue: QuoteSourceVenue;
  status: QuoteStatus;
  side: TradeSide;
  impactLabel: QuoteImpactLabel;
  depthLabel: QuoteDepthLabel;
  ts: number;
  reasons: string[];
}

/**
 * DeepBook orderbook snapshot (input for normalization)
 */
export interface DeepBookOrderbookSnapshot {
  bids: Array<{ price: number; volume: number }>;
  asks: Array<{ price: number; volume: number }>;
  ts: number;
}

/**
 * Cetus pool snapshot (input for normalization)
 */
export interface CetusPoolSnapshot {
  sqrtPrice: number;
  liquidity: number;
  ts: number;
}

/**
 * Quote sources (input for router)
 */
export interface QuoteSources {
  deepbookWs?: DeepBookOrderbookSnapshot;
  deepbookHttp?: DeepBookOrderbookSnapshot;
  cetusPool?: CetusPoolSnapshot;
}
