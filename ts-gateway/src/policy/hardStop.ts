/**
 * PR156: v1.4 Auto Execution Policy - HardStop Logic (READ-ONLY)
 *
 * Purpose:
 *   Manage HardStop state with streak tracking and TTL auto-recovery.
 *   Aggressive policy: Only lock when truly broken.
 *
 * Constitutional Constraints:
 *   - Never throws: Always returns HardStopState
 *   - Label-only output: No numbers in warnings
 *   - Aggressive: High thresholds before locking
 *   - TTL auto-recovery: Locks expire automatically
 *
 * HardStop Thresholds (Aggressive + HardStop):
 *   - Oracle.ERROR consecutive 3 → 30 min lock
 *   - Simulation FAIL consecutive 2 → 60 min lock
 *   - Unexpected exception 1 → 60 min lock
 *   - NO_ROUTE consecutive 10 → 15 min lock
 */

import { HardStopState, HardStopReason, PolicyInput } from "./types";
import { sanitizeWarnings } from "./guards";

/**
 * HardStop thresholds (constitutional constants)
 */
const HARDSTOP_THRESHOLDS = {
  // Oracle ERROR consecutive threshold
  ORACLE_ERROR_STREAK: 3,
  ORACLE_ERROR_TTL_MS: 30 * 60 * 1000, // 30 minutes

  // Simulation FAIL consecutive threshold
  SIM_FAIL_STREAK: 2,
  SIM_FAIL_TTL_MS: 60 * 60 * 1000, // 60 minutes

  // Unexpected exception threshold (one-shot)
  UNEXPECTED_EXCEPTION_TTL_MS: 60 * 60 * 1000, // 60 minutes

  // NO_ROUTE consecutive threshold
  NO_ROUTE_STREAK: 10,
  NO_ROUTE_TTL_MS: 15 * 60 * 1000, // 15 minutes
};

/**
 * Create initial HardStop state (no locks)
 *
 * @returns Initial HardStop state
 */
export function createInitialHardStopState(): HardStopState {
  return {
    active: false,
    reason: "NONE",
    activatedAt: 0,
    ttlMs: 0,
    streaks: {
      oracleError: 0,
      simFail: 0,
      noRoute: 0,
      unexpectedException: false,
    },
    warnings: [],
  };
}

/**
 * Check if HardStop TTL has expired
 *
 * @param state - Current HardStop state
 * @param now - Current timestamp (ms)
 * @returns True if TTL expired
 */
export function isHardStopExpired(state: HardStopState, now: number): boolean {
  if (!state.active) {
    return false;
  }

  const elapsed = now - state.activatedAt;
  return elapsed >= state.ttlMs;
}

/**
 * Deactivate HardStop (TTL expired or manual reset)
 *
 * @param state - Current HardStop state
 * @returns Updated state (inactive)
 */
export function deactivateHardStop(state: HardStopState): HardStopState {
  return {
    ...state,
    active: false,
    reason: "NONE",
    activatedAt: 0,
    ttlMs: 0,
    warnings: sanitizeWarnings(["HARDSTOP_RELEASED"]),
  };
}

/**
 * Activate HardStop with reason and TTL
 *
 * @param state - Current HardStop state
 * @param reason - HardStop reason
 * @param ttlMs - TTL in milliseconds
 * @param now - Current timestamp (ms)
 * @returns Updated state (active)
 */
export function activateHardStop(
  state: HardStopState,
  reason: HardStopReason,
  ttlMs: number,
  now: number
): HardStopState {
  const warnings: string[] = [];

  // Add reason-specific warning (label-only, no numbers)
  switch (reason) {
    case "ORACLE_ERROR_STREAK":
      warnings.push("HARDSTOP_ORACLE_ERROR_STREAK");
      break;
    case "SIM_FAIL_STREAK":
      warnings.push("HARDSTOP_SIM_FAIL_STREAK");
      break;
    case "UNEXPECTED_EXCEPTION":
      warnings.push("HARDSTOP_UNEXPECTED_EXCEPTION");
      break;
    case "NO_ROUTE_STREAK":
      warnings.push("HARDSTOP_NO_ROUTE_STREAK");
      break;
    default:
      warnings.push("HARDSTOP_UNKNOWN_REASON");
  }

  return {
    ...state,
    active: true,
    reason,
    activatedAt: now,
    ttlMs,
    warnings: sanitizeWarnings(warnings),
  };
}

