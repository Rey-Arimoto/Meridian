/**
 * PR158: v1.4 Cooldown Gate (READ-ONLY)
 *
 * Purpose:
 *   Track last activity and enforce cooldown period.
 *   Prevent rapid-fire execution (noise suppression).
 *
 * Constitutional Constraints:
 *   - READ-ONLY: Cooldown evaluation only, no execution
 *   - Fixed rules: No learning, no optimization
 *   - Never throws: Always returns CooldownResult
 *   - Label-only output: No numbers in reasons/warnings
 *   - Conservative: Unknown state → don't block (warn only, approach B)
 */

/**
 * Cooldown status
 */
export type CooldownStatus = "AVAILABLE" | "BLOCKED" | "UNKNOWN" | "ERROR";

/**
 * Cooldown configuration (fixed thresholds)
 */
export interface CooldownConfig {
  // Cooldown period in milliseconds (internal numeric, not in output)
  // Default: 600_000 (10 minutes)
  cooldownMs: number;

  // Count simulation success as activity?
  // Default: true
  countSimulationAsActivity: boolean;
}

/**
 * Cooldown state (persistent)
 */
export interface CooldownState {
  // Last activity timestamp (epoch ms)
  lastActivityTs?: number;

  // Activity kind (for debugging/logging)
  lastActivityKind?: "EXECUTED" | "SIMULATED" | "PLANNED" | "UNKNOWN";
}

/**
 * Cooldown evaluation result
 */
export interface CooldownResult {
  // Status
  status: CooldownStatus;

  // Is cooldown blocking?
  blocked?: boolean;

  // Reasons (label-only, no numbers)
  reasons: string[];

  // Warnings (label-only, no numbers)
  warnings: string[];

  // Next state (for persistence)
  nextState: CooldownState;
}

/**
 * Fixed cooldown thresholds (constitutional constants)
 */
const COOLDOWN_THRESHOLDS = {
  // Default cooldown period (10 minutes)
  DEFAULT_COOLDOWN_MS: 600_000,

  // Default: count simulation as activity
  DEFAULT_COUNT_SIMULATION: true,
};

/**
 * Initialize cooldown state (no activity yet)
 *
 * @returns Initial cooldown state
 */
export function initCooldownStateV1(): CooldownState {
  return {
    lastActivityTs: undefined,
    lastActivityKind: undefined,
  };
}

/**
 * Evaluate cooldown (main API)
 *
 * @param state - Current cooldown state
 * @param nowTs - Current timestamp (epoch ms)
 * @param cfg - Optional cooldown configuration
 * @returns Cooldown evaluation result
 *
 * Fixed rules (never throws):
 *   1. If lastActivityTs is undefined → AVAILABLE (no activity yet)
 *   2. Calculate elapsed = nowTs - lastActivityTs
 *   3. If elapsed < cooldownMs → BLOCKED (cooldown active)
 *   4. Else → AVAILABLE (cooldown expired)
 *
 * IMPORTANT: Returns label-only reasons/warnings (no numeric values)
 */
export function evaluateCooldownV1(
  state: CooldownState,
  nowTs: number,
  cfg?: Partial<CooldownConfig>
): CooldownResult {
  const reasons: string[] = [];
  const warnings: string[] = [];

  try {
    // Merge config with defaults
    const cooldownMs =
      cfg?.cooldownMs ?? COOLDOWN_THRESHOLDS.DEFAULT_COOLDOWN_MS;

    // Step 1: Check if there's any activity yet
    if (
      !state.lastActivityTs ||
      typeof state.lastActivityTs !== "number" ||
      isNaN(state.lastActivityTs)
    ) {
      reasons.push("REASON_NO_ACTIVITY_YET");

      return {
        status: "AVAILABLE",
        blocked: false,
        reasons,
        warnings,
        nextState: state,
      };
    }

    // Step 2: Calculate elapsed time
    const elapsed = nowTs - state.lastActivityTs;

    // Step 3: Check if within cooldown period
    if (elapsed < cooldownMs) {
      // Cooldown is still active → BLOCKED
      reasons.push("REASON_COOLDOWN_ACTIVE");

      return {
        status: "BLOCKED",
        blocked: true,
        reasons,
        warnings,
        nextState: state,
      };
    } else {
      // Cooldown expired → AVAILABLE
      reasons.push("REASON_COOLDOWN_EXPIRED");

      return {
        status: "AVAILABLE",
        blocked: false,
        reasons,
        warnings,
        nextState: state,
      };
    }
  } catch (error) {
    // Defensive: Never throw, return ERROR state
    return {
      status: "ERROR",
      blocked: undefined,
      reasons: ["REASON_COOLDOWN_EVALUATION_ERROR"],
      warnings: ["WARN_COOLDOWN_EVALUATION_ERROR"],
      nextState: state,
    };
  }
}

/**
 * Mark activity (update state after execution/simulation)
 *
 * @param state - Current cooldown state
 * @param nowTs - Activity timestamp (epoch ms)
 * @param kind - Activity kind
 * @returns Updated cooldown state
 *
 * Call this after successful execution or simulation to update the cooldown state.
 */
export function markActivityV1(
  state: CooldownState,
  nowTs: number,
  kind: "EXECUTED" | "SIMULATED"
): CooldownState {
  return {
    lastActivityTs: nowTs,
    lastActivityKind: kind,
  };
}

/**
 * Get cooldown summary (for logging/debugging)
 *
 * @param result - Cooldown result
 * @returns Summary string (label-only)
 */
export function getCooldownSummary(result: CooldownResult): string {
  if (result.status === "BLOCKED") {
    return "COOLDOWN_ACTIVE";
  }

  if (result.status === "AVAILABLE") {
    return "COOLDOWN_AVAILABLE";
  }

  if (result.status === "UNKNOWN") {
    return "COOLDOWN_UNKNOWN";
  }

  return "COOLDOWN_ERROR";
}
