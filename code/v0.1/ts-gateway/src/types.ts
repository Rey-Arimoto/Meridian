/**
 * Meridian TS Gateway — v0.1
 * Type definitions for execution boundary
 *
 * IMPORTANT:
 * - This file is part of the v0.1 frozen interface.
 * - Do NOT introduce business logic here.
 */

/**
 * Swap direction relative to the base asset.
 * base_to_quote : sell base, receive quote
 * quote_to_base : buy base, spend quote
 */
export type DeepSwapSide = "base_to_quote" | "quote_to_base";

/**
 * Request payload for DeepBook swap.
 * (v0.1: structural definition only, execution is stubbed)
 */
export interface DeepSwapRequest {
  side: DeepSwapSide;
  poolKey: string;

  /** Amount of input asset (human-readable) */
  amount: number;

  /** Optional DEEP token amount (usually 0 in v0.1) */
  deepAmount: number;

  /** Minimum acceptable output amount (slippage guard) */
  minOut: number;

  /** Client-generated id for audit / trace */
  clientOrderId?: string;
}

/**
 * Response returned by TS Gateway.
 * Always returned, even on failure.
 */
export interface DeepSwapResponse {
  /** Execution status */
  ok: boolean;

  side: DeepSwapSide;
  poolKey: string;
  amount: number;

  /** Actual output amount (0 on failure) */
  amountOut: number;

  /** Sui transaction digest if executed */
  txDigest?: string;

  /** Echo back client id */
  clientOrderId?: string;

  /** Error message if ok === false */
  errorMessage?: string;
}
