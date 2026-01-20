"use strict";
/**
 * PR163: v1.4 Supervisor Loop (READ-ONLY)
 * PR164: Telemetry integration
 *
 * Purpose:
 *   24/7 operational loop that ticks periodically, evaluates resume conditions,
 *   and runs TWAP-lite execution when safe.
 *
 * Constitutional Constraints:
 *   - READ-ONLY: Fixed tick logic, no learning, no optimization
 *   - Double-key maintained: PR156 policy controls execution
 *   - Safe defaults: Uncertain → WAIT
 *   - Label-only: All actions/reasons are labels
 *   - Defensive: Never throws, always returns result
 */
var __awaiter = (this && this.__awaiter) || function (thisArg, _arguments, P, generator) {
    function adopt(value) { return value instanceof P ? value : new P(function (resolve) { resolve(value); }); }
    return new (P || (P = Promise))(function (resolve, reject) {
        function fulfilled(value) { try { step(generator.next(value)); } catch (e) { reject(e); } }
        function rejected(value) { try { step(generator["throw"](value)); } catch (e) { reject(e); } }
        function step(result) { result.done ? resolve(result.value) : adopt(result.value).then(fulfilled, rejected); }
        step((generator = generator.apply(thisArg, _arguments || [])).next());
    });
};
var __generator = (this && this.__generator) || function (thisArg, body) {
    var _ = { label: 0, sent: function() { if (t[0] & 1) throw t[1]; return t[1]; }, trys: [], ops: [] }, f, y, t, g = Object.create((typeof Iterator === "function" ? Iterator : Object).prototype);
    return g.next = verb(0), g["throw"] = verb(1), g["return"] = verb(2), typeof Symbol === "function" && (g[Symbol.iterator] = function() { return this; }), g;
    function verb(n) { return function (v) { return step([n, v]); }; }
    function step(op) {
        if (f) throw new TypeError("Generator is already executing.");
        while (g && (g = 0, op[0] && (_ = 0)), _) try {
            if (f = 1, y && (t = op[0] & 2 ? y["return"] : op[0] ? y["throw"] || ((t = y["return"]) && t.call(y), 0) : y.next) && !(t = t.call(y, op[1])).done) return t;
            if (y = 0, t) op = [op[0] & 2, t.value];
            switch (op[0]) {
                case 0: case 1: t = op; break;
                case 4: _.label++; return { value: op[1], done: false };
                case 5: _.label++; y = op[1]; op = [0]; continue;
                case 7: op = _.ops.pop(); _.trys.pop(); continue;
                default:
                    if (!(t = _.trys, t = t.length > 0 && t[t.length - 1]) && (op[0] === 6 || op[0] === 2)) { _ = 0; continue; }
                    if (op[0] === 3 && (!t || (op[1] > t[0] && op[1] < t[3]))) { _.label = op[1]; break; }
                    if (op[0] === 6 && _.label < t[1]) { _.label = t[1]; t = op; break; }
                    if (t && _.label < t[2]) { _.label = t[2]; _.ops.push(op); break; }
                    if (t[2]) _.ops.pop();
                    _.trys.pop(); continue;
            }
            op = body.call(thisArg, _);
        } catch (e) { op = [6, e]; y = 0; } finally { f = t = 0; }
        if (op[0] & 5) throw op[1]; return { value: op[0] ? op[1] : void 0, done: true };
    }
};
var __spreadArray = (this && this.__spreadArray) || function (to, from, pack) {
    if (pack || arguments.length === 2) for (var i = 0, l = from.length, ar; i < l; i++) {
        if (ar || !(i in from)) {
            if (!ar) ar = Array.prototype.slice.call(from, 0, i);
            ar[i] = from[i];
        }
    }
    return to.concat(ar || Array.prototype.slice.call(from));
};
Object.defineProperty(exports, "__esModule", { value: true });
exports.runSupervisorOnceV1 = runSupervisorOnceV1;
var resumePolicy_1 = require("../rebalance/resumePolicy");
var telemetry_1 = require("../telemetry");
var snapshot_1 = require("../snapshot");
var spec_1 = require("../spec");
var interface_1 = require("../orchestrator/interface");
/**
 * PR207: Summarize resume reason codes for telemetry
 *
 * @param codes - Array of resume reason code strings
 * @param maxCodes - Maximum number of codes to include (default: 8)
 * @returns Summary object with status and joined string
 *
 * Rules:
 * - Empty/undefined → {status: "EMPTY", joined: ""}
 * - Filter to string-only values (defensive)
 * - Deduplicate via Set
 * - Sort alphabetically (deterministic)
 * - Truncate to maxCodes (with REASONS_TRUNCATED marker)
 * - Join with pipe separator
 */
function summarizeResumeReasonCodesV1(codes, maxCodes) {
    if (maxCodes === void 0) { maxCodes = 8; }
    try {
        if (!Array.isArray(codes) || codes.length === 0) {
            return { status: "EMPTY", joined: "" };
        }
        // Filter to strings only (defensive)
        var stringCodes = codes.filter(function (c) { return typeof c === "string" && c.length > 0; });
        if (stringCodes.length === 0) {
            return { status: "EMPTY", joined: "" };
        }
        // Deduplicate and sort
        var unique = Array.from(new Set(stringCodes)).sort();
        // Truncate if needed
        var final = unique;
        if (unique.length > maxCodes) {
            final = unique.slice(0, maxCodes);
            final.push("REASONS_TRUNCATED");
        }
        return { status: "PRESENT", joined: final.join("|") };
    }
    catch (_a) {
        // Defensive: Never throw
        return { status: "EMPTY", joined: "" };
    }
}
/**
 * PR208: Generate resume ID for resume re-execution traceability
 *
 * @returns Resume ID in format RESUME_{timestamp}_{random}
 */
function generateResumeIdV1() {
    var ts = Date.now();
    var rand = Math.floor(Math.random() * 100000);
    return "RESUME_".concat(ts, "_").concat(rand);
}
/**
 * PR207: Derive resume reason codes from inputs and decision
 *
 * @param inputs - Resume inputs
 * @param decision - Resume decision
 * @param resumeState - Resume state (optional)
 * @returns Array of resume reason codes
 *
 * Maps resume evaluation inputs and decision to structured reason codes.
 * Always returns at least one code (RESUME_UNKNOWN as fallback).
 */
function deriveResumeReasonCodesV1(inputs, decision, resumeState) {
    var codes = [];
    try {
        // Decision status
        if (decision.status === "RESUMABLE") {
            codes.push("RESUME_ALLOWED");
        }
        else if (decision.status === "WAIT") {
            codes.push("RESUME_BLOCKED");
        }
        else if (decision.status === "ABANDON") {
            codes.push("RESUME_EXPIRED");
        }
        else {
            codes.push("RESUME_UNKNOWN");
        }
        // Oracle condition
        if (inputs.oracleStatus === "AVAILABLE") {
            codes.push("RESUME_ORACLE_AVAILABLE");
        }
        else if (inputs.oracleStatus === "STALE" || inputs.oracleStatus === "ERROR") {
            codes.push("RESUME_ORACLE_UNAVAILABLE");
        }
        // Gate condition
        if (inputs.gateStatus === "PASS") {
            codes.push("RESUME_GATE_PASS");
        }
        else if (inputs.gateStatus === "BLOCK" || inputs.gateStatus === "ERROR") {
            codes.push("RESUME_GATE_BLOCK");
        }
        // Route condition
        if (inputs.routeAvailable === true) {
            codes.push("RESUME_ROUTE_AVAILABLE");
        }
        else if (inputs.routeAvailable === false) {
            codes.push("RESUME_ROUTE_UNAVAILABLE");
        }
        // Policy/HardStop condition
        if (inputs.hardStopActive === true) {
            codes.push("RESUME_HARDSTOP_ACTIVE");
        }
        else if (inputs.hardStopActive === false) {
            codes.push("RESUME_HARDSTOP_INACTIVE");
        }
        if (inputs.policyEnvEnabled === true) {
            codes.push("RESUME_POLICY_ENV_ENABLED");
        }
        else if (inputs.policyEnvEnabled === false) {
            codes.push("RESUME_POLICY_ENV_DISABLED");
        }
        // Phase condition
        var phaseLabel = inputs.phaseLabel;
        if (phaseLabel === "PHASE_NORMAL" || phaseLabel === "PHASE_RECOVERY") {
            codes.push("RESUME_PHASE_NORMAL");
        }
        else if (phaseLabel === "PHASE_DOWN_SHOCK" ||
            phaseLabel === "PHASE_UP_SHOCK" ||
            phaseLabel === "PHASE_UP_REVERSAL" ||
            phaseLabel === "PHASE_DOWN_REVERSAL") {
            codes.push("RESUME_PHASE_RISK");
        }
        // Timeout condition (check if resumeAfterTs is set and if we've passed it)
        if (resumeState === null || resumeState === void 0 ? void 0 : resumeState.resumeAfterTs) {
            if (inputs.nowTs >= resumeState.resumeAfterTs) {
                codes.push("RESUME_TIMEOUT_OK");
            }
            else {
                codes.push("RESUME_TIMEOUT_EXCEEDED");
            }
        }
        // Defensive fallback
        if (codes.length === 0) {
            codes.push("RESUME_UNKNOWN");
        }
        return codes;
    }
    catch (_a) {
        // Defensive: Never throw
        return ["RESUME_UNKNOWN"];
    }
}
/**
 * PR213: Summarize resume strategy reason codes (label-only)
 *
 * @param codes - Array of strategy reason codes
 * @returns Summary object with status and joined string
 *
 * Purpose:
 *   Create deterministic, fixed-length summary of strategy codes for telemetry.
 *   Same pattern as summarizeResumeReasonCodesV1.
 *
 * Rules:
 *   - Empty/undefined → {status: "EMPTY", joined: ""}
 *   - Filter to string-only values (defensive)
 *   - Deduplicate via Set
 *   - Sort alphabetically (deterministic ordering)
 *   - Take first 8 items
 *   - If truncated, append "REASONS_TRUNCATED"
 *   - Join with "|" separator
 *
 * IMPORTANT: Never throws, always returns summary
 */
function summarizeStrategyCodesV1(codes) {
    try {
        if (!codes || codes.length === 0) {
            return { status: "EMPTY", joined: "" };
        }
        // Defensive: filter to string-only, dedupe, sort
        var filtered = codes.filter(function (c) { return typeof c === "string" && c.length > 0; });
        if (filtered.length === 0) {
            return { status: "EMPTY", joined: "" };
        }
        var deduped = Array.from(new Set(filtered));
        var sorted = deduped.sort();
        var maxCodes = 8;
        var truncated = sorted.length > maxCodes;
        var taken = sorted.slice(0, maxCodes);
        if (truncated) {
            taken.push("REASONS_TRUNCATED");
        }
        return {
            status: "PRESENT",
            joined: taken.join("|"),
        };
    }
    catch (_a) {
        // Defensive: Never throw
        return { status: "EMPTY", joined: "" };
    }
}
/**
 * PR213: Derive resume strategy from origin context (Autonomous Recovery Strategy v1)
 *
 * @param resumeDecision - Resume decision from evaluateResumeV1
 * @param resumeState - Resume state (contains origin context from PR209)
 * @returns Strategy and reason codes
 *
 * Purpose:
 *   Determine HOW to retry execution based on WHY it stopped.
 *   Safe defaults: dangerous scenarios → SIM_ONLY or WAIT.
 *
 * Constitutional:
 *   - READ-ONLY: Fixed mapping rules, no learning/optimization
 *   - Safe defaults: GATE/PHASE → SIM_ONLY, POLICY → WAIT
 *   - Label-only: All outputs are strings
 *   - Deterministic: Same inputs → same outputs
 *
 * Strategy derivation rules (v1):
 *   1. If resume decision ≠ RESUMABLE → follow decision
 *      - WAIT → WAIT_FOR_RECOVERY
 *      - ABANDON → ABANDON
 *   2. If RESUMABLE → inspect origin stop cause:
 *      - TIMEOUT → RETRY_IMMEDIATE (safe to retry)
 *      - GATE → RETRY_SAFE_SIM_ONLY (may still be blocked)
 *      - PHASE → RETRY_SAFE_SIM_ONLY (market risk may persist)
 *      - POLICY → WAIT_FOR_UNLOCK (hardstop/env key)
 *      - NONE/unknown → RETRY_SAFE_SIM_ONLY (safe default)
 *
 * IMPORTANT: Never throws, always returns strategy
 */
function deriveResumeStrategyV1(resumeDecision, resumeState) {
    try {
        var codes = [];
        // Rule 1: Non-RESUMABLE decisions
        if (resumeDecision.status === "WAIT") {
            codes.push("STRAT_DECISION_WAIT");
            return { strategy: "WAIT_FOR_RECOVERY", codes: codes };
        }
        if (resumeDecision.status === "ABANDON") {
            codes.push("STRAT_DECISION_ABANDON");
            return { strategy: "ABANDON", codes: codes };
        }
        if (resumeDecision.status !== "RESUMABLE") {
            // UNKNOWN or unexpected status → safe default
            codes.push("STRAT_DECISION_UNKNOWN");
            return { strategy: "WAIT_FOR_RECOVERY", codes: codes };
        }
        // Rule 2: RESUMABLE → inspect origin context (PR209 fields)
        var originStopCause = (resumeState === null || resumeState === void 0 ? void 0 : resumeState.originStopCause) || "NONE";
        var originRunReasonCodes_1 = (resumeState === null || resumeState === void 0 ? void 0 : resumeState.originRunReasonCodes) || [];
        // Helper: check if reason codes contain prefix
        var hasReasonPrefix = function (prefix) {
            return originRunReasonCodes_1.some(function (code) {
                return typeof code === "string" && code.includes(prefix);
            });
        };
        // TIMEOUT → safe to retry immediately
        if (originStopCause === "TIMEOUT") {
            codes.push("STRAT_FROM_TIMEOUT");
            return { strategy: "RETRY_IMMEDIATE", codes: codes };
        }
        // GATE → retry in SIM_ONLY (gate may still block)
        if (originStopCause === "GATE" || hasReasonPrefix("RUN_GATE_")) {
            codes.push("STRAT_FROM_GATE");
            codes.push("STRAT_EXEC_MODE_SIM_ONLY");
            return { strategy: "RETRY_SAFE_SIM_ONLY", codes: codes };
        }
        // PHASE → retry in SIM_ONLY (market risk may persist)
        if (originStopCause === "PHASE" ||
            hasReasonPrefix("RUN_PHASE_") ||
            hasReasonPrefix("PHASE_TXN_")) {
            codes.push("STRAT_FROM_PHASE_RISK");
            codes.push("STRAT_EXEC_MODE_SIM_ONLY");
            return { strategy: "RETRY_SAFE_SIM_ONLY", codes: codes };
        }
        // POLICY → wait for unlock (hardstop/env key)
        if (originStopCause === "POLICY" || hasReasonPrefix("RUN_POLICY_")) {
            codes.push("STRAT_FROM_POLICY");
            codes.push("STRAT_WAIT_FOR_UNLOCK");
            return { strategy: "WAIT_FOR_UNLOCK", codes: codes };
        }
        // NONE/unknown → safe default (SIM_ONLY)
        codes.push("STRAT_FROM_UNKNOWN");
        codes.push("STRAT_EXEC_MODE_SIM_ONLY");
        return { strategy: "RETRY_SAFE_SIM_ONLY", codes: codes };
    }
    catch (_a) {
        // Defensive: Never throw, return safe default
        return {
            strategy: "WAIT_FOR_RECOVERY",
            codes: ["STRAT_ERROR"],
        };
    }
}
/**
 * PR214: Derive execution mode override from resume strategy (Enforcement v1)
 *
 * @param resumeStrategy - Resume strategy from PR213
 * @param currentDesiredMode - Current/desired execution mode (optional)
 * @returns Enforced execution mode and reason codes
 *
 * Purpose:
 *   Enforce strategy-driven execution control. Strategy determines safe mode
 *   for resumed execution based on stop cause and risk assessment.
 *
 * Constitutional:
 *   - READ-ONLY: Fixed mapping rules, no learning
 *   - Safety-first: NEVER allow LIVE execution (v1.4 constraint)
 *   - Safe defaults: Cap at DRY_RUN, prefer SIM_ONLY for risky scenarios
 *   - Label-only: All codes are strings
 *   - Deterministic: Same inputs → same outputs
 *
 * Enforcement rules (v1):
 *   1. RETRY_SAFE_SIM_ONLY → enforcedMode = "SIM_ONLY"
 *   2. WAIT_FOR_UNLOCK → enforcedMode = "SIM_ONLY"
 *   3. WAIT_FOR_RECOVERY → enforcedMode = "SIM_ONLY"
 *   4. RETRY_IMMEDIATE → cap at DRY_RUN (never escalate to LIVE)
 *      - If currentDesiredMode = "LIVE" → enforcedMode = "DRY_RUN" (capped)
 *      - If currentDesiredMode = "DRY_RUN" → enforcedMode = "DRY_RUN" (keep)
 *      - Else → enforcedMode = "SIM_ONLY" (safe default)
 *   5. ABANDON → enforcedMode = "SIM_ONLY" (shouldn't re-exec)
 *   6. Unknown → enforcedMode = "SIM_ONLY" (safe default)
 *
 * IMPORTANT: Never throws, always returns enforcement decision
 */
