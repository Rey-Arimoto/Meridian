/**
 * PR156: v1.4 Auto Execution Policy (Aggressive + HardStop) - Test Suite
 *
 * Verification:
 *   - Double-key system (env + policy)
 *   - HardStop thresholds and TTL
 *   - Streak tracking and reset
 *   - Heartbeat monitoring
 *   - Guards validation
 *
 * Required test cases (minimum 12):
 *   1. env disabled → SIM_ONLY
 *   2. env enabled & no hardstop → ALLOW
 *   3. oracle error streak 3 → BLOCKED
 *   4. oracle reset when AVAILABLE
 *   5. sim fail streak 2 → BLOCKED
 *   6. no route streak 10 → BLOCKED
 *   7. exceptionFlag true → BLOCKED
 *   8. TTL not expired → still active
 *   9. TTL expired → inactive
 *  10. heartbeat OK when all present & not hardstop
 *  11. heartbeat DEGRADED when oracle missing
 *  12. guards: warnings with numbers/token/prescriptive/trading rejected
 */

import { strict as assert } from "assert";
import {
  evaluateExecutionPolicy,
  isExecutionAllowed,
  checkEnvKey,
  createInitialHardStopState,
  updateHardStopState,
  isHardStopExpired,
  runHeartbeat,
  isHeartbeatHealthy,
  containsNumericLike,
  containsForbiddenVocab,
  containsTokenLiteral,
  validatePolicyOutput,
  PolicyInput,
  HardStopState,
} from "../src/policy";

/**
 * Test 1: env disabled → SIM_ONLY
 */
async function test1_env_disabled_sim_only() {
  console.log("\n[TEST 1] Env disabled → SIM_ONLY");

  // Save original env
  const originalEnv = process.env.MERIDIAN_EXECUTION_ENABLED;

  try {
    // Set env to disabled
    delete process.env.MERIDIAN_EXECUTION_ENABLED;

    const input: PolicyInput = {
      oracleStatus: "AVAILABLE",
      simulationStatus: "PASS",
      routeStatus: "AVAILABLE",
    };

    const result = evaluateExecutionPolicy(input);

    // Assert: status should be SIM_ONLY
    assert.strictEqual(result.status, "SIM_ONLY");
    assert.strictEqual(result.envOk, false);
    assert.strictEqual(isExecutionAllowed(result), false);
    assert.ok(result.warnings.includes("POLICY_ENV_DISABLED"));

    console.log("  ✓ Env disabled → status=SIM_ONLY");
    console.log(`  ✓ envOk=${result.envOk}, policyOk=${result.policyOk}`);
  } finally {
    // Restore original env
    if (originalEnv !== undefined) {
      process.env.MERIDIAN_EXECUTION_ENABLED = originalEnv;
    }
  }
}

/**
 * Test 2: env enabled & no hardstop → ALLOW
 */
async function test2_env_enabled_allow() {
  console.log("\n[TEST 2] Env enabled & no hardstop → ALLOW");

  // Save original env
  const originalEnv = process.env.MERIDIAN_EXECUTION_ENABLED;

  try {
    // Set env to enabled
    process.env.MERIDIAN_EXECUTION_ENABLED = "true";

    const input: PolicyInput = {
      oracleStatus: "AVAILABLE",
      simulationStatus: "PASS",
      routeStatus: "AVAILABLE",
    };

    const result = evaluateExecutionPolicy(input);

    // Assert: status should be ALLOW
    assert.strictEqual(result.status, "ALLOW");
    assert.strictEqual(result.envOk, true);
    assert.strictEqual(result.policyOk, true);
    assert.strictEqual(isExecutionAllowed(result), true);

    console.log("  ✓ Env enabled & no hardstop → status=ALLOW");
    console.log(`  ✓ envOk=${result.envOk}, policyOk=${result.policyOk}`);
  } finally {
    // Restore original env
    if (originalEnv !== undefined) {
      process.env.MERIDIAN_EXECUTION_ENABLED = originalEnv;
    } else {
      delete process.env.MERIDIAN_EXECUTION_ENABLED;
    }
  }
}

