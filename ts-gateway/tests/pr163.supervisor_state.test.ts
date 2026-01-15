/**
 * PR163: v1.4 Supervisor + State + CLI - Test Suite
 *
 * Tests for persistent state, supervisor loop, and status CLI.
 *
 * Test Cases (12):
 *   State Store (5):
 *     1. State file absent → readState OK (defensive)
 *     2. writeState → readState roundtrip
 *     3. patchState merges correctly
 *     4. Corrupted JSON → status=ERROR + warnings (no throw)
 *     5. Unknown fields present → ignore (forward-compatible)
 *   Supervisor (5):
 *     6. resumeState=WAIT → runner not called (action=ACTION_WAIT_RESUME)
 *     7. resumeState=RESUMABLE → runner called (stub)
 *     8. ABANDON → lastRun updated
 *     9. HardStop active → action=ACTION_WAIT_HARDSTOP
 *     10. No resumeState → normal execution
 *   CLI/Guards (2):
 *     11. CLI output contains no numerics
 *     12. sanitizeStateForDisplay removes timestamps
 */

import { describe, test, expect, beforeEach, afterEach } from "bun:test";
import * as fs from "fs";
import * as path from "path";
import * as os from "os";
import {
  createFileStateStore,
  MeridianStateV1,
  createEmptyStateV1,
  sanitizeStateForDisplay,
  containsNumericPatterns,
} from "../src/state";
import { runSupervisorOnceV1, SupervisorDeps } from "../src/supervisor";

describe("PR163: State Store", () => {
  const testDir = path.join(os.tmpdir(), `meridian-test-${Date.now()}`);
  const testStatePath = path.join(testDir, "state.json");

  beforeEach(() => {
    // Create test directory
    if (!fs.existsSync(testDir)) {
      fs.mkdirSync(testDir, { recursive: true });
    }
  });

  afterEach(() => {
    // Cleanup test directory
    if (fs.existsSync(testDir)) {
      fs.rmSync(testDir, { recursive: true, force: true });
    }
  });

  test("Test 1: State file absent → readState OK (defensive)", async () => {
    const store = createFileStateStore(testStatePath);
    const result = await store.readState();

    expect(result.status).toBe("OK");
    expect(result.state.version).toBe("v1");
    expect(result.warnings).toContain("WARN_STATE_FILE_NOT_FOUND");
  });

  test("Test 2: writeState → readState roundtrip", async () => {
    const store = createFileStateStore(testStatePath);

    const testState: MeridianStateV1 = {
      version: "v1",
      updatedAtTs: Date.now(),
      lastRun: {
        status: "COMPLETED",
        warnings: [],
      },
      warnings: [],
    };

    const writeResult = await store.writeState(testState);
    expect(writeResult.status).toBe("OK");

    const readResult = await store.readState();
    expect(readResult.status).toBe("OK");
    expect(readResult.state.version).toBe("v1");
    expect(readResult.state.lastRun?.status).toBe("COMPLETED");
  });

  test("Test 3: patchState merges correctly", async () => {
    const store = createFileStateStore(testStatePath);

    // Write initial state
    const initialState = createEmptyStateV1();
    initialState.lastRun = {
      status: "COMPLETED",
      warnings: [],
    };
    await store.writeState(initialState);

    // Patch state
    const patchResult = await store.patchState({
      hardStop: {
        active: true,
        reason: "REASON_TEST",
      },
    });

    expect(patchResult.status).toBe("OK");
    expect(patchResult.state.lastRun?.status).toBe("COMPLETED"); // Preserved
    expect(patchResult.state.hardStop?.active).toBe(true); // Added
  });

  test("Test 4: Corrupted JSON → status=ERROR + warnings (no throw)", async () => {
    const store = createFileStateStore(testStatePath);

    // Write corrupted JSON
    fs.writeFileSync(testStatePath, "{invalid json", "utf-8");

    const result = await store.readState();

    expect(result.status).toBe("ERROR");
    expect(result.warnings).toContain("WARN_STATE_READ_ERROR");
    expect(result.warnings).toContain("WARN_STATE_JSON_CORRUPT");
  });

  test("Test 5: Unknown fields present → ignore (forward-compatible)", async () => {
    const store = createFileStateStore(testStatePath);

    // Write state with unknown field
    const stateWithUnknown = {
      version: "v1",
      updatedAtTs: Date.now(),
      unknownField: "should be ignored",
      futureFeature: { data: "test" },
      warnings: [],
    };

    fs.writeFileSync(testStatePath, JSON.stringify(stateWithUnknown), "utf-8");

    const result = await store.readState();

    expect(result.status).toBe("OK");
    expect(result.state.version).toBe("v1");
    // Unknown fields are preserved but ignored
  });
});