function deriveExecutionModeOverrideFromStrategyV1(resumeStrategy, currentDesiredMode) {
    try {
        var codes = [];
        // Rule 1-3: Safe retry strategies → SIM_ONLY
        if (resumeStrategy === "RETRY_SAFE_SIM_ONLY" ||
            resumeStrategy === "WAIT_FOR_UNLOCK" ||
            resumeStrategy === "WAIT_FOR_RECOVERY") {
            codes.push("STRAT_ENFORCE_EXEC_MODE_SIM_ONLY");
            return { enforcedMode: "SIM_ONLY", enforcedCodes: codes };
        }
        // Rule 4: RETRY_IMMEDIATE → cap at DRY_RUN (never allow LIVE)
        if (resumeStrategy === "RETRY_IMMEDIATE") {
            if (currentDesiredMode === "LIVE") {
                // Cap LIVE down to DRY_RUN (v1.4 safety constraint)
                codes.push("STRAT_ENFORCE_CAPPED_FROM_LIVE");
                codes.push("STRAT_ENFORCE_EXEC_MODE_DRY_RUN");
                return { enforcedMode: "DRY_RUN", enforcedCodes: codes };
            }
            else if (currentDesiredMode === "DRY_RUN") {
                // Keep DRY_RUN (no override needed)
                codes.push("STRAT_ENFORCE_NO_OVERRIDE");
                return { enforcedMode: "DRY_RUN", enforcedCodes: codes };
            }
            else {
                // Default to SIM_ONLY (safe)
                codes.push("STRAT_ENFORCE_EXEC_MODE_SIM_ONLY");
                return { enforcedMode: "SIM_ONLY", enforcedCodes: codes };
            }
        }
        // Rule 5-6: ABANDON or unknown → SIM_ONLY (safe default)
        codes.push("STRAT_ENFORCE_EXEC_MODE_SIM_ONLY");
        return { enforcedMode: "SIM_ONLY", enforcedCodes: codes };
    }
    catch (_a) {
        // Defensive: Never throw, return safe default
        return {
            enforcedMode: "SIM_ONLY",
            enforcedCodes: ["STRAT_ENFORCE_ERROR"],
        };
    }
}
/**
 * PR215: Derive resume re-execution timing from strategy (Timing Control v1)
 *
 * @param resumeStrategy - Resume strategy from PR213
 * @param originStopCause - Origin stop cause from PR209
 * @returns Timing decision with delay class, offset label, and reason codes
 *
 * Purpose:
 *   Determine WHEN to re-execute based on WHY it stopped.
 *   Provides explainable delay/backoff without numeric timestamps.
 *
 * Constitutional:
 *   - READ-ONLY: Fixed delay mapping, no learning
 *   - Label-only: No numeric milliseconds/timestamps
 *   - Deterministic: Same inputs → same outputs
 *   - Scheduler-less v1: Decision only, no actual scheduling
 *
 * Timing mapping rules (v1):
 *   1. TIMEOUT / RETRY_IMMEDIATE → IMMEDIATE + DELAY_0S
 *   2. GATE / PHASE / RETRY_SAFE_SIM_ONLY → BACKOFF_SHORT + DELAY_2M
 *   3. POLICY / WAIT_FOR_UNLOCK → MANUAL + DELAY_1H
 *   4. WAIT_FOR_RECOVERY → BACKOFF_LONG + DELAY_15M
 *   5. ABANDON → MANUAL + DELAY_1H
 *   6. Unknown → BACKOFF_SHORT + DELAY_2M (safe default)
 *
 * IMPORTANT: Never throws, always returns timing decision
 */
function deriveResumeReexecTimingV1(args) {
    try {
        var resumeStrategy = args.resumeStrategy, originStopCause = args.originStopCause;
        var codes = [];
        // Rule 1: TIMEOUT or RETRY_IMMEDIATE → execute immediately
        if (originStopCause === "TIMEOUT" || resumeStrategy === "RETRY_IMMEDIATE") {
            if (originStopCause === "TIMEOUT") {
                codes.push("TIMING_FROM_TIMEOUT");
            }
            codes.push("TIMING_IMMEDIATE");
            codes.push("TIMING_DELAY_0S");
            return {
                delayClass: "IMMEDIATE",
                delayOffsetLabel: "DELAY_0S",
                timingReasonCodes: codes,
            };
        }
        // Rule 2: GATE/PHASE or RETRY_SAFE_SIM_ONLY → short backoff
        if (originStopCause === "GATE" ||
            originStopCause === "PHASE" ||
            resumeStrategy === "RETRY_SAFE_SIM_ONLY") {
            if (originStopCause === "GATE") {
                codes.push("TIMING_FROM_GATE");
            }
            if (originStopCause === "PHASE") {
                codes.push("TIMING_FROM_PHASE");
            }
            codes.push("TIMING_BACKOFF_SHORT");
            codes.push("TIMING_DELAY_2M");
            return {
                delayClass: "BACKOFF_SHORT",
                delayOffsetLabel: "DELAY_2M",
                timingReasonCodes: codes,
            };
        }
        // Rule 3: POLICY or WAIT_FOR_UNLOCK → manual intervention
        if (originStopCause === "POLICY" || resumeStrategy === "WAIT_FOR_UNLOCK") {
            if (originStopCause === "POLICY") {
                codes.push("TIMING_FROM_POLICY");
            }
            codes.push("TIMING_MANUAL");
            codes.push("TIMING_DELAY_1H");
            return {
                delayClass: "MANUAL",
                delayOffsetLabel: "DELAY_1H",
                timingReasonCodes: codes,
            };
        }
        // Rule 4: WAIT_FOR_RECOVERY → long backoff
        if (resumeStrategy === "WAIT_FOR_RECOVERY") {
            codes.push("TIMING_FROM_RECOVERY");
            codes.push("TIMING_BACKOFF_LONG");
            codes.push("TIMING_DELAY_15M");
            return {
                delayClass: "BACKOFF_LONG",
                delayOffsetLabel: "DELAY_15M",
                timingReasonCodes: codes,
            };
        }
        // Rule 5: ABANDON → manual (no re-exec)
        if (resumeStrategy === "ABANDON") {
            codes.push("TIMING_MANUAL");
            codes.push("TIMING_DELAY_1H");
            return {
                delayClass: "MANUAL",
                delayOffsetLabel: "DELAY_1H",
                timingReasonCodes: codes,
            };
        }
        // Rule 6: Unknown → safe default (short backoff)
        codes.push("TIMING_UNKNOWN");
        codes.push("TIMING_BACKOFF_SHORT");
        codes.push("TIMING_DELAY_2M");
        return {
            delayClass: "BACKOFF_SHORT",
            delayOffsetLabel: "DELAY_2M",
            timingReasonCodes: codes,
        };
    }
    catch (_a) {
        // Defensive: Never throw, return safe default
        return {
            delayClass: "BACKOFF_SHORT",
            delayOffsetLabel: "DELAY_2M",
            timingReasonCodes: ["TIMING_ERROR"],
        };
    }
}
/**
 * PR217: Derive orchestrator policy hooks v1 (label-only)
 *
 * Purpose:
 *   Derive execution timing/condition hints from resume context.
 *   Outputs are "constraints/intentions" NOT schedules.
 *   Actual scheduling is orchestrator responsibility.
 *
 * Inputs:
 *   - resumeStrategy (PR213)
 *   - resumeDelayClass (PR215)
 *   - resumeDelayOffsetLabel (PR215)
 *   - originStopCause (PR209)
 *   - policyStatus / unlockStatus (existing labels)
 *
 * Outputs (all label-only):
 *   - orch_policy_class: "NONE" | "DELAY_WINDOW" | "RETRY_LIMIT" | "MARKET_GUARD" | "UNKNOWN"
 *   - orch_not_before: "NB_0S" | "NB_30S" | "NB_2M" | "NB_5M" | "NB_15M" | "NB_1H" | "UNKNOWN"
 *   - orch_deadline: "DL_1M" | "DL_5M" | "DL_15M" | "DL_1H" | "DL_6H" | "DL_24H" | "NONE" | "UNKNOWN"
 *   - orch_retry_limit: "RETRY_0" | "RETRY_1" | "RETRY_3" | "RETRY_5" | "RETRY_10" | "UNKNOWN"
 *   - orch_market_guard: "GUARD_NONE" | "GUARD_ORACLE_OK" | "GUARD_GATE_PASS" | "GUARD_LIQUID_OK" | "UNKNOWN"
 *   - orch_hint_codes: pipe-joined, dedup/sort/truncate(8)
 *
 * Fixed Mapping Rules (v1):
 *   delayClass → orch_policy_class + orch_not_before:
 *     IMMEDIATE → "NONE" + "NB_0S"
 *     BACKOFF_SHORT → "DELAY_WINDOW" + "NB_2M"
 *     BACKOFF_LONG → "DELAY_WINDOW" + "NB_15M"
 *     MANUAL → "DELAY_WINDOW" + "NB_1H"
 *
 *   originStopCause → orch_retry_limit + orch_market_guard:
 *     TIMEOUT → "RETRY_3" + "GUARD_ORACLE_OK"
 *     GATE → "RETRY_5" + "GUARD_GATE_PASS"
 *     POLICY → "RETRY_0" + "GUARD_NONE"
 *     PHASE → "RETRY_3" + "GUARD_GATE_PASS"
 *     NONE → "RETRY_3" + "GUARD_ORACLE_OK"
 *
 *   deadline: v1 = "DL_1H" (simple default, refinement in v2+)
 *
 * IMPORTANT: Never throws, always returns hooks decision
 */
function deriveOrchPolicyHooksV1(args) {
    try {
        var resumeDelayClass = args.resumeDelayClass, resumeDelayOffsetLabel = args.resumeDelayOffsetLabel, originStopCause = args.originStopCause;
        var codes = [];
        // Derive orch_policy_class and orch_not_before from delayClass
        var policyClass = "DELAY_WINDOW";
        var notBefore = "NB_2M";
        if (resumeDelayClass === "IMMEDIATE") {
            policyClass = "NONE";
            notBefore = "NB_0S";
            codes.push("HINT_DELAY_IMMEDIATE");
        }
        else if (resumeDelayClass === "BACKOFF_SHORT") {
            policyClass = "DELAY_WINDOW";
            notBefore = "NB_2M";
            codes.push("HINT_DELAY_BACKOFF_SHORT");
        }
        else if (resumeDelayClass === "BACKOFF_LONG") {
            policyClass = "DELAY_WINDOW";
            notBefore = "NB_15M";
            codes.push("HINT_DELAY_BACKOFF_LONG");
        }
        else if (resumeDelayClass === "MANUAL") {
            policyClass = "DELAY_WINDOW";
            notBefore = "NB_1H";
            codes.push("HINT_DELAY_MANUAL");
        }
        else {
            // Unknown/undefined → safe default
            policyClass = "DELAY_WINDOW";
            notBefore = "NB_2M";
            codes.push("HINT_DELAY_UNKNOWN");
        }
        // Derive orch_retry_limit and orch_market_guard from originStopCause
        var retryLimit = "RETRY_3";
        var marketGuard = "GUARD_ORACLE_OK";
        if (originStopCause === "TIMEOUT") {
            retryLimit = "RETRY_3";
            marketGuard = "GUARD_ORACLE_OK";
            codes.push("HINT_FROM_TIMEOUT");
            codes.push("HINT_RETRY_LIMIT_3");
            codes.push("HINT_GUARD_ORACLE_OK");
        }
        else if (originStopCause === "GATE") {
            retryLimit = "RETRY_5";
            marketGuard = "GUARD_GATE_PASS";
            codes.push("HINT_FROM_GATE");
            codes.push("HINT_RETRY_LIMIT_5");
            codes.push("HINT_GUARD_GATE_PASS");
        }
        else if (originStopCause === "POLICY") {
            retryLimit = "RETRY_0";
            marketGuard = "GUARD_NONE";
            codes.push("HINT_FROM_POLICY");
            codes.push("HINT_RETRY_LIMIT_0");
            codes.push("HINT_GUARD_NONE");
        }
        else if (originStopCause === "PHASE") {
            retryLimit = "RETRY_3";
            marketGuard = "GUARD_GATE_PASS";
            codes.push("HINT_FROM_PHASE");
            codes.push("HINT_RETRY_LIMIT_3");
            codes.push("HINT_GUARD_GATE_PASS");
        }
        else {
            // NONE or unknown → safe default
            retryLimit = "RETRY_3";
            marketGuard = "GUARD_ORACLE_OK";
            codes.push("HINT_FROM_UNKNOWN");
            codes.push("HINT_RETRY_LIMIT_3");
            codes.push("HINT_GUARD_ORACLE_OK");
        }
        // Deadline: v1 = simple default (refinement in v2+)
        var deadline = "DL_1H";
        codes.push("HINT_DEADLINE_1H");
        // Process hint codes: dedup, sort, truncate to 8
        var uniqueCodes = Array.from(new Set(codes)).sort();
        var truncated = uniqueCodes.slice(0, 8);
        if (uniqueCodes.length > 8) {
            truncated.push("REASONS_TRUNCATED");
        }
        var hintCodesJoined = truncated.join("|");
        var hintCodesStatus = truncated.length > 0 ? "PRESENT" : "EMPTY";
        return {
            orch_policy_class: policyClass,
            orch_not_before: notBefore,
            orch_deadline: deadline,
            orch_retry_limit: retryLimit,
            orch_market_guard: marketGuard,
            orch_hint_codes_status: hintCodesStatus,
            orch_hint_codes: hintCodesJoined,
        };
    }
    catch (_a) {
        // Defensive: Never throw, return safe default
        return {
            orch_policy_class: "UNKNOWN",
            orch_not_before: "UNKNOWN",
            orch_deadline: "UNKNOWN",
            orch_retry_limit: "UNKNOWN",
            orch_market_guard: "UNKNOWN",
            orch_hint_codes_status: "EMPTY",
            orch_hint_codes: "",
        };
    }
}
/**
 * PR219: Derive resume strategy escalation from orchestrator feedback v1
 *
 * @param args - Escalation inputs
 * @returns Escalated strategy and reason codes
 *
 * Purpose:
 *   Use PR218 orchestrator feedback (orchLastStatus / orchLastOutcomeCodes)
 *   to deterministically escalate/de-escalate the next resume strategy.
 *
 * Constitutional:
 *   - READ-ONLY: Rule-based, no learning
 *   - Label-only: No numeric durations/counters
 *   - Safety-first: Never escalate to LIVE
 *   - Defensive: Never throws, handles unknown inputs gracefully
 *   - Deterministic: Same inputs → same outputs (sorted codes)
 *
 * Rules (v1):
 *   - SKIPPED_POLICY → WAIT_FOR_UNLOCK (policy says no)
 *   - SKIPPED_WINDOW → WAIT_FOR_RECOVERY (window not satisfied)
 *   - FAILED_MARKET → WAIT_FOR_RECOVERY (market says unsafe)
 *   - FAILED_NETWORK → RETRY_SAFE_SIM_ONLY (de-risk)
 *   - SUCCEEDED → RETRY_IMMEDIATE (success → immediate)
 *   - Unknown/missing → no change (keep baseStrategy)
 */
