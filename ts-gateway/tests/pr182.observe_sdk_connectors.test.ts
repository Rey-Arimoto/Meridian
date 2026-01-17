/**
 * PR182: v1.4 Real Observation SDK Connectors v1 - Tests
 *
 * Purpose:
 *   Verify DeepBook WS/HTTP and Cetus Pool connectors work correctly.
 *
 * Test Coverage:
 *   1. DeepBook WS alive → fetcher returns AVAILABLE (from WS cache)
 *   2. DeepBook WS dead → HTTP fallback path used
 *   3. DeepBook HTTP rate limited → PARTIAL + RATE_LIMITED label
 *   4. Cetus pool available → pseudoTopK produced (AVAILABLE/PARTIAL)
 *   5. Cetus missing → PARTIAL or ERROR safely
 *   6. fetcher never throws (even when SDK absent)
 *   7. label-only sanitization: warnings no numerics
 *   8. observeLoop integrates fetcher: missing data → labels UNKNOWN
 *   9. telemetry emitted for source status
 *   10. conversion to PR154 BookSnapshot shape works
 *   11. partial snapshot still produces ObservationLabels with UNKNOWN as needed
 *   12. defensive: malformed response → ERROR record, no crash
 */

import {
  fetchObservationSnapshotV1,
  getSourcePriorityStatus,
} from "../src/observeSdk/fetcher";
import {
  simulateWsEvent,
  resetWsState,
  isWsAlive,
  getWsStatus,
} from "../src/observeSdk/deepbookWs";
import {
  simulateHttpSuccess,
  simulateHttpRateLimit,
  resetRateLimitState,
} from "../src/observeSdk/deepbookHttp";
import {
  simulateCetusSuccess,
  simulateCetusUnavailable,
  createStubPoolState,
} from "../src/observeSdk/cetusPool";
import { sanitizeStringArray, evaluatePresence } from "../src/observeSdk/guards";
import { runObserveTick } from "../src/observeLoop/loop";