describe("PR163: Supervisor", () => {
  const testDir = path.join(os.tmpdir(), `meridian-supervisor-test-${Date.now()}`);
  const testStatePath = path.join(testDir, "state.json");

  beforeEach(() => {
    if (!fs.existsSync(testDir)) {
      fs.mkdirSync(testDir, { recursive: true });
    }
  });

  afterEach(() => {
    if (fs.existsSync(testDir)) {
      fs.rmSync(testDir, { recursive: true, force: true });
    }
  });

  test("Test 6: resumeState=WAIT → runner not called", async () => {
    const store = createFileStateStore(testStatePath);

    // Setup state with resumeState
    const state: MeridianStateV1 = {
      version: "v1",
      updatedAtTs: Date.now(),
      resumeState: {
        status: "STOPPED",
        stopReason: "STOP_ORACLE_STALE",
        stopAtTs: Date.now(),
        warnings: [],
      },
      warnings: [],
    };
    await store.writeState(state);

    let runnerCalled = false;

    const deps: SupervisorDeps = {
      evaluatePolicy: async () => ({
        allowExecution: true,
        hardStopActive: false,
        status: "ALLOW",
        reasons: [],
      }),
      getResumeInputs: async () => ({
        nowTs: Date.now(),
        oracleStatus: "STALE", // Still stale
        gateStatus: "PASS",
        phaseLabel: "PHASE_NORMAL",
        routeAvailable: true,
        hardStopActive: false,
        policyEnvEnabled: true,
      }),
      runTwapExecution: async () => {
        runnerCalled = true;
        return { status: "COMPLETED", reasons: [] };
      },
    };

    const result = await runSupervisorOnceV1(store, {}, deps);

    expect(result.status).toBe("OK");
    expect(result.action).toBe("ACTION_WAIT_RESUME");
    expect(runnerCalled).toBe(false); // Runner should NOT be called
  });

  test("Test 7: resumeState=RESUMABLE → runner called", async () => {
    const store = createFileStateStore(testStatePath);

    // Setup state with resumeState
    const state: MeridianStateV1 = {
      version: "v1",
      updatedAtTs: Date.now(),
      resumeState: {
        status: "STOPPED",
        stopReason: "STOP_ORACLE_STALE",
        stopAtTs: Date.now(),
        warnings: [],
      },
      warnings: [],
    };
    await store.writeState(state);

    let runnerCalled = false;

    const deps: SupervisorDeps = {
      evaluatePolicy: async () => ({
        allowExecution: true,
        hardStopActive: false,
        status: "ALLOW",
        reasons: [],
      }),
      getResumeInputs: async () => ({
        nowTs: Date.now(),
        oracleStatus: "AVAILABLE", // Recovered
        gateStatus: "PASS",
        phaseLabel: "PHASE_NORMAL",
        routeAvailable: true,
        hardStopActive: false,
        policyEnvEnabled: true,
      }),
      runTwapExecution: async () => {
        runnerCalled = true;
        return { status: "COMPLETED", reasons: [] };
      },
    };

    const result = await runSupervisorOnceV1(store, {}, deps);

    expect(result.status).toBe("OK");
    expect(result.action).toBe("ACTION_RUN_TWAP");
    expect(runnerCalled).toBe(true); // Runner SHOULD be called
  });

  test("Test 8: ABANDON → lastRun updated", async () => {
    const store = createFileStateStore(testStatePath);

    // Setup state with ABANDON-able resumeState
    const state: MeridianStateV1 = {
      version: "v1",
      updatedAtTs: Date.now(),
      resumeState: {
        status: "STOPPED",
        stopReason: "STOP_DURATION_EXCEEDED",
        stopAtTs: Date.now(),
        warnings: [],
      },
      warnings: [],
    };
    await store.writeState(state);

    const deps: SupervisorDeps = {
      evaluatePolicy: async () => ({
        allowExecution: true,
        hardStopActive: false,
        status: "ALLOW",
        reasons: [],
      }),
      getResumeInputs: async () => ({
        nowTs: Date.now(),
        oracleStatus: "AVAILABLE",
        gateStatus: "PASS",
        phaseLabel: "PHASE_NORMAL",
        routeAvailable: true,
        hardStopActive: false,
        policyEnvEnabled: true,
      }),
    };

    const result = await runSupervisorOnceV1(store, {}, deps);

    expect(result.status).toBe("OK");
    expect(result.action).toBe("ACTION_ABORT");

    // Check state was updated
    const readResult = await store.readState();
    expect(readResult.state.lastRun?.status).toBe("ABANDONED");
  });

  test("Test 9: HardStop active → action=ACTION_WAIT_HARDSTOP", async () => {
    const store = createFileStateStore(testStatePath);

    const deps: SupervisorDeps = {
      evaluatePolicy: async () => ({
        allowExecution: false,
        hardStopActive: true,
        status: "BLOCKED",
        reasons: ["REASON_HARDSTOP_ACTIVE"],
      }),
    };

    const result = await runSupervisorOnceV1(store, {}, deps);

    expect(result.status).toBe("OK");
    expect(result.action).toBe("ACTION_WAIT_HARDSTOP");
  });

  test("Test 10: No resumeState → normal execution", async () => {
    const store = createFileStateStore(testStatePath);

    let runnerCalled = false;

    const deps: SupervisorDeps = {
      evaluatePolicy: async () => ({
        allowExecution: true,
        hardStopActive: false,
        status: "ALLOW",
        reasons: [],
      }),
      runTwapExecution: async () => {
        runnerCalled = true;
        return { status: "COMPLETED", reasons: [] };
      },
    };

    const result = await runSupervisorOnceV1(store, {}, deps);

    expect(result.status).toBe("OK");
    expect(result.action).toBe("ACTION_RUN_TWAP");
    expect(runnerCalled).toBe(true);
  });
});