function deriveResumeEscalationV1(args) {
    try {
        var baseStrategy = args.baseStrategy, orchLastStatus = args.orchLastStatus, orchLastOutcomeCodes = args.orchLastOutcomeCodes;
        var codes = [];
        // Always include marker code
        codes.push("STRAT_ESC_APPLIED_V1");
        // Defensive: Normalize outcome codes to string array
        var normalizedOutcomeCodes_1 = [];
        if (Array.isArray(orchLastOutcomeCodes)) {
            for (var _i = 0, orchLastOutcomeCodes_1 = orchLastOutcomeCodes; _i < orchLastOutcomeCodes_1.length; _i++) {
                var code = orchLastOutcomeCodes_1[_i];
                if (typeof code === "string") {
                    normalizedOutcomeCodes_1.push(code);
                }
            }
        }
        // Helper: check if outcome codes contain prefix
        var hasOutcomePrefix = function (prefix) {
            return normalizedOutcomeCodes_1.some(function (code) { return code.includes(prefix); });
        };
        // Rule A: SKIPPED_POLICY → WAIT_FOR_UNLOCK
        if (orchLastStatus === "SKIPPED_POLICY" ||
            hasOutcomePrefix("ORCH_POLICY_")) {
            codes.push("STRAT_ESC_FROM_ORCH_STATUS_SKIPPED_POLICY");
            codes.push("STRAT_ESC_TO_WAIT_FOR_UNLOCK");
            return { strategy: "WAIT_FOR_UNLOCK", codes: codes.sort() };
        }
        // Rule B: SKIPPED_WINDOW → WAIT_FOR_RECOVERY
        if (orchLastStatus === "SKIPPED_WINDOW" ||
            hasOutcomePrefix("ORCH_NOT_BEFORE_ACTIVE") ||
            hasOutcomePrefix("ORCH_DEADLINE_EXCEEDED")) {
            codes.push("STRAT_ESC_FROM_ORCH_STATUS_SKIPPED_WINDOW");
            codes.push("STRAT_ESC_TO_WAIT_FOR_RECOVERY");
            return { strategy: "WAIT_FOR_RECOVERY", codes: codes.sort() };
        }
        // Rule C: FAILED_MARKET → WAIT_FOR_RECOVERY
        if (orchLastStatus === "FAILED_MARKET") {
            codes.push("STRAT_ESC_FROM_ORCH_STATUS_FAILED_MARKET");
            codes.push("STRAT_ESC_TO_WAIT_FOR_RECOVERY");
            return { strategy: "WAIT_FOR_RECOVERY", codes: codes.sort() };
        }
        // Rule D: FAILED_NETWORK → RETRY_SAFE_SIM_ONLY (de-risk)
        if (orchLastStatus === "FAILED_NETWORK") {
            codes.push("STRAT_ESC_FROM_ORCH_STATUS_FAILED_NETWORK");
            codes.push("STRAT_ESC_TO_RETRY_SAFE_SIM_ONLY");
            return { strategy: "RETRY_SAFE_SIM_ONLY", codes: codes.sort() };
        }
        // Rule E: SUCCEEDED → RETRY_IMMEDIATE (with PR225 consecutive success gating)
        if (orchLastStatus === "SUCCEEDED") {
            // PR225: Use the updated success count from supervisor (already incremented)
            var successCount = args.consecutiveSuccesses || 0;
            // PR225: Require 2 consecutive successes before escalating to IMMEDIATE
            if (successCount >= 2) {
                codes.push("STRAT_ESC_FROM_ORCH_STATUS_SUCCEEDED");
                codes.push("STRAT_ESC_TO_RETRY_IMMEDIATE");
                codes.push("STRAT_ESC_CONSECUTIVE_SUCCESS_GATE_PASS");
                return { strategy: "RETRY_IMMEDIATE", codes: codes.sort() };
            }
            else {
                // First success, wait for confirmation (keep baseStrategy)
                codes.push("STRAT_ESC_FROM_ORCH_STATUS_SUCCEEDED");
                codes.push("STRAT_ESC_CONSECUTIVE_SUCCESS_GATE_WAIT");
                return { strategy: baseStrategy, codes: codes.sort() };
            }
        }
        // Rule F: No orch feedback or unknown status → keep baseStrategy
        if (!orchLastStatus || orchLastStatus === "UNKNOWN") {
            codes.push("STRAT_ESC_NO_CHANGE_NO_ORCH_FEEDBACK");
            return { strategy: baseStrategy, codes: codes.sort() };
        }
        // Other statuses (DISPATCHED, FAILED_UNKNOWN, etc.) → keep baseStrategy
        codes.push("STRAT_ESC_NO_CHANGE_ORCH_STATUS_" + orchLastStatus);
        return { strategy: baseStrategy, codes: codes.sort() };
    }
    catch (_a) {
        // Defensive: Never throw, return safe default (keep baseStrategy)
        return {
            strategy: args.baseStrategy || "WAIT_FOR_RECOVERY",
            codes: ["STRAT_ESC_ERROR"],
        };
    }
}
/**
 * PR220: Summarize market regime codes (label-only)
 *
 * @param codes - Array of regime codes
 * @param maxCodes - Maximum codes to include (default: 8)
 * @returns Summary object with status and joined string
 *
 * Constitutional:
 *   - Defensive: Handles undefined/non-string values
 *   - Deterministic: Dedup via Set, sort alphabetically
 *   - Label-only: No numeric values, all strings
 */
function summarizeMarketRegimeCodesV1(codes, maxCodes) {
    if (maxCodes === void 0) { maxCodes = 8; }
    try {
        if (!codes || codes.length === 0) {
            return { status: "EMPTY", joined: "" };
        }
        // Filter to strings only (defensive)
        var stringCodes = [];
        for (var _i = 0, codes_1 = codes; _i < codes_1.length; _i++) {
            var code = codes_1[_i];
            if (typeof code === "string") {
                stringCodes.push(code);
            }
        }
        if (stringCodes.length === 0) {
            return { status: "EMPTY", joined: "" };
        }
        // Dedup via Set, sort alphabetically (deterministic)
        var uniqueCodes = Array.from(new Set(stringCodes)).sort();
        // Truncate to maxCodes
        var truncated = uniqueCodes.slice(0, maxCodes);
        if (uniqueCodes.length > maxCodes) {
            truncated.push("REASONS_TRUNCATED");
        }
        // Join with pipe separator
        var joined = truncated.join("|");
        return { status: "PRESENT", joined: joined };
    }
    catch (_a) {
        // Defensive: Never throw
        return { status: "EMPTY", joined: "" };
    }
}
/**
 * PR220: Derive market regime from signals v1
 *
 * @param signals - Label-only market signals
 * @returns Regime classification and reason codes
 *
 * Purpose:
 *   Classify market conditions to inform strategy/timing decisions.
 *   Enables regime-aware recovery without numeric calculations.
 *
 * Constitutional:
 *   - READ-ONLY: Derived from signals, no learning
 *   - Label-only: No BPS/prices/numeric thresholds
 *   - Deterministic: Same signals → same regime
 *   - Defensive: Handles missing/unknown signals gracefully
 *   - Safety-first: Uncertain signals → conservative regimes
 *
 * Rules (v1, hierarchical precedence):
 *   1. Oracle issues → REGIME_ORACLE_UNCERTAIN
 *   2. Liquidity issues → REGIME_ILLIQUID
 *   3. Volatility signals → REGIME_VOLATILE
 *   4. Network issues → REGIME_NETWORK_UNSTABLE
 *   5. Insufficient signals → REGIME_UNKNOWN
 *   6. Otherwise → REGIME_NORMAL
 */
function deriveMarketRegimeV1(signals) {
    try {
        var codes = [];
        // Rule 1: Oracle issues (highest priority - affects all pricing)
        if (signals.oracle_status === "ORACLE_UNAVAILABLE" ||
            signals.oracle_status === "ORACLE_STALE") {
            codes.push("REGIME_BY_ORACLE_UNCERTAIN");
            return { regime: "REGIME_ORACLE_UNCERTAIN", codes: codes.sort() };
        }
        // Rule 2: Liquidity issues (depth or quote unavailable)
        if (signals.gate_depth_status === "DEPTH_THIN" ||
            signals.gate_depth_status === "DEPTH_UNAVAILABLE" ||
            signals.quote_status === "QUOTE_UNAVAILABLE" ||
            signals.quote_status === "QUOTE_STALE") {
            codes.push("REGIME_BY_LIQUIDITY_THIN");
            return { regime: "REGIME_ILLIQUID", codes: codes.sort() };
        }
        // Rule 3: Volatility (phase shock or gate block)
        if (signals.phase_label === "PHASE_DOWN_SHOCK" ||
            signals.phase_label === "PHASE_UP_REVERSAL" ||
            signals.gate_status === "BLOCK") {
            codes.push("REGIME_BY_VOLATILITY");
            return { regime: "REGIME_VOLATILE", codes: codes.sort() };
        }
        // Rule 4: Network issues
        if (signals.network_status === "NET_DEGRADED" ||
            signals.network_status === "NET_FAIL") {
            codes.push("REGIME_BY_NETWORK");
            return { regime: "REGIME_NETWORK_UNSTABLE", codes: codes.sort() };
        }
        // Rule 5: Check if we have sufficient signals to classify as NORMAL
        // Just check for presence, not specific values (defensive)
        var hasOracleSignal = signals.oracle_status !== undefined;
        var hasGateSignal = signals.gate_status !== undefined;
        var hasNetworkSignal = signals.network_status !== undefined;
        if (!hasOracleSignal && !hasGateSignal && !hasNetworkSignal) {
            codes.push("REGIME_BY_UNKNOWN");
            return { regime: "REGIME_UNKNOWN", codes: codes.sort() };
        }
        // Rule 6: Normal conditions (all signals nominal or at least no red flags)
        codes.push("REGIME_BY_NORMAL");
        return { regime: "REGIME_NORMAL", codes: codes.sort() };
    }
    catch (_a) {
        // Defensive: Never throw, return safe default
        return { regime: "REGIME_UNKNOWN", codes: ["REGIME_ERROR"] };
    }
}
/**
 * PR224: Confirm regime change with hysteresis (2-tick confirmation)
 *
 * @param instantRegime - Instant regime from current signals
 * @param priorRegime - Last confirmed regime (from previous tick)
 * @param regimeHistory - Last N instant regimes (circular buffer)
 * @returns Confirmed regime and hysteresis codes
 *
 * Purpose:
 *   Prevent regime oscillation from transient signal flaps.
 *   Require regime to be stable for 2 consecutive ticks before changing.
 *
 * Constitutional:
 *   - READ-ONLY: Fixed hysteresis rules, no learning
 *   - Label-only: All codes are strings
 *   - Deterministic: Same history → same output
 *   - Defensive: Never throws, handles undefined gracefully
 *
 * Rules:
 *   1. No prior OR no change → use instant regime (NO_CHANGE)
 *   2. Regime changed:
 *      - If last instant regime in history equals current instant → CONFIRMED change
 *      - Else → HOLD prior regime (wait for confirmation)
 */
function confirmRegimeChangeV1(instantRegime, priorRegime, regimeHistory) {
    try {
        var codes = [];
        // Rule 1: First read or no change → use instant regime
        if (!priorRegime || instantRegime === priorRegime) {
            codes.push("REGIME_HYSTERESIS_NO_CHANGE");
            return { regime: instantRegime, codes: codes };
        }
        // Rule 2: Regime changed - check if confirmed by history
        // Defensive: Check if regimeHistory has entries
        if (!regimeHistory || regimeHistory.length === 0) {
            // No history, treat as first change (tentative, hold prior)
            codes.push("REGIME_HYSTERESIS_HOLD");
            return { regime: priorRegime, codes: codes };
        }
        var lastInstantRegime = regimeHistory[regimeHistory.length - 1];
        if (lastInstantRegime === instantRegime) {
            // 2 consecutive ticks with same new regime → confirmed change
            codes.push("REGIME_HYSTERESIS_CONFIRMED");
            return { regime: instantRegime, codes: codes };
        }
        else {
            // Tentative change, wait for confirmation (hold prior)
            codes.push("REGIME_HYSTERESIS_HOLD");
            return { regime: priorRegime, codes: codes };
        }
    }
    catch (_a) {
        // Defensive: Never throw, return safe default (use instant regime)
        return { regime: instantRegime, codes: ["REGIME_HYSTERESIS_ERROR"] };
    }
}
/**
 * PR220: Derive resume strategy from regime × escalation matrix v1
 *
 * @param args - Matrix inputs
 * @returns Final strategy after regime overlay and reason codes
 *
 * Purpose:
 *   Apply regime-aware overlays to escalated strategy for safer autonomous recovery.
 *   Ensures strategy selection respects market conditions.
 *
 * Constitutional:
 *   - READ-ONLY: Fixed overlay rules, no learning
 *   - Label-only: No numeric values
 *   - Safety-first: Regimes force conservative overlays
 *   - Defensive: Handles missing inputs gracefully
 *   - Deterministic: Same inputs → same outputs (codes sorted)
 *
 * Matrix Rules (v1, regime overlays applied after escalation):
 *   1. REGIME_ORACLE_UNCERTAIN / REGIME_ILLIQUID → Force WAIT_FOR_RECOVERY
 *   2. REGIME_VOLATILE → Force RETRY_SAFE_SIM_ONLY
 *   3. REGIME_NETWORK_UNSTABLE → De-risk RETRY_IMMEDIATE to RETRY_SAFE_SIM_ONLY
 *   4. REGIME_NORMAL → Keep baseStrategy
 *   5. REGIME_UNKNOWN → Safe default (de-risk RETRY_IMMEDIATE)
 *
 * Note: baseStrategy comes from PR219 escalation output
 */
function deriveResumeStrategyFromMatrixV1(args) {
    try {
        var baseStrategy = args.baseStrategy, regime = args.regime;
        var codes = [];
        // Always include marker code
        codes.push("MATRIX_APPLIED_V1");
        // Rule 1: Oracle uncertain or illiquid → Force WAIT_FOR_RECOVERY
        if (regime === "REGIME_ORACLE_UNCERTAIN" || regime === "REGIME_ILLIQUID") {
            codes.push("MATRIX_FORCE_WAIT_RECOVERY");
            return { strategy: "WAIT_FOR_RECOVERY", codes: codes.sort() };
        }
        // Rule 2: Volatile → Force RETRY_SAFE_SIM_ONLY
        if (regime === "REGIME_VOLATILE") {
            codes.push("MATRIX_FORCE_SIM_ONLY_VOLATILE");
            return { strategy: "RETRY_SAFE_SIM_ONLY", codes: codes.sort() };
        }
        // Rule 3: Network unstable → De-risk RETRY_IMMEDIATE
        if (regime === "REGIME_NETWORK_UNSTABLE") {
            if (baseStrategy === "RETRY_IMMEDIATE") {
                codes.push("MATRIX_DERISK_NETWORK");
                return { strategy: "RETRY_SAFE_SIM_ONLY", codes: codes.sort() };
            }
            else {
                codes.push("MATRIX_KEEP_BASE_NETWORK");
                return { strategy: baseStrategy, codes: codes.sort() };
            }
        }
        // Rule 4: Normal → Keep baseStrategy
        if (regime === "REGIME_NORMAL") {
            codes.push("MATRIX_KEEP_BASE");
            return { strategy: baseStrategy, codes: codes.sort() };
        }
        // Rule 5: Unknown → Safe default (de-risk RETRY_IMMEDIATE)
        if (!regime || regime === "REGIME_UNKNOWN") {
            if (baseStrategy === "RETRY_IMMEDIATE") {
                codes.push("MATRIX_SAFE_DEFAULT_UNKNOWN");
                return { strategy: "RETRY_SAFE_SIM_ONLY", codes: codes.sort() };
            }
            else {
                codes.push("MATRIX_KEEP_BASE_UNKNOWN");
                return { strategy: baseStrategy, codes: codes.sort() };
            }
        }
        // Default: Keep baseStrategy (defensive fallback)
        codes.push("MATRIX_KEEP_BASE_FALLBACK");
        return { strategy: baseStrategy, codes: codes.sort() };
    }
    catch (_a) {
        // Defensive: Never throw, return safe default
        return {
            strategy: args.baseStrategy || "WAIT_FOR_RECOVERY",
            codes: ["MATRIX_ERROR"],
        };
    }
}
/**
 * PR228: Classify oscillation change count into label-only class
 *
 * @param count - Internal change count (never emitted as raw number)
 * @returns Label class: CHG_LOW|CHG_MEDIUM|CHG_HIGH|CHG_EXCEEDED|CHG_UNKNOWN
 *
 * Constitutional:
 *   - Label-only: Never emit raw count
 *   - Deterministic: Same count → same class
 *   - Defensive: Handles undefined
 */
function classifyOscillationChangeLevelV1(count) {
    try {
        if (count === undefined || count === null) {
            return "CHG_UNKNOWN";
        }
        if (count >= 11) {
            return "CHG_EXCEEDED"; // Over threshold (>10)
        }
        else if (count >= 7) {
            return "CHG_HIGH"; // 7-10
        }
        else if (count >= 3) {
            return "CHG_MEDIUM"; // 3-6
        }
        else {
            return "CHG_LOW"; // 0-2
        }
    }
    catch (_a) {
        return "CHG_UNKNOWN";
    }
}
/**
 * PR228: Determine oscillation window status (fresh vs reset)
 *
 * @param lastChangeTs - Timestamp of last change (ms)
 * @param nowMs - Current timestamp (ms)
 * @returns WINDOW_FRESH | WINDOW_RESET | WINDOW_UNKNOWN
 *
 * Constitutional:
 *   - Label-only: No numeric timestamps emitted
 *   - Deterministic: Same inputs → same output
 */