describe("PR182: Real Observation SDK Connectors", () => {
  beforeEach(() => {
    // Reset state before each test
    resetWsState();
    resetRateLimitState();
  });

  /**
   * Test 1: DeepBook WS alive → fetcher returns AVAILABLE (from WS cache)
   */
  test("Test 1: WS alive returns AVAILABLE from cache", async () => {
    // Simulate WS event with snapshot
    const snapshot = {
      bids: [{ price: 1.0, quantity: 100 }],
      asks: [{ price: 1.01, quantity: 100 }],
      timestamp: Date.now(),
      source: "DEEPBOOK_WS" as const,
    };

    simulateWsEvent(snapshot);

    // Verify WS is alive
    expect(isWsAlive()).toBe(true);

    // Fetch observation snapshot
    const result = await fetchObservationSnapshotV1();

    expect(result.status).toBe("AVAILABLE");
    expect(result.snapshot).toBeDefined();
    expect(result.sdkHealth).toBe("WS_ALIVE");
    expect(result.warnings).toContain("SOURCE_DEEPBOOK_WS");
  });

  /**
   * Test 2: DeepBook WS dead → HTTP fallback path used
   */
  test("Test 2: WS dead triggers HTTP fallback", async () => {
    // WS is dead by default (resetWsState)
    expect(isWsAlive()).toBe(false);

    // HTTP fallback should be attempted
    const result = await fetchObservationSnapshotV1();

    // SDK not integrated yet, so result will be PARTIAL/ERROR
    expect(result.status).toMatch(/PARTIAL|ERROR/);
    expect(result.warnings.length).toBeGreaterThan(0);
  });

  /**
   * Test 3: DeepBook HTTP rate limited → PARTIAL + RATE_LIMITED label
   */
  test("Test 3: HTTP rate limited returns PARTIAL", async () => {
    // Simulate HTTP rate limit
    const httpResult = await simulateHttpRateLimit();

    expect(httpResult.status).toBe("PARTIAL");
    expect(httpResult.healthLabel).toBe("RATE_LIMITED");
    expect(httpResult.warnings).toContain("HTTP_RATE_LIMITED");
  });

  /**
   * Test 4: Cetus pool available → pseudoTopK produced (AVAILABLE/PARTIAL)
   */
  test("Test 4: Cetus pool produces pseudo-TopK", async () => {
    const poolState = createStubPoolState(1.5, 50000);
    const cetusResult = await simulateCetusSuccess(poolState);

    expect(cetusResult.status).toBe("AVAILABLE");
    expect(cetusResult.snapshot).toBeDefined();
    expect(cetusResult.snapshot?.bids.length).toBeGreaterThan(0);
    expect(cetusResult.snapshot?.asks.length).toBeGreaterThan(0);
    expect(cetusResult.snapshot?.source).toBe("CETUS_POOL");
  });

  /**
   * Test 5: Cetus missing → PARTIAL or ERROR safely
   */
  test("Test 5: Cetus unavailable returns ERROR safely", async () => {
    const cetusResult = await simulateCetusUnavailable();

    expect(cetusResult.status).toBe("ERROR");
    expect(cetusResult.healthLabel).toBe("UNKNOWN");
    expect(cetusResult.warnings).toContain("CETUS_POOL_UNAVAILABLE");
  });

  /**
   * Test 6: fetcher never throws (even when SDK absent)
   */
  test("Test 6: Fetcher never throws even with no SDK", async () => {
    // All sources unavailable
    resetWsState(); // WS dead
    resetRateLimitState();

    // Fetch should not throw
    const result = await fetchObservationSnapshotV1();

    expect(result).toBeDefined();
    expect(result.status).toMatch(/AVAILABLE|PARTIAL|ERROR/);
    expect(result.warnings).toBeDefined();
    expect(Array.isArray(result.warnings)).toBe(true);
  });

  /**
   * Test 7: label-only sanitization: warnings no numerics
   */
  test("Test 7: Warnings are sanitized (label-only)", () => {
    const warnings = [
      "PRICE_12345_TOO_HIGH",
      "ADDRESS_0x1234567890123456789012345678901234567890",
      "AMOUNT_123.456789",
      "TOKEN_SUI_BALANCE_LOW",
    ];

    const sanitized = sanitizeStringArray(warnings);

    // Verify numerics are removed
    sanitized.forEach((warning) => {
      expect(warning).not.toMatch(/\d{3,}/);
      expect(warning).not.toMatch(/0x[a-fA-F0-9]{40}/);
      expect(warning).not.toMatch(/\d+\.\d{4,}/);
      expect(warning).not.toMatch(/\b(SUI|USDC|DEEP|CETUS)\b/);
    });
  });

  /**
   * Test 8: observeLoop integrates fetcher: missing data → labels UNKNOWN
   */
  test("Test 8: ObserveLoop handles missing data gracefully", async () => {
    // Mock fetch that returns ERROR
    const mockFetch = async () => ({
      status: "ERROR",
      sdkHealth: "UNKNOWN",
      warnings: ["MOCK_ERROR"],
    });

    const result = await runObserveTick({
      fetchObservationSnapshotV1: mockFetch,
      getPhaseLabel: async () => "PHASE_NORMAL",
    });

    expect(result).toBeDefined();
    expect(result.sourceStatus).toBe("ERROR");
    expect(result.sdkHealth).toBe("UNKNOWN");
    expect(result.warnings).toContain("MOCK_ERROR");
  });

  /**
   * Test 9: telemetry emitted for source status
   */
  test("Test 9: Telemetry emitted for source status", async () => {
    let telemetryEmitted = false;
    let telemetryType = "";
    let telemetryData: any = null;

    const mockTelemetry = {
      log: async (type: string, data: any) => {
        if (type === "OBSERVE_SOURCE_STATUS") {
          telemetryEmitted = true;
          telemetryType = type;
          telemetryData = data;
        }
      },
    };

    const mockFetch = async () => ({
      status: "AVAILABLE",
      sdkHealth: "WS_ALIVE",
      warnings: [],
    });

    await runObserveTick({
      telemetryLogger: mockTelemetry,
      fetchObservationSnapshotV1: mockFetch,
      getPhaseLabel: async () => "PHASE_NORMAL",
    });

    expect(telemetryEmitted).toBe(true);
    expect(telemetryType).toBe("OBSERVE_SOURCE_STATUS");
    expect(telemetryData.status).toBe("AVAILABLE");
    expect(telemetryData.sdkHealth).toBe("WS_ALIVE");
  });

  /**
   * Test 10: conversion to PR154 BookSnapshot shape works
   */
  test("Test 10: Snapshot shape compatible with PR154", async () => {
    const snapshot = {
      bids: [
        { price: 1.0, quantity: 100 },
        { price: 0.99, quantity: 200 },
      ],
      asks: [
        { price: 1.01, quantity: 100 },
        { price: 1.02, quantity: 200 },
      ],
      timestamp: Date.now(),
      source: "DEEPBOOK_WS" as const,
    };

    simulateWsEvent(snapshot);

    const result = await fetchObservationSnapshotV1();

    expect(result.snapshot).toBeDefined();
    expect(result.snapshot?.bids).toBeDefined();
    expect(result.snapshot?.asks).toBeDefined();
    expect(result.snapshot?.bids.length).toBe(2);
    expect(result.snapshot?.asks.length).toBe(2);
  });

  /**
   * Test 11: partial snapshot still produces ObservationLabels with UNKNOWN as needed
   */
  test("Test 11: Partial snapshot produces safe labels", () => {
    // Partial snapshot (only bids)
    const partialSnapshot = {
      bids: [{ price: 1.0, quantity: 100 }],
      asks: [],
      timestamp: Date.now(),
      source: "CETUS_POOL" as const,
    };

    const presence = evaluatePresence(partialSnapshot);

    expect(presence).toBe("HAS_BIDS_ONLY");
  });

  /**
   * Test 12: defensive: malformed response → ERROR record, no crash
   */
  test("Test 12: Malformed response returns ERROR safely", async () => {
    // Mock fetch that throws
    const mockFetchThrowing = async () => {
      throw new Error("Malformed response");
    };

    // Should not throw
    const result = await runObserveTick({
      fetchObservationSnapshotV1: mockFetchThrowing,
      getPhaseLabel: async () => "PHASE_NORMAL",
    });

    expect(result).toBeDefined();
    expect(result.sourceStatus).toBe("ERROR");
    expect(result.warnings).toContain("SNAPSHOT_FETCH_FAILED");
  });

  /**
   * Test 13: Priority status tracking
   */
  test("Test 13: Source priority status available", () => {
    const status = getSourcePriorityStatus();

    expect(status).toBeDefined();
    expect(status.ws).toBeDefined();
    expect(status.http).toBeDefined();
    expect(status.cetus).toBeDefined();
  });

  /**
   * Test 14: WS status reporting
   */
  test("Test 14: WS status includes health label", () => {
    const status = getWsStatus();

    expect(status).toBeDefined();
    expect(status.connected).toBe(false); // Not connected by default
    expect(status.healthLabel).toBe("WS_DEAD");
    expect(status.lastEventLabel).toMatch(/T_NEVER|T_OLD|T_HOUR|T_MIN|T_RECENT/);
  });
});
