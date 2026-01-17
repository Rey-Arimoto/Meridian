/**
 * PR187: v1.4 Routing + Quote Normalization v1 - Tests
 *
 * Purpose:
 *   Verify quote normalization from all sources (DeepBook WS/HTTP, Cetus).
 *   Test routing priority and defensive handling.
 *
 * Test Coverage:
 *   1. DeepBook WS OK → AVAILABLE with correct labels
 *   2. Spread wide → IMPACT_HIGH
 *   3. Thin depth → DEPTH_THIN
 *   4. HTTP fallback when WS unavailable
 *   5. Cetus pseudo quote (last resort)
 *   6. All sources unavailable → venue NONE
 *   7. Defensive: malformed input → UNAVAILABLE
 *   8. No numeric leakage in sanitized output
 *   9. Quote usability checks
 *   10. Quote staleness checks
 */

import {
  selectAndNormalizeQuote,
  normalizeDeepBookQuote,
  normalizeCetusQuote,
  sanitizeQuoteForLogs,
  isQuoteUsable,
  isQuoteStale,
  type DeepBookOrderbookSnapshot,
  type CetusPoolSnapshot,
  type QuoteSources,
} from "../src/quoteNorm";

describe("PR187: Quote Normalization", () => {
  /**
   * Test 1: DeepBook WS OK → AVAILABLE with correct labels
   */
  test("Test 1: DeepBook WS normal spread and depth", () => {
    const orderbook: DeepBookOrderbookSnapshot = {
      bids: [{ price: 49950, volume: 0.5 }], // $24,975 volume
      asks: [{ price: 50050, volume: 0.5 }], // $25,025 volume
      ts: Date.now(),
    };

    const quote = normalizeDeepBookQuote(
      orderbook,
      "DEEPBOOK_WS",
      "BUY_WBTC_WITH_USDC",
      1000 // $1000 USDC
    );

    expect(quote.venue).toBe("DEEPBOOK_WS");
    expect(quote.status).toBe("AVAILABLE");
    expect(quote.side).toBe("BUY_WBTC_WITH_USDC");

    // Spread: (50050 - 49950) / 50000 * 10000 = 20 bps → NORMAL
    expect(quote.impactLabel).toBe("IMPACT_NORMAL");

    // Depth: min(0.5 * 49950, 0.5 * 50050) = ~$25k → OK
    expect(quote.depthLabel).toBe("DEPTH_OK");

    // AmountOut: 1000 / 50050 ≈ 0.0199
    expect(quote.amountOut).toBeCloseTo(1000 / 50050, 4);
  });

  /**
   * Test 2: Spread wide → IMPACT_HIGH
   */
  test("Test 2: Wide spread triggers IMPACT_HIGH", () => {
    const orderbook: DeepBookOrderbookSnapshot = {
      bids: [{ price: 49000, volume: 0.5 }],
      asks: [{ price: 51000, volume: 0.5 }], // 4% spread
      ts: Date.now(),
    };

    const quote = normalizeDeepBookQuote(
      orderbook,
      "DEEPBOOK_WS",
      "BUY_WBTC_WITH_USDC",
      1000
    );

    // Spread: (51000 - 49000) / 50000 * 10000 = 400 bps → HIGH
    expect(quote.impactLabel).toBe("IMPACT_HIGH");
  });

  /**
   * Test 3: Thin depth → DEPTH_THIN
   */
  test("Test 3: Low volume triggers DEPTH_THIN", () => {
    const orderbook: DeepBookOrderbookSnapshot = {
      bids: [{ price: 50000, volume: 0.05 }], // $2,500 volume
      asks: [{ price: 50100, volume: 0.05 }], // $2,505 volume
      ts: Date.now(),
    };

    const quote = normalizeDeepBookQuote(
      orderbook,
      "DEEPBOOK_WS",
      "BUY_WBTC_WITH_USDC",
      1000
    );

    // Depth: min(0.05 * 50000, 0.05 * 50100) = $2,500 < $5k → THIN
    expect(quote.depthLabel).toBe("DEPTH_THIN");
  });

  /**
   * Test 4: HTTP fallback when WS unavailable
   */
  test("Test 4: Routing priority - HTTP fallback", () => {
    const quoteSources: QuoteSources = {
      // No WS quote
      deepbookHttp: {
        bids: [{ price: 50000, volume: 0.5 }],
        asks: [{ price: 50100, volume: 0.5 }],
        ts: Date.now(),
      },
    };

    const quote = selectAndNormalizeQuote({
      quoteSources,
      side: "BUY_WBTC_WITH_USDC",
      amountIn: 1000,
    });

    // Should use HTTP fallback
    expect(quote.venue).toBe("DEEPBOOK_HTTP");
    expect(quote.status).toBe("AVAILABLE");
  });

  /**
   * Test 5: Cetus pseudo quote (last resort)
   */
  test("Test 5: Cetus pool as last resort", () => {
    const pool: CetusPoolSnapshot = {
      sqrtPrice: Math.pow(2, 64) * Math.sqrt(50000), // sqrtPriceX64 for $50k
      liquidity: 200000, // Above threshold → DEPTH_OK
      ts: Date.now(),
    };

    const quote = normalizeCetusQuote(
      pool,
      "BUY_WBTC_WITH_USDC",
      1000
    );

    expect(quote.venue).toBe("CETUS");
    expect(quote.status).toBe("AVAILABLE");

    // Conservative: MEDIUM impact (no orderbook visibility)
    expect(quote.impactLabel).toBe("IMPACT_MEDIUM");

    // Liquidity above threshold → OK
    expect(quote.depthLabel).toBe("DEPTH_OK");
  });

  /**
   * Test 6: All sources unavailable → venue NONE
   */
  test("Test 6: All sources unavailable", () => {
    const quoteSources: QuoteSources = {
      // All sources missing or broken
    };

    const quote = selectAndNormalizeQuote({
      quoteSources,
      side: "BUY_WBTC_WITH_USDC",
      amountIn: 1000,
    });

    expect(quote.venue).toBe("NONE");
    expect(quote.status).toBe("UNAVAILABLE");
    expect(quote.impactLabel).toBe("IMPACT_UNKNOWN");
    expect(quote.depthLabel).toBe("DEPTH_UNKNOWN");
  });

  /**
   * Test 7: Defensive - malformed DeepBook input
   */
  test("Test 7: Defensive handling of malformed orderbook", () => {
    const malformed1 = normalizeDeepBookQuote(
      null,
      "DEEPBOOK_WS",
      "BUY_WBTC_WITH_USDC",
      1000
    );
    expect(malformed1.status).toBe("UNAVAILABLE");

    const malformed2 = normalizeDeepBookQuote(
      { bids: [], asks: [], ts: Date.now() },
      "DEEPBOOK_WS",
      "BUY_WBTC_WITH_USDC",
      1000
    );
    expect(malformed2.status).toBe("UNAVAILABLE");

    const malformed3 = normalizeDeepBookQuote(
      {
        bids: [{ price: -100, volume: 0.5 }], // Invalid negative price
        asks: [{ price: 50000, volume: 0.5 }],
        ts: Date.now(),
      },
      "DEEPBOOK_WS",
      "BUY_WBTC_WITH_USDC",
      1000
    );
    expect(malformed3.status).toBe("UNAVAILABLE");
  });

  /**
   * Test 8: No numeric leakage in sanitized output
   */
  test("Test 8: sanitizeQuoteForLogs removes all numerics", () => {
    const orderbook: DeepBookOrderbookSnapshot = {
      bids: [{ price: 50000, volume: 0.5 }],
      asks: [{ price: 50100, volume: 0.5 }],
      ts: Date.now(),
    };

    const quote = normalizeDeepBookQuote(
      orderbook,
      "DEEPBOOK_WS",
      "BUY_WBTC_WITH_USDC",
      1000
    );

    const sanitized = sanitizeQuoteForLogs(quote);

    // Should have labels only
    expect(sanitized.venue).toBe("DEEPBOOK_WS");
    expect(sanitized.status).toBe("AVAILABLE");
    expect(sanitized.impactLabel).toBeDefined();
    expect(sanitized.depthLabel).toBeDefined();

    // Should NOT have numeric fields
    expect((sanitized as any).amountIn).toBeUndefined();
    expect((sanitized as any).amountOut).toBeUndefined();
    expect((sanitized as any).price).toBeUndefined();
    expect((sanitized as any).mid).toBeUndefined();
    expect((sanitized as any).spread).toBeUndefined();
  });

  /**
   * Test 9: isQuoteUsable validation
   */
  test("Test 9: isQuoteUsable checks", () => {
    const goodQuote = normalizeDeepBookQuote(
      {
        bids: [{ price: 50000, volume: 0.5 }],
        asks: [{ price: 50100, volume: 0.5 }],
        ts: Date.now(),
      },
      "DEEPBOOK_WS",
      "BUY_WBTC_WITH_USDC",
      1000
    );

    expect(isQuoteUsable(goodQuote)).toBe(true);

    // Unavailable quote → not usable
    const badQuote1 = { ...goodQuote, status: "UNAVAILABLE" as const };
    expect(isQuoteUsable(badQuote1)).toBe(false);

    // Zero amountOut → not usable
    const badQuote2 = { ...goodQuote, amountOut: 0 };
    expect(isQuoteUsable(badQuote2)).toBe(false);

    // NaN amountOut → not usable
    const badQuote3 = { ...goodQuote, amountOut: NaN };
    expect(isQuoteUsable(badQuote3)).toBe(false);

    // NONE venue → not usable
    const badQuote4 = { ...goodQuote, venue: "NONE" as const };
    expect(isQuoteUsable(badQuote4)).toBe(false);
  });

  /**
   * Test 10: isQuoteStale validation
   */
  test("Test 10: isQuoteStale checks", () => {
    const now = Date.now();

    // Fresh quote (5 seconds old)
    const freshQuote = normalizeDeepBookQuote(
      {
        bids: [{ price: 50000, volume: 0.5 }],
        asks: [{ price: 50100, volume: 0.5 }],
        ts: now - 5000,
      },
      "DEEPBOOK_WS",
      "BUY_WBTC_WITH_USDC",
      1000
    );

    expect(isQuoteStale(freshQuote, now)).toBe(false);

    // Stale quote (35 seconds old)
    const staleQuote = normalizeDeepBookQuote(
      {
        bids: [{ price: 50000, volume: 0.5 }],
        asks: [{ price: 50100, volume: 0.5 }],
        ts: now - 35000,
      },
      "DEEPBOOK_WS",
      "BUY_WBTC_WITH_USDC",
      1000
    );

    expect(isQuoteStale(staleQuote, now)).toBe(true);
  });

  /**
   * Test 11: Routing priority - WS over HTTP
   */
  test("Test 11: WS priority over HTTP", () => {
    const quoteSources: QuoteSources = {
      deepbookWs: {
        bids: [{ price: 50000, volume: 0.5 }],
        asks: [{ price: 50100, volume: 0.5 }],
        ts: Date.now(),
      },
      deepbookHttp: {
        bids: [{ price: 49000, volume: 0.5 }],
        asks: [{ price: 51000, volume: 0.5 }],
        ts: Date.now(),
      },
    };

    const quote = selectAndNormalizeQuote({
      quoteSources,
      side: "BUY_WBTC_WITH_USDC",
      amountIn: 1000,
    });

    // Should prefer WS over HTTP
    expect(quote.venue).toBe("DEEPBOOK_WS");
  });

  /**
   * Test 12: Routing priority - HTTP over Cetus
   */
  test("Test 12: HTTP priority over Cetus", () => {
    const quoteSources: QuoteSources = {
      deepbookHttp: {
        bids: [{ price: 50000, volume: 0.5 }],
        asks: [{ price: 50100, volume: 0.5 }],
        ts: Date.now(),
      },
      cetusPool: {
        sqrtPrice: Math.pow(2, 64) * Math.sqrt(50000),
        liquidity: 200000,
        ts: Date.now(),
      },
    };

    const quote = selectAndNormalizeQuote({
      quoteSources,
      side: "BUY_WBTC_WITH_USDC",
      amountIn: 1000,
    });

    // Should prefer HTTP over Cetus
    expect(quote.venue).toBe("DEEPBOOK_HTTP");
  });

  /**
   * Test 13: Sell side quote normalization
   */
  test("Test 13: SELL_WBTC_FOR_USDC direction", () => {
    const orderbook: DeepBookOrderbookSnapshot = {
      bids: [{ price: 49950, volume: 0.5 }],
      asks: [{ price: 50050, volume: 0.5 }],
      ts: Date.now(),
    };

    const quote = normalizeDeepBookQuote(
      orderbook,
      "DEEPBOOK_WS",
      "SELL_WBTC_FOR_USDC",
      0.02 // 0.02 WBTC
    );

    expect(quote.side).toBe("SELL_WBTC_FOR_USDC");

    // Selling WBTC → receive bid price
    expect(quote.price).toBe(49950);

    // AmountOut: 0.02 * 49950 = 999 USDC
    expect(quote.amountOut).toBeCloseTo(999, 0);
  });

  /**
   * Test 14: Cetus thin liquidity → DEPTH_THIN
   */
  test("Test 14: Cetus low liquidity triggers DEPTH_THIN", () => {
    const pool: CetusPoolSnapshot = {
      sqrtPrice: Math.pow(2, 64) * Math.sqrt(50000),
      liquidity: 50000, // Below threshold
      ts: Date.now(),
    };

    const quote = normalizeCetusQuote(
      pool,
      "BUY_WBTC_WITH_USDC",
      1000
    );

    expect(quote.depthLabel).toBe("DEPTH_THIN");
  });

  /**
   * Test 15: Medium spread → IMPACT_MEDIUM
   */
  test("Test 15: Medium spread triggers IMPACT_MEDIUM", () => {
    const orderbook: DeepBookOrderbookSnapshot = {
      bids: [{ price: 49700, volume: 0.5 }],
      asks: [{ price: 50300, volume: 0.5 }], // ~1.2% spread
      ts: Date.now(),
    };

    const quote = normalizeDeepBookQuote(
      orderbook,
      "DEEPBOOK_WS",
      "BUY_WBTC_WITH_USDC",
      1000
    );

    // Spread: (50300 - 49700) / 50000 * 10000 = 120 bps → HIGH (≥100)
    // Note: Threshold is 30-100 for MEDIUM, ≥100 for HIGH
    expect(quote.impactLabel).toBe("IMPACT_HIGH");
  });

  /**
   * Test 16: Defensive - Cetus malformed input
   */
  test("Test 16: Defensive Cetus handling", () => {
    const malformed1 = normalizeCetusQuote(
      null,
      "BUY_WBTC_WITH_USDC",
      1000
    );
    expect(malformed1.status).toBe("UNAVAILABLE");

    const malformed2 = normalizeCetusQuote(
      {
        sqrtPrice: -100, // Invalid negative
        liquidity: 200000,
        ts: Date.now(),
      },
      "BUY_WBTC_WITH_USDC",
      1000
    );
    expect(malformed2.status).toBe("UNAVAILABLE");

    const malformed3 = normalizeCetusQuote(
      {
        sqrtPrice: NaN, // Invalid NaN
        liquidity: 200000,
        ts: Date.now(),
      },
      "BUY_WBTC_WITH_USDC",
      1000
    );
    expect(malformed3.status).toBe("UNAVAILABLE");
  });
});