/**
 * Update HardStop state based on policy input
 *
 * @param state - Current HardStop state
 * @param input - Policy input (oracle/sim/route status)
 * @param now - Current timestamp (ms)
 * @returns Updated HardStop state
 *
 * Logic:
 *   1. Check if TTL expired → deactivate
 *   2. If already active → keep active (until TTL expires)
 *   3. Update streaks based on input
 *   4. Check thresholds → activate if needed
 */
export function updateHardStopState(
  state: HardStopState,
  input: PolicyInput,
  now: number
): HardStopState {
  try {
    // Step 1: Check TTL expiration
    if (state.active && isHardStopExpired(state, now)) {
      state = deactivateHardStop(state);
    }

    // Step 2: If still active, keep active
    if (state.active) {
      return state;
    }

    // Step 3: Update streaks and check thresholds
    let updatedState = { ...state };

    // Oracle ERROR streak
    if (input.oracleStatus === "ERROR") {
      updatedState.streaks.oracleError += 1;

      if (
        updatedState.streaks.oracleError >=
        HARDSTOP_THRESHOLDS.ORACLE_ERROR_STREAK
      ) {
        return activateHardStop(
          updatedState,
          "ORACLE_ERROR_STREAK",
          HARDSTOP_THRESHOLDS.ORACLE_ERROR_TTL_MS,
          now
        );
      }
    } else if (input.oracleStatus === "AVAILABLE") {
      // Reset oracle streak on AVAILABLE
      updatedState.streaks.oracleError = 0;
    }

    // Simulation FAIL streak
    if (
      input.simulationStatus === "ERROR" ||
      input.simulationStatus === "BLOCK"
    ) {
      updatedState.streaks.simFail += 1;

      if (updatedState.streaks.simFail >= HARDSTOP_THRESHOLDS.SIM_FAIL_STREAK) {
        return activateHardStop(
          updatedState,
          "SIM_FAIL_STREAK",
          HARDSTOP_THRESHOLDS.SIM_FAIL_TTL_MS,
          now
        );
      }
    } else if (input.simulationStatus === "PASS") {
      // Reset sim streak on PASS
      updatedState.streaks.simFail = 0;
    }

    // NO_ROUTE streak
    if (input.routeStatus === "NONE") {
      updatedState.streaks.noRoute += 1;

      if (updatedState.streaks.noRoute >= HARDSTOP_THRESHOLDS.NO_ROUTE_STREAK) {
        return activateHardStop(
          updatedState,
          "NO_ROUTE_STREAK",
          HARDSTOP_THRESHOLDS.NO_ROUTE_TTL_MS,
          now
        );
      }
    } else if (input.routeStatus === "AVAILABLE") {
      // Reset route streak on AVAILABLE
      updatedState.streaks.noRoute = 0;
    }

    // Unexpected exception (one-shot)
    if (input.unexpectedException) {
      updatedState.streaks.unexpectedException = true;

      return activateHardStop(
        updatedState,
        "UNEXPECTED_EXCEPTION",
        HARDSTOP_THRESHOLDS.UNEXPECTED_EXCEPTION_TTL_MS,
        now
      );
    }

    return updatedState;
  } catch (error) {
    // Defensive: Never throw, return error state
    return {
      ...state,
      warnings: sanitizeWarnings(["HARDSTOP_UPDATE_ERROR"]),
    };
  }
}

/**
 * Get HardStop status summary (for logging/debugging)
 *
 * @param state - HardStop state
 * @returns Status summary (label-only)
 */
export function getHardStopSummary(state: HardStopState): string {
  if (!state.active) {
    return "HARDSTOP_INACTIVE";
  }

  return `HARDSTOP_ACTIVE_${state.reason}`;
}
