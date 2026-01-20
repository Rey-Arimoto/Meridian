"use strict";
/**
 * PR216: Recovery Orchestration Interface (Scheduler-less Deferred Re-exec) v1
 * PR217: Orchestrator Policy Hooks v1 (Instruction extension)
 *
 * Purpose:
 *   External orchestrator integration for deferred resume re-execution.
 *   Supervisor emits instruction payloads, external orchestrator ACKs and dispatches.
 *   PR217 adds execution timing/condition hints (policy hooks).
 *
 * Constitutional Constraints:
 *   - READ-ONLY: Decision outputs only, no scheduling
 *   - Label-only: All values are strings, no numeric timestamps/durations
 *   - Defensive: Never throws, handles file I/O errors gracefully
 *   - Idempotent: ACK prevents duplicate enqueues
 */
var __createBinding = (this && this.__createBinding) || (Object.create ? (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    var desc = Object.getOwnPropertyDescriptor(m, k);
    if (!desc || ("get" in desc ? !m.__esModule : desc.writable || desc.configurable)) {
      desc = { enumerable: true, get: function() { return m[k]; } };
    }
    Object.defineProperty(o, k2, desc);
}) : (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    o[k2] = m[k];
}));
var __setModuleDefault = (this && this.__setModuleDefault) || (Object.create ? (function(o, v) {
    Object.defineProperty(o, "default", { enumerable: true, value: v });
}) : function(o, v) {
    o["default"] = v;
});
var __importStar = (this && this.__importStar) || (function () {
    var ownKeys = function(o) {
        ownKeys = Object.getOwnPropertyNames || function (o) {
            var ar = [];
            for (var k in o) if (Object.prototype.hasOwnProperty.call(o, k)) ar[ar.length] = k;
            return ar;
        };
        return ownKeys(o);
    };
    return function (mod) {
        if (mod && mod.__esModule) return mod;
        var result = {};
        if (mod != null) for (var k = ownKeys(mod), i = 0; i < k.length; i++) if (k[i] !== "default") __createBinding(result, mod, k[i]);
        __setModuleDefault(result, mod);
        return result;
    };
})();
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
Object.defineProperty(exports, "__esModule", { value: true });
exports.buildOrchestrationInstructionV1 = buildOrchestrationInstructionV1;
exports.appendOrchQueueV1 = appendOrchQueueV1;
exports.loadOrchAckSetV1 = loadOrchAckSetV1;
exports.appendOrchResultV1 = appendOrchResultV1;
exports.loadOrchResultLinesV1 = loadOrchResultLinesV1;
exports.loadOrchResultSeenSetV1 = loadOrchResultSeenSetV1;
exports.markOrchResultSeenV1 = markOrchResultSeenV1;
var fs = __importStar(require("fs"));
var path = __importStar(require("path"));
var os = __importStar(require("os"));
/**
 * Build orchestration instruction v1
 *
 * @param args - Instruction arguments
 * @returns Orchestration instruction (never throws)
 */
function buildOrchestrationInstructionV1(args) {
    try {
        // Derive orch_action from delay_class_v1
        var orchAction = "DEFER";
        if (args.delayClassV1 === "MANUAL") {
            orchAction = "MANUAL";
        }
        else if (args.resumeStatus === "ABANDON") {
            orchAction = "ABANDON";
        }
        else if (args.delayClassV1 !== "IMMEDIATE") {
            orchAction = "DEFER";
        }
        // Process hint codes: dedup, sort, truncate to 8
        var hintCodesStatus = "EMPTY";
        var hintCodesJoined = "";
        if (args.hintCodes && args.hintCodes.length > 0) {
            var uniqueCodes = Array.from(new Set(args.hintCodes)).sort();
            var truncated = uniqueCodes.slice(0, 8);
            if (uniqueCodes.length > 8) {
                truncated.push("REASONS_TRUNCATED");
            }
            hintCodesJoined = truncated.join("|");
            hintCodesStatus = "PRESENT";
        }
        var instruction = {
            instruction_version: "ORCH_V1",
            resume_id: args.resumeId,
            previous_run_id: args.previousRunId,
            stop_reason: args.stopReason,
            resume_status: args.resumeStatus,
            resume_strategy: args.resumeStrategy,
            enforced_execution_mode: args.enforcedExecutionMode,
            delay_class_v1: args.delayClassV1,
            delay_offset_v1: args.delayOffsetV1,
            orch_action: orchAction,
            orch_hint_codes_status: hintCodesStatus,
            orch_hint_codes: hintCodesJoined,
        };
        // PR217: Add policy hooks if provided (backward compatible)
        if (args.policyHooks) {
            instruction.orch_policy_class = args.policyHooks.orch_policy_class;
            instruction.orch_not_before = args.policyHooks.orch_not_before;
            instruction.orch_deadline = args.policyHooks.orch_deadline;
            instruction.orch_retry_limit = args.policyHooks.orch_retry_limit;
            instruction.orch_market_guard = args.policyHooks.orch_market_guard;
        }
        return instruction;
    }
    catch (error) {
        // Defensive: Return minimal valid instruction on error
        return {
            instruction_version: "ORCH_V1",
            resume_id: args.resumeId || "UNKNOWN",
            previous_run_id: args.previousRunId || "UNKNOWN",
            stop_reason: args.stopReason || "UNKNOWN",
            resume_status: args.resumeStatus || "UNKNOWN",
            orch_action: "DEFER",
            orch_hint_codes_status: "EMPTY",
            orch_hint_codes: "",
        };
    }
}
/**
 * Append orchestration instruction to queue file
 *
 * @param instruction - Instruction to enqueue
 * @returns Promise (never throws, catches errors internally)
 */
