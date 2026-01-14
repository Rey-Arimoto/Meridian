/**
 * PR156: v1.4 Auto Execution Policy - Heartbeat (READ-ONLY)
 *
 * Purpose:
 *   Provide system health check with component status monitoring.
 *   Continuous monitoring of oracle, router, simulation, and HardStop.
 *
 * Constitutional Constraints:
 *   - Never throws: Always returns HeartbeatResult
 *   - Label-only output: No numbers in warnings
 *   - Quick check: Lightweight, suitable for frequent polling
 */

import { HeartbeatResult, HeartbeatStatus, PolicyInput, PolicyResult } from "./types";
import { sanitizeWarnings } from "./guards";

/**
 * Run system heartbeat check
 *
 * @param input - Policy input (oracle/sim/route status)
 * @param policyResult - Current policy result (optional)
 * @returns Heartbeat result
 *
 * Logic:
 *   1. Check component health (oracle, router, simulation)
 *   2. Check HardStop status
 *   3. Determine overall health status
 *   4. Check if execution allowed
 *
 * Status levels:
 *   - OK: All components operational, execution allowed
 *   - DEGRADED: Some components unavailable but not critical
 *   - CRITICAL: HardStop active or critical failure
 *   - ERROR: Heartbeat check failed
 */
export function runHeartbeat(
  input: PolicyInput,
  policyResult?: PolicyResult
): HeartbeatResult {
  const warnings: string[] = [];
  const timestamp = Date.now();

  try {
    // Step 1: Check component health

    // Oracle health
    let oracleHealth: "AVAILABLE" | "DEGRADED" | "ERROR";
    if (input.oracleStatus === "AVAILABLE") {
      oracleHealth = "AVAILABLE";
    } else if (input.oracleStatus === "STALE") {
      oracleHealth = "DEGRADED";
      warnings.push("HEARTBEAT_ORACLE_DEGRADED");
    } else {
      oracleHealth = "ERROR";
      warnings.push("HEARTBEAT_ORACLE_ERROR");
    }

    // Router health
    let routerHealth: "AVAILABLE" | "DEGRADED" | "ERROR";
    if (input.routeStatus === "AVAILABLE") {
      routerHealth = "AVAILABLE";
    } else if (input.routeStatus === "NONE") {
      routerHealth = "DEGRADED";
      warnings.push("HEARTBEAT_ROUTER_DEGRADED");
    } else {
      routerHealth = "ERROR";
      warnings.push("HEARTBEAT_ROUTER_ERROR");
    }

    // Simulation health
    let simulationHealth: "AVAILABLE" | "DEGRADED" | "ERROR";
    if (input.simulationStatus === "PASS") {
      simulationHealth = "AVAILABLE";
    } else if (input.simulationStatus === "RISKY") {
      simulationHealth = "DEGRADED";
      warnings.push("HEARTBEAT_SIMULATION_DEGRADED");
    } else if (
      input.simulationStatus === "BLOCK" ||
      input.simulationStatus === "ERROR"
    ) {
      simulationHealth = "ERROR";
      warnings.push("HEARTBEAT_SIMULATION_ERROR");
    } else {
      simulationHealth = "AVAILABLE";
    }

    // Step 2: Check HardStop status
    const hardStopActive = policyResult?.hardStopState
      ? policyResult.hardStopState.active
      : false;

    if (hardStopActive) {
      warnings.push("HEARTBEAT_HARDSTOP_ACTIVE");
    }

    // Step 3: Determine overall health status
    let status: HeartbeatStatus;

    if (hardStopActive) {
      // HardStop active → CRITICAL
      status = "CRITICAL";
    } else if (
      oracleHealth === "ERROR" ||
      routerHealth === "ERROR" ||
      simulationHealth === "ERROR"
    ) {
      // Any component ERROR → CRITICAL
      status = "CRITICAL";
    } else if (
      oracleHealth === "DEGRADED" ||
      routerHealth === "DEGRADED" ||
      simulationHealth === "DEGRADED"
    ) {
      // Any component DEGRADED → DEGRADED
      status = "DEGRADED";
    } else {
      // All components OK → OK
      status = "OK";
    }

    // Step 4: Check if execution allowed
    const executionAllowed = policyResult ? policyResult.status === "ALLOW" : false;

    return {
      status,
      executionAllowed,
      components: {
        oracle: oracleHealth,
        router: routerHealth,
        simulation: simulationHealth,
      },
      hardStopActive,
      warnings: sanitizeWarnings(warnings),
      timestamp,
    };
  } catch (error) {
    // Defensive: Never throw, return ERROR status
    return {
      status: "ERROR",
      executionAllowed: false,
      components: {
        oracle: "ERROR",
        router: "ERROR",
        simulation: "ERROR",
      },
      hardStopActive: false,
      warnings: sanitizeWarnings(["HEARTBEAT_CHECK_ERROR"]),
      timestamp,
    };
  }
}

/**
 * Get heartbeat status summary (for logging/debugging)
 *
 * @param result - Heartbeat result
 * @returns Status summary (label-only)
 */
export function getHeartbeatSummary(result: HeartbeatResult): string {
  if (result.status === "OK") {
    return "HEARTBEAT_OK";
  }

  if (result.status === "DEGRADED") {
    return "HEARTBEAT_DEGRADED";
  }

  if (result.status === "CRITICAL") {
    return "HEARTBEAT_CRITICAL";
  }

  return "HEARTBEAT_ERROR";
}

/**
 * Check if heartbeat is healthy (OK or DEGRADED)
 *
 * @param result - Heartbeat result
 * @returns True if healthy
 */
export function isHeartbeatHealthy(result: HeartbeatResult): boolean {
  return result.status === "OK" || result.status === "DEGRADED";
}
