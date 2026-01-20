"use strict";
/**
 * PR165: v1.4 Market Regime Snapshot Export v1 - Exporter
 *
 * Purpose:
 *   Build and save market regime snapshots for strategy verification.
 *
 * Constitutional Constraints:
 *   - READ-ONLY: Snapshots are observations, not recommendations
 *   - Defensive: Never throws, always returns snapshot (even on error)
 *   - Fixed rules: No prediction, no optimization, no learning
 *   - Append-only: JSONL format, one snapshot per line
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
exports.buildMarketRegimeSnapshotV1 = buildMarketRegimeSnapshotV1;
exports.resolveSnapshotLogPath = resolveSnapshotLogPath;
exports.appendSnapshotV1 = appendSnapshotV1;
exports.readRecentSnapshotsV1 = readRecentSnapshotsV1;
exports.readFilteredSnapshotsV1 = readFilteredSnapshotsV1;
var fs = __importStar(require("fs"));
var path = __importStar(require("path"));
var os = __importStar(require("os"));
var guards_1 = require("./guards");
/**
 * Build presence flags from inputs
 *
 * @param inputs - Snapshot inputs
 * @returns Presence flags
 */
function buildPresence(inputs) {
    var _a;
    var latest = inputs === null || inputs === void 0 ? void 0 : inputs.latest;
    return {
        hasOracle: ((_a = latest === null || latest === void 0 ? void 0 : latest.numerics) === null || _a === void 0 ? void 0 : _a.oracleAgeMs) !== undefined ||
            (latest === null || latest === void 0 ? void 0 : latest.gateDecision) !== undefined,
        hasObservationLabels: (latest === null || latest === void 0 ? void 0 : latest.observation) !== undefined,
        hasShockPhase: (latest === null || latest === void 0 ? void 0 : latest.shockPhase) !== undefined,
        hasStress: (latest === null || latest === void 0 ? void 0 : latest.stress) !== undefined,
        hasEscalation: (latest === null || latest === void 0 ? void 0 : latest.stressEscalated) !== undefined,
        hasActionShape: (latest === null || latest === void 0 ? void 0 : latest.actionShape) !== undefined,
        hasTemplateId: (latest === null || latest === void 0 ? void 0 : latest.templateId) !== undefined,
        hasRoute: (latest === null || latest === void 0 ? void 0 : latest.route) !== undefined,
        hasGate: (latest === null || latest === void 0 ? void 0 : latest.gateDecision) !== undefined,
        hasPolicy: (latest === null || latest === void 0 ? void 0 : latest.policyDecision) !== undefined,
        hasHardStop: (latest === null || latest === void 0 ? void 0 : latest.hardStop) !== undefined,
        hasCooldown: (latest === null || latest === void 0 ? void 0 : latest.cooldown) !== undefined,
        hasDrift: (latest === null || latest === void 0 ? void 0 : latest.drift) !== undefined,
        hasResume: (latest === null || latest === void 0 ? void 0 : latest.resume) !== undefined,
    };
}
/**
 * Build labels from inputs (label-only)
 *
 * @param inputs - Snapshot inputs
 * @returns Snapshot labels
 */
function buildLabels(inputs) {
    var latest = inputs === null || inputs === void 0 ? void 0 : inputs.latest;
    var labels = {};
    // Observation labels (PR154)
    if (latest === null || latest === void 0 ? void 0 : latest.observation) {
        labels.impulse = latest.observation.impulse;
        labels.thinning = latest.observation.thinning;
        labels.dominance = latest.observation.dominance;
        labels.absorption = latest.observation.absorption;
    }
    // Higher-level labels
    if (latest === null || latest === void 0 ? void 0 : latest.shockPhase)
        labels.shockPhase = latest.shockPhase;
    if (latest === null || latest === void 0 ? void 0 : latest.stress)
        labels.stress = latest.stress;
    if (latest === null || latest === void 0 ? void 0 : latest.stressEscalated)
        labels.stressEscalated = latest.stressEscalated;
    if (latest === null || latest === void 0 ? void 0 : latest.actionShape)
        labels.actionShape = latest.actionShape;
    if (latest === null || latest === void 0 ? void 0 : latest.templateId)
        labels.templateId = latest.templateId;
    if (latest === null || latest === void 0 ? void 0 : latest.route)
        labels.route = latest.route;
    if (latest === null || latest === void 0 ? void 0 : latest.gateDecision)
        labels.gateDecision = latest.gateDecision;
    if (latest === null || latest === void 0 ? void 0 : latest.blockReason)
        labels.blockReason = latest.blockReason;
    if (latest === null || latest === void 0 ? void 0 : latest.policyDecision)
        labels.policyDecision = latest.policyDecision;
    if (latest === null || latest === void 0 ? void 0 : latest.policyReason)
        labels.policyReason = latest.policyReason;
    if (latest === null || latest === void 0 ? void 0 : latest.hardStop)
        labels.hardStop = latest.hardStop;
    if (latest === null || latest === void 0 ? void 0 : latest.cooldown)
        labels.cooldown = latest.cooldown;
    if (latest === null || latest === void 0 ? void 0 : latest.drift)
        labels.drift = latest.drift;
    if (latest === null || latest === void 0 ? void 0 : latest.resume)
        labels.resume = latest.resume;
    // Sanitize all labels
    for (var _i = 0, _a = Object.entries(labels); _i < _a.length; _i++) {
        var _b = _a[_i], key = _b[0], value = _b[1];
        if (typeof value === "string") {
            labels[key] = (0, guards_1.sanitizeSnapshotLabel)(value);
        }
    }
    return labels;
}
/**
 * Determine snapshot status (AVAILABLE / PARTIAL / ERROR)
 *
 * Fixed rule:
 *   - AVAILABLE: hasShockPhase && hasStress && hasActionShape && hasTemplateId && hasGate && hasPolicy
 *   - PARTIAL: Snapshot built but missing some components
 *   - ERROR: Inputs invalid or construction failed
 *
 * @param presence - Presence flags
 * @returns Snapshot status
 */