/**
 * Test 3: oracle error streak 3 → BLOCKED
 */
async function test3_oracle_error_streak() {
  console.log("\n[TEST 3] Oracle error streak 3 → BLOCKED");

  // Save original env
  const originalEnv = process.env.MERIDIAN_EXECUTION_ENABLED;

  try {
    // Set env to enabled
    process.env.MERIDIAN_EXECUTION_ENABLED = "true";

    let state = createInitialHardStopState();
    const now = Date.now();

    // Simulate 3 consecutive oracle errors
    for (let i = 1; i <= 3; i++) {
      const input: PolicyInput = {
        oracleStatus: "ERROR",
        simulationStatus: "PASS",
        routeStatus: "AVAILABLE",
      };

      const result = evaluateExecutionPolicy(input, state, now);
      state = result.hardStopState;

      console.log(
        `  Round ${i}: streak=${state.streaks.oracleError}, active=${state.active}`
      );

      if (i < 3) {
        // Not yet locked
        assert.strictEqual(state.active, false);
      } else {
        // Should be locked after 3rd error
        assert.strictEqual(state.active, true);
        assert.strictEqual(state.reason, "ORACLE_ERROR_STREAK");
        assert.strictEqual(result.status, "BLOCKED");
        assert.ok(result.warnings.includes("HARDSTOP_ORACLE_ERROR_STREAK"));
      }
    }

    console.log("  ✓ Oracle error × 3 → HardStop active");
    console.log(`  ✓ HardStop reason: ${state.reason}`);
  } finally {
    // Restore original env
    if (originalEnv !== undefined) {
      process.env.MERIDIAN_EXECUTION_ENABLED = originalEnv;
    } else {
      delete process.env.MERIDIAN_EXECUTION_ENABLED;
    }
  }
}

/**
 * Test 4: oracle reset when AVAILABLE
 */
async function test4_oracle_reset() {
  console.log("\n[TEST 4] Oracle reset when AVAILABLE");

  let state = createInitialHardStopState();
  const now = Date.now();

  // Simulate 2 errors, then AVAILABLE
  for (let i = 1; i <= 2; i++) {
    const input: PolicyInput = {
      oracleStatus: "ERROR",
      simulationStatus: "PASS",
      routeStatus: "AVAILABLE",
    };

    state = updateHardStopState(state, input, now);
  }

  console.log(`  After 2 errors: streak=${state.streaks.oracleError}`);
  assert.strictEqual(state.streaks.oracleError, 2);

  // Now send AVAILABLE → should reset streak
  const inputAvailable: PolicyInput = {
    oracleStatus: "AVAILABLE",
    simulationStatus: "PASS",
    routeStatus: "AVAILABLE",
  };

  state = updateHardStopState(state, inputAvailable, now);

  console.log(`  After AVAILABLE: streak=${state.streaks.oracleError}`);
  assert.strictEqual(state.streaks.oracleError, 0);
  assert.strictEqual(state.active, false);

  console.log("  ✓ Oracle AVAILABLE → streak reset to 0");
}

/**
 * Test 5: sim fail streak 2 → BLOCKED
 */