function classifyOscillationWindowStatusV1(lastChangeTs, nowMs) {
    try {
        if (!lastChangeTs) {
            return "WINDOW_UNKNOWN";
        }
        var HOUR_MS = 60 * 60 * 1000;
        var ageMs = nowMs - lastChangeTs;
        if (ageMs > HOUR_MS) {
            return "WINDOW_RESET"; // Outside 1-hour window, will reset on next change
        }
        else {
            return "WINDOW_FRESH"; // Within 1-hour window
        }
    }
    catch (_a) {
        return "WINDOW_UNKNOWN";
    }
}
/**
 * PR228: Summarize code array into status + joined string
 *
 * @param codes - Array of code strings
 * @returns {status: PRESENT|EMPTY, joined: pipe-separated string}
 *
 * Constitutional:
 *   - Defensive: Never throws
 *   - Deterministic: Dedup, sort, truncate(8)
 */
function summarizeCodeArrayV1(codes) {
    try {
        if (!codes || codes.length === 0) {
            return { status: "EMPTY", joined: "" };
        }
        // Defensive: filter non-strings
        var validCodes = codes.filter(function (c) { return typeof c === "string" && c.length > 0; });
        if (validCodes.length === 0) {
            return { status: "EMPTY", joined: "" };
        }
        // Dedup + sort
        var uniqueCodes = Array.from(new Set(validCodes)).sort();
        // Truncate to 8
        var truncated = uniqueCodes.length > 8
            ? __spreadArray(__spreadArray([], uniqueCodes.slice(0, 8), true), ["REASONS_TRUNCATED"], false) : uniqueCodes;
        return { status: "PRESENT", joined: truncated.join("|") };
    }
    catch (_a) {
        return { status: "EMPTY", joined: "" };
    }
}
/**
 * PR229: Derive Recovery Budget Decision v1 (暴走防止)
 *
 * Purpose:
 *   Enforce budget rules to prevent autonomous recovery from running away.
 *   Rules (in priority order):
 *     1. Attempt limit: >=10 attempts → ABANDON
 *     2. Oscillation cooldown: CHG_EXCEEDED → DEFER BACKOFF_LONG
 *     3. FAILED_MARKET cap: >=2/hour → DEFER MANUAL
 *     4. IMMEDIATE rate limit: >=3/hour → DEFER BACKOFF_LONG
 *
 * Constitutional:
 *   - READ-ONLY: Fixed rules, no learning
 *   - Label-only: Budget status classes (B0/B1/B2, R0/R1/R2, etc.)
 *   - Deterministic: Same inputs → same decision
 *   - Defensive: Never throws, handles malformed state
 *
 * @param args - Budget decision inputs
 * @returns Budget decision with action, codes, and status labels
 */
function deriveRecoveryBudgetDecisionV1(args) {
    var _a, _b, _c, _d, _e, _f, _g, _h;
    var codes = [];
    try {
        // Constants (constitutional READ-ONLY)
        var MAX_RECOVERY_ATTEMPTS = 10;
        var MAX_IMMEDIATE_PER_1H = 3;
        var FAILED_MARKET_PER_1H_MAX = 2;
        var HOUR_MS = 60 * 60 * 1000;
        // Extract budget tracking fields (defensive)
        var attemptCount = (_b = (_a = args.resumeState) === null || _a === void 0 ? void 0 : _a.recoveryAttemptCount) !== null && _b !== void 0 ? _b : 0;
        var windowAnchorTs = (_d = (_c = args.resumeState) === null || _c === void 0 ? void 0 : _c.recoveryWindowAnchorTs) !== null && _d !== void 0 ? _d : 0;
        var immediateCountInWindow = (_f = (_e = args.resumeState) === null || _e === void 0 ? void 0 : _e.recoveryImmediateCountInWindow) !== null && _f !== void 0 ? _f : 0;
        var failedMarketCountInWindow = (_h = (_g = args.resumeState) === null || _g === void 0 ? void 0 : _g.recoveryFailedMarketCountInWindow) !== null && _h !== void 0 ? _h : 0;
        // Classify attempt budget status
        var budgetAttemptStatus = "B_UNKNOWN";
        if (attemptCount >= MAX_RECOVERY_ATTEMPTS) {
            budgetAttemptStatus = "B2_LIMIT_EXCEEDED";
        }
        else if (attemptCount >= MAX_RECOVERY_ATTEMPTS - 2) {
            budgetAttemptStatus = "B1_NEAR_LIMIT";
        }
        else {
            budgetAttemptStatus = "B0_OK";
        }
        // Classify IMMEDIATE rate status (within window)
        var budgetImmediateRateStatus = "R_UNKNOWN";
        var windowAge = windowAnchorTs > 0 ? args.nowMs - windowAnchorTs : HOUR_MS + 1;
        var windowActive = windowAge <= HOUR_MS;
        if (windowActive) {
            if (immediateCountInWindow >= MAX_IMMEDIATE_PER_1H) {
                budgetImmediateRateStatus = "R2_LIMIT_EXCEEDED";
            }
            else if (immediateCountInWindow >= MAX_IMMEDIATE_PER_1H - 1) {
                budgetImmediateRateStatus = "R1_NEAR_LIMIT";
            }
            else {
                budgetImmediateRateStatus = "R0_OK";
            }
        }
        else {
            budgetImmediateRateStatus = "R0_OK"; // Window expired, reset counts
        }
        // Classify FAILED_MARKET rate status (within window)
        var budgetFailedMarketRateStatus = "F_UNKNOWN";
        if (windowActive) {
            if (failedMarketCountInWindow >= FAILED_MARKET_PER_1H_MAX) {
                budgetFailedMarketRateStatus = "F2_LIMIT_EXCEEDED";
            }
            else if (failedMarketCountInWindow >= FAILED_MARKET_PER_1H_MAX - 1) {
                budgetFailedMarketRateStatus = "F1_NEAR_LIMIT";
            }
            else {
                budgetFailedMarketRateStatus = "F0_OK";
            }
        }
        else {
            budgetFailedMarketRateStatus = "F0_OK"; // Window expired
        }
        // Classify oscillation cooldown status
        var budgetOscCooldownStatus = "C_UNKNOWN";
        if (args.oscChangeLevelStrategy === "CHG_EXCEEDED" || args.oscChangeLevelRegime === "CHG_EXCEEDED") {
            budgetOscCooldownStatus = "C1_COOLDOWN_ACTIVE";
        }
        else {
            budgetOscCooldownStatus = "C0_OK";
        }
        // Rule 1: Attempt limit (>=10 → ABANDON)
        if (attemptCount >= MAX_RECOVERY_ATTEMPTS) {
            codes.push("BUDGET_ABANDON_ATTEMPT_LIMIT_EXCEEDED");
            codes.push("BUDGET_ATTEMPT_COUNT_".concat(attemptCount));
            return {
                action: "ABANDON",
                codes: codes,
                budgetAttemptStatus: budgetAttemptStatus,
                budgetImmediateRateStatus: budgetImmediateRateStatus,
                budgetFailedMarketRateStatus: budgetFailedMarketRateStatus,
                budgetOscCooldownStatus: budgetOscCooldownStatus,
            };
        }
        // Rule 2: Oscillation cooldown (CHG_EXCEEDED → DEFER BACKOFF_LONG)
        if (budgetOscCooldownStatus === "C1_COOLDOWN_ACTIVE") {
            codes.push("BUDGET_DEFER_OSC_COOLDOWN");
            codes.push("BUDGET_OSC_STRATEGY_".concat(args.oscChangeLevelStrategy));
            codes.push("BUDGET_OSC_REGIME_".concat(args.oscChangeLevelRegime));
            return {
                action: "DEFER",
                overrideDelayClass: "BACKOFF_LONG",
                overrideDelayOffsetLabel: "DELAY_15M",
                codes: codes,
                budgetAttemptStatus: budgetAttemptStatus,
                budgetImmediateRateStatus: budgetImmediateRateStatus,
                budgetFailedMarketRateStatus: budgetFailedMarketRateStatus,
                budgetOscCooldownStatus: budgetOscCooldownStatus,
            };
        }
        // Rule 3: FAILED_MARKET cap (>=2/hour → DEFER MANUAL)
        if (budgetFailedMarketRateStatus === "F2_LIMIT_EXCEEDED") {
            codes.push("BUDGET_DEFER_FAILED_MARKET_CAP");
            codes.push("BUDGET_FAILED_MARKET_COUNT_".concat(failedMarketCountInWindow));
            return {
                action: "DEFER",
                overrideDelayClass: "MANUAL",
                overrideDelayOffsetLabel: "DELAY_1H",
                codes: codes,
                budgetAttemptStatus: budgetAttemptStatus,
                budgetImmediateRateStatus: budgetImmediateRateStatus,
                budgetFailedMarketRateStatus: budgetFailedMarketRateStatus,
                budgetOscCooldownStatus: budgetOscCooldownStatus,
            };
        }
        // Rule 4: IMMEDIATE rate limit (>=3/hour → DEFER BACKOFF_LONG)
        if (budgetImmediateRateStatus === "R2_LIMIT_EXCEEDED" &&
            args.desiredDelayClass === "IMMEDIATE") {
            codes.push("BUDGET_DEFER_IMMEDIATE_RATE_LIMIT");
            codes.push("BUDGET_IMMEDIATE_COUNT_".concat(immediateCountInWindow));
            return {
                action: "DEFER",
                overrideDelayClass: "BACKOFF_LONG",
                overrideDelayOffsetLabel: "DELAY_15M",
                codes: codes,
                budgetAttemptStatus: budgetAttemptStatus,
                budgetImmediateRateStatus: budgetImmediateRateStatus,
                budgetFailedMarketRateStatus: budgetFailedMarketRateStatus,
                budgetOscCooldownStatus: budgetOscCooldownStatus,
            };
        }
        // All budget checks passed → ALLOW
        codes.push("BUDGET_ALLOW_ALL_OK");
        if (budgetAttemptStatus === "B1_NEAR_LIMIT") {
            codes.push("BUDGET_WARN_ATTEMPT_NEAR_LIMIT");
        }
        if (budgetImmediateRateStatus === "R1_NEAR_LIMIT") {
            codes.push("BUDGET_WARN_IMMEDIATE_NEAR_LIMIT");
        }
        if (budgetFailedMarketRateStatus === "F1_NEAR_LIMIT") {
            codes.push("BUDGET_WARN_FAILED_MARKET_NEAR_LIMIT");
        }
        return {
            action: "ALLOW",
            codes: codes,
            budgetAttemptStatus: budgetAttemptStatus,
            budgetImmediateRateStatus: budgetImmediateRateStatus,
            budgetFailedMarketRateStatus: budgetFailedMarketRateStatus,
            budgetOscCooldownStatus: budgetOscCooldownStatus,
        };
    }
    catch (err) {
        // Defensive: Budget evaluation error → DEFER MANUAL (safe default)
        codes.push("BUDGET_ERROR_EVALUATION_FAILED");
        codes.push("BUDGET_ERROR_".concat(String(err).substring(0, 50)));
        return {
            action: "DEFER",
            overrideDelayClass: "MANUAL",
            overrideDelayOffsetLabel: "DELAY_1H",
            codes: codes,
            budgetAttemptStatus: "B_UNKNOWN",
            budgetImmediateRateStatus: "R_UNKNOWN",
            budgetFailedMarketRateStatus: "F_UNKNOWN",
            budgetOscCooldownStatus: "C_UNKNOWN",
        };
    }
}
/**
 * PR226: Detect strategy/regime oscillation (telemetry only)
 *
 * @param args - Oscillation detection inputs
 * @returns Warnings and codes (does NOT change decisions)
 *
 * Purpose:
 *   Emit warning telemetry if strategy/regime changes >10 times/hour.
 *   Helps operators detect flapping signals or policy issues.
 *
 * Constitutional:
 *   - READ-ONLY: Detection only, no intervention
 *   - Label-only: Counts converted to classes (not emitted as raw numbers)
 *   - Defensive: Never throws, handles undefined
 *   - Deterministic: Same inputs → same outputs
 *
 * Logic:
 *   - Track changes within 1-hour rolling window
 *   - Threshold: >10 changes/hour triggers warning
 *   - Reset counter if >1h since last change
 */
function detectOscillationV1(args) {
    try {
        var resumeState = args.resumeState, currentStrategy = args.currentStrategy, currentRegime = args.currentRegime, nowMs = args.nowMs;
        var warnings = [];
        var codes = [];
        var HOUR_MS = 60 * 60 * 1000;
        var OSCILLATION_THRESHOLD = 10;
        // Strategy oscillation check
        if (resumeState.lastObservedStrategy &&
            resumeState.lastObservedStrategy !== currentStrategy) {
            // Strategy changed
            var timeSinceLastChange = resumeState.lastStrategyChangeTs
                ? nowMs - resumeState.lastStrategyChangeTs
                : HOUR_MS + 1;
            if (timeSinceLastChange > HOUR_MS) {
                // Reset counter (new hour window)
                resumeState.strategyChangeCount = 1;
            }
            else {
                // Increment counter
                resumeState.strategyChangeCount = (resumeState.strategyChangeCount || 0) + 1;
                if (resumeState.strategyChangeCount > OSCILLATION_THRESHOLD) {
                    warnings.push("WARN_STRATEGY_OSCILLATION_DETECTED");
                    codes.push("OSC_STRATEGY_OVER_THRESHOLD");
                }
            }
            resumeState.lastStrategyChangeTs = nowMs;
        }
        // Regime oscillation check
        if (resumeState.lastObservedRegime && resumeState.lastObservedRegime !== currentRegime) {
            // Regime changed
            var timeSinceLastChange = resumeState.lastRegimeChangeTs
                ? nowMs - resumeState.lastRegimeChangeTs
                : HOUR_MS + 1;
            if (timeSinceLastChange > HOUR_MS) {
                // Reset counter (new hour window)
                resumeState.regimeChangeCount = 1;
            }
            else {
                // Increment counter
                resumeState.regimeChangeCount = (resumeState.regimeChangeCount || 0) + 1;
                if (resumeState.regimeChangeCount > OSCILLATION_THRESHOLD) {
                    warnings.push("WARN_REGIME_OSCILLATION_DETECTED");
                    codes.push("OSC_REGIME_OVER_THRESHOLD");
                }
            }
            resumeState.lastRegimeChangeTs = nowMs;
        }
        // Always update last observed values (defensive)
        resumeState.lastObservedStrategy = currentStrategy;
        resumeState.lastObservedRegime = currentRegime;
        return { warnings: warnings, codes: codes };
    }
    catch (_a) {
        // Defensive: Never throw, return empty
        return { warnings: [], codes: ["OSC_DETECTION_ERROR"] };
    }
}
/**
 * Run supervisor once (single tick)
 *
 * @param store - State store
 * @param cfg - Config (optional)
 * @param deps - Dependencies (optional, for testing)
 * @returns Tick result
 *
 * Fixed Tick Flow:
 *   Step 0: Read state
 *   Step 1: Evaluate policy (PR156)
 *   Step 2: If resumeState exists, evaluate resume (PR162)
 *   Step 3: If RESUMABLE, run TWAP execution (PR159/161/162)
 *   Step 4: Save results to state
 *   Step 5: Update health
 *
 * IMPORTANT: Never throws, always returns result (defensive)
 */
