/**
 * PR181: v1.4 Observe 1s Loop + Chunk 10s + Immediate STOP v1 - Tests
 *
 * Purpose:
 *   Verify observe loop, state updates, and immediate STOP capability.
 *
 * Test Coverage:
 *   1. ObserveLoop 1 tick saves state
 *   2. Interval=1s multiple ticks progress
 *   3. Phase=PRE_SHOCK → stopSignal=STOP
 *   4. Phase=NORMAL → stopSignal=NO_STOP
 *   5. Oracle=STALE → stopSignal=STOP
 *   6. HardStopActive → stopSignal=STOP
 *   7. SpecLock pending ACK no activeSpec → stopSignal=STOP
 *   8. Runner sleep中 stopToken STOP → 即STOP
 *   9. StopToken CLEAR → next run possible
 *   10. ObserveAndLabel exception → observeState.status=ERROR (no throw)
 *   11. CLI status label-only
 *   12. Telemetry failures non-fatal
 */

import {
  evaluateObserveState,
  evaluateStopSignal,
  runObserveTick,
  getStopToken,
  updateStopToken,
  sleepMs,
} from "../src/observeLoop/loop";
import { ObserveStateV1, PhaseLabel } from "../src/observeLoop/types";

describe("PR181: Observe 1s Loop + Chunk 10s + Immediate STOP", () => {
  /**
   * Test 1: ObserveLoop 1 tick saves state
   */
  test("Test 1: Observe tick saves state", async () => {
    let savedState: any = null;

    const mockStateStore = {
      patchState: async (patch: any) => {
        savedState = patch;
      },
    };

    const result = await runObserveTick({
      stateStore: mockStateStore,
      getPhaseLabel: async () => "PHASE_NORMAL",
      getTrendLabel: async () => "RANGE",
      getOracleStatus: async () => "AVAILABLE",
      getLabelsPresence: async () => "HAS_LABELS",
    });

    expect(result).toBeDefined();
    expect(result.status).toBe("AVAILABLE");
    expect(savedState).toBeDefined();
    expect(savedState.observeState).toBeDefined();
  });

  /**
   * Test 2: Interval=1s multiple ticks (simulated)
   */
  test("Test 2: Multiple ticks can progress", async () => {
    const ticks: ObserveStateV1[] = [];

    for (let i = 0; i < 3; i++) {
      const result = await runObserveTick({
        getPhaseLabel: async () => "PHASE_NORMAL",
      });
      ticks.push(result);
    }

    expect(ticks.length).toBe(3);
    ticks.forEach((tick) => {
      expect(tick.status).toBeDefined();
    });
  });

  /**
   * Test 3: Phase=PRE_SHOCK → stopSignal=STOP
   */
  test("Test 3: PRE_SHOCK phase triggers STOP", () => {
    const observeState: ObserveStateV1 = {
      status: "AVAILABLE",
      phaseLabel: "PHASE_PRE_SHOCK",
      trendLabel: "UNKNOWN",
      labelsPresence: "NO_LABELS",
      oracleStatus: "AVAILABLE",
      stopSignal: "UNKNOWN",
      warnings: [],
    };

    const stopSignal = evaluateStopSignal(observeState, false, false);

    expect(stopSignal).toBe("STOP");
  });

  /**
   * Test 4: Phase=NORMAL → stopSignal=NO_STOP
   */
  test("Test 4: NORMAL phase allows continuation", () => {
    const observeState: ObserveStateV1 = {
      status: "AVAILABLE",
      phaseLabel: "PHASE_NORMAL",
      trendLabel: "UNKNOWN",
      labelsPresence: "NO_LABELS",
      oracleStatus: "AVAILABLE",
      stopSignal: "UNKNOWN",
      warnings: [],
    };

    const stopSignal = evaluateStopSignal(observeState, false, false);

    expect(stopSignal).toBe("NO_STOP");
  });

  /**
   * Test 5: Oracle=STALE → stopSignal=STOP
   */
  test("Test 5: STALE oracle triggers STOP", () => {
    const observeState: ObserveStateV1 = {
      status: "AVAILABLE",
      phaseLabel: "PHASE_NORMAL",
      trendLabel: "UNKNOWN",
      labelsPresence: "NO_LABELS",
      oracleStatus: "STALE",
      stopSignal: "UNKNOWN",
      warnings: [],
    };

    const stopSignal = evaluateStopSignal(observeState, false, false);

    expect(stopSignal).toBe("STOP");
  });

  /**
   * Test 6: HardStopActive → stopSignal=STOP
   */
  test("Test 6: HardStop active triggers STOP", () => {
    const observeState: ObserveStateV1 = {
      status: "AVAILABLE",
      phaseLabel: "PHASE_NORMAL",
      trendLabel: "UNKNOWN",
      labelsPresence: "NO_LABELS",
      oracleStatus: "AVAILABLE",
      stopSignal: "UNKNOWN",
      warnings: [],
    };

    const stopSignal = evaluateStopSignal(observeState, true, false);

    expect(stopSignal).toBe("STOP");
  });

  /**
   * Test 7: SpecLock pending ACK no activeSpec → stopSignal=STOP
   */
  test("Test 7: Spec lock pending without activeSpec triggers STOP", () => {
    const observeState: ObserveStateV1 = {
      status: "AVAILABLE",
      phaseLabel: "PHASE_NORMAL",
      trendLabel: "UNKNOWN",
      labelsPresence: "NO_LABELS",
      oracleStatus: "AVAILABLE",
      stopSignal: "UNKNOWN",
      warnings: [],
    };

    const stopSignal = evaluateStopSignal(observeState, false, true);

    expect(stopSignal).toBe("STOP");
  });

  /**
   * Test 8: Sleep中 stopToken STOP → 即STOP (AbortSignal)
   */
  test("Test 8: Sleep with abort signal resolves immediately", async () => {
    const controller = new AbortController();
    const start = Date.now();

    // Abort after 100ms
    setTimeout(() => controller.abort(), 100);

    // Try to sleep 5000ms
    await sleepMs(5000, controller.signal);

    const elapsed = Date.now() - start;

    // Should abort around 100ms, not 5000ms
    expect(elapsed).toBeLessThan(1000);
  });

  /**
   * Test 9: StopToken CLEAR → next run possible
   */
  test("Test 9: Stop token can be cleared", () => {
    updateStopToken("STOP", "TEST_STOP");
    let token = getStopToken();
    expect(token.status).toBe("STOP");

    updateStopToken("CLEAR", "TEST_CLEAR");
    token = getStopToken();
    expect(token.status).toBe("CLEAR");
  });

  /**
   * Test 10: ObserveAndLabel exception → observeState.status=ERROR (no throw)
   */
  test("Test 10: Observe tick handles exception defensively", async () => {
    const result = await runObserveTick({
      getPhaseLabel: async () => {
        throw new Error("Test error");
      },
    });

    expect(result).toBeDefined();
    expect(result.status).toBe("ERROR");
    expect(result.phaseLabel).toBe("PHASE_ERROR");
    expect(result.stopSignal).toBe("STOP");
  });

  /**
   * Test 11: CLI status label-only
   */
  test("Test 11: Observe state warnings are label-only", async () => {
    const result = await evaluateObserveState({
      getPhaseLabel: async () => "PHASE_NORMAL",
    });

    expect(result.warnings).toBeDefined();
    expect(Array.isArray(result.warnings)).toBe(true);

    // Warnings should not contain numbers
    result.warnings.forEach((warning) => {
      expect(warning).not.toMatch(/\d{3,}/);
      expect(warning).not.toMatch(/0x[a-fA-F0-9]{40}/);
    });
  });

  /**
   * Test 12: Telemetry failures non-fatal
   */
  test("Test 12: Telemetry failures do not crash observe tick", async () => {
    const mockTelemetry = {
      log: async () => {
        throw new Error("Telemetry error");
      },
    };

    // Should not throw
    const result = await runObserveTick({
      telemetryLogger: mockTelemetry,
      getPhaseLabel: async () => "PHASE_NORMAL",
    });

    expect(result).toBeDefined();
    expect(result.status).toBe("AVAILABLE");
  });

  /**
   * Test 13: All shock phases trigger STOP
   */
  test("Test 13: All shock/reversal phases trigger STOP", () => {
    const shockPhases: PhaseLabel[] = [
      "PHASE_PRE_SHOCK",
      "PHASE_UP_SHOCK",
      "PHASE_DOWN_SHOCK",
      "PHASE_UP_REVERSAL",
      "PHASE_DOWN_REVERSAL",
    ];

    shockPhases.forEach((phase) => {
      const observeState: ObserveStateV1 = {
        status: "AVAILABLE",
        phaseLabel: phase,
        trendLabel: "UNKNOWN",
        labelsPresence: "NO_LABELS",
        oracleStatus: "AVAILABLE",
        stopSignal: "UNKNOWN",
        warnings: [],
      };

      const stopSignal = evaluateStopSignal(observeState, false, false);
      expect(stopSignal).toBe("STOP");
    });
  });

  /**
   * Test 14: Recovery phase allows continuation
   */
  test("Test 14: RECOVERY phase allows continuation", () => {
    const observeState: ObserveStateV1 = {
      status: "AVAILABLE",
      phaseLabel: "PHASE_RECOVERY",
      trendLabel: "UNKNOWN",
      labelsPresence: "NO_LABELS",
      oracleStatus: "AVAILABLE",
      stopSignal: "UNKNOWN",
      warnings: [],
    };

    const stopSignal = evaluateStopSignal(observeState, false, false);

    expect(stopSignal).toBe("NO_STOP");
  });
});
