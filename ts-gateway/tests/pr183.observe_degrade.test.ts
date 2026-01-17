/**
 * PR183: v1.4 Observation Load + Cost Control (Fixed Rules) v1 - Tests
 *
 * Purpose:
 *   Verify tier-based degradation logic for observation load control.
 *
 * Test Coverage:
 *   1. WS_ALIVE → nextFetchAllowed=NO (HTTP not fetched)
 *   2. WS_ALIVE → observeDegraded=NO
 *   3. WS_DEAD + tier=1S + lastFetchMs old → YES
 *   4. WS_DEAD + tier=5S + lastFetchMs new → NO
 *   5. RATE_LIMITED → tier degrades 1 level
 *   6. BACKOFF → tier degrades 1 level (max 10S)
 *   7. HTTP_OK × 2 → tier improves 1 level
 *   8. HTTP_OK × 1 → no improvement yet (streak condition)
 *   9. UNKNOWN inputs → defensive (UNKNOWN returned, no exception)
 *   10. observeLoop integration: fetch called/not called as expected
 */

import {
  initDegradeState,
  updateDegradeState,
  updateLastFetchTimestamp,
  getTierInterval,
  DegradeStateV1,
} from "../src/observeLoop/degrade";
import { runObserveTick } from "../src/observeLoop/loop";

