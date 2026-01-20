"use strict";
/**
 * PR179: v1.4 Spec Version Lock + Human ACK Gate v1 - Lock Evaluation
 *
 * Purpose:
 *   Evaluate spec lock status to determine if execution can proceed with new spec.
 *
 * Constitutional Constraints:
 *   - Fixed rules: Deterministic lock evaluation
 *   - Defensive: Never throws, always returns result
 *   - Safety: LOCKED_EXPIRED does not auto-unlock (observation label only)
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
exports.evaluateSpecLockV1 = evaluateSpecLockV1;
var store_1 = require("./store");
var guards_1 = require("./guards");
/**
 * Default config
 */
var DEFAULT_CONFIG = {
    ttlMs: 6 * 60 * 60 * 1000, // 6 hours
};
/**
 * Evaluate spec lock status
 *
 * @param cfg - Optional config override
 * @param pathOverride - Optional path override for testing
 * @returns Lock result
 */
function evaluateSpecLockV1(cfg, pathOverride) {
    return __awaiter(this, void 0, void 0, function () {
        var config, warnings, latestSpecRecord, latestSpec, latestAckedSpec, now, specAge, status_1, ttlLabel, error_1;
        return __generator(this, function (_a) {
            switch (_a.label) {
                case 0:
                    config = __assign(__assign({}, DEFAULT_CONFIG), cfg);
                    warnings = [];
                    _a.label = 1;
                case 1:
                    _a.trys.push([1, 4, , 5]);
                    return [4 /*yield*/, (0, store_1.readLatestSpecRecordV1)(pathOverride === null || pathOverride === void 0 ? void 0 : pathOverride.specLog)];
                case 2:
                    latestSpecRecord = _a.sent();
                    // Case A: No spec records
                    if (!latestSpecRecord) {
                        return [2 /*return*/, {
                                kind: "SPEC_LOCK_RESULT_V1",
                                status: "ACTIVE_OK",
                                activeSpec: "SPEC_NONE",
                                warnings: [(0, guards_1.buildLabelWarning)("INFO_NO_SPEC_RECORDS")],
                            }];
                    }
                    latestSpec = latestSpecRecord.specVersion;
                    return [4 /*yield*/, (0, store_1.readLatestAckedSpecV1)(pathOverride === null || pathOverride === void 0 ? void 0 : pathOverride.ackLog)];
                case 3:
                    latestAckedSpec = _a.sent();
                    // Case B: Spec exists, but no ACK at all
                    if (!latestAckedSpec) {
                        return [2 /*return*/, {
                                kind: "SPEC_LOCK_RESULT_V1",
                                status: "LOCKED_PENDING_ACK",
                                latestSpec: latestSpec,
                                activeSpec: undefined,
                                ttlLabel: "TTL_UNKNOWN",
                                warnings: [(0, guards_1.buildLabelWarning)("WARN_NO_ACK_FOUND")],
                            }];
                    }
                    // Case C: Latest spec matches latest ACKed spec
                    if (latestSpec === latestAckedSpec) {
                        return [2 /*return*/, {
                                kind: "SPEC_LOCK_RESULT_V1",
                                status: "ACTIVE_OK",
                                activeSpec: latestAckedSpec,
                                latestSpec: latestSpec,
                                ttlLabel: "TTL_OK",
                                warnings: [],
                            }];
                    }
                    now = Date.now();
                    specAge = now - latestSpecRecord.createdAt;
                    status_1 = "LOCKED_PENDING_ACK";
                    ttlLabel = "TTL_OK";
                    if (specAge > config.ttlMs) {
                        status_1 = "LOCKED_EXPIRED";
                        ttlLabel = "TTL_EXPIRED";
                        warnings.push((0, guards_1.buildLabelWarning)("WARN_SPEC_TTL_EXPIRED"));
                    }
                    else {
                        warnings.push((0, guards_1.buildLabelWarning)("WARN_SPEC_PENDING_ACK"));
                    }
                    return [2 /*return*/, {
                            kind: "SPEC_LOCK_RESULT_V1",
                            status: status_1,
                            activeSpec: latestAckedSpec, // Use old ACKed spec for execution
                            latestSpec: latestSpec,
                            ttlLabel: ttlLabel,
                            warnings: warnings,
                        }];
                case 4:
                    error_1 = _a.sent();
                    // Case E: Error during evaluation
                    return [2 /*return*/, {
                            kind: "SPEC_LOCK_RESULT_V1",
                            status: "ERROR",
                            warnings: [(0, guards_1.buildLabelWarning)("WARN_SPEC_LOCK_EVAL_FAILED")],
                        }];
                case 5: return [2 /*return*/];
            }
        });
    });
}