function appendOrchQueueV1(instruction) {
    return __awaiter(this, void 0, void 0, function () {
        var queuePath, dir, line;
        return __generator(this, function (_a) {
            try {
                queuePath = path.join(os.homedir(), ".meridian", "orch_queue.jsonl");
                dir = path.dirname(queuePath);
                if (!fs.existsSync(dir)) {
                    fs.mkdirSync(dir, { recursive: true });
                }
                line = JSON.stringify(instruction) + "\n";
                fs.appendFileSync(queuePath, line, "utf8");
            }
            catch (error) {
                // Defensive: Catch and ignore (telemetry will still record ORCH_ENQUEUE)
                // In production, consider logging to stderr or separate error log
            }
            return [2 /*return*/];
        });
    });
}
/**
 * Load ACK set from ACK file
 *
 * @returns Set of resume_id values that have been ACKed (never throws)
 */
function loadOrchAckSetV1() {
    try {
        var ackPath = path.join(os.homedir(), ".meridian", "orch_ack.jsonl");
        // Return empty set if file doesn't exist
        if (!fs.existsSync(ackPath)) {
            return new Set();
        }
        // Read file and parse each line
        var content = fs.readFileSync(ackPath, "utf8");
        var lines = content.trim().split("\n");
        var ackedSet = new Set();
        for (var _i = 0, lines_1 = lines; _i < lines_1.length; _i++) {
            var line = lines_1[_i];
            if (!line.trim())
                continue;
            try {
                var record = JSON.parse(line);
                if (record.v === "ACK_V1" && record.ack_status === "ACKED") {
                    ackedSet.add(record.resume_id);
                }
            }
            catch (parseError) {
                // Defensive: Skip malformed lines
                continue;
            }
        }
        return ackedSet;
    }
    catch (error) {
        // Defensive: Return empty set on any error
        return new Set();
    }
}
/**
 * PR218: Append orchestration result to result file
 *
 * @param result - Result to record
 * @returns Promise (never throws, catches errors internally)
 */
function appendOrchResultV1(result) {
    return __awaiter(this, void 0, void 0, function () {
        var resultPath, dir, line;
        return __generator(this, function (_a) {
            try {
                resultPath = path.join(os.homedir(), ".meridian", "orch_result.jsonl");
                dir = path.dirname(resultPath);
                if (!fs.existsSync(dir)) {
                    fs.mkdirSync(dir, { recursive: true });
                }
                line = JSON.stringify(result) + "\n";
                fs.appendFileSync(resultPath, line, "utf8");
            }
            catch (error) {
                // Defensive: Catch and ignore (telemetry will still record ORCH_RESULT)
            }
            return [2 /*return*/];
        });
    });
}
/**
 * PR218: Load orchestration result lines from result file
 *
 * @param limit - Maximum number of lines to read (default: 200)
 * @returns Array of result records (never throws, skips malformed lines)
 */
function loadOrchResultLinesV1(limit) {
    if (limit === void 0) { limit = 200; }
    try {
        var resultPath = path.join(os.homedir(), ".meridian", "orch_result.jsonl");
        // Return empty array if file doesn't exist
        if (!fs.existsSync(resultPath)) {
            return [];
        }
        // Read file and parse each line
        var content = fs.readFileSync(resultPath, "utf8");
        var lines = content.trim().split("\n");
        var results = [];
        // Read up to limit lines (from end, newest first)
        var startIdx = Math.max(0, lines.length - limit);
        for (var i = startIdx; i < lines.length; i++) {
            var line = lines[i];
            if (!line.trim())
                continue;
            try {
                var result = JSON.parse(line);
                if (result.v === "v1" && result.resume_id && result.result_id) {
                    results.push(result);
                }
            }
            catch (parseError) {
                // Defensive: Skip malformed lines
                continue;
            }
        }
        return results;
    }
    catch (error) {
        // Defensive: Return empty array on any error
        return [];
    }
}
/**
 * PR218: Load seen result IDs from seen file
 *
 * @returns Set of result_id values that have been seen (never throws)
 */
function loadOrchResultSeenSetV1() {
    try {
        var seenPath = path.join(os.homedir(), ".meridian", "orch_result_seen.jsonl");
        // Return empty set if file doesn't exist
        if (!fs.existsSync(seenPath)) {
            return new Set();
        }
        // Read file and collect result_ids
        var content = fs.readFileSync(seenPath, "utf8");
        var lines = content.trim().split("\n");
        var seenSet = new Set();
        for (var _i = 0, lines_2 = lines; _i < lines_2.length; _i++) {
            var line = lines_2[_i];
            if (!line.trim())
                continue;
            try {
                var record = JSON.parse(line);
                if (record.result_id) {
                    seenSet.add(record.result_id);
                }
            }
            catch (parseError) {
                // Defensive: Skip malformed lines
                continue;
            }
        }
        return seenSet;
    }
    catch (error) {
        // Defensive: Return empty set on any error
        return new Set();
    }
}
/**
 * PR218: Mark result as seen (append to seen file)
 *
 * @param resultId - Result ID to mark as seen
 * @returns Promise (never throws, catches errors internally)
 */
function markOrchResultSeenV1(resultId) {
    return __awaiter(this, void 0, void 0, function () {
        var seenPath, dir, line;
        return __generator(this, function (_a) {
            try {
                seenPath = path.join(os.homedir(), ".meridian", "orch_result_seen.jsonl");
                dir = path.dirname(seenPath);
                if (!fs.existsSync(dir)) {
                    fs.mkdirSync(dir, { recursive: true });
                }
                line = JSON.stringify({ result_id: resultId }) + "\n";
                fs.appendFileSync(seenPath, line, "utf8");
            }
            catch (error) {
                // Defensive: Catch and ignore
            }
            return [2 /*return*/];
        });
    });
}