function runSupervisorOnceV1(store, cfg, deps) {
    return __awaiter(this, void 0, void 0, function () {
        var warnings, notes, getNowMs, readResult, state, orchAckSet, _i, orchAckSet_1, resumeId, orchResults, orchResultSeenSet, _a, orchResults_1, result, outcomeSummary, uniqueCodes, truncated, hintSummary, uniqueCodes, truncated, policyResult, specLockResult, error_1, resumeInputs, resumeDecision, resumeReasonCodes, resumeReasonSummary, resumeId, previousRunId, stopReason, resumeStatus, resumeStrategy, resumeStrategyCodes, strategySummary, enforcedExecutionMode, enforcedCodes, enforcedSummary, resumeDelayClass, resumeDelayOffsetLabel, resumeTimingReasonCodes, timingSummary, baseStrategy, escalatedStrategy, escalationCodes, escalationSummary, marketRegime, marketRegimeCodes, regimeSummary, matrixStrategy, matrixCodes, matrixSummary, orchFeedbackFreshness, orchFeedbackAge, regimeHysteresisClass, successStreakClass, successGateStatus, oscillationStatus, oscillationCodes, strategyDerived, nowMs, ORCH_FEEDBACK_STALE_THRESHOLD_MS, effectiveOrchLastStatus, ageMs, consecutiveSuccesses, lastOrchEffectiveStatus, escalation, regimeSignals, regimeSignalsCodes, resumeInputs, error_2, regime, instantRegime, priorRegime, regimeHistory, hysteresis, updatedHistory, matrix, oscillation, successCount, hasStrategyOsc, hasRegimeOsc, regimeInstant, regimeConfirmed, regimeHysteresisAction, regimeHysteresisCodes, regimeHysteresisCodesSummary, consecutiveSuccessesClass, successGate, successGateCodes, successGateCodesSummary, nowMsForOsc, oscWindowStatus, oscChangeLevelStrategy, oscChangeLevelRegime, oscBasisCodes, oscBasisCodesSummary, enforcement, timing, budgetDecision, budgetAttemptStatus, budgetImmediateRateStatus, budgetFailedMarketRateStatus, budgetOscCooldownStatus, budgetAction, budgetCodes, budgetCodesSummary, runResult, MAX_DEFERRAL_COUNT, MAX_DEFERRAL_AGE_MS, deferralCount, firstDeferredAtTs, deferralAgeMs, deferralAgeClass, deferralCountClass, policyHooks, orchInstruction, HOUR_MS, nowMsBudget, newAttemptCount, currentWindowAnchor, windowAge, windowNeedsReset, newWindowAnchor, newImmediateCount, newFailedMarketCount, error_3, lastRun, error_4;
        var _b, _c, _d, _e, _f, _g, _h, _j, _k, _l, _m, _o, _p, _q, _r, _s;
        return __generator(this, function (_t) {
            switch (_t.label) {
                case 0:
                    warnings = [];
                    notes = [];
                    getNowMs = (deps === null || deps === void 0 ? void 0 : deps.getNowMs) || (function () { return Date.now(); });
                    _t.label = 1;
                case 1:
                    _t.trys.push([1, 79, , 80]);
                    notes.push("NOTE_SUPERVISOR_TICK_START");
                    // PR164: Emit SUPERVISOR_TICK event
                    return [4 /*yield*/, (0, telemetry_1.appendEventV1)((0, telemetry_1.createEventV1)("SUPERVISOR_TICK", "INFO", {
                            action: "TICK_START",
                        })).catch(function () { })];
                case 2:
                    // PR164: Emit SUPERVISOR_TICK event
                    _t.sent(); // Defensive: Don't fail on telemetry error
                    return [4 /*yield*/, store.readState()];
                case 3:
                    readResult = _t.sent();
                    warnings.push.apply(warnings, readResult.warnings);
                    if (readResult.status === "ERROR") {
                        notes.push("NOTE_STATE_READ_ERROR");
                        return [2 /*return*/, {
                                status: "ERROR",
                                action: "ACTION_ERROR",
                                warnings: warnings,
                                notes: notes,
                            }];
                    }
                    state = readResult.state;
                    notes.push("NOTE_STATE_LOADED");
                    orchAckSet = (0, interface_1.loadOrchAckSetV1)();
                    if (!(orchAckSet.size > 0)) return [3 /*break*/, 7];
                    notes.push("NOTE_ORCH_ACK_LOADED_COUNT_".concat(orchAckSet.size));
                    _i = 0, orchAckSet_1 = orchAckSet;
                    _t.label = 4;
                case 4:
                    if (!(_i < orchAckSet_1.length)) return [3 /*break*/, 7];
                    resumeId = orchAckSet_1[_i];
                    return [4 /*yield*/, (0, telemetry_1.appendEventV1)((0, telemetry_1.createEventV1)("ORCH_ACK", "INFO", {
                            resume_id: resumeId,
                            ack_status: "ACKED",
                        })).catch(function () { })];
                case 5:
                    _t.sent(); // Defensive: Don't fail on telemetry error
                    _t.label = 6;
                case 6:
                    _i++;
                    return [3 /*break*/, 4];
                case 7:
                    orchResults = (0, interface_1.loadOrchResultLinesV1)(200);
                    orchResultSeenSet = (0, interface_1.loadOrchResultSeenSetV1)();
                    if (!(orchResults.length > 0)) return [3 /*break*/, 13];
                    notes.push("NOTE_ORCH_RESULT_LOADED_COUNT_".concat(orchResults.length));
                    _a = 0, orchResults_1 = orchResults;
                    _t.label = 8;
                case 8:
                    if (!(_a < orchResults_1.length)) return [3 /*break*/, 13];
                    result = orchResults_1[_a];
                    // Skip if already seen (idempotency)
                    if (orchResultSeenSet.has(result.result_id)) {
                        return [3 /*break*/, 12];
                    }
                    // Mark as seen
                    return [4 /*yield*/, (0, interface_1.markOrchResultSeenV1)(result.result_id)];
                case 9:
                    // Mark as seen
                    _t.sent();
                    outcomeSummary = {
                        status: "EMPTY",
                        joined: "",
                    };
                    if (result.outcome_codes && result.outcome_codes.length > 0) {
                        uniqueCodes = Array.from(new Set(result.outcome_codes)).sort();
                        truncated = uniqueCodes.slice(0, 8);
                        if (uniqueCodes.length > 8) {
                            truncated.push("REASONS_TRUNCATED");
                        }
                        outcomeSummary = {
                            status: "PRESENT",
                            joined: truncated.join("|"),
                        };
                    }
                    hintSummary = {
                        status: "EMPTY",
                        joined: "",
                    };
                    if (result.hint_codes && result.hint_codes.length > 0) {
                        uniqueCodes = Array.from(new Set(result.hint_codes)).sort();
                        truncated = uniqueCodes.slice(0, 8);
                        if (uniqueCodes.length > 8) {
                            truncated.push("REASONS_TRUNCATED");
                        }
                        hintSummary = {
                            status: "PRESENT",
                            joined: truncated.join("|"),
                        };
                    }
                    // Emit ORCH_RESULT telemetry event
                    return [4 /*yield*/, (0, telemetry_1.appendEventV1)((0, telemetry_1.createEventV1)("ORCH_RESULT", "INFO", {
                            resume_id: result.resume_id,
                            orch_result_id: result.result_id,
                            orch_result_status: result.status,
                            orch_outcome_codes_status: outcomeSummary.status,
                            orch_outcome_codes: outcomeSummary.joined,
                            orch_hint_codes_status: hintSummary.status,
                            orch_hint_codes: hintSummary.joined,
                        })).catch(function () { })];
                case 10:
                    // Emit ORCH_RESULT telemetry event
                    _t.sent(); // Defensive: Don't fail on telemetry error
                    if (!(state.resumeState &&
                        state.resumeState.status === "STOPPED" &&
                        result.resume_id === ((_b = state.lastRun) === null || _b === void 0 ? void 0 : _b.resumeId))) return [3 /*break*/, 12];
                    // Update orchestrator feedback fields
                    state.resumeState.orchLastStatus = result.status;
                    state.resumeState.orchLastOutcomeCodes = result.outcome_codes || [];
                    state.resumeState.orchLastResultId = result.result_id;
                    // PR221: Track when orchestrator feedback was received (staleness guard)
                    state.resumeState.orchLastStatusTs = getNowMs();
                    // Persist updated state (defensive: don't fail tick on error)
                    return [4 /*yield*/, store.patchState({ resumeState: state.resumeState }).catch(function () { })];
                case 11:
                    // Persist updated state (defensive: don't fail tick on error)
                    _t.sent();
                    _t.label = 12;
                case 12:
                    _a++;
                    return [3 /*break*/, 8];
                case 13:
                    policyResult = void 0;
                    if (!(deps === null || deps === void 0 ? void 0 : deps.evaluatePolicy)) return [3 /*break*/, 15];
                    return [4 /*yield*/, deps.evaluatePolicy()];
                case 14:
                    policyResult = _t.sent();
                    return [3 /*break*/, 16];
                case 15:
                    // Default: assume policy OK (for minimal implementation)
                    policyResult = {
                        allowExecution: true,
                        hardStopActive: false,
                        status: "ALLOW",
                        reasons: [],
                    };
                    _t.label = 16;
                case 16:
                    notes.push("NOTE_POLICY_STATUS_".concat(policyResult.status));
                    _t.label = 17;
                case 17:
                    _t.trys.push([17, 27, , 28]);
                    return [4 /*yield*/, (0, spec_1.evaluateSpecLockV1)()];
                case 18:
                    specLockResult = _t.sent();
                    if (!(specLockResult.status === "ACTIVE_OK")) return [3 /*break*/, 20];
                    return [4 /*yield*/, (0, telemetry_1.appendEventV1)((0, telemetry_1.createEventV1)("SPEC_LOCK_STATUS", "INFO", {
                            status: specLockResult.status,
                            activeSpec: specLockResult.activeSpec || "SPEC_NONE",
                        })).catch(function () { })];
                case 19:
                    _t.sent();
                    return [3 /*break*/, 26];
                case 20:
                    if (!(specLockResult.status === "LOCKED_EXPIRED")) return [3 /*break*/, 22];
                    return [4 /*yield*/, (0, telemetry_1.appendEventV1)((0, telemetry_1.createEventV1)("SPEC_LOCK_EXPIRED", "WARN", {
                            status: specLockResult.status,
                            activeSpec: specLockResult.activeSpec || "NONE",
                            latestSpec: specLockResult.latestSpec || "NONE",
                        })).catch(function () { })];
                case 21:
                    _t.sent();
                    notes.push("NOTE_SPEC_LOCK_EXPIRED");
                    return [3 /*break*/, 26];
                case 22:
                    if (!(specLockResult.status === "LOCKED_PENDING_ACK")) return [3 /*break*/, 24];
                    return [4 /*yield*/, (0, telemetry_1.appendEventV1)((0, telemetry_1.createEventV1)("SPEC_LOCK_STATUS", "WARN", {
                            status: specLockResult.status,
                            latestSpec: specLockResult.latestSpec || "NONE",
                        })).catch(function () { })];
                case 23:
                    _t.sent();
                    notes.push("NOTE_SPEC_PENDING_ACK");
                    return [3 /*break*/, 26];
                case 24:
                    if (!(specLockResult.status === "ERROR")) return [3 /*break*/, 26];
                    return [4 /*yield*/, (0, telemetry_1.appendEventV1)((0, telemetry_1.createEventV1)("SPEC_LOCK_ERROR", "ERROR", {
                            status: specLockResult.status,
                        })).catch(function () { })];
                case 25:
                    _t.sent();
                    warnings.push("WARN_SPEC_LOCK_ERROR");
                    _t.label = 26;
                case 26:
                    warnings.push.apply(warnings, specLockResult.warnings);
                    return [3 /*break*/, 28];
                case 27:
                    error_1 = _t.sent();
                    // Defensive: Don't fail supervisor on spec lock error
                    warnings.push("WARN_SPEC_LOCK_EVAL_EXCEPTION");
                    return [3 /*break*/, 28];
                case 28:
                    if (!policyResult.hardStopActive) return [3 /*break*/, 31];
                    notes.push("NOTE_HARDSTOP_ACTIVE_WAITING");
                    // PR164: Emit POLICY_BLOCK event
                    return [4 /*yield*/, (0, telemetry_1.appendEventV1)((0, telemetry_1.createEventV1)("POLICY_BLOCK", "WARN", {
                            policy_reason: policyResult.reasons[0] || "HARDSTOP_ACTIVE",
                        })).catch(function () { })];
                case 29:
                    // PR164: Emit POLICY_BLOCK event
                    _t.sent();
                    // Update state with HardStop info
                    return [4 /*yield*/, store.patchState({
                            hardStop: {
                                active: true,
                                reason: policyResult.reasons[0],
                            },
                            health: {
                                oracle: ((_c = state.health) === null || _c === void 0 ? void 0 : _c.oracle) || "UNKNOWN",
                                route: ((_d = state.health) === null || _d === void 0 ? void 0 : _d.route) || "UNKNOWN",
                                policy: "DENY",
                                notes: ["NOTE_HARDSTOP_ACTIVE"],
                            },
                        })];
                case 30:
                    // Update state with HardStop info
                    _t.sent();
                    return [2 /*return*/, {
                            status: "OK",
                            action: "ACTION_WAIT_HARDSTOP",
                            warnings: warnings,
                            notes: notes,
                        }];
                case 31:
                    if (!state.resumeState) return [3 /*break*/, 42];
                    notes.push("NOTE_RESUME_STATE_EXISTS");
                    resumeInputs = void 0;
                    if (!(deps === null || deps === void 0 ? void 0 : deps.getResumeInputs)) return [3 /*break*/, 33];
                    return [4 /*yield*/, deps.getResumeInputs()];
                case 32:
                    resumeInputs = _t.sent();
                    return [3 /*break*/, 34];
                case 33:
                    // Default: assume all conditions OK (for minimal implementation)
                    resumeInputs = {
                        nowTs: getNowMs(),
                        oracleStatus: "AVAILABLE",
                        gateStatus: "PASS",
                        phaseLabel: "PHASE_NORMAL",
                        routeAvailable: true,
                        hardStopActive: false,
                        policyEnvEnabled: true,
                    };
                    _t.label = 34;
                case 34:
                    resumeDecision = (0, resumePolicy_1.evaluateResumeV1)(state.resumeState, resumeInputs);
                    notes.push("NOTE_RESUME_DECISION_".concat(resumeDecision.status));
                    resumeReasonCodes = deriveResumeReasonCodesV1(resumeInputs, resumeDecision, state.resumeState);
                    resumeReasonSummary = summarizeResumeReasonCodesV1(resumeReasonCodes);
                    // PR164/PR207: Emit RESUME_EVAL event with reason codes
                    return [4 /*yield*/, (0, telemetry_1.appendEventV1)((0, telemetry_1.createEventV1)("RESUME_EVAL", "INFO", {
                            resume_status: resumeDecision.status,
                            stop_reason: state.resumeState.stopReason,
                            resume_reason_codes_status: resumeReasonSummary.status, // PR207
                            resume_reason_codes: resumeReasonSummary.joined, // PR207
                        }, resumeDecision.reasons)).catch(function () { })];
                case 35:
                    // PR164/PR207: Emit RESUME_EVAL event with reason codes
                    _t.sent();
                    // PR207: Emit RESUME_DECISION event for final decision audit trail
                    return [4 /*yield*/, (0, telemetry_1.appendEventV1)((0, telemetry_1.createEventV1)("RESUME_DECISION", "INFO", {
                            resume_status: resumeDecision.status,
                            stop_reason: state.resumeState.stopReason,
                            resume_reason_codes_status: resumeReasonSummary.status,
                            resume_reason_codes: resumeReasonSummary.joined,
                        })).catch(function () { })];
                case 36:
                    // PR207: Emit RESUME_DECISION event for final decision audit trail
                    _t.sent();
                    if (!(resumeDecision.status === "WAIT")) return [3 /*break*/, 38];
                    notes.push("NOTE_WAIT_RESUME_CONDITIONS");
                    // Update health
                    return [4 /*yield*/, store.patchState({
                            health: {
                                oracle: resumeInputs.oracleStatus || "UNKNOWN",
                                route: resumeInputs.routeAvailable ? "AVAILABLE" : "NONE",
                                policy: policyResult.allowExecution ? "OK" : "DENY",
                                notes: ["NOTE_WAIT_RESUME"],
                            },
                        })];
                case 37:
                    // Update health
                    _t.sent();
                    return [2 /*return*/, {
                            status: "OK",
                            action: "ACTION_WAIT_RESUME",
                            warnings: warnings,
                            notes: notes,
                        }];
                case 38:
                    if (!(resumeDecision.status === "ABANDON")) return [3 /*break*/, 40];
                    notes.push("NOTE_ABANDON_RUN");
                    // Update state: mark as abandoned
                    return [4 /*yield*/, store.patchState({
                            lastRun: {
                                status: "ABANDONED",
                                stopReason: state.resumeState.stopReason,
                                warnings: __spreadArray(__spreadArray([], state.resumeState.warnings, true), ["WARN_RUN_ABANDONED"], false),
                            },
                            resumeState: undefined, // Clear resume state
                        })];
                case 39:
                    // Update state: mark as abandoned
                    _t.sent();
                    return [2 /*return*/, {
                            status: "OK",
                            action: "ACTION_ABORT",
                            warnings: warnings,
                            notes: notes,
                        }];
                case 40:
                    if (resumeDecision.status === "UNKNOWN") {
                        notes.push("NOTE_RESUME_UNKNOWN");
                        // Treat as WAIT (conservative)
                        return [2 /*return*/, {
                                status: "OK",
                                action: "ACTION_WAIT_RESUME",
                                warnings: __spreadArray(__spreadArray([], warnings, true), ["WARN_RESUME_UNKNOWN"], false),
                                notes: notes,
                            }];
                    }
                    _t.label = 41;
                case 41:
                    // RESUMABLE → continue to execution
                    notes.push("NOTE_RESUME_RESUMABLE");
                    _t.label = 42;
                case 42:
                    if (!(policyResult.allowExecution || (cfg === null || cfg === void 0 ? void 0 : cfg.dryRun))) return [3 /*break*/, 77];
                    notes.push("NOTE_RUN_TWAP_EXECUTION");
                    resumeId = void 0;
                    previousRunId = void 0;
                    stopReason = void 0;
                    resumeStatus = void 0;
                    resumeStrategy = void 0;
                    resumeStrategyCodes = void 0;
                    strategySummary = {
                        status: "EMPTY",
                        joined: "",
                    };
                    enforcedExecutionMode = void 0;
                    enforcedCodes = void 0;
                    enforcedSummary = {
                        status: "EMPTY",
                        joined: "",
                    };
                    resumeDelayClass = void 0;
                    resumeDelayOffsetLabel = void 0;
                    resumeTimingReasonCodes = void 0;
                    timingSummary = {
                        status: "EMPTY",
                        joined: "",
                    };
                    baseStrategy = void 0;
                    escalatedStrategy = void 0;
                    escalationCodes = void 0;
                    escalationSummary = {
                        status: "EMPTY",
                        joined: "",
                    };
                    marketRegime = void 0;
                    marketRegimeCodes = void 0;
                    regimeSummary = {
                        status: "EMPTY",
                        joined: "",
                    };
                    matrixStrategy = void 0;
                    matrixCodes = void 0;
                    matrixSummary = {
                        status: "EMPTY",
                        joined: "",
                    };
                    orchFeedbackFreshness = "NONE";
                    orchFeedbackAge = "AGE_NONE";
                    regimeHysteresisClass = "H_UNKNOWN";
                    successStreakClass = "S_UNKNOWN";
                    successGateStatus = "GATE_UNKNOWN";
                    oscillationStatus = "OSC_NONE";
                    oscillationCodes = [];
                    if (!state.resumeState) return [3 /*break*/, 52];
                    resumeId = generateResumeIdV1();
                    // Extract previous run ID if available (assume lastRun has runId)
                    previousRunId = ((_e = state.lastRun) === null || _e === void 0 ? void 0 : _e.runId) || "UNKNOWN";
                    stopReason = state.resumeState.stopReason;
                    resumeStatus = "RESUMABLE"; // If we're here, resume decision was RESUMABLE
                    strategyDerived = deriveResumeStrategyV1({ status: "RESUMABLE", reasons: [] }, state.resumeState);
                    baseStrategy = strategyDerived.strategy;
                    resumeStrategyCodes = strategyDerived.codes;
                    nowMs = getNowMs();
                    ORCH_FEEDBACK_STALE_THRESHOLD_MS = 15 * 60 * 1000;
                    effectiveOrchLastStatus = state.resumeState.orchLastStatus;
                    if (state.resumeState.orchLastStatus && state.resumeState.orchLastStatusTs) {
                        ageMs = nowMs - state.resumeState.orchLastStatusTs;
                        if (ageMs > ORCH_FEEDBACK_STALE_THRESHOLD_MS) {
                            orchFeedbackFreshness = "STALE";
                            orchFeedbackAge = "AGE_STALE";
                            effectiveOrchLastStatus = undefined; // Ignore stale feedback
                            warnings.push("WARN_ORCH_FEEDBACK_STALE");
                        }
                        else {
                            orchFeedbackFreshness = "FRESH";
                            orchFeedbackAge = "AGE_FRESH";
                        }
                    }
                    else if (state.resumeState.orchLastStatus) {
                        // Have status but no timestamp (backward compatibility)
                        orchFeedbackFreshness = "FRESH"; // Assume fresh if no timestamp
                        orchFeedbackAge = "AGE_FRESH";
                    }
                    else {
                        orchFeedbackFreshness = "NONE";
                        orchFeedbackAge = "AGE_NONE";
                    }
                    consecutiveSuccesses = state.resumeState.consecutiveSuccesses || 0;
                    lastOrchEffectiveStatus = state.resumeState.lastOrchEffectiveStatus;
                    // Reset counter if effective status changed (deterministic reset)
                    if (effectiveOrchLastStatus !== lastOrchEffectiveStatus) {
                        if (effectiveOrchLastStatus === "SUCCEEDED") {
                            consecutiveSuccesses = 1; // First success
                        }
                        else {
                            consecutiveSuccesses = 0; // Non-success resets counter
                        }
                    }
                    else if (effectiveOrchLastStatus === "SUCCEEDED") {
                        consecutiveSuccesses += 1; // Increment on consecutive success
                    }
                    // Update resumeState with current values (for next tick)
                    state.resumeState.consecutiveSuccesses = consecutiveSuccesses;
                    state.resumeState.lastOrchEffectiveStatus = effectiveOrchLastStatus;
                    escalation = deriveResumeEscalationV1({
                        originStopCause: state.resumeState.originStopCause,
                        baseStrategy: baseStrategy,
                        orchLastStatus: effectiveOrchLastStatus, // PR221: May be undefined if stale
                        orchLastOutcomeCodes: state.resumeState.orchLastOutcomeCodes,
                        consecutiveSuccesses: consecutiveSuccesses,
                    });
                    escalatedStrategy = escalation.strategy;
                    escalationCodes = escalation.codes;
                    regimeSignals = {};
                    regimeSignalsCodes = [];
                    if (!(deps === null || deps === void 0 ? void 0 : deps.getResumeInputs)) return [3 /*break*/, 47];
                    _t.label = 43;
                case 43:
                    _t.trys.push([43, 45, , 46]);
                    return [4 /*yield*/, deps.getResumeInputs()];
                case 44:
                    resumeInputs = _t.sent();
                    // Map resume inputs to regime signals
                    if (resumeInputs.oracleStatus) {
                        if (resumeInputs.oracleStatus === "AVAILABLE") {
                            regimeSignals.oracle_status = "ORACLE_OK";
                        }
                        else if (resumeInputs.oracleStatus === "STALE") {
                            regimeSignals.oracle_status = "ORACLE_STALE";
                        }
                        else {
                            // UNAVAILABLE, ERROR, or unknown → ORACLE_UNAVAILABLE
                            regimeSignals.oracle_status = "ORACLE_UNAVAILABLE";
                        }
                        regimeSignalsCodes.push("REGIME_SIGNAL_ORACLE_PRESENT");
                    }
                    else {
                        regimeSignalsCodes.push("REGIME_SIGNAL_ORACLE_MISSING");
                    }
                    if (resumeInputs.gateStatus) {
                        // Filter to valid regime signal gate_status values
                        if (resumeInputs.gateStatus === "PASS" || resumeInputs.gateStatus === "BLOCK") {
                            regimeSignals.gate_status = resumeInputs.gateStatus;
                        }
                        else {
                            regimeSignals.gate_status = "UNKNOWN";
                        }
                        regimeSignalsCodes.push("REGIME_SIGNAL_GATE_PRESENT");
                    }
                    else {
                        regimeSignalsCodes.push("REGIME_SIGNAL_GATE_MISSING");
                    }
                    if (resumeInputs.phaseLabel) {
                        regimeSignals.phase_label = resumeInputs.phaseLabel;
                        regimeSignalsCodes.push("REGIME_SIGNAL_PHASE_PRESENT");
                    }
                    else {
                        regimeSignalsCodes.push("REGIME_SIGNAL_PHASE_MISSING");
                    }
                    // Note: network_status, gate_depth_status, quote_status not available from resumeInputs v1
                    regimeSignalsCodes.push("REGIME_SIGNAL_NETWORK_MISSING");
                    regimeSignalsCodes.push("REGIME_SIGNAL_DEPTH_MISSING");
                    regimeSignalsCodes.push("REGIME_SIGNAL_QUOTE_MISSING");
                    regimeSignalsCodes.push("REGIME_SIGNALS_FROM_DEPS_FRESH");
                    return [3 /*break*/, 46];
                case 45:
                    error_2 = _t.sent();
                    // Fallback to stale signals if deps fails
                    warnings.push("WARN_REGIME_SIGNALS_DEPS_ERROR");
                    regimeSignals.phase_label = state.resumeState.lastPhaseLabel;
                    regimeSignalsCodes.push("REGIME_SIGNALS_FROM_RESUMESTATE_STALE");
                    return [3 /*break*/, 46];
                case 46: return [3 /*break*/, 48];
                case 47:
                    // Fallback: use stale signals from resumeState (backward compatibility)
                    regimeSignals.phase_label = state.resumeState.lastPhaseLabel;
                    regimeSignalsCodes.push("REGIME_SIGNALS_FROM_RESUMESTATE_STALE");
                    warnings.push("WARN_REGIME_SIGNALS_STALE");
                    _t.label = 48;
                case 48:
                    regime = deriveMarketRegimeV1(regimeSignals);
                    instantRegime = regime.regime;
                    marketRegimeCodes = __spreadArray(__spreadArray([], regime.codes, true), regimeSignalsCodes, true);
                    priorRegime = state.resumeState.priorRegime;
                    regimeHistory = state.resumeState.regimeHistory || [];
                    hysteresis = confirmRegimeChangeV1(instantRegime, priorRegime, regimeHistory);
                    marketRegime = hysteresis.regime; // Confirmed regime (may differ from instant)
                    marketRegimeCodes.push.apply(// Confirmed regime (may differ from instant)
                    marketRegimeCodes, hysteresis.codes); // Add hysteresis codes
                    updatedHistory = __spreadArray(__spreadArray([], regimeHistory, true), [instantRegime], false).slice(-3);
                    state.resumeState.regimeHistory = updatedHistory;
                    state.resumeState.priorRegime = marketRegime; // Persist confirmed regime
                    // Persist regime in ResumeState (for next tick / telemetry)
                    state.resumeState.marketRegime = marketRegime;
                    state.resumeState.marketRegimeCodes = marketRegimeCodes;
                    matrix = deriveResumeStrategyFromMatrixV1({
                        baseStrategy: escalatedStrategy, // Input is escalated strategy from PR219
                        originStopCause: state.resumeState.originStopCause,
                        regime: marketRegime,
                        orchLastStatus: state.resumeState.orchLastStatus,
                    });
                    matrixStrategy = matrix.strategy;
                    matrixCodes = matrix.codes;
                    // Use matrix strategy as final resumeStrategy for subsequent steps
                    resumeStrategy = matrixStrategy;
                    oscillation = detectOscillationV1({
                        resumeState: state.resumeState,
                        currentStrategy: resumeStrategy,
                        currentRegime: marketRegime,
                        nowMs: getNowMs(),
                    });
                    warnings.push.apply(warnings, oscillation.warnings); // Add oscillation warnings (if any)
                    oscillationCodes = oscillation.codes;
                    // PR224: Derive hysteresis class label (label-only, no raw numbers)
                    if (hysteresis.codes.includes("REGIME_HYSTERESIS_NO_CHANGE")) {
                        regimeHysteresisClass = "H0_NO_CHANGE";
                    }
                    else if (hysteresis.codes.includes("REGIME_HYSTERESIS_CONFIRMED")) {
                        regimeHysteresisClass = "H1_CONFIRMED";
                    }
                    else if (hysteresis.codes.includes("REGIME_HYSTERESIS_HOLD")) {
                        regimeHysteresisClass = "H2_HOLD";
                    }
                    else {
                        regimeHysteresisClass = "H_ERROR";
                    }
                    successCount = state.resumeState.consecutiveSuccesses || 0;
                    if (successCount === 0) {
                        successStreakClass = "S0";
                    }
                    else if (successCount === 1) {
                        successStreakClass = "S1";
                    }
                    else {
                        successStreakClass = "S2_PLUS";
                    }
                    // PR225: Derive success gate status from escalation codes
                    if (escalationCodes.includes("STRAT_ESC_CONSECUTIVE_SUCCESS_GATE_PASS")) {
                        successGateStatus = "GATE_PASS";
                    }
                    else if (escalationCodes.includes("STRAT_ESC_CONSECUTIVE_SUCCESS_GATE_WAIT")) {
                        successGateStatus = "GATE_WAIT";
                    }
                    else {
                        successGateStatus = "GATE_NA"; // Not applicable (no gating logic applied)
                    }
                    hasStrategyOsc = oscillation.warnings.some(function (w) {
                        return w.includes("STRATEGY_OSCILLATION");
                    });
                    hasRegimeOsc = oscillation.warnings.some(function (w) {
                        return w.includes("REGIME_OSCILLATION");
                    });
                    if (hasStrategyOsc && hasRegimeOsc) {
                        oscillationStatus = "OSC_WARN_BOTH";
                    }
                    else if (hasStrategyOsc) {
                        oscillationStatus = "OSC_WARN_STRATEGY";
                    }
                    else if (hasRegimeOsc) {
                        oscillationStatus = "OSC_WARN_REGIME";
                    }
                    else {
                        oscillationStatus = "OSC_NONE";
                    }
                    regimeInstant = instantRegime;
                    regimeConfirmed = marketRegime;
                    regimeHysteresisAction = regimeHysteresisClass;
                    regimeHysteresisCodes = hysteresis.codes;
                    regimeHysteresisCodesSummary = summarizeCodeArrayV1(regimeHysteresisCodes);
                    consecutiveSuccessesClass = successStreakClass;
                    successGate = successGateStatus;
                    successGateCodes = [];
                    if (escalationCodes.includes("STRAT_ESC_CONSECUTIVE_SUCCESS_GATE_PASS")) {
                        successGateCodes.push("STRAT_ESC_CONSEC_GATE_PASS");
                    }
                    if (escalationCodes.includes("STRAT_ESC_CONSECUTIVE_SUCCESS_GATE_WAIT")) {
                        successGateCodes.push("STRAT_ESC_CONSEC_GATE_WAIT");
                    }
                    if (escalationCodes.includes("STRAT_ESC_FROM_ORCH_STATUS_SUCCEEDED")) {
                        successGateCodes.push("STRAT_ESC_CONSEC_SUCCESS_S" + (successCount >= 2 ? "2_PLUS" : successCount));
                    }
                    if (successGateCodes.length === 0) {
                        successGateCodes.push("STRAT_ESC_CONSEC_GATE_NA");
                    }
                    successGateCodesSummary = summarizeCodeArrayV1(successGateCodes);
                    nowMsForOsc = getNowMs();
                    oscWindowStatus = classifyOscillationWindowStatusV1(state.resumeState.lastStrategyChangeTs || state.resumeState.lastRegimeChangeTs, nowMsForOsc);
                    oscChangeLevelStrategy = classifyOscillationChangeLevelV1(state.resumeState.strategyChangeCount);
                    oscChangeLevelRegime = classifyOscillationChangeLevelV1(state.resumeState.regimeChangeCount);
                    oscBasisCodes = __spreadArray([], oscillationCodes, true);
                    if (oscWindowStatus === "WINDOW_RESET") {
                        oscBasisCodes.push("OSC_WINDOW_RESET");
                    }
                    else if (oscWindowStatus === "WINDOW_FRESH") {
                        oscBasisCodes.push("OSC_WINDOW_FRESH");
                    }
                    if (oscChangeLevelStrategy === "CHG_EXCEEDED") {
                        oscBasisCodes.push("OSC_STRATEGY_LEVEL_EXCEEDED");
                    }
                    if (oscChangeLevelRegime === "CHG_EXCEEDED") {
                        oscBasisCodes.push("OSC_REGIME_LEVEL_EXCEEDED");
                    }
                    oscBasisCodesSummary = summarizeCodeArrayV1(oscBasisCodes);
                    strategySummary = summarizeStrategyCodesV1(resumeStrategyCodes);
                    escalationSummary = summarizeStrategyCodesV1(escalationCodes);
                    regimeSummary = summarizeMarketRegimeCodesV1(marketRegimeCodes);
                    matrixSummary = summarizeStrategyCodesV1(matrixCodes);
                    enforcement = deriveExecutionModeOverrideFromStrategyV1(resumeStrategy, undefined // No current desired mode available in minimal supervisor
                    );
                    enforcedExecutionMode = enforcement.enforcedMode;
                    enforcedCodes = enforcement.enforcedCodes;
                    enforcedSummary = summarizeStrategyCodesV1(enforcedCodes);
                    timing = deriveResumeReexecTimingV1({
                        resumeStrategy: resumeStrategy,
                        originStopCause: state.resumeState.originStopCause,
                    });
                    resumeDelayClass = timing.delayClass;
                    resumeDelayOffsetLabel = timing.delayOffsetLabel;
                    resumeTimingReasonCodes = timing.timingReasonCodes;
                    timingSummary = summarizeStrategyCodesV1(resumeTimingReasonCodes);
                    budgetDecision = deriveRecoveryBudgetDecisionV1({
                        desiredDelayClass: resumeDelayClass,
                        desiredDelayOffsetLabel: resumeDelayOffsetLabel,
                        orchEffectiveStatus: state.resumeState.orchLastStatus,
                        oscChangeLevelStrategy: oscChangeLevelStrategy,
                        oscChangeLevelRegime: oscChangeLevelRegime,
                        resumeState: state.resumeState,
                        nowMs: getNowMs(),
                    });
                    budgetAttemptStatus = budgetDecision.budgetAttemptStatus;
                    budgetImmediateRateStatus = budgetDecision.budgetImmediateRateStatus;
                    budgetFailedMarketRateStatus = budgetDecision.budgetFailedMarketRateStatus;
                    budgetOscCooldownStatus = budgetDecision.budgetOscCooldownStatus;
                    budgetAction = budgetDecision.action;
                    budgetCodes = budgetDecision.codes;
                    budgetCodesSummary = summarizeCodeArrayV1(budgetCodes);
                    // PR229: Apply budget override if needed
                    if (budgetDecision.overrideDelayClass) {
                        resumeDelayClass = budgetDecision.overrideDelayClass;
                        resumeDelayOffsetLabel = (budgetDecision.overrideDelayOffsetLabel || resumeDelayOffsetLabel);
                        resumeTimingReasonCodes = __spreadArray(__spreadArray(__spreadArray([], resumeTimingReasonCodes, true), [
                            "TIMING_OVERRIDDEN_BY_BUDGET"
                        ], false), budgetCodes, true);
                        timingSummary = summarizeStrategyCodesV1(resumeTimingReasonCodes);
                    }
                    if (!(budgetAction === "ABANDON")) return [3 /*break*/, 50];
                    // Abandon resume (budget limit exceeded)
                    warnings.push("WARN_RESUME_ABANDONED_BUDGET_LIMIT");
                    notes.push("NOTE_BUDGET_LIMIT_EXCEEDED");
                    // Emit RESUME_REEXEC_ABANDONED event
                    return [4 /*yield*/, (0, telemetry_1.appendEventV1)((0, telemetry_1.createEventV1)("RESUME_REEXEC_ABANDONED", "WARN", {
                            resume_id: resumeId || "UNKNOWN",
                            previous_run_id: previousRunId || "UNKNOWN",
                            abandon_reason: "BUDGET_LIMIT_EXCEEDED",
                            budget_attempt_status: budgetAttemptStatus,
                            budget_codes: budgetCodes.join("|") || "NONE",
                        })).catch(function () { })];
                case 49:
                    // Emit RESUME_REEXEC_ABANDONED event
                    _t.sent();
                    // Return ACTION_ABORT (skip runner call, clear resume state)
                    return [2 /*return*/, {
                            status: "OK",
                            action: "ACTION_ABORT",
                            warnings: warnings,
                            notes: notes,
                        }];
                case 50:
                    // PR213/PR214/PR215/PR219/PR220/PR228/PR229: Set resume fields on runPlan before execution
                    if (deps === null || deps === void 0 ? void 0 : deps.setRunPlanResumeFields) {
                        deps.setRunPlanResumeFields({
                            resumeId: resumeId,
                            previousRunId: previousRunId,
                            resumeStopReason: stopReason,
                            resumeStrategy: resumeStrategy,
                            resumeStrategyCodes: resumeStrategyCodes,
                            resumeStrategyEnforcedExecutionMode: enforcedExecutionMode,
                            resumeStrategyEnforcedCodes: enforcedCodes,
                            resumeDelayClassV1: resumeDelayClass,
                            resumeDelayOffsetLabelV1: resumeDelayOffsetLabel,
                            resumeDelayReasonCodesV1: resumeTimingReasonCodes,
                            resumeEscalatedStrategy: escalatedStrategy, // PR219
                            resumeEscalationCodes: escalationCodes, // PR219
                            resumeMarketRegime: marketRegime, // PR220
                            resumeMarketRegimeCodes: marketRegimeCodes, // PR220
                            resumeMatrixStrategy: matrixStrategy, // PR220
                            resumeMatrixCodes: matrixCodes, // PR220
                            // PR228: Observability pack (passthrough to runner)
                            resumeRegimeInstant: regimeInstant,
                            resumeRegimeConfirmed: regimeConfirmed,
                            resumeRegimeHysteresisAction: regimeHysteresisAction,
                            resumeRegimeHysteresisCodes: regimeHysteresisCodes,
                            resumeConsecutiveSuccessesClass: consecutiveSuccessesClass,
                            resumeSuccessGate: successGate,
                            resumeSuccessGateCodes: successGateCodes,
                            resumeOscWindowStatus: oscWindowStatus,
                            resumeOscChangeLevelStrategy: oscChangeLevelStrategy,
                            resumeOscChangeLevelRegime: oscChangeLevelRegime,
                            resumeOscBasisCodes: oscBasisCodes,
                            // PR229: Recovery Budgeting (label-only status fields)
                            resumeBudgetAttemptStatus: budgetAttemptStatus,
                            resumeBudgetImmediateRateStatus: budgetImmediateRateStatus,
                            resumeBudgetFailedMarketRateStatus: budgetFailedMarketRateStatus,
                            resumeBudgetOscCooldownStatus: budgetOscCooldownStatus,
                            resumeBudgetAction: budgetAction,
                            resumeBudgetCodes: budgetCodes,
                        });
                    }
                    // PR208: Emit RESUME_REEXEC_ATTEMPT before runner call
                    // PR213: Add resume strategy labels
                    // PR214: Add enforcement labels
                    // PR215: Add timing labels
                    // PR219: Add escalation labels
                    // PR220: Add regime/matrix labels
                    // PR221: Add orch feedback freshness labels
                    // PR224: Add regime hysteresis labels
                    // PR225: Add consecutive success gating labels
                    // PR226: Add oscillation detection labels
                    // PR228: Add observability pack (instant/confirmed, gate codes, osc basis)
                    return [4 /*yield*/, (0, telemetry_1.appendEventV1)((0, telemetry_1.createEventV1)("RESUME_REEXEC_ATTEMPT", "INFO", {
                            resume_id: resumeId,
                            previous_run_id: previousRunId,
                            stop_reason: stopReason,
                            resume_status: resumeStatus,
                            resume_base_strategy: baseStrategy, // PR219
                            resume_strategy: resumeStrategy, // PR213 (now matrix in PR220)
                            resume_escalated_strategy: escalatedStrategy, // PR219
                            resume_strategy_codes_status: strategySummary.status, // PR213
                            resume_strategy_codes: strategySummary.joined, // PR213
                            resume_escalation_codes_status: escalationSummary.status, // PR219
                            resume_escalation_codes: escalationSummary.joined, // PR219
                            orch_last_status: state.resumeState.orchLastStatus || "NONE", // PR219 (causality)
                            orch_feedback_freshness: orchFeedbackFreshness, // PR221
                            orch_feedback_age: orchFeedbackAge, // PR221
                            resume_market_regime: marketRegime || "REGIME_UNKNOWN", // PR220
                            resume_market_regime_codes_status: regimeSummary.status, // PR220
                            resume_market_regime_codes: regimeSummary.joined, // PR220
                            resume_matrix_strategy: matrixStrategy || "UNKNOWN", // PR220
                            resume_matrix_codes_status: matrixSummary.status, // PR220
                            resume_matrix_codes: matrixSummary.joined, // PR220
                            resume_enforced_execution_mode: enforcedExecutionMode, // PR214
                            resume_enforced_codes_status: enforcedSummary.status, // PR214
                            resume_enforced_codes: enforcedSummary.joined, // PR214
                            resume_delay_class: resumeDelayClass, // PR215
                            resume_delay_offset_label: resumeDelayOffsetLabel, // PR215
                            resume_timing_codes_status: timingSummary.status, // PR215
                            resume_timing_codes: timingSummary.joined, // PR215
                            resume_regime_hysteresis: regimeHysteresisClass, // PR224
                            resume_success_streak_status: successStreakClass, // PR225
                            resume_success_gate: successGateStatus, // PR225
                            resume_oscillation_status: oscillationStatus, // PR226
                            resume_oscillation_codes: oscillationCodes.join("|") || "NONE", // PR226
                            // PR228: Observability pack
                            resume_regime_instant: regimeInstant, // Instant (before hysteresis)
                            resume_regime_confirmed: regimeConfirmed, // Confirmed (after hysteresis)
                            resume_regime_hysteresis_action: regimeHysteresisAction, // H0/H1/H2
                            resume_regime_hysteresis_codes_status: regimeHysteresisCodesSummary.status,
                            resume_regime_hysteresis_codes: regimeHysteresisCodesSummary.joined,
                            resume_consecutive_successes_class: consecutiveSuccessesClass, // S0/S1/S2_PLUS
                            resume_success_gate_codes_status: successGateCodesSummary.status,
                            resume_success_gate_codes: successGateCodesSummary.joined,
                            resume_osc_window_status: oscWindowStatus, // WINDOW_FRESH/RESET
                            resume_osc_change_level_strategy: oscChangeLevelStrategy, // CHG_LOW/MEDIUM/HIGH/EXCEEDED
                            resume_osc_change_level_regime: oscChangeLevelRegime, // CHG_LOW/MEDIUM/HIGH/EXCEEDED
                            resume_osc_basis_codes_status: oscBasisCodesSummary.status,
                            resume_osc_basis_codes: oscBasisCodesSummary.joined,
                            // PR229: Recovery Budgeting labels
                            resume_budget_attempt_status: budgetAttemptStatus, // B0_OK | B1_NEAR_LIMIT | B2_LIMIT_EXCEEDED
                            resume_budget_immediate_rate_status: budgetImmediateRateStatus, // R0_OK | R1_NEAR_LIMIT | R2_LIMIT_EXCEEDED
                            resume_budget_failed_market_rate_status: budgetFailedMarketRateStatus, // F0_OK | F1_NEAR_LIMIT | F2_LIMIT_EXCEEDED
                            resume_budget_osc_cooldown_status: budgetOscCooldownStatus, // C0_OK | C1_COOLDOWN_ACTIVE
                            resume_budget_action: budgetAction, // ALLOW | DEFER | ABANDON
                            resume_budget_codes_status: budgetCodesSummary.status,
                            resume_budget_codes: budgetCodesSummary.joined,
                        })).catch(function () { })];
                case 51:
                    // PR208: Emit RESUME_REEXEC_ATTEMPT before runner call
                    // PR213: Add resume strategy labels
                    // PR214: Add enforcement labels
                    // PR215: Add timing labels
                    // PR219: Add escalation labels
                    // PR220: Add regime/matrix labels
                    // PR221: Add orch feedback freshness labels
                    // PR224: Add regime hysteresis labels
                    // PR225: Add consecutive success gating labels
                    // PR226: Add oscillation detection labels
                    // PR228: Add observability pack (instant/confirmed, gate codes, osc basis)
                    _t.sent(); // Defensive: Don't fail on telemetry error
                    _t.label = 52;
                case 52:
                    runResult = void 0;
                    if (!(resumeDelayClass && resumeDelayClass !== "IMMEDIATE")) return [3 /*break*/, 63];
                    MAX_DEFERRAL_COUNT = 50;
                    MAX_DEFERRAL_AGE_MS = 24 * 60 * 60 * 1000;
                    deferralCount = (((_f = state.resumeState) === null || _f === void 0 ? void 0 : _f.deferralCount) || 0) + 1;
                    firstDeferredAtTs = ((_g = state.resumeState) === null || _g === void 0 ? void 0 : _g.firstDeferredAtTs) || getNowMs();
                    deferralAgeMs = getNowMs() - firstDeferredAtTs;
                    deferralAgeClass = "AGE_FRESH";
                    if (deferralAgeMs >= MAX_DEFERRAL_AGE_MS) {
                        deferralAgeClass = "AGE_EXPIRED";
                    }
                    else if (deferralAgeMs >= 12 * 60 * 60 * 1000) { // 12 hours
                        deferralAgeClass = "AGE_OLD";
                    }
                    else if (deferralAgeMs >= 1 * 60 * 60 * 1000) { // 1 hour
                        deferralAgeClass = "AGE_MODERATE";
                    }
                    deferralCountClass = "COUNT_LOW";
                    if (deferralCount >= MAX_DEFERRAL_COUNT) {
                        deferralCountClass = "COUNT_EXCEEDED";
                    }
                    else if (deferralCount >= 30) {
                        deferralCountClass = "COUNT_HIGH";
                    }
                    else if (deferralCount >= 10) {
                        deferralCountClass = "COUNT_MEDIUM";
                    }
                    if (!(deferralCount >= MAX_DEFERRAL_COUNT || deferralAgeMs >= MAX_DEFERRAL_AGE_MS)) return [3 /*break*/, 55];
                    // Abandon resume (exceeded deferral limits)
                    warnings.push("WARN_RESUME_ABANDONED_MAX_DEFERRALS");
                    notes.push("NOTE_DEFERRAL_LIMIT_EXCEEDED");
                    // Emit RESUME_REEXEC_ABANDONED event
                    return [4 /*yield*/, (0, telemetry_1.appendEventV1)((0, telemetry_1.createEventV1)("RESUME_REEXEC_ABANDONED", "WARN", {
                            resume_id: resumeId || "UNKNOWN",
                            previous_run_id: previousRunId || "UNKNOWN",
                            stop_reason: stopReason || "UNKNOWN",
                            abandon_reason: "ABANDON_MAX_DEFERRALS",
                            deferral_count: String(deferralCount), // String to keep label-only
                            deferral_count_class: deferralCountClass,
                            deferral_age_class: deferralAgeClass,
                            resume_strategy: resumeStrategy || "UNKNOWN",
                            resume_delay_class: resumeDelayClass || "UNKNOWN",
                        })).catch(function () { })];
                case 53:
                    // Emit RESUME_REEXEC_ABANDONED event
                    _t.sent(); // Defensive: Don't fail on telemetry error
                    // Update state: mark as abandoned
                    return [4 /*yield*/, store.patchState({
                            lastRun: {
                                status: "ABANDONED",
                                stopReason: ((_h = state.resumeState) === null || _h === void 0 ? void 0 : _h.stopReason) || "UNKNOWN",
                                warnings: __spreadArray(__spreadArray([], (((_j = state.resumeState) === null || _j === void 0 ? void 0 : _j.warnings) || []), true), ["WARN_RUN_ABANDONED_MAX_DEFERRALS"], false),
                            },
                            resumeState: undefined, // Clear resume state
                        })];
                case 54:
                    // Update state: mark as abandoned
                    _t.sent();
                    return [2 /*return*/, {
                            status: "OK",
                            action: "ACTION_ABORT",
                            warnings: warnings,
                            notes: notes,
                        }];
                case 55:
                    if (!resumeId) return [3 /*break*/, 62];
                    return [4 /*yield*/, (0, telemetry_1.appendEventV1)((0, telemetry_1.createEventV1)("RESUME_REEXEC_DEFERRED", "INFO", {
                            resume_id: resumeId,
                            previous_run_id: previousRunId || "UNKNOWN",
                            stop_reason: stopReason || "UNKNOWN",
                            resume_strategy: resumeStrategy || "UNKNOWN",
                            resume_delay_class: resumeDelayClass,
                            resume_delay_offset_label: resumeDelayOffsetLabel || "UNKNOWN",
                            resume_timing_codes_status: timingSummary.status,
                            resume_timing_codes: timingSummary.joined,
                            deferred_reason: "DEFERRED_BY_TIMING_CLASS",
                            deferral_count: String(deferralCount), // PR222
                            deferral_count_class: deferralCountClass, // PR222
                            deferral_age_class: deferralAgeClass, // PR222
                        })).catch(function () { })];
                case 56:
                    _t.sent(); // Defensive: Don't fail on telemetry error
                    if (!state.resumeState) return [3 /*break*/, 58];
                    state.resumeState.deferralCount = deferralCount;
                    state.resumeState.firstDeferredAtTs = firstDeferredAtTs;
                    return [4 /*yield*/, store.patchState({ resumeState: state.resumeState }).catch(function () { })];
                case 57:
                    _t.sent();
                    _t.label = 58;
                case 58:
                    if (!!orchAckSet.has(resumeId)) return [3 /*break*/, 61];
                    policyHooks = deriveOrchPolicyHooksV1({
                        resumeStrategy: resumeStrategy,
                        resumeDelayClass: resumeDelayClass,
                        resumeDelayOffsetLabel: resumeDelayOffsetLabel,
                        originStopCause: (_k = state.resumeState) === null || _k === void 0 ? void 0 : _k.originStopCause,
                    });
                    orchInstruction = (0, interface_1.buildOrchestrationInstructionV1)({
                        resumeId: resumeId,
                        previousRunId: previousRunId || "UNKNOWN",
                        stopReason: stopReason || "UNKNOWN",
                        resumeStatus: resumeStatus || "UNKNOWN",
                        resumeStrategy: resumeStrategy,
                        enforcedExecutionMode: enforcedExecutionMode,
                        delayClassV1: resumeDelayClass,
                        delayOffsetV1: resumeDelayOffsetLabel,
                        hintCodes: __spreadArray(__spreadArray(__spreadArray([], (resumeStrategyCodes || []), true), (enforcedCodes || []), true), (resumeTimingReasonCodes || []), true),
                        policyHooks: policyHooks,
                    });
                    // PR216/PR217: Emit ORCH_ENQUEUE event
                    return [4 /*yield*/, (0, telemetry_1.appendEventV1)((0, telemetry_1.createEventV1)("ORCH_ENQUEUE", "INFO", {
                            instruction_version: orchInstruction.instruction_version,
                            resume_id: orchInstruction.resume_id,
                            previous_run_id: orchInstruction.previous_run_id,
                            stop_reason: orchInstruction.stop_reason,
                            resume_strategy: orchInstruction.resume_strategy || "UNKNOWN",
                            enforced_execution_mode: orchInstruction.enforced_execution_mode || "UNKNOWN",
                            delay_class_v1: orchInstruction.delay_class_v1 || "UNKNOWN",
                            delay_offset_v1: orchInstruction.delay_offset_v1 || "UNKNOWN",
                            orch_action: orchInstruction.orch_action,
                            orch_hint_codes_status: orchInstruction.orch_hint_codes_status,
                            orch_hint_codes: orchInstruction.orch_hint_codes,
                            // PR217: Policy hooks labels
                            orch_policy_class: orchInstruction.orch_policy_class || "UNKNOWN",
                            orch_not_before: orchInstruction.orch_not_before || "UNKNOWN",
                            orch_deadline: orchInstruction.orch_deadline || "UNKNOWN",
                            orch_retry_limit: orchInstruction.orch_retry_limit || "UNKNOWN",
                            orch_market_guard: orchInstruction.orch_market_guard || "UNKNOWN",
                        })).catch(function () { })];
                case 59:
                    // PR216/PR217: Emit ORCH_ENQUEUE event
                    _t.sent(); // Defensive: Don't fail on telemetry error
                    // PR216: Write to orchestration queue file
                    return [4 /*yield*/, (0, interface_1.appendOrchQueueV1)(orchInstruction)];
                case 60:
                    // PR216: Write to orchestration queue file
                    _t.sent();
                    return [3 /*break*/, 62];
                case 61:
                    notes.push("NOTE_ORCH_ENQUEUE_SKIPPED_ALREADY_ACKED");
                    _t.label = 62;
                case 62:
                    // Set runResult to indicate deferred status
                    runResult = {
                        status: "DEFERRED",
                        reasons: __spreadArray(["REASON_RESUME_DEFERRED_BY_TIMING"], (resumeTimingReasonCodes || []), true),
                    };
                    return [3 /*break*/, 73];
                case 63:
                    HOUR_MS = 60 * 60 * 1000;
                    nowMsBudget = getNowMs();
                    newAttemptCount = (((_l = state.resumeState) === null || _l === void 0 ? void 0 : _l.recoveryAttemptCount) || 0) + 1;
                    currentWindowAnchor = ((_m = state.resumeState) === null || _m === void 0 ? void 0 : _m.recoveryWindowAnchorTs) || 0;
                    windowAge = currentWindowAnchor > 0 ? nowMsBudget - currentWindowAnchor : HOUR_MS + 1;
                    windowNeedsReset = windowAge > HOUR_MS;
                    newWindowAnchor = currentWindowAnchor;
                    newImmediateCount = ((_o = state.resumeState) === null || _o === void 0 ? void 0 : _o.recoveryImmediateCountInWindow) || 0;
                    newFailedMarketCount = ((_p = state.resumeState) === null || _p === void 0 ? void 0 : _p.recoveryFailedMarketCountInWindow) || 0;
                    if (windowNeedsReset) {
                        // Reset window (new 1-hour period)
                        newWindowAnchor = nowMsBudget;
                        newImmediateCount = 0;
                        newFailedMarketCount = 0;
                    }
                    // Increment IMMEDIATE count if delayClass is IMMEDIATE
                    if (resumeDelayClass === "IMMEDIATE") {
                        newImmediateCount = newImmediateCount + 1;
                    }
                    // Increment FAILED_MARKET count if orchLastStatus is FAILED_MARKET
                    if (((_q = state.resumeState) === null || _q === void 0 ? void 0 : _q.orchLastStatus) === "FAILED_MARKET") {
                        newFailedMarketCount = newFailedMarketCount + 1;
                    }
                    // Update resumeState with new counters
                    if (state.resumeState) {
                        state.resumeState.recoveryAttemptCount = newAttemptCount;
                        state.resumeState.recoveryWindowAnchorTs = newWindowAnchor;
                        state.resumeState.recoveryImmediateCountInWindow = newImmediateCount;
                        state.resumeState.recoveryFailedMarketCountInWindow = newFailedMarketCount;
                        if (windowNeedsReset) {
                            state.resumeState.recoveryWindowLastResetTs = nowMsBudget;
                        }
                    }
                    _t.label = 64;
                case 64:
                    _t.trys.push([64, 70, , 73]);
                    if (!(deps === null || deps === void 0 ? void 0 : deps.runTwapExecution)) return [3 /*break*/, 66];
                    return [4 /*yield*/, deps.runTwapExecution()];
                case 65:
                    runResult = _t.sent();
                    return [3 /*break*/, 67];
                case 66:
                    // Default: no-op (for minimal implementation)
                    runResult = {
                        status: "COMPLETED",
                        reasons: ["REASON_NO_RUNNER_PROVIDED"],
                    };
                    _t.label = 67;
                case 67:
                    if (!resumeId) return [3 /*break*/, 69];
                    return [4 /*yield*/, (0, telemetry_1.appendEventV1)((0, telemetry_1.createEventV1)("RESUME_REEXEC_RESULT", "INFO", {
                            resume_id: resumeId,
                            previous_run_id: previousRunId || "UNKNOWN",
                            next_run_id: runResult.runId || "UNKNOWN",
                            stop_reason: stopReason || "UNKNOWN",
                            resume_status: resumeStatus || "UNKNOWN",
                            execution_status: runResult.status,
                            resume_base_strategy: baseStrategy || "UNKNOWN", // PR219
                            resume_strategy: resumeStrategy || "UNKNOWN", // PR213 (now matrix in PR220)
                            resume_escalated_strategy: escalatedStrategy || "UNKNOWN", // PR219
                            resume_strategy_codes_status: strategySummary.status, // PR213
                            resume_strategy_codes: strategySummary.joined, // PR213
                            resume_escalation_codes_status: escalationSummary.status, // PR219
                            resume_escalation_codes: escalationSummary.joined, // PR219
                            orch_last_status: ((_r = state.resumeState) === null || _r === void 0 ? void 0 : _r.orchLastStatus) || "NONE", // PR219 (causality)
                            orch_feedback_freshness: orchFeedbackFreshness, // PR221
                            orch_feedback_age: orchFeedbackAge, // PR221
                            resume_market_regime: marketRegime || "REGIME_UNKNOWN", // PR220
                            resume_market_regime_codes_status: regimeSummary.status, // PR220
                            resume_market_regime_codes: regimeSummary.joined, // PR220
                            resume_matrix_strategy: matrixStrategy || "UNKNOWN", // PR220
                            resume_matrix_codes_status: matrixSummary.status, // PR220
                            resume_matrix_codes: matrixSummary.joined, // PR220
                            resume_enforced_execution_mode: enforcedExecutionMode || "UNKNOWN", // PR214
                            resume_enforced_codes_status: enforcedSummary.status, // PR214
                            resume_enforced_codes: enforcedSummary.joined, // PR214
                            resume_delay_class: resumeDelayClass || "UNKNOWN", // PR215
                            resume_delay_offset_label: resumeDelayOffsetLabel || "UNKNOWN", // PR215
                            resume_timing_codes_status: timingSummary.status, // PR215
                            resume_timing_codes: timingSummary.joined, // PR215
                        })).catch(function () { })];
                case 68:
                    _t.sent(); // Defensive: Don't fail on telemetry error
                    _t.label = 69;
                case 69: return [3 /*break*/, 73];
                case 70:
                    error_3 = _t.sent();
                    if (!resumeId) return [3 /*break*/, 72];
                    return [4 /*yield*/, (0, telemetry_1.appendEventV1)((0, telemetry_1.createEventV1)("RESUME_REEXEC_RESULT", "ERROR", {
                            resume_id: resumeId,
                            previous_run_id: previousRunId || "UNKNOWN",
                            next_run_id: "ERROR",
                            stop_reason: stopReason || "UNKNOWN",
                            resume_status: resumeStatus || "UNKNOWN",
                            execution_status: "ERROR",
                            resume_base_strategy: baseStrategy || "UNKNOWN", // PR219
                            resume_strategy: resumeStrategy || "UNKNOWN", // PR213 (now matrix in PR220)
                            resume_escalated_strategy: escalatedStrategy || "UNKNOWN", // PR219
                            resume_strategy_codes_status: strategySummary.status, // PR213
                            resume_strategy_codes: strategySummary.joined, // PR213
                            resume_escalation_codes_status: escalationSummary.status, // PR219
                            resume_escalation_codes: escalationSummary.joined, // PR219
                            orch_last_status: ((_s = state.resumeState) === null || _s === void 0 ? void 0 : _s.orchLastStatus) || "NONE", // PR219 (causality)
                            orch_feedback_freshness: orchFeedbackFreshness, // PR221
                            orch_feedback_age: orchFeedbackAge, // PR221
                            resume_market_regime: marketRegime || "REGIME_UNKNOWN", // PR220
                            resume_market_regime_codes_status: regimeSummary.status, // PR220
                            resume_market_regime_codes: regimeSummary.joined, // PR220
                            resume_matrix_strategy: matrixStrategy || "UNKNOWN", // PR220
                            resume_matrix_codes_status: matrixSummary.status, // PR220
                            resume_matrix_codes: matrixSummary.joined, // PR220
                            resume_enforced_execution_mode: enforcedExecutionMode || "UNKNOWN", // PR214
                            resume_enforced_codes_status: enforcedSummary.status, // PR214
                            resume_enforced_codes: enforcedSummary.joined, // PR214
                            resume_delay_class: resumeDelayClass || "UNKNOWN", // PR215
                            resume_delay_offset_label: resumeDelayOffsetLabel || "UNKNOWN", // PR215
                            resume_timing_codes_status: timingSummary.status, // PR215
                            resume_timing_codes: timingSummary.joined, // PR215
                        }, ["ERROR_RUNNER_EXCEPTION"])).catch(function () { })];
                case 71:
                    _t.sent(); // Defensive: Don't fail on telemetry error
                    _t.label = 72;
                case 72: 
                // Re-throw to maintain existing error handling
                throw error_3;
                case 73:
                    notes.push("NOTE_RUN_STATUS_".concat(runResult.status));
                    lastRun = {
                        status: runResult.status,
                        warnings: runResult.reasons,
                    };
                    if (!(runResult.status === "STOPPED" && runResult.resumeState)) return [3 /*break*/, 75];
                    return [4 /*yield*/, store.patchState({
                            lastRun: lastRun,
                            resumeState: runResult.resumeState,
                        })];
                case 74:
                    _t.sent();
                    return [2 /*return*/, {
                            status: "OK",
                            action: "ACTION_RUN_TWAP",
                            warnings: warnings,
                            notes: notes,
                        }];
                case 75: 
                // If completed, clear resumeState
                return [4 /*yield*/, store.patchState({
                        lastRun: lastRun,
                        resumeState: undefined,
                    })];
                case 76:
                    // If completed, clear resumeState
                    _t.sent();
                    return [2 /*return*/, {
                            status: "OK",
                            action: "ACTION_RUN_TWAP",
                            warnings: warnings,
                            notes: notes,
                        }];
                case 77:
                    // No action needed
                    notes.push("NOTE_NO_ACTION_NEEDED");
                    // PR165: Save snapshot (defensive, failure doesn't abort tick)
                    return [4 /*yield*/, saveSnapshotDefensive(state, policyResult)];
                case 78:
                    // PR165: Save snapshot (defensive, failure doesn't abort tick)
                    _t.sent();
                    return [2 /*return*/, {
                            status: "OK",
                            action: "ACTION_NOOP",
                            warnings: warnings,
                            notes: notes,
                        }];
                case 79:
                    error_4 = _t.sent();
                    warnings.push("WARN_SUPERVISOR_UNEXPECTED_ERROR");
                    return [2 /*return*/, {
                            status: "ERROR",
                            action: "ACTION_ERROR",
                            warnings: warnings,
                            notes: notes,
                        }];
                case 80: return [2 /*return*/];
            }
        });
    });
}
/**
 * Save snapshot (defensive helper)
 *
 * PR165: Generate and save market regime snapshot at tick completion.
 * Failures are logged to telemetry but don't abort the tick.
 *
 * @param state - Current state
 * @param policyResult - Policy result
 */
