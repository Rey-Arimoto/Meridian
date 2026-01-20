"use strict";
/**
 * PR179: v1.4 Spec Version Lock + Human ACK Gate v1 - Store
 *
 * Purpose:
 *   Append-only JSONL logs for spec records and ACKs.
 *
 * Constitutional Constraints:
 *   - Append-only: No mutations
 *   - Defensive: Corrupted lines are skipped, never throws
 *   - Label-only: Warnings must be sanitized
 */
var __assign = (this && this.__assign) || function () {
    __assign = Object.assign || function(t) {
        for (var s, i = 1, n = arguments.length; i < n; i++) {
            s = arguments[i];
            for (var p in s) if (Object.prototype.hasOwnProperty.call(s, p))
                t[p] = s[p];
        }
        return t;
    };
    return __assign.apply(this, arguments);
};
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
exports.appendSpecRecordV1 = appendSpecRecordV1;
exports.appendSpecAckRecordV1 = appendSpecAckRecordV1;
exports.readRecentSpecRecordsV1 = readRecentSpecRecordsV1;
exports.readRecentSpecAcksV1 = readRecentSpecAcksV1;
exports.readLatestSpecRecordV1 = readLatestSpecRecordV1;
exports.readLatestAckForSpecV1 = readLatestAckForSpecV1;
exports.readLatestAckedSpecV1 = readLatestAckedSpecV1;
var fs = __importStar(require("fs"));
var path = __importStar(require("path"));
var os = __importStar(require("os"));
var guards_1 = require("./guards");
/**
 * Default storage paths
 */
var DEFAULT_SPEC_LOG = path.join(os.homedir(), ".meridian", "specs.log");
var DEFAULT_ACK_LOG = path.join(os.homedir(), ".meridian", "spec_acks.log");
/**
 * Ensure directory exists
 *
 * @param filePath - File path
 */
function ensureDir(filePath) {
    var dir = path.dirname(filePath);
    if (!fs.existsSync(dir)) {
        fs.mkdirSync(dir, { recursive: true });
    }
}
/**
 * Append spec record
 *
 * @param rec - Spec record
 * @param pathOverride - Optional path override
 * @returns Result with status and warnings
 */
function appendSpecRecordV1(rec, pathOverride) {
    return __awaiter(this, void 0, void 0, function () {
        var logPath, sanitized, line;
        return __generator(this, function (_a) {
            try {
                logPath = pathOverride || DEFAULT_SPEC_LOG;
                ensureDir(logPath);
                sanitized = __assign(__assign({}, rec), { warnings: (0, guards_1.sanitizeWarnings)(rec.warnings) });
                line = JSON.stringify(sanitized) + "\n";
                fs.appendFileSync(logPath, line, "utf8");
                return [2 /*return*/, { status: "OK", warnings: [] }];
            }
            catch (error) {
                return [2 /*return*/, { status: "ERROR", warnings: ["WARN_SPEC_APPEND_FAILED"] }];
            }
            return [2 /*return*/];
        });
    });
}
/**
 * Append spec ACK record
 *
 * @param rec - ACK record
 * @param pathOverride - Optional path override
 * @returns Result with status and warnings
 */
function appendSpecAckRecordV1(rec, pathOverride) {
    return __awaiter(this, void 0, void 0, function () {
        var logPath, sanitized, line;
        return __generator(this, function (_a) {
            try {
                logPath = pathOverride || DEFAULT_ACK_LOG;
                ensureDir(logPath);
                sanitized = __assign(__assign({}, rec), { warnings: (0, guards_1.sanitizeWarnings)(rec.warnings) });
                line = JSON.stringify(sanitized) + "\n";
                fs.appendFileSync(logPath, line, "utf8");
                return [2 /*return*/, { status: "OK", warnings: [] }];
            }
            catch (error) {
                return [2 /*return*/, { status: "ERROR", warnings: ["WARN_ACK_APPEND_FAILED"] }];
            }
            return [2 /*return*/];
        });
    });
}
/**
 * Read recent spec records
 *
 * @param opts - Options with tail limit
 * @param pathOverride - Optional path override
 * @returns Spec records
 */
