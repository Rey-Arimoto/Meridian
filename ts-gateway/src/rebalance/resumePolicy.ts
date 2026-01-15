/**
 * PR162: v1.4 Partial Resume Policy (READ-ONLY)
 *
 * Purpose:
 *   When TWAP-lite STOPs, define fixed "resume conditions" per stop reason.
 *   STOP = "wait until conditions are met", not "failure/termination".
 *
 * Constitutional Constraints:
 *   - READ-ONLY: Fixed table, no learning, no optimization, no prediction
 *   - Safe defaults: Uncertain/missing inputs → UNKNOWN or WAIT
 *   - Label-only: No numbers in reasons/warnings/diagnostics
 *   - Never throws: Always returns ResumeDecision
 *   - STOP ≠ HardStop: Resume policy is "can we resume?", not system lockdown
 *   - Execution still requires PR156 double-key (env + HardStop)
 */

import { ResumeState, ResumeStatus, StopReason } from "./types";

/**
 * Resume decision
 */
export interface ResumeDecision {
  // Resume status
  status: ResumeStatus; // RESUMABLE | WAIT | ABANDON | UNKNOWN

  // Reasons (label-only)
  reasons: string[];

  // Next check hint (label-only, for scheduling)
  nextCheckHint?: "SOON" | "NORMAL" | "SLOW";
}

/**
 * Resume evaluation inputs (current conditions)
 */
export interface ResumeInputs {
  // Current timestamp (internal numeric only)
  nowTs: number;

  // Oracle status
  oracleStatus?: "AVAILABLE" | "STALE" | "ERROR";

  // Gate status
  gateStatus?: "PASS" | "BLOCK" | "ERROR";

  // Gate block reasons (label-only)
  blockReasons?: string[];

  // Phase label (label-only)
  phaseLabel?: string;

  // Route availability
  routeAvailable?: boolean | "UNKNOWN";

  // HardStop active status
  hardStopActive?: boolean | "UNKNOWN";

  // Policy env enabled status
  policyEnvEnabled?: boolean | "UNKNOWN";
}

/**
 * Evaluate resume policy (v1)
 *
 * @param state - Resume state (from stopped run)
 * @param inputs - Current conditions
 * @returns Resume decision
 *
 * Fixed Decision Table (priority order, first-match-wins):
 *
 * A. ABANDON (cannot resume, give up):
 *   1. STOP_DURATION_EXCEEDED → ABANDON
 *   2. STOP_POLICY_DENY → ABANDON
 *
 * B. WAIT (wait for conditions to improve):
 *   3. STOP_HARDSTOP_ACTIVE and hardStopActive=true → WAIT
 *   4. STOP_ORACLE_STALE → WAIT until oracleStatus=AVAILABLE
 *   5. STOP_ORACLE_ERROR → WAIT until oracleStatus=AVAILABLE
 *   6. STOP_NO_ROUTE → WAIT until routeAvailable=true
 *   7. STOP_PHASE_POLICY → WAIT until phaseLabel in {NORMAL, RECOVERY}
 *   8. STOP_QUOTE_STALE → WAIT until gateStatus=PASS
 *   9. STOP_QUOTE_INCONSISTENT → WAIT until gateStatus=PASS
 *   10. STOP_IMPACT_HIGH → WAIT until gateStatus=PASS
 *   11. STOP_SLIPPAGE_HIGH → WAIT until gateStatus=PASS
 *   12. STOP_DEPTH_THIN → WAIT until gateStatus=PASS
 *   13. STOP_BLOCKED_STREAK → WAIT until resumeAfterTs (short cooldown)
 *
 * C. RESUMABLE (can resume now):
 *   14. All conditions OK:
 *       - policyEnvEnabled=true
 *       - hardStopActive=false
 *       - oracleStatus=AVAILABLE
 *       - gateStatus=PASS
 *       - phaseLabel in {NORMAL, RECOVERY}
 *       - routeAvailable=true
 *       → RESUMABLE
 *
 * D. UNKNOWN (insufficient/inconsistent inputs):
 *   15. Missing critical inputs → UNKNOWN
 *
 * IMPORTANT: Never throws, always returns decision
 */