function determineStatus(presence) {
    var isAvailable = presence.hasShockPhase &&
        presence.hasStress &&
        presence.hasActionShape &&
        presence.hasTemplateId &&
        presence.hasGate &&
        presence.hasPolicy;
    if (isAvailable) {
        return "AVAILABLE";
    }
    else {
        return "PARTIAL";
    }
}
/**
 * Build market regime snapshot v1
 *
 * Purpose:
 *   Build a snapshot from current system state for strategy verification.
 *
 * @param inputs - Snapshot inputs (optional)
 * @returns Market regime snapshot (never throws)
 */
function buildMarketRegimeSnapshotV1(inputs) {
    return __awaiter(this, void 0, void 0, function () {
        var warnings, presence, labels, numerics, status_1, ts, rand, id, snapshot;
        var _a;
        return __generator(this, function (_b) {
            warnings = [];
            try {
                presence = buildPresence(inputs);
                labels = buildLabels(inputs);
                numerics = ((_a = inputs === null || inputs === void 0 ? void 0 : inputs.latest) === null || _a === void 0 ? void 0 : _a.numerics)
                    ? {
                        notionalUsd: inputs.latest.numerics.notionalUsd,
                        targetNotionalUsd: inputs.latest.numerics.targetNotionalUsd,
                        oracleAgeMs: inputs.latest.numerics.oracleAgeMs,
                    }
                    : undefined;
                status_1 = determineStatus(presence);
                ts = Date.now();
                rand = Math.floor(Math.random() * 1000);
                id = "snap_".concat(ts, "_").concat(rand);
                snapshot = {
                    version: "v1.0",
                    kind: "REGIME_SNAPSHOT",
                    status: status_1,
                    ts: ts,
                    id: id,
                    warnings: warnings,
                    presence: presence,
                    labels: labels,
                    numerics: numerics,
                    build: inputs === null || inputs === void 0 ? void 0 : inputs.build,
                };
                return [2 /*return*/, snapshot];
            }
            catch (error) {
                // Defensive: Even on error, return a minimal snapshot
                warnings.push("WARN_SNAPSHOT_BUILD_ERROR");
                return [2 /*return*/, {
                        version: "v1.0",
                        kind: "REGIME_SNAPSHOT",
                        status: "ERROR",
                        ts: Date.now(),
                        id: "snap_error_".concat(Date.now()),
                        warnings: warnings,
                        presence: {
                            hasOracle: false,
                            hasObservationLabels: false,
                            hasShockPhase: false,
                            hasStress: false,
                            hasEscalation: false,
                            hasActionShape: false,
                            hasTemplateId: false,
                            hasRoute: false,
                            hasGate: false,
                            hasPolicy: false,
                            hasHardStop: false,
                            hasCooldown: false,
                            hasDrift: false,
                            hasResume: false,
                        },
                        labels: {},
                    }];
            }
            return [2 /*return*/];
        });
    });
}
/**
 * Resolve snapshot log path
 *
 * @returns Snapshot log file path
 */
function resolveSnapshotLogPath() {
    return (process.env.MERIDIAN_SNAPSHOTS_PATH ||
        path.join(os.homedir(), ".meridian", "snapshots.log"));
}
/**
 * Append snapshot to log (JSONL format)
 *
 * Purpose:
 *   Append snapshot to JSONL file (one snapshot per line).
 *   Append-only, never modifies existing lines.
 *
 * @param snapshot - Snapshot to append
 * @param cfg - Configuration (optional)
 * @returns Result with status and warnings
 */
