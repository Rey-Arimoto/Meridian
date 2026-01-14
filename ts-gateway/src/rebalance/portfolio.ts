/**
 * PR152: v1.4 TS Portfolio Snapshot (READ-ONLY)
 *
 * Purpose:
 *   Observe wallet balances and calculate current portfolio weights.
 *   This is a stub implementation - actual wallet integration in future PR.
 *
 * Constitutional Constraints:
 *   - READ-ONLY: No mutations, no trades
 *   - Privacy: Never log private keys or sensitive data
 *   - Defensive: Handle errors gracefully
 */

import { PortfolioSnapshot, TokenSymbol } from "./types";

/**
 * Portfolio dependencies (abstracted for testing)
 */
export interface PortfolioDeps {
  // Get token balance (as string)
  getBalance: (symbol: TokenSymbol) => Promise<string>;

  // Get token price in USD
  getPriceUsd: (symbol: TokenSymbol) => Promise<number>;
}

/**
 * Get portfolio snapshot
 *
 * @param deps - Portfolio dependencies
 * @returns Portfolio snapshot
 *
 * @example
 * const snapshot = await getPortfolioSnapshot({
 *   getBalance: async (symbol) => "1000.0",
 *   getPriceUsd: async (symbol) => symbol === "USDC" ? 1.0 : 45000.0,
 * });
 */
export async function getPortfolioSnapshot(
  deps: PortfolioDeps
): Promise<PortfolioSnapshot> {
  // Get balances
  const wbtcBalance = await deps.getBalance("WBTC");
  const usdcBalance = await deps.getBalance("USDC");
  const suiBalance = await deps.getBalance("SUI");

  // Get prices
  const wbtcPriceUsd = await deps.getPriceUsd("WBTC");
  const usdcPriceUsd = await deps.getPriceUsd("USDC"); // Should always be 1.0

  // Parse balances to numbers for calculation
  const wbtcAmount = parseFloat(wbtcBalance);
  const usdcAmount = parseFloat(usdcBalance);

  // Calculate USD values
  const wbtcValueUsd = wbtcAmount * wbtcPriceUsd;
  const usdcValueUsd = usdcAmount * usdcPriceUsd;

  // Total USD (excluding SUI - SUI is gas only)
  const totalUsd = wbtcValueUsd + usdcValueUsd;

  // Calculate weights (normalized to 1.0)
  let wbtcWeight = 0;
  let usdcWeight = 0;

  if (totalUsd > 0) {
    wbtcWeight = wbtcValueUsd / totalUsd;
    usdcWeight = usdcValueUsd / totalUsd;
  } else {
    // Edge case: empty portfolio
    wbtcWeight = 0.5;
    usdcWeight = 0.5;
  }

  return {
    balances: {
      WBTC: wbtcBalance,
      USDC: usdcBalance,
      SUI: suiBalance,
    },
    pricesUsd: {
      WBTC: wbtcPriceUsd,
      USDC: usdcPriceUsd,
    },
    valuesUsd: {
      WBTC: wbtcValueUsd,
      USDC: usdcValueUsd,
    },
    weights: {
      WBTC: wbtcWeight,
      USDC: usdcWeight,
    },
    totalUsd,
    timestamp: Date.now(),
  };
}

/**
 * Create stub portfolio dependencies (for testing)
 *
 * @param overrides - Override default stub behavior
 * @returns Stub portfolio dependencies
 */
export function createStubPortfolioDeps(
  overrides?: Partial<PortfolioDeps>
): PortfolioDeps {
  return {
    getBalance: async (symbol: TokenSymbol) => {
      // Default stub balances
      switch (symbol) {
        case "WBTC":
          return "0.01"; // 0.01 wBTC
        case "USDC":
          return "500.0"; // 500 USDC
        case "SUI":
          return "1.0"; // 1 SUI (gas)
        default:
          return "0.0";
      }
    },
    getPriceUsd: async (symbol: TokenSymbol) => {
      // Default stub prices
      switch (symbol) {
        case "WBTC":
          return 45000.0; // $45k per wBTC
        case "USDC":
          return 1.0; // $1 per USDC (stablecoin)
        case "SUI":
          return 2.0; // $2 per SUI
        default:
          return 0.0;
      }
    },
    ...overrides,
  };
}
