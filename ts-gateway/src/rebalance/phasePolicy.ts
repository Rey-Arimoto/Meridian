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

/**
 * PR212: Phase Policy Evaluator v1 (separation of concerns)
 *
 * Purpose:
 *   Evaluate phase transitions and determine STOP conditions.
 *   Separates phase decision logic from execution loop.
 *
 * Constitutional:
 *   - READ-ONLY: Fixed rules, no learning, no optimization
 *   - Defensive: Never throws, always returns decision
 *   - Label-only: transitionCodes are strings only
 *   - Deterministic: Same inputs → same outputs
 */

import type { PhasePolicyInputsV1, PhasePolicyDecisionV1, StopCause } from "./types";

/**
 * Phase transition reason code constants (PR211 taxonomy)
 */
// Transition types (state machine edges)
const PHASE_TXN_NORMAL_TO_RANGE = "PHASE_TXN_NORMAL_TO_RANGE";
const PHASE_TXN_RANGE_TO_DOWN_SHOCK = "PHASE_TXN_RANGE_TO_DOWN_SHOCK";
const PHASE_TXN_RANGE_TO_UP_REVERSAL = "PHASE_TXN_RANGE_TO_UP_REVERSAL";
const PHASE_TXN_DOWN_SHOCK_TO_RANGE = "PHASE_TXN_DOWN_SHOCK_TO_RANGE";
const PHASE_TXN_UP_REVERSAL_TO_RANGE = "PHASE_TXN_UP_REVERSAL_TO_RANGE";
const PHASE_TXN_UNKNOWN = "PHASE_TXN_UNKNOWN";

// Trigger categories (root causes) - for future use
const PHASE_TRIG_GATE_BLOCK = "PHASE_TRIG_GATE_BLOCK";
const PHASE_TRIG_POLICY_HARDSTOP = "PHASE_TRIG_POLICY_HARDSTOP";
const PHASE_TRIG_TIMEOUT_PRESSURE = "PHASE_TRIG_TIMEOUT_PRESSURE";

/**
 * Evaluate phase policy v1
 *
 * @param inputs - Phase policy inputs (prev/current phase, gate/policy status, etc.)
 * @returns Phase policy decision (next phase, transition codes, stop decision)
 *
 * This function:
 * 1. Detects phase transitions (prevPhase → currentPhase)
 * 2. Determines transition type (PHASE_TXN_*)
 * 3. Adds trigger codes (PHASE_TRIG_*) based on context (gate/policy/timeout)
 * 4. Decides if run should STOP (using existing evaluatePhaseStopPolicyV1 logic)
 *
 * PR212a: Updated to use label-only inputs (no numeric values)
 *
 * Note: Trigger codes (PHASE_TRIG_*) are added only if context is available.
 *       If called before gate/policy evaluation, trigger codes will be empty.
 *
 * IMPORTANT: Never throws, always returns decision
 */
export function evaluatePhasePolicyV1(inputs: PhasePolicyInputsV1): PhasePolicyDecisionV1 {
  try {
    const { prevPhase, currentPhase, gateStatus, policyStatus, blockedStreakStatus, timeoutStatus } = inputs;

    // Initialize transition codes
    const transitionCodes: string[] = [];

    // Detect phase transition
    let changed = false;
    if (prevPhase !== "PHASE_UNKNOWN" && currentPhase !== prevPhase) {
      changed = true;

      // Determine transition type
      const transitionKey = `${prevPhase}_TO_${currentPhase}`;

      // Map transition to taxonomy (PR211 logic from runner.ts)
      if (transitionKey === "PHASE_NORMAL_TO_PHASE_RANGE") {
        transitionCodes.push(PHASE_TXN_NORMAL_TO_RANGE);
      } else if (transitionKey === "PHASE_RANGE_TO_PHASE_DOWN_SHOCK") {
        transitionCodes.push(PHASE_TXN_RANGE_TO_DOWN_SHOCK);
      } else if (transitionKey === "PHASE_RANGE_TO_PHASE_UP_REVERSAL") {
        transitionCodes.push(PHASE_TXN_RANGE_TO_UP_REVERSAL);
      } else if (transitionKey === "PHASE_DOWN_SHOCK_TO_PHASE_RANGE") {
        transitionCodes.push(PHASE_TXN_DOWN_SHOCK_TO_RANGE);
      } else if (transitionKey === "PHASE_UP_REVERSAL_TO_PHASE_RANGE") {
        transitionCodes.push(PHASE_TXN_UP_REVERSAL_TO_RANGE);
      } else {
        transitionCodes.push(PHASE_TXN_UNKNOWN);
      }

      // Add trigger codes based on context (label-only)
      if (gateStatus === "BLOCK") {
        transitionCodes.push(PHASE_TRIG_GATE_BLOCK);
      }
      if (policyStatus === "BLOCKED") {
        transitionCodes.push(PHASE_TRIG_POLICY_HARDSTOP);
      }
      // PR212a: Use label-only timeout status
      if (timeoutStatus === "TIMEOUT_EXCEEDED") {
        transitionCodes.push(PHASE_TRIG_TIMEOUT_PRESSURE);
      }
    }

    // PR212d: Check timeout STOP condition (takes precedence)
    if (timeoutStatus === "TIMEOUT_EXCEEDED") {
      return {
        nextPhase: currentPhase,
        changed,
        transitionCodes,
        shouldStop: true,
        stopCause: "TIMEOUT",
      };
    }

    // PR212d: Check blocked streak STOP condition
    if (blockedStreakStatus === "STREAK_EXCEEDED") {
      return {
        nextPhase: currentPhase,
        changed,
        transitionCodes,
        shouldStop: true,
        stopCause: "GATE",
      };
    }

    // Evaluate STOP policy (reuse existing logic)
    const stopDecision = evaluatePhaseStopPolicyV1(
      prevPhase as PhaseLabel,
      currentPhase as PhaseLabel
    );

    // Determine stop cause (if shouldStop)
    let stopCause: StopCause | undefined;
    if (stopDecision.shouldStop) {
      stopCause = "PHASE";
    }

    return {
      nextPhase: currentPhase,
      changed,
      transitionCodes,
      shouldStop: stopDecision.shouldStop,
      stopCause,
    };
  } catch (error) {
    // Defensive: Never throw, return safe default
    return {
      nextPhase: inputs.currentPhase || "PHASE_UNKNOWN",
      changed: false,
      transitionCodes: [],
      shouldStop: true,
      stopCause: "PHASE",
    };
  }
}