function appendSnapshotV1(snapshot, cfg) {
    return __awaiter(this, void 0, void 0, function () {
        var warnings, logPath, dir, line, error_1;
        return __generator(this, function (_a) {
            switch (_a.label) {
                case 0:
                    warnings = [];
                    _a.label = 1;
                case 1:
                    _a.trys.push([1, 5, , 6]);
                    logPath = (cfg === null || cfg === void 0 ? void 0 : cfg.path) || resolveSnapshotLogPath();
                    dir = path.dirname(logPath);
                    if (!!fs.existsSync(dir)) return [3 /*break*/, 3];
                    return [4 /*yield*/, fs.promises.mkdir(dir, { recursive: true })];
                case 2:
                    _a.sent();
                    _a.label = 3;
                case 3:
                    line = JSON.stringify(snapshot) + "\n";
                    // Append to file
                    return [4 /*yield*/, fs.promises.appendFile(logPath, line, "utf-8")];
                case 4:
                    // Append to file
                    _a.sent();
                    return [2 /*return*/, {
                            status: "OK",
                            warnings: warnings,
                        }];
                case 5:
                    error_1 = _a.sent();
                    warnings.push("WARN_SNAPSHOT_WRITE_FAILED");
                    return [2 /*return*/, {
                            status: "ERROR",
                            warnings: warnings,
                        }];
                case 6: return [2 /*return*/];
            }
        });
    });
}
/**
 * Read recent snapshots from log
 *
 * @param cfg - Configuration (optional)
 * @param opts - Read options (optional)
 * @returns Snapshots array and warnings
 */
function readRecentSnapshotsV1(cfg, opts) {
    return __awaiter(this, void 0, void 0, function () {
        var warnings, snapshots, maxLines, logPath, content, lines, recentLines, _i, recentLines_1, line, parsed, error_2;
        return __generator(this, function (_a) {
            switch (_a.label) {
                case 0:
                    warnings = [];
                    snapshots = [];
                    maxLines = (opts === null || opts === void 0 ? void 0 : opts.maxLines) || 200;
                    _a.label = 1;
                case 1:
                    _a.trys.push([1, 3, , 4]);
                    logPath = (cfg === null || cfg === void 0 ? void 0 : cfg.path) || resolveSnapshotLogPath();
                    // Check if file exists
                    if (!fs.existsSync(logPath)) {
                        warnings.push("WARN_SNAPSHOT_LOG_NOT_FOUND");
                        return [2 /*return*/, { snapshots: snapshots, warnings: warnings }];
                    }
                    return [4 /*yield*/, fs.promises.readFile(logPath, "utf-8")];
                case 2:
                    content = _a.sent();
                    lines = content.split("\n").filter(function (line) { return line.trim() !== ""; });
                    recentLines = lines.slice(-maxLines);
                    // Parse each line
                    for (_i = 0, recentLines_1 = recentLines; _i < recentLines_1.length; _i++) {
                        line = recentLines_1[_i];
                        try {
                            parsed = JSON.parse(line);
                            // Basic validation
                            if (parsed.version === "v1.0" && parsed.ts && parsed.kind) {
                                snapshots.push(parsed);
                            }
                            else {
                                warnings.push("WARN_SNAPSHOT_PARSE_INVALID_SCHEMA");
                            }
                        }
                        catch (parseError) {
                            warnings.push("WARN_SNAPSHOT_PARSE_FAILED_LINE");
                            // Continue parsing other lines
                        }
                    }
                    return [2 /*return*/, { snapshots: snapshots, warnings: warnings }];
                case 3:
                    error_2 = _a.sent();
                    warnings.push("WARN_SNAPSHOT_READ_FAILED");
                    return [2 /*return*/, { snapshots: snapshots, warnings: warnings }];
                case 4: return [2 /*return*/];
            }
        });
    });
}
/**
 * Read filtered snapshots
 *
 * @param filter - Filter options
 * @param cfg - Configuration (optional)
 * @returns Filtered snapshots and warnings
 */
function readFilteredSnapshotsV1(filter, cfg) {
    return __awaiter(this, void 0, void 0, function () {
        var result, filteredSnapshots;
        return __generator(this, function (_a) {
            switch (_a.label) {
                case 0: return [4 /*yield*/, readRecentSnapshotsV1(cfg, {
                        maxLines: filter.maxLines,
                    })];
                case 1:
                    result = _a.sent();
                    filteredSnapshots = result.snapshots;
                    if (filter.status) {
                        filteredSnapshots = filteredSnapshots.filter(function (s) { return s.status === filter.status; });
                    }
                    if (filter.kind) {
                        filteredSnapshots = filteredSnapshots.filter(function (s) { return s.kind === filter.kind; });
                    }
                    return [2 /*return*/, {
                            snapshots: filteredSnapshots,
                            warnings: result.warnings,
                        }];
            }
        });
    });
}