async function test5_sim_fail_streak() {
  console.log("\n[TEST 5] Sim fail streak 2 → BLOCKED");

  // Save original env
  const originalEnv = process.env.MERIDIAN_EXECUTION_ENABLED;

  try {
    // Set env to enabled
    process.env.MERIDIAN_EXECUTION_ENABLED = "true";

    let state = createInitialHardStopState();
    const now = Date.now();

    // Simulate 2 consecutive sim failures
    for (let i = 1; i <= 2; i++) {
      const input: PolicyInput = {
        oracleStatus: "AVAILABLE",
        simulationStatus: "BLOCK", // Sim failure
        routeStatus: "AVAILABLE",
      };

      const result = evaluateExecutionPolicy(input, state, now);
      state = result.hardStopState;

      console.log(
        `  Round ${i}: streak=${state.streaks.simFail}, active=${state.active}`
      );

      if (i < 2) {
        // Not yet locked
        assert.strictEqual(state.active, false);
      } else {
        // Should be locked after 2nd failure
        assert.strictEqual(state.active, true);
        assert.strictEqual(state.reason, "SIM_FAIL_STREAK");
        assert.strictEqual(result.status, "BLOCKED");
        assert.ok(result.warnings.includes("HARDSTOP_SIM_FAIL_STREAK"));
      }
    }

    console.log("  ✓ Sim fail × 2 → HardStop active");
    console.log(`  ✓ HardStop reason: ${state.reason}`);
  } finally {
    // Restore original env
    if (originalEnv !== undefined) {
      process.env.MERIDIAN_EXECUTION_ENABLED = originalEnv;
    } else {
      delete process.env.MERIDIAN_EXECUTION_ENABLED;
    }
  }
}

/**
 * Test 6: no route streak 10 → BLOCKED
 */
async function test6_no_route_streak() {
  console.log("\n[TEST 6] No route streak 10 → BLOCKED");

  // Save original env
  const originalEnv = process.env.MERIDIAN_EXECUTION_ENABLED;

  try {
    // Set env to enabled
    process.env.MERIDIAN_EXECUTION_ENABLED = "true";

    let state = createInitialHardStopState();
    const now = Date.now();

    // Simulate 10 consecutive NO_ROUTE
    for (let i = 1; i <= 10; i++) {
      const input: PolicyInput = {
        oracleStatus: "AVAILABLE",
        simulationStatus: "PASS",
        routeStatus: "NONE", // No route
      };

      const result = evaluateExecutionPolicy(input, state, now);
      state = result.hardStopState;

      if (i < 10) {
        // Not yet locked
        assert.strictEqual(state.active, false);
      } else {
        // Should be locked after 10th NO_ROUTE
        assert.strictEqual(state.active, true);
        assert.strictEqual(state.reason, "NO_ROUTE_STREAK");
        assert.strictEqual(result.status, "BLOCKED");
        assert.ok(result.warnings.includes("HARDSTOP_NO_ROUTE_STREAK"));
      }
    }

    console.log("  ✓ NO_ROUTE × 10 → HardStop active");
    console.log(`  ✓ HardStop reason: ${state.reason}`);
  } finally {
    // Restore original env
    if (originalEnv !== undefined) {
      process.env.MERIDIAN_EXECUTION_ENABLED = originalEnv;
    } else {
      delete process.env.MERIDIAN_EXECUTION_ENABLED;
    }
  }
}

/**
 * Test 7: exceptionFlag true → BLOCKED
 */
async function test7_unexpected_exception() {
  console.log("\n[TEST 7] ExceptionFlag true → BLOCKED");

  // Save original env
  const originalEnv = process.env.MERIDIAN_EXECUTION_ENABLED;

  try {
    // Set env to enabled
    process.env.MERIDIAN_EXECUTION_ENABLED = "true";

    let state = createInitialHardStopState();
    const now = Date.now();

    // Simulate unexpected exception (one-shot)
    const input: PolicyInput = {
      oracleStatus: "AVAILABLE",
      simulationStatus: "PASS",
      routeStatus: "AVAILABLE",
      unexpectedException: true, // Exception flag
    };

    const result = evaluateExecutionPolicy(input, state, now);
    state = result.hardStopState;

    // Should be locked immediately
    assert.strictEqual(state.active, true);
    assert.strictEqual(state.reason, "UNEXPECTED_EXCEPTION");
    assert.strictEqual(result.status, "BLOCKED");
    assert.ok(result.warnings.includes("HARDSTOP_UNEXPECTED_EXCEPTION"));

    console.log("  ✓ Exception flag → HardStop active (one-shot)");
    console.log(`  ✓ HardStop reason: ${state.reason}`);
  } finally {
    // Restore original env
    if (originalEnv !== undefined) {
      process.env.MERIDIAN_EXECUTION_ENABLED = originalEnv;
    } else {
      delete process.env.MERIDIAN_EXECUTION_ENABLED;
    }
  }
}

