/**
 * PR156: v1.4 Auto Execution Policy (Aggressive + HardStop) - Type Definitions
 *
 * Purpose:
 *   Define types for execution policy with double-key system (env + policy).
 *   Aggressive policy (doesn't stop easily) + HardStop (stops when broken).
 *
 * Constitutional Constraints:
 *   - Double key: env key (MERIDIAN_EXECUTION_ENABLED) + policy key (HardStop)
 *   - Label-only output: No numbers/tokens/vocab in warnings
 *   - Never throws: Always returns records
 *   - Aggressive: Don't stop for transient issues
 *   - HardStop: Stop only when truly broken (with TTL auto-recovery)
 */

/**
 * Policy status (final execution decision)
 *
 * - ALLOW: Both keys OK, execution allowed
 * - SIM_ONLY: Env disabled or policy prefers simulation
 * - BLOCKED: HardStop active, execution blocked
 * - ERROR: Policy evaluation failed
 */
export type PolicyStatus = "ALLOW" | "SIM_ONLY" | "BLOCKED" | "ERROR";

/**
 * HardStop reason (why execution is locked)
 *
 * - NONE: No HardStop active
 * - ORACLE_ERROR_STREAK: Oracle failed consecutively (3+ times)
 * - SIM_FAIL_STREAK: Simulation failed consecutively (2+ times)
 * - UNEXPECTED_EXCEPTION: Unexpected exception occurred (1+ times)
 * - NO_ROUTE_STREAK: No route available consecutively (10+ times)
 */
export type HardStopReason =
  | "NONE"
  | "ORACLE_ERROR_STREAK"
  | "SIM_FAIL_STREAK"
  | "UNEXPECTED_EXCEPTION"
  | "NO_ROUTE_STREAK";

/**
 * HardStop state (persistent lock state)
 */
export interface HardStopState {
  // Is HardStop currently active?
  active: boolean;

  // Reason for HardStop (NONE if not active)
  reason: HardStopReason;

  // When was HardStop activated (timestamp ms, 0 if not active)
  activatedAt: number;

  // TTL in milliseconds (how long until auto-release)
  ttlMs: number;

  // Consecutive error counters (internal tracking, not in output)
  streaks: {
    oracleError: number; // Oracle.ERROR consecutive count
    simFail: number; // Simulation FAIL consecutive count
    noRoute: number; // NO_ROUTE consecutive count
    unexpectedException: boolean; // Exception flag (one-shot)
  };

  // Warnings (label-only, no numbers)
  warnings: string[];
}

/**
 * Policy evaluation result
 */
export interface PolicyResult {
  // Final policy status
  status: PolicyStatus;

  // Environment key status
  envOk: boolean;

  // Policy key status (HardStop not active)
  policyOk: boolean;

  // HardStop state (if any)
  hardStopState: HardStopState;

  // Warnings (label-only, no numbers)
  warnings: string[];
}

/**
 * Heartbeat status (system health check)
 *
 * - OK: All systems operational
 * - DEGRADED: Some systems unavailable but not critical
 * - CRITICAL: HardStop active or critical failure
 * - ERROR: Heartbeat check failed
 */
export type HeartbeatStatus = "OK" | "DEGRADED" | "CRITICAL" | "ERROR";

/**
 * Heartbeat result (system health snapshot)
 */
export interface HeartbeatResult {
  // Overall health status
  status: HeartbeatStatus;

  // Is execution currently allowed?
  executionAllowed: boolean;

  // Component health
  components: {
    oracle: "AVAILABLE" | "DEGRADED" | "ERROR";
    router: "AVAILABLE" | "DEGRADED" | "ERROR";
    simulation: "AVAILABLE" | "DEGRADED" | "ERROR";
  };

  // HardStop active?
  hardStopActive: boolean;

  // Warnings (label-only, no numbers)
  warnings: string[];

  // Timestamp
  timestamp: number;
}

/**
 * Policy input (from system components)
 */
export interface PolicyInput {
  // Oracle status
  oracleStatus?: "AVAILABLE" | "STALE" | "ERROR";

  // Simulation status
  simulationStatus?: "PASS" | "RISKY" | "BLOCK" | "ERROR";

  // Route status
  routeStatus?: "AVAILABLE" | "NONE" | "ERROR";

  // Exception flag (set by executor if unexpected error)
  unexpectedException?: boolean;
}