describe("PR163: CLI/Guards", () => {
  test("Test 11: CLI output contains no numerics", () => {
    // Test numeric pattern detection
    expect(containsNumericPatterns("WARN_ORACLE_STALE")).toBe(false);
    expect(containsNumericPatterns("STOP_PHASE_POLICY")).toBe(false);
    expect(containsNumericPatterns("PHASE_NORMAL")).toBe(false);

    // Should detect numerics
    expect(containsNumericPatterns("Price: $100.50")).toBe(true);
    expect(containsNumericPatterns("Balance: 1234 USDC")).toBe(true);
    expect(containsNumericPatterns("Slippage: 5%")).toBe(true);
    expect(containsNumericPatterns("Address: 0x1234abcd")).toBe(true);
  });

  test("Test 12: sanitizeStateForDisplay removes timestamps", () => {
    const state: MeridianStateV1 = {
      version: "v1",
      updatedAtTs: 1234567890,
      resumeState: {
        status: "STOPPED",
        stopReason: "STOP_ORACLE_STALE",
        stopAtTs: 1234567890,
        resumeAfterTs: 1234568890,
        warnings: [],
      },
      hardStop: {
        active: true,
        reason: "REASON_TEST",
        untilTs: 1234568890,
      },
      cooldown: {
        lastActionTs: 1234567890,
      },
      warnings: [],
    };

    const sanitized = sanitizeStateForDisplay(state);

    // Timestamps should be removed
    expect(sanitized.updatedAtTs).toBeUndefined();
    expect((sanitized.resumeState as any)?.stopAtTs).toBeUndefined();
    expect((sanitized.resumeState as any)?.resumeAfterTs).toBeUndefined();
    expect((sanitized.hardStop as any)?.untilTs).toBeUndefined();
    expect((sanitized.cooldown as any)?.lastActionTs).toBeUndefined();

    // Labels should be preserved
    expect((sanitized.resumeState as any)?.stopReason).toBe("STOP_ORACLE_STALE");
    expect((sanitized.hardStop as any)?.reason).toBe("REASON_TEST");
  });
});
