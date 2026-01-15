/**
 * PR161: v1.4 TWAP-lite Phase Re-evaluation Policy (READ-ONLY)
 *
 * Purpose:
 *   During chunked execution, stop immediately if shock phase escalates dangerously.
 *   STOP ≠ HardStop (this is "pause for re-planning", not system lockdown).
 *
 * Constitutional Constraints:
 *   - READ-ONLY: Fixed rules, no learning, no optimization, no prediction
 *   - Safe defaults: Unknown/Error → STOP
 *   - Label-only: No numbers in warnings/reasons
 *   - Never throws: Always returns PhasePolicyDecision
 *   - Conservative: Dangerous direction → STOP, relaxation direction → continue
 */

/**
 * Phase labels (from PR149/PR154 observation)
 */
export type PhaseLabel =
  | "PHASE_UNKNOWN"
  | "PHASE_NORMAL"
  | "PHASE_PRE_SHOCK"
  | "PHASE_UP_SHOCK"
  | "PHASE_DOWN_SHOCK"
  | "PHASE_UP_REVERSAL"
  | "PHASE_DOWN_REVERSAL"
  | "PHASE_RECOVERY"
  | "PHASE_ERROR";

/**
 * Phase STOP reason (label-only)
 */
export type PhaseStopReason =
  | "STOP_PHASE_UNKNOWN"
  | "STOP_PHASE_ESCALATED"
  | "STOP_PHASE_CHANGED"
  | "STOP_PHASE_ERROR"
  | "NO_STOP";

/**
 * Phase policy decision
 */
export interface PhasePolicyDecision {
  // Should stop the run?
  shouldStop: boolean;

  // Reason (label-only)
  reason: PhaseStopReason;

  // Warnings (label-only)
  warnings: string[];
}

/**
 * Evaluate phase STOP policy (v1)
 *
 * @param prev - Previous phase label (undefined if first chunk)
 * @param now - Current phase label
 * @returns Phase policy decision
 *
 * Fixed STOP table (dangerous direction escalations):
 *   1. now = PHASE_UNKNOWN → STOP (data loss is unsafe)
 *   2. now = PHASE_ERROR → STOP (observation error)
 *   3. prev in {NORMAL, RECOVERY} and now = PRE_SHOCK → STOP (escalation)
 *   4. prev = PRE_SHOCK and now in {UP_SHOCK, DOWN_SHOCK} → STOP (escalation)
 *   5. prev = UP_SHOCK and now = UP_REVERSAL → STOP (template flip)
 *   6. prev = DOWN_SHOCK and now = DOWN_REVERSAL → STOP (template flip)
 *   7. prev = PRE_SHOCK and now in {UP_REVERSAL, DOWN_REVERSAL} → STOP (skip transition)
 *
 * NO STOP (relaxation direction or neutral):
 *   - now = PHASE_RECOVERY → continue (de-escalation)
 *   - SHOCK → NORMAL → continue (de-escalation)
 *   - Same phase → continue
 *
 * IMPORTANT: Never throws, always returns decision
 */
export function evaluatePhaseStopPolicyV1(
  prev: PhaseLabel | undefined,
  now: PhaseLabel
): PhasePolicyDecision {
  const warnings: string[] = [];

  try {
    // Rule 1: PHASE_UNKNOWN → STOP
    if (now === "PHASE_UNKNOWN") {
      warnings.push("WARN_PHASE_UNKNOWN");

      return {
        shouldStop: true,
        reason: "STOP_PHASE_UNKNOWN",
        warnings,
      };
    }

    // Rule 2: PHASE_ERROR → STOP
    if (now === "PHASE_ERROR") {
      warnings.push("WARN_PHASE_ERROR");

      return {
        shouldStop: true,
        reason: "STOP_PHASE_ERROR",
        warnings,
      };
    }

    // If no previous phase (first chunk), don't stop
    if (!prev) {
      return {
        shouldStop: false,
        reason: "NO_STOP",
        warnings,
      };
    }

    // Rule 3: prev in {NORMAL, RECOVERY} and now = PRE_SHOCK → STOP
    if (
      (prev === "PHASE_NORMAL" || prev === "PHASE_RECOVERY") &&
      now === "PHASE_PRE_SHOCK"
    ) {
      warnings.push("WARN_PHASE_ESCALATED_TO_PRE_SHOCK");

      return {
        shouldStop: true,
        reason: "STOP_PHASE_ESCALATED",
        warnings,
      };
    }

    // Rule 4: prev = PRE_SHOCK and now in {UP_SHOCK, DOWN_SHOCK} → STOP
    if (
      prev === "PHASE_PRE_SHOCK" &&
      (now === "PHASE_UP_SHOCK" || now === "PHASE_DOWN_SHOCK")
    ) {
      warnings.push("WARN_PHASE_ESCALATED_TO_SHOCK");

      return {
        shouldStop: true,
        reason: "STOP_PHASE_ESCALATED",
        warnings,
      };
    }

    // Rule 5: prev = UP_SHOCK and now = UP_REVERSAL → STOP
    if (prev === "PHASE_UP_SHOCK" && now === "PHASE_UP_REVERSAL") {
      warnings.push("WARN_PHASE_CHANGED_TO_REVERSAL");

      return {
        shouldStop: true,
        reason: "STOP_PHASE_CHANGED",
        warnings,
      };
    }

    // Rule 6: prev = DOWN_SHOCK and now = DOWN_REVERSAL → STOP
    if (prev === "PHASE_DOWN_SHOCK" && now === "PHASE_DOWN_REVERSAL") {
      warnings.push("WARN_PHASE_CHANGED_TO_REVERSAL");

      return {
        shouldStop: true,
        reason: "STOP_PHASE_CHANGED",
        warnings,
      };
    }

    // Rule 7: prev = PRE_SHOCK and now in {UP_REVERSAL, DOWN_REVERSAL} → STOP
    if (
      prev === "PHASE_PRE_SHOCK" &&
      (now === "PHASE_UP_REVERSAL" || now === "PHASE_DOWN_REVERSAL")
    ) {
      warnings.push("WARN_PHASE_SKIP_TRANSITION");

      return {
        shouldStop: true,
        reason: "STOP_PHASE_CHANGED",
        warnings,
      };
    }

    // All other transitions: NO STOP (including relaxation)
    return {
      shouldStop: false,
      reason: "NO_STOP",
      warnings,
    };
  } catch (error) {
    // Defensive: Never throw
    return {
      shouldStop: true,
      reason: "STOP_PHASE_ERROR",
      warnings: ["WARN_PHASE_EVALUATION_ERROR"],
    };
  }
}

/**
 * Get phase policy summary (for logging/debugging)
 *
 * @param decision - Phase policy decision
 * @returns Summary string (label-only)
 */
export function getPhasePolicySummary(decision: PhasePolicyDecision): string {
  if (decision.shouldStop) {
    return `PHASE_POLICY_STOP_${decision.reason}`;
  }

  return "PHASE_POLICY_CONTINUE";
}