describe("PR183: Observation Load + Cost Control (Fixed Rules)", () => {
  /**
   * Test 1: WS_ALIVE → nextFetchAllowed=NO (HTTP not fetched)
   */
  test("Test 1: WS alive prevents HTTP fetch", () => {
    const state = initDegradeState();
    const nowMs = Date.now();

    const result = updateDegradeState({
      prev: state,
      wsAlive: true,
      httpHealth: "UNKNOWN",
      nowMs,
    });

    expect(result.nextFetchAllowed).toBe("NO");
    expect(result.observeTier).toBe("TIER_1S");
  });

  /**
   * Test 2: WS_ALIVE → observeDegraded=NO
   */
  test("Test 2: WS alive means not degraded", () => {
    const state = initDegradeState();
    const nowMs = Date.now();

    const result = updateDegradeState({
      prev: state,
      wsAlive: true,
      httpHealth: "UNKNOWN",
      nowMs,
    });

    expect(result.observeDegraded).toBe("NO");
  });

  /**
   * Test 3: WS_DEAD + tier=1S + lastFetchMs old → YES
   */
  test("Test 3: WS dead with old lastFetch allows fetch", () => {
    const state = initDegradeState();
    const oldTime = Date.now() - 2000; // 2 seconds ago
    const stateWithOldFetch = updateLastFetchTimestamp(state, oldTime);
    const nowMs = Date.now();

    const result = updateDegradeState({
      prev: stateWithOldFetch,
      wsAlive: false,
      httpHealth: "HTTP_OK",
      nowMs,
    });

    expect(result.nextFetchAllowed).toBe("YES");
    expect(result.observeTier).toBe("TIER_1S");
  });

  /**
   * Test 4: WS_DEAD + tier=5S + lastFetchMs new → NO
   */
  test("Test 4: Tier 5S with recent fetch blocks fetch", () => {
    const state: DegradeStateV1 = {
      tier: "TIER_5S",
      lastFetchMs: Date.now() - 1000, // 1 second ago
      okStreak: 0,
    };
    const nowMs = Date.now();

    const result = updateDegradeState({
      prev: state,
      wsAlive: false,
      httpHealth: "HTTP_OK",
      nowMs,
    });

    // Tier 5S requires 5 seconds, only 1 second elapsed
    expect(result.nextFetchAllowed).toBe("NO");
  });

  /**
   * Test 5: RATE_LIMITED → tier degrades 1 level
   */
  test("Test 5: Rate limited degrades tier", () => {
    const state: DegradeStateV1 = {
      tier: "TIER_1S",
      lastFetchMs: 0,
      okStreak: 0,
    };
    const nowMs = Date.now();

    const result = updateDegradeState({
      prev: state,
      wsAlive: false,
      httpHealth: "RATE_LIMITED",
      nowMs,
    });

    expect(result.observeTier).toBe("TIER_2S");
    expect(result.warnings).toContain("TIER_DEGRADED_TIER_1S_TO_TIER_2S");
  });

  /**
   * Test 6: BACKOFF → tier degrades 1 level (max 10S)
   */
  test("Test 6: Backoff degrades tier to max 10S", () => {
    // Start at 5S, degrade to 10S
    const state: DegradeStateV1 = {
      tier: "TIER_5S",
      lastFetchMs: 0,
      okStreak: 0,
    };
    const nowMs = Date.now();

    const result1 = updateDegradeState({
      prev: state,
      wsAlive: false,
      httpHealth: "BACKOFF",
      nowMs,
    });

    expect(result1.observeTier).toBe("TIER_10S");

    // Degrade again from 10S → should stay at 10S (max)
    const result2 = updateDegradeState({
      prev: result1.next,
      wsAlive: false,
      httpHealth: "BACKOFF",
      nowMs,
    });

    expect(result2.observeTier).toBe("TIER_10S");
    expect(result2.warnings.length).toBe(0); // No change warning
  });

  /**
   * Test 7: HTTP_OK × 2 → tier improves 1 level
   */
  test("Test 7: Two consecutive HTTP_OK improves tier", () => {
    const state: DegradeStateV1 = {
      tier: "TIER_5S",
      lastFetchMs: 0,
      okStreak: 0,
    };
    const nowMs = Date.now();

    // First OK
    const result1 = updateDegradeState({
      prev: state,
      wsAlive: false,
      httpHealth: "HTTP_OK",
      nowMs,
    });

    expect(result1.observeTier).toBe("TIER_5S"); // No change yet
    expect(result1.next.okStreak).toBe(1);

    // Second OK → improvement
    const result2 = updateDegradeState({
      prev: result1.next,
      wsAlive: false,
      httpHealth: "HTTP_OK",
      nowMs,
    });

    expect(result2.observeTier).toBe("TIER_2S"); // Improved
    expect(result2.warnings).toContain("TIER_IMPROVED_TIER_5S_TO_TIER_2S");
    expect(result2.next.okStreak).toBe(0); // Reset after improvement
  });

  /**
   * Test 8: HTTP_OK × 1 → no improvement yet (streak condition)
   */
  test("Test 8: Single HTTP_OK does not improve tier", () => {
    const state: DegradeStateV1 = {
      tier: "TIER_10S",
      lastFetchMs: 0,
      okStreak: 0,
    };
    const nowMs = Date.now();

    const result = updateDegradeState({
      prev: state,
      wsAlive: false,
      httpHealth: "HTTP_OK",
      nowMs,
    });

    expect(result.observeTier).toBe("TIER_10S"); // No change
    expect(result.next.okStreak).toBe(1); // Streak incremented
  });

  /**
   * Test 9: UNKNOWN inputs → defensive (UNKNOWN returned, no exception)
   */
  test("Test 9: Unknown inputs handled defensively", () => {
    const state = initDegradeState();
    const nowMs = Date.now();

    const result = updateDegradeState({
      prev: state,
      wsAlive: "UNKNOWN",
      httpHealth: "UNKNOWN",
      nowMs,
    });

    expect(result.observeDegraded).toBe("UNKNOWN");
    expect(result.observeTier).toBe("TIER_1S"); // Preserved
    // Should not throw
  });

  /**
   * Test 10: observeLoop integration: fetch called/not called as expected
   */
  test("Test 10: ObserveLoop integration respects degrade state", async () => {
    let fetchCalled = false;

    const mockFetch = async () => {
      fetchCalled = true;
      return {
        status: "AVAILABLE",
        sdkHealth: "HTTP_OK",
        warnings: [],
      };
    };

    const mockDegradeState: DegradeStateV1 = {
      tier: "TIER_1S",
      lastFetchMs: 0, // Old fetch
      okStreak: 0,
    };

    // Test 1: WS alive → fetch NOT called
    fetchCalled = false;
    await runObserveTick({
      fetchObservationSnapshotV1: mockFetch,
      getDegradeState: async () => mockDegradeState,
      getWsAlive: async () => true,
      getHttpHealth: async () => "HTTP_OK",
      getPhaseLabel: async () => "PHASE_NORMAL",
    });

    expect(fetchCalled).toBe(false);

    // Test 2: WS dead + tier allows → fetch called
    fetchCalled = false;
    await runObserveTick({
      fetchObservationSnapshotV1: mockFetch,
      getDegradeState: async () => mockDegradeState,
      getWsAlive: async () => false,
      getHttpHealth: async () => "HTTP_OK",
      getPhaseLabel: async () => "PHASE_NORMAL",
    });

    expect(fetchCalled).toBe(true);
  });

  /**
   * Test 11: observeDegraded=YES when tier > 1S
   */
  test("Test 11: observeDegraded=YES when tier degraded", () => {
    const state: DegradeStateV1 = {
      tier: "TIER_5S",
      lastFetchMs: 0,
      okStreak: 0,
    };
    const nowMs = Date.now();

    const result = updateDegradeState({
      prev: state,
      wsAlive: false,
      httpHealth: "HTTP_OK",
      nowMs,
    });

    expect(result.observeDegraded).toBe("YES");
  });

  /**
   * Test 12: getTierInterval returns correct intervals
   */
  test("Test 12: Tier intervals are correct", () => {
    expect(getTierInterval("TIER_1S")).toBe(1000);
    expect(getTierInterval("TIER_2S")).toBe(2000);
    expect(getTierInterval("TIER_5S")).toBe(5000);
    expect(getTierInterval("TIER_10S")).toBe(10000);
    expect(getTierInterval("UNKNOWN")).toBe(10000); // Safe default
  });

  /**
   * Test 13: Tier improvement stops at TIER_1S
   */
  test("Test 13: Tier improvement stops at TIER_1S", () => {
    const state: DegradeStateV1 = {
      tier: "TIER_1S",
      lastFetchMs: 0,
      okStreak: 1, // Already 1 OK
    };
    const nowMs = Date.now();

    const result = updateDegradeState({
      prev: state,
      wsAlive: false,
      httpHealth: "HTTP_OK",
      nowMs,
    });

    expect(result.observeTier).toBe("TIER_1S"); // Can't improve beyond 1S
    expect(result.next.okStreak).toBe(0); // Reset after attempting improvement
  });

  /**
   * Test 14: Telemetry emitted for degrade status
   */
  test("Test 14: Telemetry emitted for degrade status", async () => {
    let telemetryEmitted = false;
    let telemetryType = "";
    let telemetryData: any = null;

    const mockTelemetry = {
      log: async (type: string, data: any) => {
        if (type === "OBSERVE_DEGRADE_STATUS") {
          telemetryEmitted = true;
          telemetryType = type;
          telemetryData = data;
        }
      },
    };

    await runObserveTick({
      telemetryLogger: mockTelemetry,
      getDegradeState: async () => initDegradeState(),
      getWsAlive: async () => false,
      getHttpHealth: async () => "HTTP_OK",
      getPhaseLabel: async () => "PHASE_NORMAL",
    });

    expect(telemetryEmitted).toBe(true);
    expect(telemetryType).toBe("OBSERVE_DEGRADE_STATUS");
    expect(telemetryData.tier).toBeDefined();
    expect(telemetryData.degraded).toBeDefined();
    expect(telemetryData.nextFetchAllowed).toBeDefined();
  });
});
