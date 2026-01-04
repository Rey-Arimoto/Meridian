# Meridian TS Gateway (v0.1)

This gateway is the "hands" for Meridian.
It holds the Sui private key **only here** and exposes minimal HTTP APIs for swaps.

## Guarantees (v0.1)
- Private key never leaves TS gateway
- Python calls gateway over HTTP only
- Minimal health + swap endpoint

## Setup
```bash
cd ts-gateway
cp .env.example .env
# edit .env and set SUI_PRIVATE_KEY
npm install
npm run dev

Endpoints
	•	GET /api/health
	•	POST /api/swap_deepbook (v0.1: skeleton; amountOut parsing may be TODO)

v0.1 focuses on wiring and safety boundaries.
v0.2+ will harden swap correctness, quote validation, and amountOut parsing.

---

# `ts-gateway/src/` 以下

## `ts-gateway/src/types.ts`

```ts
export type DeepSwapSide = "base_to_quote" | "quote_to_base";

export interface DeepSwapRequest {
  side: DeepSwapSide;
  poolKey: string;

  /**
   * v0.1 semantics:
   * - base_to_quote: amount = base amount in
   * - quote_to_base: amount = quote amount in
   */
  amount: number;

  /**
   * Deep incentives / routing parameter (optional for v0.1)
   */
  deepAmount: number;

  /**
   * Minimum output amount (slippage guard lives on caller side)
   */
  minOut: number;

  clientOrderId?: string;
}

export interface DeepSwapResponse {
  ok: boolean;
  side: DeepSwapSide;
  poolKey: string;

  amount: number;
  amountOut: number;

  txDigest?: string;
  clientOrderId?: string;

  errorMessage?: string;
}
