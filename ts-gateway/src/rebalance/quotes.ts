/**
 * PR153: v1.4 Quote Interface + Stub (READ-ONLY)
 * PR157: v1.4 Slippage + minOut Guard + Quote Consistency (READ-ONLY)
 *
 * Purpose:
 *   Define quote interface for Cetus and DeepBook.
 *   Stub implementation returns deterministic labels for testing.
 *   Future PR will replace with actual SDK/HTTP calls.
 *
 * PR157 Updates:
 *   - Add required fields: side, amountIn, amountOut, ts
 *   - Enable minOut calculation and consistency checks
 *
 * Constitutional Constraints:
 *   - READ-ONLY: No execution, just quote fetching
 *   - Stub only: Deterministic for testing
 *   - Label-only output: Impact/slippage/depth as labels
 *   - Numeric values: Internal only (amountIn/amountOut)
 */

/**
 * Quote venue
 */
export type QuoteVenue = "CETUS" | "DEEPBOOK";

/**
 * Impact label (price impact severity)
 */
export type ImpactLabel =
  | "IMPACT_UNKNOWN"
  | "IMPACT_LOW"
  | "IMPACT_MED"
  | "IMPACT_HIGH";

/**
 * Slippage label (slippage severity)
 */
export type SlipLabel = "SLIP_UNKNOWN" | "SLIP_LOW" | "SLIP_MED" | "SLIP_HIGH";

/**
 * Depth label (liquidity depth)
 */
export type DepthLabel = "DEPTH_UNKNOWN" | "DEPTH_OK" | "DEPTH_THIN";

/**
 * Fee label (fee tier)
 */
export type FeeLabel = "FEE_UNKNOWN" | "FEE_LOW" | "FEE_MED" | "FEE_HIGH";

/**
 * Swap side
 */
export type SwapSide = "WBTC_TO_USDC" | "USDC_TO_WBTC";

/**
 * Quote request
 */
export interface QuoteRequest {
  // Trading pair reference (e.g., "WBTC-USDC")
  pairRef: string;

  // Notional USD amount
  notionalUsd: number;

  // Swap side
  side: SwapSide;
}

/**
 * Quote result (PR157: Extended with numeric fields for minOut calculation)
 */
export interface QuoteResult {
  // Venue
  venue: QuoteVenue;

  // Status
  status: "AVAILABLE" | "UNAVAILABLE" | "ERROR";

  // Swap side (PR157: Required for consistency check)
  side: SwapSide;

  // Amount in (PR157: Internal numeric, required for minOut)
  amountIn: number;

  // Amount out (PR157: Internal numeric, required for minOut)
  amountOut: number;

  // Timestamp (PR157: epoch ms, for staleness check)
  ts: number;

  // Impact label
  impact: ImpactLabel;

  // Slippage label
  slippage: SlipLabel;

  // Depth label
  depth: DepthLabel;

  // Fee label
  fee: FeeLabel;

  // Warnings (label-only, no numbers)
  warnings: string[];
}

/**
 * Get quote from Cetus (stub implementation)
 *
 * @param req - Quote request
 * @returns Quote result
 *
 * Stub behavior:
 *   - notionalUsd < 1000 → IMPACT_LOW, SLIP_LOW, DEPTH_OK, FEE_LOW
 *   - notionalUsd 1000-10000 → IMPACT_MED, SLIP_MED, DEPTH_OK, FEE_MED
 *   - notionalUsd > 10000 → IMPACT_HIGH, SLIP_HIGH, DEPTH_THIN, FEE_HIGH
 *   - Always AVAILABLE (stub)
 */
