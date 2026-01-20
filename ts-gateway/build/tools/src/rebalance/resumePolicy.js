"use strict";
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
Object.defineProperty(exports, "__esModule", { value: true });
exports.evaluateResumeV1 = evaluateResumeV1;
exports.getResumePolicySummary = getResumePolicySummary;
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
function evaluateResumeV1(state, inputs) {
    var reasons = [];
    try {
        // === A. ABANDON ===
        // Rule 1: DURATION_EXCEEDED → ABANDON
        if (state.stopReason === "STOP_DURATION_EXCEEDED") {
            reasons.push("REASON_ABANDON_DURATION_EXCEEDED");
            return {
                status: "ABANDON",
                reasons: reasons,
                nextCheckHint: undefined, // No retry
            };
        }
        // Rule 2: POLICY_DENY → ABANDON
        if (state.stopReason === "STOP_POLICY_DENY") {
            reasons.push("REASON_ABANDON_POLICY_DENY");
            return {
                status: "ABANDON",
                reasons: reasons,
                nextCheckHint: undefined, // No retry
            };
        }
        // === B. WAIT ===
        // Rule 3: HARDSTOP_ACTIVE + hardStopActive=true → WAIT
        if (state.stopReason === "STOP_HARDSTOP_ACTIVE" &&
            inputs.hardStopActive === true) {
            reasons.push("REASON_WAIT_HARDSTOP_ACTIVE");
            return {
                status: "WAIT",
                reasons: reasons,
                nextCheckHint: "NORMAL",
            };
        }
        // Rule 4: ORACLE_STALE → WAIT until AVAILABLE
        if (state.stopReason === "STOP_ORACLE_STALE") {
            if (inputs.oracleStatus === "AVAILABLE") {
                // Oracle recovered, check other conditions
            }
            else {
                reasons.push("REASON_WAIT_ORACLE_STALE");
                return {
                    status: "WAIT",
                    reasons: reasons,
                    nextCheckHint: "SOON",
                };
            }
        }
        // Rule 5: ORACLE_ERROR → WAIT until AVAILABLE
        if (state.stopReason === "STOP_ORACLE_ERROR") {
            if (inputs.oracleStatus === "AVAILABLE") {
                // Oracle recovered, check other conditions
            }
            else {
                reasons.push("REASON_WAIT_ORACLE_ERROR");
                return {
                    status: "WAIT",
                    reasons: reasons,
                    nextCheckHint: "NORMAL",
                };
            }
        }
        // Rule 6: NO_ROUTE → WAIT until routeAvailable=true
        if (state.stopReason === "STOP_NO_ROUTE") {
            if (inputs.routeAvailable === true) {
                // Route recovered, check other conditions
            }
            else {
                reasons.push("REASON_WAIT_NO_ROUTE");
                return {
                    status: "WAIT",
                    reasons: reasons,
                    nextCheckHint: "NORMAL",
                };
            }
        }
        // Rule 7: PHASE_POLICY → WAIT until phase NORMAL/RECOVERY
        if (state.stopReason === "STOP_PHASE_POLICY") {
            if (inputs.phaseLabel === "PHASE_NORMAL" ||
                inputs.phaseLabel === "PHASE_RECOVERY") {
                // Phase recovered, check other conditions
            }
            else {
                reasons.push("REASON_WAIT_PHASE_POLICY");
                return {
                    status: "WAIT",
                    reasons: reasons,
                    nextCheckHint: "SOON", // Phase can change quickly (10s)
                };
            }
        }
        // Rules 8-12: Quote/Impact/Slippage/Depth → WAIT until gate PASS
        var gateRelatedReasons = [
            "STOP_QUOTE_STALE",
            "STOP_QUOTE_INCONSISTENT",
            "STOP_IMPACT_HIGH",
            "STOP_SLIPPAGE_HIGH",
            "STOP_DEPTH_THIN",
        ];
        if (gateRelatedReasons.includes(state.stopReason)) {
            if (inputs.gateStatus === "PASS") {
                // Gate passed, check other conditions
            }
            else {
                reasons.push("REASON_WAIT_GATE_".concat(state.stopReason.replace("STOP_", "")));
                return {
                    status: "WAIT",
                    reasons: reasons,
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
                    reasons: reasons,
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
                reasons: reasons,
                nextCheckHint: "SLOW",
            };
        }
        // Check HardStop
        if (inputs.hardStopActive === true) {
            reasons.push("REASON_WAIT_HARDSTOP_ACTIVE");
            return {
                status: "WAIT",
                reasons: reasons,
                nextCheckHint: "NORMAL",
            };
        }
        // Check oracle
        if (inputs.oracleStatus !== "AVAILABLE") {
            reasons.push("REASON_WAIT_ORACLE_NOT_AVAILABLE");
            return {
                status: "WAIT",
                reasons: reasons,
                nextCheckHint: "SOON",
            };
        }
        // Check gate
        if (inputs.gateStatus !== "PASS") {
            reasons.push("REASON_WAIT_GATE_NOT_PASS");
            return {
                status: "WAIT",
                reasons: reasons,
                nextCheckHint: "NORMAL",
            };
        }
        // Check phase
        if (inputs.phaseLabel !== "PHASE_NORMAL" &&
            inputs.phaseLabel !== "PHASE_RECOVERY") {
            reasons.push("REASON_WAIT_PHASE_NOT_SAFE");
            return {
                status: "WAIT",
                reasons: reasons,
                nextCheckHint: "SOON",
            };
        }
        // Check route
        if (inputs.routeAvailable !== true) {
            reasons.push("REASON_WAIT_ROUTE_NOT_AVAILABLE");
            return {
                status: "WAIT",
                reasons: reasons,
                nextCheckHint: "NORMAL",
            };
        }
        // All conditions OK → RESUMABLE
        reasons.push("REASON_RESUMABLE_ALL_CONDITIONS_OK");
        return {
            status: "RESUMABLE",
            reasons: reasons,
            nextCheckHint: "SOON",
        };
    }
    catch (error) {
        // === D. UNKNOWN (defensive) ===
        reasons.push("REASON_UNKNOWN_EVALUATION_ERROR");
        return {
            status: "UNKNOWN",
            reasons: reasons,
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
function getResumePolicySummary(decision) {
    return "RESUME_POLICY_".concat(decision.status);
}
