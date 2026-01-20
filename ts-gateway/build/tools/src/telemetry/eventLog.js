"use strict";
/**
 * PR164: v1.4 Event Log (READ-ONLY)
 *
 * Purpose:
 *   Append-only JSONL audit log for telemetry events.
 *
 * Constitutional Constraints:
 *   - READ-ONLY: Record facts only, no learning, no optimization
 *   - Defensive: Never throws, returns warnings on failure
 *   - Append-only: JSONL format (1 event = 1 line)
 *   - Safe defaults: Missing file → empty array, corrupted lines → skip with warning
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
exports.resolveEventLogPath = resolveEventLogPath;
exports.appendEventV1 = appendEventV1;
exports.readRecentEventsV1 = readRecentEventsV1;
exports.readFilteredEventsV1 = readFilteredEventsV1;
var fs = __importStar(require("fs"));
var path = __importStar(require("path"));
var os = __importStar(require("os"));
var guards_1 = require("./guards");
/**
 * Resolve event log path (from env or default)
 *
 * @returns Event log file path
 */
function resolveEventLogPath() {
    return (process.env.MERIDIAN_EVENTS_PATH ||
        path.join(os.homedir(), ".meridian", "events.log"));
}
/**
 * Append event to log (defensive)
 *
 * @param event - Event to append
 * @param cfg - Configuration (optional)
 * @returns Result with ok flag and warnings
 */
function appendEventV1(event, cfg) {
    return __awaiter(this, void 0, void 0, function () {
        var warnings, logPath, sanitizedEvent, dir, line, error_1;
        return __generator(this, function (_a) {
            switch (_a.label) {
                case 0:
                    warnings = [];
                    _a.label = 1;
                case 1:
                    _a.trys.push([1, 5, , 6]);
                    logPath = (cfg === null || cfg === void 0 ? void 0 : cfg.path) || resolveEventLogPath();
                    sanitizedEvent = (0, guards_1.validateEventV1)(event);
                    dir = path.dirname(logPath);
                    if (!!fs.existsSync(dir)) return [3 /*break*/, 3];
                    return [4 /*yield*/, fs.promises.mkdir(dir, { recursive: true })];
                case 2:
                    _a.sent();
                    _a.label = 3;
                case 3:
                    line = JSON.stringify(sanitizedEvent) + "\n";
                    // Append to file
                    return [4 /*yield*/, fs.promises.appendFile(logPath, line, "utf-8")];
                case 4:
                    // Append to file
                    _a.sent();
                    return [2 /*return*/, {
                            ok: true,
                            warnings: warnings,
                        }];
                case 5:
                    error_1 = _a.sent();
                    warnings.push("WARN_EVENT_APPEND_FAILED");
                    return [2 /*return*/, {
                            ok: false,
                            warnings: warnings,
                        }];
                case 6: return [2 /*return*/];
            }
        });
    });
}
/**
 * Read recent events from log (defensive)
 *
 * @param cfg - Configuration (optional)
 * @param opts - Read options (optional)
 * @returns Events array and warnings
 */
function readRecentEventsV1(cfg, opts) {
    return __awaiter(this, void 0, void 0, function () {
        var warnings, events, maxLines, logPath, content, lines, recentLines, _i, recentLines_1, line, parsed, error_2;
        return __generator(this, function (_a) {
            switch (_a.label) {
                case 0:
                    warnings = [];
                    events = [];
                    maxLines = (opts === null || opts === void 0 ? void 0 : opts.maxLines) || 200;
                    _a.label = 1;
                case 1:
                    _a.trys.push([1, 3, , 4]);
                    logPath = (cfg === null || cfg === void 0 ? void 0 : cfg.path) || resolveEventLogPath();
                    // Check if file exists
                    if (!fs.existsSync(logPath)) {
                        warnings.push("WARN_EVENT_LOG_NOT_FOUND");
                        return [2 /*return*/, { events: events, warnings: warnings }];
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
                            // Basic validation (defensive)
                            if (parsed.v === "v1" && parsed.ts && parsed.type) {
                                events.push(parsed);
                            }
                            else {
                                warnings.push("WARN_EVENT_PARSE_INVALID_SCHEMA");
                            }
                        }
                        catch (parseError) {
                            warnings.push("WARN_EVENT_PARSE_FAILED_LINE");
                            // Continue parsing other lines
                        }
                    }
                    return [2 /*return*/, { events: events, warnings: warnings }];
                case 3:
                    error_2 = _a.sent();
                    warnings.push("WARN_EVENT_READ_FAILED");
                    return [2 /*return*/, { events: events, warnings: warnings }];
                case 4: return [2 /*return*/];
            }
        });
    });
}
/**
 * Read events with filter (defensive)
 *
 * @param filter - Filter options
 * @param cfg - Configuration (optional)
 * @returns Filtered events and warnings
 */
function readFilteredEventsV1(filter, cfg) {
    return __awaiter(this, void 0, void 0, function () {
        var result, filteredEvents;
        return __generator(this, function (_a) {
            switch (_a.label) {
                case 0: return [4 /*yield*/, readRecentEventsV1(cfg, { maxLines: filter.maxLines })];
                case 1:
                    result = _a.sent();
                    filteredEvents = result.events;
                    if (filter.type) {
                        filteredEvents = filteredEvents.filter(function (e) { return e.type === filter.type; });
                    }
                    if (filter.level) {
                        filteredEvents = filteredEvents.filter(function (e) { return e.level === filter.level; });
                    }
                    return [2 /*return*/, {
                            events: filteredEvents,
                            warnings: result.warnings,
                        }];
            }
        });
    });
}
