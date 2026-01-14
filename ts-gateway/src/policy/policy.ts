/**
 * PR156: v1.4 Auto Execution Policy - Main Policy Logic (READ-ONLY)
 *
 * Purpose:
 *   Evaluate execution policy using double-key system (env + policy).
 *   Aggressive policy: Don't stop for transient issues.
 *   HardStop: Stop only when truly broken (with TTL auto-recovery).
 *
 * Constitutional Constraints:
 *   - Double key: env key (MERIDIAN_EXECUTION_ENABLED) + policy key (HardStop)
 *   - allowExecution = envOk && policyOk
 *   - Never throws: Always returns PolicyResult
 *   - Label-only output: No numbers in warnings
 *
 * Policy Decision Tree:
 *   1. envOk = (MERIDIAN_EXECUTION_ENABLED === "true")
 *   2. policyOk = (HardStop not active)
 *   3. If !envOk → SIM_ONLY
 *   4. If !policyOk → BLOCKED
 *   5. If envOk && policyOk → ALLOW
 */

import { PolicyResult, PolicyStatus, PolicyInput, HardStopState } from "./types";
import { updateHardStopState, createInitialHardStopState } from "./hardStop";
import { sanitizeWarnings } from "./guards";

/**
 * Check environment key (MERIDIAN_EXECUTION_ENABLED)
 *
 * @returns True if env allows execution
 */
export function checkEnvKey(): boolean {
  const envValue = process.env.MERIDIAN_EXECUTION_ENABLED;
  return envValue === "true";
}

/**
 * Evaluate execution policy (main API)
 *
 * @param input - Policy input (oracle/sim/route status)
 * @param currentHardStopState - Current HardStop state (optional, creates initial if not provided)
 * @param now - Current timestamp (ms, optional, uses Date.now() if not provided)
 * @returns Policy evaluation result
 *
 * Decision logic:
 *   1. Check env key
 *   2. Update HardStop state
 *   3. Check policy key (HardStop not active)
 *   4. Determine final status
 *
 * IMPORTANT: Never throws exceptions. Always returns PolicyResult.
 */
export function evaluateExecutionPolicy(
  input: PolicyInput,
  currentHardStopState?: HardStopState,
  now?: number
): PolicyResult {
  const warnings: string[] = [];
  const timestamp = now ?? Date.now();

  try {
    // Step 1: Check env key
    const envOk = checkEnvKey();

    if (!envOk) {
      warnings.push("POLICY_ENV_DISABLED");
    }

    // Step 2: Update HardStop state
    const hardStopState = updateHardStopState(
      currentHardStopState ?? createInitialHardStopState(),
      input,
      timestamp
    );

    // Add HardStop warnings to policy warnings
    if (hardStopState.warnings.length > 0) {
      warnings.push(...hardStopState.warnings);
    }

    // Step 3: Check policy key (HardStop not active)
    const policyOk = !hardStopState.active;

    if (!policyOk) {
      warnings.push("POLICY_HARDSTOP_ACTIVE");
    }

    // Step 4: Determine final status
    let status: PolicyStatus;

    if (!envOk) {
      // Env disabled → SIM_ONLY
      status = "SIM_ONLY";
    } else if (!policyOk) {
      // HardStop active → BLOCKED
      status = "BLOCKED";
    } else {
      // Both keys OK → ALLOW
      status = "ALLOW";
    }

    return {
      status,
      envOk,
      policyOk,
      hardStopState,
      warnings: sanitizeWarnings(warnings),
    };
  } catch (error) {
    // Defensive: Never throw, return ERROR status
    return {
      status: "ERROR",
      envOk: false,
      policyOk: false,
      hardStopState: currentHardStopState ?? createInitialHardStopState(),
      warnings: sanitizeWarnings(["POLICY_EVALUATION_ERROR"]),
    };
  }
}

/**
 * Check if execution is allowed (convenience function)
 *
 * @param result - Policy result
 * @returns True if execution allowed
 */
export function isExecutionAllowed(result: PolicyResult): boolean {
  return result.status === "ALLOW";
}

/**
 * Get policy status summary (for logging/debugging)
 *
 * @param result - Policy result
 * @returns Status summary (label-only)
 */
export function getPolicySummary(result: PolicyResult): string {
  if (result.status === "ALLOW") {
    return "POLICY_ALLOW";
  }

  if (result.status === "SIM_ONLY") {
    return "POLICY_SIM_ONLY";
  }

  if (result.status === "BLOCKED") {
    return `POLICY_BLOCKED_${result.hardStopState.reason}`;
  }

  return "POLICY_ERROR";
}