function readRecentSpecRecordsV1(opts, pathOverride) {
    return __awaiter(this, void 0, void 0, function () {
        var logPath, content, lines, records, startIdx, i, parsed;
        return __generator(this, function (_a) {
            try {
                logPath = pathOverride || DEFAULT_SPEC_LOG;
                if (!fs.existsSync(logPath)) {
                    return [2 /*return*/, []];
                }
                content = fs.readFileSync(logPath, "utf8");
                lines = content.trim().split("\n").filter(function (l) { return l.length > 0; });
                records = [];
                startIdx = Math.max(0, lines.length - opts.tail);
                for (i = startIdx; i < lines.length; i++) {
                    try {
                        parsed = JSON.parse(lines[i]);
                        if (parsed.kind === "SPEC_RECORD_V1") {
                            records.push(parsed);
                        }
                    }
                    catch (_b) {
                        // Skip corrupted lines
                        continue;
                    }
                }
                return [2 /*return*/, records];
            }
            catch (_c) {
                return [2 /*return*/, []];
            }
            return [2 /*return*/];
        });
    });
}
/**
 * Read recent ACK records
 *
 * @param opts - Options with tail limit
 * @param pathOverride - Optional path override
 * @returns ACK records
 */
function readRecentSpecAcksV1(opts, pathOverride) {
    return __awaiter(this, void 0, void 0, function () {
        var logPath, content, lines, records, startIdx, i, parsed;
        return __generator(this, function (_a) {
            try {
                logPath = pathOverride || DEFAULT_ACK_LOG;
                if (!fs.existsSync(logPath)) {
                    return [2 /*return*/, []];
                }
                content = fs.readFileSync(logPath, "utf8");
                lines = content.trim().split("\n").filter(function (l) { return l.length > 0; });
                records = [];
                startIdx = Math.max(0, lines.length - opts.tail);
                for (i = startIdx; i < lines.length; i++) {
                    try {
                        parsed = JSON.parse(lines[i]);
                        if (parsed.kind === "SPEC_ACK_V1") {
                            records.push(parsed);
                        }
                    }
                    catch (_b) {
                        // Skip corrupted lines
                        continue;
                    }
                }
                return [2 /*return*/, records];
            }
            catch (_c) {
                return [2 /*return*/, []];
            }
            return [2 /*return*/];
        });
    });
}
/**
 * Read latest spec record
 *
 * @param pathOverride - Optional path override
 * @returns Latest spec record or undefined
 */
function readLatestSpecRecordV1(pathOverride) {
    return __awaiter(this, void 0, void 0, function () {
        var records;
        return __generator(this, function (_a) {
            switch (_a.label) {
                case 0: return [4 /*yield*/, readRecentSpecRecordsV1({ tail: 100 }, pathOverride)];
                case 1:
                    records = _a.sent();
                    return [2 /*return*/, records.length > 0 ? records[records.length - 1] : undefined];
            }
        });
    });
}
/**
 * Read latest ACK for a specific spec version
 *
 * @param specVersion - Spec version
 * @param pathOverride - Optional path override
 * @returns Latest ACK record or undefined
 */
function readLatestAckForSpecV1(specVersion, pathOverride) {
    return __awaiter(this, void 0, void 0, function () {
        var acks, i;
        return __generator(this, function (_a) {
            switch (_a.label) {
                case 0: return [4 /*yield*/, readRecentSpecAcksV1({ tail: 100 }, pathOverride)];
                case 1:
                    acks = _a.sent();
                    // Find latest ACK for this spec
                    for (i = acks.length - 1; i >= 0; i--) {
                        if (acks[i].specVersion === specVersion) {
                            return [2 /*return*/, acks[i]];
                        }
                    }
                    return [2 /*return*/, undefined];
            }
        });
    });
}
/**
 * Read latest ACKed spec version
 *
 * @param pathOverride - Optional path override
 * @returns Latest ACKed spec version or undefined
 */
function readLatestAckedSpecV1(pathOverride) {
    return __awaiter(this, void 0, void 0, function () {
        var acks;
        return __generator(this, function (_a) {
            switch (_a.label) {
                case 0: return [4 /*yield*/, readRecentSpecAcksV1({ tail: 100 }, pathOverride)];
                case 1:
                    acks = _a.sent();
                    if (acks.length === 0) {
                        return [2 /*return*/, undefined];
                    }
                    // Return the spec version from the most recent ACK
                    return [2 /*return*/, acks[acks.length - 1].specVersion];
            }
        });
    });
}