/**
 * Test 8: TTL not expired → still active
 */
async function test8_ttl_not_expired() {
  console.log("\n[TEST 8] TTL not expired → still active");

  let state = createInitialHardStopState();
  const now = Date.now();

  // Activate HardStop with 30 min TTL
  const input: PolicyInput = {
    oracleStatus: "ERROR",
    simulationStatus: "PASS",
    routeStatus: "AVAILABLE",
  };

  // Trigger oracle error streak
  for (let i = 0; i < 3; i++) {
    state = updateHardStopState(state, input, now);
  }

  assert.strictEqual(state.active, true);
  console.log(`  HardStop activated at: ${state.activatedAt}, TTL: ${state.ttlMs}ms`);

  // Check after 10 minutes (TTL = 30 min, so not expired)
  const tenMinutesLater = now + 10 * 60 * 1000;
  const stillActive = !isHardStopExpired(state, tenMinutesLater);

  assert.strictEqual(stillActive, true);

  console.log("  ✓ TTL not expired (10 min < 30 min) → still active");
}

/**
 * Test 9: TTL expired → inactive
 */
async function test9_ttl_expired() {
  console.log("\n[TEST 9] TTL expired → inactive");

  let state = createInitialHardStopState();
  const now = Date.now();

  // Activate HardStop with 30 min TTL
  const input: PolicyInput = {
    oracleStatus: "ERROR",
    simulationStatus: "PASS",
    routeStatus: "AVAILABLE",
  };

  // Trigger oracle error streak
  for (let i = 0; i < 3; i++) {
    state = updateHardStopState(state, input, now);
  }

  assert.strictEqual(state.active, true);
  console.log(`  HardStop activated at: ${state.activatedAt}, TTL: ${state.ttlMs}ms`);

  // Check after 31 minutes (TTL = 30 min, so expired)
  const thirtyOneMinutesLater = now + 31 * 60 * 1000;

  // Update state with new input → should deactivate due to TTL
  const inputAfterTTL: PolicyInput = {
    oracleStatus: "AVAILABLE",
    simulationStatus: "PASS",
    routeStatus: "AVAILABLE",
  };

  state = updateHardStopState(state, inputAfterTTL, thirtyOneMinutesLater);

  assert.strictEqual(state.active, false);
  assert.strictEqual(state.reason, "NONE");
  assert.ok(state.warnings.includes("HARDSTOP_RELEASED"));

  console.log("  ✓ TTL expired (31 min > 30 min) → deactivated");
}

/**
 * Test 10: heartbeat OK when all present & not hardstop
 */
async function test10_heartbeat_ok() {
  console.log("\n[TEST 10] Heartbeat OK when all present & not hardstop");

  // Save original env
  const originalEnv = process.env.MERIDIAN_EXECUTION_ENABLED;

  try {
    // Set env to enabled
    process.env.MERIDIAN_EXECUTION_ENABLED = "true";

    const input: PolicyInput = {
      oracleStatus: "AVAILABLE",
      simulationStatus: "PASS",
      routeStatus: "AVAILABLE",
    };

    const policyResult = evaluateExecutionPolicy(input);
    const heartbeat = runHeartbeat(input, policyResult);

    // Assert: heartbeat should be OK
    assert.strictEqual(heartbeat.status, "OK");
    assert.strictEqual(heartbeat.executionAllowed, true);
    assert.strictEqual(heartbeat.hardStopActive, false);
    assert.strictEqual(heartbeat.components.oracle, "AVAILABLE");
    assert.strictEqual(heartbeat.components.router, "AVAILABLE");
    assert.strictEqual(heartbeat.components.simulation, "AVAILABLE");
    assert.strictEqual(isHeartbeatHealthy(heartbeat), true);

    console.log("  ✓ Heartbeat status=OK (all components healthy)");
    console.log(`  ✓ Execution allowed: ${heartbeat.executionAllowed}`);
  } finally {
    // Restore original env
    if (originalEnv !== undefined) {
      process.env.MERIDIAN_EXECUTION_ENABLED = originalEnv;
    } else {
      delete process.env.MERIDIAN_EXECUTION_ENABLED;
    }
  }
}