function saveSnapshotDefensive(state, policyResult) {
    return __awaiter(this, void 0, void 0, function () {
        var inputs, snapshot, saveResult, error_5;
        var _a, _b, _c, _d;
        return __generator(this, function (_e) {
            switch (_e.label) {
                case 0:
                    _e.trys.push([0, 7, , 9]);
                    inputs = {
                        latest: {
                            // Extract from state (label-only where possible)
                            hardStop: ((_a = state.hardStop) === null || _a === void 0 ? void 0 : _a.active) ? "ACTIVE" : "INACTIVE",
                            resume: state.resumeState ? "WAIT" : "NONE",
                            policyDecision: policyResult.allowExecution ? "ALLOW" : "DENY",
                            policyReason: policyResult.reasons[0],
                            // Health labels
                            gateDecision: ((_b = state.health) === null || _b === void 0 ? void 0 : _b.oracle) === "AVAILABLE" ? "PASS" : "BLOCK",
                            blockReason: ((_c = state.health) === null || _c === void 0 ? void 0 : _c.oracle) !== "AVAILABLE"
                                ? "ORACLE_".concat((_d = state.health) === null || _d === void 0 ? void 0 : _d.oracle)
                                : undefined,
                        },
                    };
                    return [4 /*yield*/, (0, snapshot_1.buildMarketRegimeSnapshotV1)(inputs)];
                case 1:
                    snapshot = _e.sent();
                    return [4 /*yield*/, (0, snapshot_1.appendSnapshotV1)(snapshot)];
                case 2:
                    saveResult = _e.sent();
                    if (!(saveResult.status === "OK")) return [3 /*break*/, 4];
                    return [4 /*yield*/, (0, telemetry_1.appendEventV1)((0, telemetry_1.createEventV1)("SNAPSHOT_SAVED", "INFO", {
                            snapshot_status: snapshot.status,
                            snapshot_kind: snapshot.kind,
                        })).catch(function () { })];
                case 3:
                    _e.sent(); // Defensive: Don't fail on telemetry error
                    return [3 /*break*/, 6];
                case 4: return [4 /*yield*/, (0, telemetry_1.appendEventV1)((0, telemetry_1.createEventV1)("SNAPSHOT_ERROR", "ERROR", {
                        snapshot_status: snapshot.status,
                    }, saveResult.warnings)).catch(function () { })];
                case 5:
                    _e.sent(); // Defensive: Don't fail on telemetry error
                    _e.label = 6;
                case 6: return [3 /*break*/, 9];
                case 7:
                    error_5 = _e.sent();
                    // Defensive: Snapshot failure doesn't abort tick
                    return [4 /*yield*/, (0, telemetry_1.appendEventV1)((0, telemetry_1.createEventV1)("SNAPSHOT_ERROR", "ERROR", {}, ["WARN_SNAPSHOT_FAILED"])).catch(function () { })];
                case 8:
                    // Defensive: Snapshot failure doesn't abort tick
                    _e.sent(); // Defensive: Don't fail on telemetry error
                    return [3 /*break*/, 9];
                case 9: return [2 /*return*/];
            }
        });
    });
}
