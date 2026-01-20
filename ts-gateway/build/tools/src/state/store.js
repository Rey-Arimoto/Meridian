"use strict";
/**
 * PR163: v1.4 State Store (READ-ONLY)
 *
 * Purpose:
 *   Persistent state storage with atomic writes and defensive reads.
 *
 * Constitutional Constraints:
 *   - READ-ONLY: No learning, no optimization
 *   - Defensive: Never throws, returns status + warnings
 *   - Atomic writes: tmp→rename to prevent corruption
 *   - Safe defaults: Missing file → empty state
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
exports.FileStateStore = void 0;
exports.createFileStateStore = createFileStateStore;
var fs = __importStar(require("fs"));
var path = __importStar(require("path"));
var os = __importStar(require("os"));
var types_1 = require("./types");
/**
 * File-based state store
 */
var FileStateStore = /** @class */ (function () {
    function FileStateStore(filePath) {
        this.filePath =
            filePath ||
                process.env.MERIDIAN_STATE_PATH ||
                path.join(os.homedir(), ".meridian", "state.json");
    }
    /**
     * Read state from file (defensive)
     */
    FileStateStore.prototype.readState = function () {
        return __awaiter(this, void 0, void 0, function () {
            var warnings, content, parsed, error_1;
            return __generator(this, function (_a) {
                switch (_a.label) {
                    case 0:
                        warnings = [];
                        _a.label = 1;
                    case 1:
                        _a.trys.push([1, 3, , 4]);
                        // Check if file exists
                        if (!fs.existsSync(this.filePath)) {
                            warnings.push("WARN_STATE_FILE_NOT_FOUND");
                            return [2 /*return*/, {
                                    status: "OK",
                                    state: (0, types_1.createEmptyStateV1)(),
                                    warnings: warnings,
                                }];
                        }
                        return [4 /*yield*/, fs.promises.readFile(this.filePath, "utf-8")];
                    case 2:
                        content = _a.sent();
                        parsed = JSON.parse(content);
                        // Validate version
                        if (parsed.version !== "v1") {
                            warnings.push("WARN_STATE_VERSION_MISMATCH");
                            return [2 /*return*/, {
                                    status: "ERROR",
                                    state: (0, types_1.createEmptyStateV1)(),
                                    warnings: warnings,
                                }];
                        }
                        return [2 /*return*/, {
                                status: "OK",
                                state: parsed,
                                warnings: warnings,
                            }];
                    case 3:
                        error_1 = _a.sent();
                        warnings.push("WARN_STATE_READ_ERROR");
                        if (error_1 instanceof SyntaxError) {
                            warnings.push("WARN_STATE_JSON_CORRUPT");
                        }
                        return [2 /*return*/, {
                                status: "ERROR",
                                state: (0, types_1.createEmptyStateV1)(),
                                warnings: warnings,
                            }];
                    case 4: return [2 /*return*/];
                }
            });
        });
    };
    /**
     * Write state to file (atomic)
     */
    FileStateStore.prototype.writeState = function (next) {
        return __awaiter(this, void 0, void 0, function () {
            var warnings, dir, content, tmpPath, error_2;
            return __generator(this, function (_a) {
                switch (_a.label) {
                    case 0:
                        warnings = [];
                        _a.label = 1;
                    case 1:
                        _a.trys.push([1, 6, , 7]);
                        dir = path.dirname(this.filePath);
                        if (!!fs.existsSync(dir)) return [3 /*break*/, 3];
                        return [4 /*yield*/, fs.promises.mkdir(dir, { recursive: true })];
                    case 2:
                        _a.sent();
                        _a.label = 3;
                    case 3:
                        // Update timestamp
                        next.updatedAtTs = Date.now();
                        content = JSON.stringify(next, null, 2);
                        tmpPath = "".concat(this.filePath, ".tmp");
                        return [4 /*yield*/, fs.promises.writeFile(tmpPath, content, "utf-8")];
                    case 4:
                        _a.sent();
                        return [4 /*yield*/, fs.promises.rename(tmpPath, this.filePath)];
                    case 5:
                        _a.sent();
                        return [2 /*return*/, {
                                status: "OK",
                                warnings: warnings,
                            }];
                    case 6:
                        error_2 = _a.sent();
                        warnings.push("WARN_STATE_WRITE_ERROR");
                        return [2 /*return*/, {
                                status: "ERROR",
                                warnings: warnings,
                            }];
                    case 7: return [2 /*return*/];
                }
            });
        });
    };
    /**
     * Patch state (read-modify-write)
     */
    FileStateStore.prototype.patchState = function (patch) {
        return __awaiter(this, void 0, void 0, function () {
            var warnings, readResult, next, writeResult, error_3;
            return __generator(this, function (_a) {
                switch (_a.label) {
                    case 0:
                        warnings = [];
                        _a.label = 1;
                    case 1:
                        _a.trys.push([1, 4, , 5]);
                        return [4 /*yield*/, this.readState()];
                    case 2:
                        readResult = _a.sent();
                        warnings.push.apply(warnings, readResult.warnings);
                        if (readResult.status === "ERROR") {
                            return [2 /*return*/, {
                                    status: "ERROR",
                                    state: readResult.state,
                                    warnings: warnings,
                                }];
                        }
                        next = __assign(__assign(__assign({}, readResult.state), patch), { updatedAtTs: Date.now() });
                        return [4 /*yield*/, this.writeState(next)];
                    case 3:
                        writeResult = _a.sent();
                        warnings.push.apply(warnings, writeResult.warnings);
                        if (writeResult.status === "ERROR") {
                            return [2 /*return*/, {
                                    status: "ERROR",
                                    state: next,
                                    warnings: warnings,
                                }];
                        }
                        return [2 /*return*/, {
                                status: "OK",
                                state: next,
                                warnings: warnings,
                            }];
                    case 4:
                        error_3 = _a.sent();
                        warnings.push("WARN_STATE_PATCH_ERROR");
                        return [2 /*return*/, {
                                status: "ERROR",
                                state: (0, types_1.createEmptyStateV1)(),
                                warnings: warnings,
                            }];
                    case 5: return [2 /*return*/];
                }
            });
        });
    };
    return FileStateStore;
}());
exports.FileStateStore = FileStateStore;
/**
 * Create file state store
 *
 * @param filePath - Optional file path (defaults to ~/.meridian/state.json)
 * @returns State store instance
 */
function createFileStateStore(filePath) {
    return new FileStateStore(filePath);
}