/**
 * Test 11: heartbeat DEGRADED when oracle missing
 */
async function test11_heartbeat_degraded() {
  console.log("\n[TEST 11] Heartbeat DEGRADED when oracle missing");

  const input: PolicyInput = {
    oracleStatus: "STALE", // Oracle degraded
    simulationStatus: "PASS",
    routeStatus: "AVAILABLE",
  };

  const heartbeat = runHeartbeat(input);

  // Assert: heartbeat should be DEGRADED
  assert.strictEqual(heartbeat.status, "DEGRADED");
  assert.strictEqual(heartbeat.components.oracle, "DEGRADED");
  assert.ok(heartbeat.warnings.includes("HEARTBEAT_ORACLE_DEGRADED"));
  assert.strictEqual(isHeartbeatHealthy(heartbeat), true); // DEGRADED is still healthy

  console.log("  ✓ Heartbeat status=DEGRADED (oracle stale)");
  console.log(`  ✓ Oracle health: ${heartbeat.components.oracle}`);
}

/**
 * Test 12: guards - warnings with numbers/token/prescriptive rejected
 */
async function test12_guards_validation() {
  console.log("\n[TEST 12] Guards: warnings validation");

  // Test 12a: Numeric values should be detected
  assert.strictEqual(containsNumericLike("Value is 123"), true);
  assert.strictEqual(containsNumericLike("HARDSTOP_ORACLE_ERROR_STREAK"), false);
  console.log("  ✓ Numeric detection works");

  // Test 12b: Forbidden vocab should be detected
  assert.strictEqual(containsForbiddenVocab("You should buy now"), true);
  assert.strictEqual(containsForbiddenVocab("POLICY_ENV_DISABLED"), false);
  console.log("  ✓ Forbidden vocab detection works");

  // Test 12c: Token literals should be detected
  assert.strictEqual(containsTokenLiteral("Swap USDC for wBTC"), true);
  assert.strictEqual(containsTokenLiteral("HARDSTOP_ACTIVE"), false);
  console.log("  ✓ Token literal detection works");

  // Test 12d: Validate clean policy output
  const cleanOutput = validatePolicyOutput([
    "POLICY_ENV_DISABLED",
    "HARDSTOP_ORACLE_ERROR_STREAK",
  ]);
  assert.strictEqual(cleanOutput.valid, true);
  assert.strictEqual(cleanOutput.violations.length, 0);
  console.log("  ✓ Clean output validation passes");

  // Test 12e: Validate dirty output (with numeric)
  const dirtyOutput = validatePolicyOutput(["Streak count is 3"]);
  assert.strictEqual(dirtyOutput.valid, false);
  assert.ok(dirtyOutput.violations.includes("NUMERIC_IN_WARNING"));
  console.log("  ✓ Dirty output validation catches violations");
}

/**
 * Main test runner
 */
async function main() {
  console.log("=".repeat(60));
  console.log("PR156: Auto Execution Policy (Aggressive + HardStop) - Test Suite");
  console.log("=".repeat(60));

  try {
    await test1_env_disabled_sim_only();
    await test2_env_enabled_allow();
    await test3_oracle_error_streak();
    await test4_oracle_reset();
    await test5_sim_fail_streak();
    await test6_no_route_streak();
    await test7_unexpected_exception();
    await test8_ttl_not_expired();
    await test9_ttl_expired();
    await test10_heartbeat_ok();
    await test11_heartbeat_degraded();
    await test12_guards_validation();

    console.log("\n" + "=".repeat(60));
    console.log("✓ All PR156 tests passed (12/12)!");
    console.log("=".repeat(60));
  } catch (error) {
    console.error("\n" + "=".repeat(60));
    console.error("✗ Test failed:");
    console.error(error);
    console.error("=".repeat(60));
    process.exit(1);
  }
}

// Run tests
main();