export function evaluateResumeV1(
  state: ResumeState,
  inputs: ResumeInputs
): ResumeDecision {
  const reasons: string[] = [];

  try {
    // === A. ABANDON ===

    // Rule 1: DURATION_EXCEEDED → ABANDON
    if (state.stopReason === "STOP_DURATION_EXCEEDED") {
      reasons.push("REASON_ABANDON_DURATION_EXCEEDED");
      return {
        status: "ABANDON",
        reasons,
        nextCheckHint: undefined, // No retry
      };
    }

    // Rule 2: POLICY_DENY → ABANDON
    if (state.stopReason === "STOP_POLICY_DENY") {
      reasons.push("REASON_ABANDON_POLICY_DENY");
      return {
        status: "ABANDON",
        reasons,
        nextCheckHint: undefined, // No retry
      };
    }

    // === B. WAIT ===

    // Rule 3: HARDSTOP_ACTIVE + hardStopActive=true → WAIT
    if (
      state.stopReason === "STOP_HARDSTOP_ACTIVE" &&
      inputs.hardStopActive === true
    ) {
      reasons.push("REASON_WAIT_HARDSTOP_ACTIVE");
      return {
        status: "WAIT",
        reasons,
        nextCheckHint: "NORMAL",
      };
    }

    // Rule 4: ORACLE_STALE → WAIT until AVAILABLE
    if (state.stopReason === "STOP_ORACLE_STALE") {
      if (inputs.oracleStatus === "AVAILABLE") {
        // Oracle recovered, check other conditions
      } else {
        reasons.push("REASON_WAIT_ORACLE_STALE");
        return {
          status: "WAIT",
          reasons,
          nextCheckHint: "SOON",
        };
      }
    }

    // Rule 5: ORACLE_ERROR → WAIT until AVAILABLE
    if (state.stopReason === "STOP_ORACLE_ERROR") {
      if (inputs.oracleStatus === "AVAILABLE") {
        // Oracle recovered, check other conditions
      } else {
        reasons.push("REASON_WAIT_ORACLE_ERROR");
        return {
          status: "WAIT",
          reasons,
          nextCheckHint: "NORMAL",
        };
      }
    }

    // Rule 6: NO_ROUTE → WAIT until routeAvailable=true
    if (state.stopReason === "STOP_NO_ROUTE") {
      if (inputs.routeAvailable === true) {
        // Route recovered, check other conditions
      } else {
        reasons.push("REASON_WAIT_NO_ROUTE");
        return {
          status: "WAIT",
          reasons,
          nextCheckHint: "NORMAL",
        };
      }
    }

    // Rule 7: PHASE_POLICY → WAIT until phase NORMAL/RECOVERY
    if (state.stopReason === "STOP_PHASE_POLICY") {
      if (
        inputs.phaseLabel === "PHASE_NORMAL" ||
        inputs.phaseLabel === "PHASE_RECOVERY"
      ) {
        // Phase recovered, check other conditions
      } else {
        reasons.push("REASON_WAIT_PHASE_POLICY");
        return {
          status: "WAIT",
          reasons,
          nextCheckHint: "SOON", // Phase can change quickly (10s)
        };
      }
    }

    // Rules 8-12: Quote/Impact/Slippage/Depth → WAIT until gate PASS
    const gateRelatedReasons: StopReason[] = [
      "STOP_QUOTE_STALE",
      "STOP_QUOTE_INCONSISTENT",
      "STOP_IMPACT_HIGH",
      "STOP_SLIPPAGE_HIGH",
      "STOP_DEPTH_THIN",
    ];

    if (gateRelatedReasons.includes(state.stopReason)) {
      if (inputs.gateStatus === "PASS") {
        // Gate passed, check other conditions
      } else {
        reasons.push(`REASON_WAIT_GATE_${state.stopReason.replace("STOP_", "")}`);
        return {
          status: "WAIT",
          reasons,
          nextCheckHint: "NORMAL",
        };
      }
    }

    // Rule 13: BLOCKED_STREAK → WAIT until resumeAfterTs
    if (state.stopReason === "STOP_BLOCKED_STREAK") {
      if (state.resumeAfterTs && inputs.nowTs < state.resumeAfterTs) {
        reasons.push("REASON_WAIT_BLOCKED_STREAK_COOLDOWN");
        return {
          status: "WAIT",
          reasons,
          nextCheckHint: "SOON",
        };
      }
      // Cooldown expired, check other conditions
    }

    // === C. RESUMABLE ===

    // Rule 14: All conditions OK → RESUMABLE
    // Check all critical conditions

    // Check policy env
    if (inputs.policyEnvEnabled !== true) {
      reasons.push("REASON_WAIT_POLICY_ENV_DISABLED");
      return {
        status: "WAIT",
        reasons,
        nextCheckHint: "SLOW",
      };
    }

    // Check HardStop
    if (inputs.hardStopActive === true) {
      reasons.push("REASON_WAIT_HARDSTOP_ACTIVE");
      return {
        status: "WAIT",
        reasons,
        nextCheckHint: "NORMAL",
      };
    }

    // Check oracle
    if (inputs.oracleStatus !== "AVAILABLE") {
      reasons.push("REASON_WAIT_ORACLE_NOT_AVAILABLE");
      return {
        status: "WAIT",
        reasons,
        nextCheckHint: "SOON",
      };
    }

    // Check gate
    if (inputs.gateStatus !== "PASS") {
      reasons.push("REASON_WAIT_GATE_NOT_PASS");
      return {
        status: "WAIT",
        reasons,
        nextCheckHint: "NORMAL",
      };
    }

    // Check phase
    if (
      inputs.phaseLabel !== "PHASE_NORMAL" &&
      inputs.phaseLabel !== "PHASE_RECOVERY"
    ) {
      reasons.push("REASON_WAIT_PHASE_NOT_SAFE");
      return {
        status: "WAIT",
        reasons,
        nextCheckHint: "SOON",
      };
    }

    // Check route
    if (inputs.routeAvailable !== true) {
      reasons.push("REASON_WAIT_ROUTE_NOT_AVAILABLE");
      return {
        status: "WAIT",
        reasons,
        nextCheckHint: "NORMAL",
      };
    }

    // All conditions OK → RESUMABLE
    reasons.push("REASON_RESUMABLE_ALL_CONDITIONS_OK");
    return {
      status: "RESUMABLE",
      reasons,
      nextCheckHint: "SOON",
    };
  } catch (error) {
    // === D. UNKNOWN (defensive) ===

    reasons.push("REASON_UNKNOWN_EVALUATION_ERROR");
    return {
      status: "UNKNOWN",
      reasons,
      nextCheckHint: "SLOW",
    };
  }
}

/**
 * Get resume policy summary (for logging/debugging)
 *
 * @param decision - Resume decision
 * @returns Summary string (label-only)
 */
export function getResumePolicySummary(decision: ResumeDecision): string {
  return `RESUME_POLICY_${decision.status}`;
}