export async function getQuoteCetus(req: QuoteRequest): Promise<QuoteResult> {
  const warnings: string[] = [];
  warnings.push("[STUB] Cetus quote is stubbed (actual SDK in future PR)");

  // Deterministic stub logic based on notional
  let impact: ImpactLabel;
  let slippage: SlipLabel;
  let depth: DepthLabel;
  let fee: FeeLabel;

  if (req.notionalUsd < 1000) {
    impact = "IMPACT_LOW";
    slippage = "SLIP_LOW";
    depth = "DEPTH_OK";
    fee = "FEE_LOW";
  } else if (req.notionalUsd < 10000) {
    impact = "IMPACT_MED";
    slippage = "SLIP_MED";
    depth = "DEPTH_OK";
    fee = "FEE_MED";
  } else {
    impact = "IMPACT_HIGH";
    slippage = "SLIP_HIGH";
    depth = "DEPTH_THIN";
    fee = "FEE_HIGH";
  }

  // PR157: Calculate stub amountIn/amountOut
  // For stub, assume wBTC price = $45000, USDC = $1
  let amountIn: number;
  let amountOut: number;

  if (req.side === "USDC_TO_WBTC") {
    // Buying wBTC with USDC
    amountIn = req.notionalUsd; // USDC amount
    amountOut = req.notionalUsd / 45000; // wBTC amount
  } else {
    // Selling wBTC for USDC
    amountIn = req.notionalUsd / 45000; // wBTC amount
    amountOut = req.notionalUsd; // USDC amount
  }

  return {
    venue: "CETUS",
    status: "AVAILABLE",
    side: req.side,
    amountIn,
    amountOut,
    ts: Date.now(), // PR157: Current timestamp
    impact,
    slippage,
    depth,
    fee,
    warnings,
  };
}

/**
 * Get quote from DeepBook (stub implementation)
 *
 * @param req - Quote request
 * @returns Quote result
 *
 * Stub behavior:
 *   - Similar to Cetus but slightly worse (for router testing)
 *   - notionalUsd < 1000 → IMPACT_LOW, SLIP_MED, DEPTH_OK, FEE_MED
 *   - notionalUsd 1000-10000 → IMPACT_MED, SLIP_HIGH, DEPTH_OK, FEE_MED
 *   - notionalUsd > 10000 → IMPACT_HIGH, SLIP_HIGH, DEPTH_THIN, FEE_HIGH
 *   - Always AVAILABLE (stub)
 */
export async function getQuoteDeepBook(
  req: QuoteRequest
): Promise<QuoteResult> {
  const warnings: string[] = [];
  warnings.push("[STUB] DeepBook quote is stubbed (actual SDK in future PR)");

  // Deterministic stub logic (slightly worse than Cetus for testing)
  let impact: ImpactLabel;
  let slippage: SlipLabel;
  let depth: DepthLabel;
  let fee: FeeLabel;

  if (req.notionalUsd < 1000) {
    impact = "IMPACT_LOW";
    slippage = "SLIP_MED"; // Worse than Cetus
    depth = "DEPTH_OK";
    fee = "FEE_MED"; // Worse than Cetus
  } else if (req.notionalUsd < 10000) {
    impact = "IMPACT_MED";
    slippage = "SLIP_HIGH"; // Worse than Cetus
    depth = "DEPTH_OK";
    fee = "FEE_MED";
  } else {
    impact = "IMPACT_HIGH";
    slippage = "SLIP_HIGH";
    depth = "DEPTH_THIN";
    fee = "FEE_HIGH";
  }

  // PR157: Calculate stub amountIn/amountOut
  // For stub, assume wBTC price = $45000, USDC = $1
  let amountIn: number;
  let amountOut: number;

  if (req.side === "USDC_TO_WBTC") {
    // Buying wBTC with USDC
    amountIn = req.notionalUsd; // USDC amount
    amountOut = req.notionalUsd / 45000; // wBTC amount
  } else {
    // Selling wBTC for USDC
    amountIn = req.notionalUsd / 45000; // wBTC amount
    amountOut = req.notionalUsd; // USDC amount
  }

  return {
    venue: "DEEPBOOK",
    status: "AVAILABLE",
    side: req.side,
    amountIn,
    amountOut,
    ts: Date.now(), // PR157: Current timestamp
    impact,
    slippage,
    depth,
    fee,
    warnings,
  };
}

/**
 * Create stub quote request (for testing)
 *
 * @param notionalUsd - Notional USD amount
 * @param side - Swap side
 * @returns Quote request
 */
export function createStubQuoteRequest(
  notionalUsd: number,
  side: SwapSide = "USDC_TO_WBTC"
): QuoteRequest {
  return {
    pairRef: "WBTC-USDC",
    notionalUsd,
    side,
  };
}
