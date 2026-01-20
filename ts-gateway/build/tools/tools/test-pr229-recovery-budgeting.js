"use strict";
// tools/test-pr229-recovery-budgeting.ts
// PR229: Recovery Budgeting v1 (暴走防止) - Comprehensive test
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
/**
 * Purpose:
 *   Test all 4 PR229 budget rules to prevent autonomous recovery runaway:
 *     Rule 1: Attempt limit (>=10 → ABANDON)
 *     Rule 2: Oscillation cooldown (CHG_EXCEEDED → DEFER BACKOFF_LONG)
 *     Rule 3: FAILED_MARKET cap (>=2/hour → DEFER MANUAL)
 *     Rule 4: IMMEDIATE rate limit (>=3/hour → DEFER BACKOFF_LONG)
 *
 * Test scenarios:
 *   1. Baseline: All budgets OK → ALLOW
 *   2. Rule 1 ABANDON: 10 attempts → ABANDON
 *   3. Rule 2 DEFER: CHG_EXCEEDED → DEFER BACKOFF_LONG
 *   4. Rule 3 DEFER: 2 FAILED_MARKET/hour → DEFER MANUAL
 *   5. Rule 4 DEFER: 3 IMMEDIATE/hour → DEFER BACKOFF_LONG
 *   6. Rule 4 Window Reset: Window expired → counts reset
 */
var supervisor_1 = require("../src/supervisor/supervisor");
var fs = __importStar(require("fs"));
var path = __importStar(require("path"));
var os = __importStar(require("os"));
function testRecoveryBudgeting() {
    return __awaiter(this, void 0, void 0, function () {
        var eventsPath, scenarios, passCount, failCount, _loop_1, _i, scenarios_1, scenario;
        var _this = this;
        return __generator(this, function (_a) {
            switch (_a.label) {
                case 0:
                    console.log("=== PR229: Recovery Budgeting v1 Test ===\n");
                    eventsPath = path.join(os.homedir(), ".meridian", "events.log");
                    // Clear events
                    console.log("Step 1: Clear test files");
                    if (fs.existsSync(eventsPath))
                        fs.unlinkSync(eventsPath);
                    scenarios = [
                        {
                            name: "Baseline: All budgets OK → ALLOW",
                            resumeState: {
                                recoveryAttemptCount: 0,
                                recoveryWindowAnchorTs: Date.now(),
                                recoveryImmediateCountInWindow: 0,
                                recoveryFailedMarketCountInWindow: 0,
                            },
                            oscChangeLevelStrategy: "CHG_LOW",
                            desiredDelayClass: "IMMEDIATE",
                            expectedBudgetAction: "ALLOW",
                            expectedBudgetAttemptStatus: "B0_OK",
                            expectedBudgetImmediateRateStatus: "R0_OK",
                            expectedBudgetFailedMarketRateStatus: "F0_OK",
                            expectedBudgetOscCooldownStatus: "C0_OK",
                        },
                        {
                            name: "Rule 1 ABANDON: 10 attempts → ABANDON",
                            resumeState: {
                                recoveryAttemptCount: 10,
                                recoveryWindowAnchorTs: Date.now(),
                                recoveryImmediateCountInWindow: 0,
                                recoveryFailedMarketCountInWindow: 0,
                            },
                            oscChangeLevelStrategy: "CHG_LOW",
                            desiredDelayClass: "IMMEDIATE",
                            expectedBudgetAction: "ABANDON",
                            expectedBudgetAttemptStatus: "B2_LIMIT_EXCEEDED",
                            expectedEventType: "RESUME_REEXEC_ABANDONED",
                            expectedAbandonReason: "BUDGET_LIMIT_EXCEEDED",
                        },
                        {
                            name: "Rule 2 DEFER: CHG_EXCEEDED → DEFER BACKOFF_LONG",
                            resumeState: {
                                recoveryAttemptCount: 0,
                                recoveryWindowAnchorTs: Date.now(),
                                recoveryImmediateCountInWindow: 0,
                                recoveryFailedMarketCountInWindow: 0,
                                strategyChangeCount: 12, // CHG_EXCEEDED (>10)
                                lastStrategyChangeTs: Date.now() - 30 * 60 * 1000, // 30 min ago (within 1h)
                            },
                            oscChangeLevelStrategy: "CHG_EXCEEDED",
                            desiredDelayClass: "IMMEDIATE",
                            expectedBudgetAction: "DEFER",
                            expectedBudgetOscCooldownStatus: "C1_COOLDOWN_ACTIVE",
                            expectedOverrideDelayClass: "BACKOFF_LONG",
                            expectedOverrideDelayOffsetLabel: "DELAY_15M",
                        },
                        {
                            name: "Rule 3 DEFER: 2 FAILED_MARKET/hour → DEFER MANUAL",
                            resumeState: {
                                recoveryAttemptCount: 0,
                                recoveryWindowAnchorTs: Date.now(),
                                recoveryImmediateCountInWindow: 0,
                                recoveryFailedMarketCountInWindow: 2, // At limit
                                orchLastStatus: "FAILED_MARKET",
                            },
                            oscChangeLevelStrategy: "CHG_LOW",
                            desiredDelayClass: "IMMEDIATE",
                            expectedBudgetAction: "DEFER",
                            expectedBudgetFailedMarketRateStatus: "F2_LIMIT_EXCEEDED",
                            expectedOverrideDelayClass: "MANUAL",
                            expectedOverrideDelayOffsetLabel: "DELAY_1H",
                        },
                        {
                            name: "Rule 4 DEFER: 3 IMMEDIATE/hour → DEFER BACKOFF_LONG",
                            resumeState: {
                                recoveryAttemptCount: 0,
                                recoveryWindowAnchorTs: Date.now(),
                                recoveryImmediateCountInWindow: 3, // At limit
                                recoveryFailedMarketCountInWindow: 0,
                            },
                            oscChangeLevelStrategy: "CHG_LOW",
                            desiredDelayClass: "IMMEDIATE",
                            expectedBudgetAction: "DEFER",
                            expectedBudgetImmediateRateStatus: "R2_LIMIT_EXCEEDED",
                            expectedOverrideDelayClass: "BACKOFF_LONG",
                            expectedOverrideDelayOffsetLabel: "DELAY_15M",
                        },
                        {
                            name: "Rule 4 Window Reset: Window expired → counts reset",
                            resumeState: {
                                recoveryAttemptCount: 0,
                                recoveryWindowAnchorTs: Date.now() - 2 * 60 * 60 * 1000, // 2 hours ago (expired)
                                recoveryImmediateCountInWindow: 3, // Stale count
                                recoveryFailedMarketCountInWindow: 2, // Stale count
                            },
                            oscChangeLevelStrategy: "CHG_LOW",
                            desiredDelayClass: "IMMEDIATE",
                            expectedBudgetAction: "ALLOW",
                            expectedBudgetImmediateRateStatus: "R0_OK", // Reset (window expired)
                            expectedBudgetFailedMarketRateStatus: "F0_OK", // Reset (window expired)
                        },
                    ];
                    passCount = 0;
                    failCount = 0;
                    _loop_1 = function (scenario) {
                        var testResumeId, mockState, mockStore, result, scenarioPass, content, lines, abandonEvents, event_1, content, lines, attemptEvents, event_2, action, status_1, status_2, status_3, status_4, delayClass, delayOffset;
                        return __generator(this, function (_b) {
                            switch (_b.label) {
                                case 0:
                                    console.log("\nScenario: ".concat(scenario.name));
                                    // Clear events for this scenario
                                    if (fs.existsSync(eventsPath))
                                        fs.unlinkSync(eventsPath);
                                    testResumeId = "RESUME_TEST_PR229_".concat(Date.now());
                                    mockState = {
                                        version: "v1",
                                        updatedAtTs: Date.now(),
                                        warnings: [],
                                        lastRun: {
                                            status: "STOPPED",
                                            warnings: [],
                                            resumeId: testResumeId,
                                        },
                                        resumeState: __assign({ status: "STOPPED", stopReason: "STOP_NO_ROUTE", stopAtTs: Date.now() - 300000, warnings: [], originStopCause: "TIMEOUT", lastPhaseLabel: "PHASE_NORMAL" }, scenario.resumeState),
                                    };
                                    mockStore = {
                                        readState: function () { return __awaiter(_this, void 0, void 0, function () {
                                            return __generator(this, function (_a) {
                                                return [2 /*return*/, ({
                                                        status: "OK",
                                                        state: mockState,
                                                        warnings: [],
                                                    })];
                                            });
                                        }); },
                                        writeState: function () { return __awaiter(_this, void 0, void 0, function () {
                                            return __generator(this, function (_a) {
                                                return [2 /*return*/, ({
                                                        status: "OK",
                                                        state: mockState,
                                                        warnings: [],
                                                    })];
                                            });
                                        }); },
                                        patchState: function () { return __awaiter(_this, void 0, void 0, function () {
                                            return __generator(this, function (_a) {
                                                return [2 /*return*/, ({
                                                        status: "OK",
                                                        state: mockState,
                                                        warnings: [],
                                                    })];
                                            });
                                        }); },
                                    };
                                    return [4 /*yield*/, (0, supervisor_1.runSupervisorOnceV1)(mockStore, {}, {
                                            evaluatePolicy: function () { return __awaiter(_this, void 0, void 0, function () {
                                                return __generator(this, function (_a) {
                                                    return [2 /*return*/, ({
                                                            allowExecution: true,
                                                            hardStopActive: false,
                                                            status: "ALLOW",
                                                            reasons: [],
                                                        })];
                                                });
                                            }); },
                                            getResumeInputs: function () { return __awaiter(_this, void 0, void 0, function () {
                                                return __generator(this, function (_a) {
                                                    return [2 /*return*/, ({
                                                            nowTs: Date.now(),
                                                            oracleStatus: "AVAILABLE",
                                                            gateStatus: "PASS",
                                                            phaseLabel: "PHASE_NORMAL",
                                                            routeAvailable: true,
                                                            hardStopActive: false,
                                                            policyEnvEnabled: true,
                                                        })];
                                                });
                                            }); },
                                            setRunPlanResumeFields: function () {
                                                // No-op for this test
                                            },
                                            runTwapExecution: function () { return __awaiter(_this, void 0, void 0, function () {
                                                return __generator(this, function (_a) {
                                                    return [2 /*return*/, {
                                                            status: "COMPLETED",
                                                            reasons: [],
                                                            runId: "test-run-next",
                                                        }];
                                                });
                                            }); },
                                        })];
                                case 1:
                                    result = _b.sent();
                                    // Wait for telemetry flush
                                    return [4 /*yield*/, new Promise(function (resolve) { return setTimeout(resolve, 100); })];
                                case 2:
                                    // Wait for telemetry flush
                                    _b.sent();
                                    scenarioPass = true;
                                    // Check for ABANDON action
                                    if (scenario.expectedEventType === "RESUME_REEXEC_ABANDONED") {
                                        if (result.action !== "ACTION_ABORT") {
                                            console.log("  \u2717 Expected ACTION_ABORT, got ".concat(result.action));
                                            scenarioPass = false;
                                        }
                                        // Verify ABANDONED event
                                        if (fs.existsSync(eventsPath)) {
                                            content = fs.readFileSync(eventsPath, "utf8");
                                            lines = content.trim().split("\n");
                                            abandonEvents = lines.filter(function (line) {
                                                return line.includes('"type":"RESUME_REEXEC_ABANDONED"');
                                            });
                                            if (abandonEvents.length > 0) {
                                                event_1 = JSON.parse(abandonEvents[abandonEvents.length - 1]);
                                                if (event_1.labels.abandon_reason !== scenario.expectedAbandonReason) {
                                                    console.log("  \u2717 Expected abandon_reason=".concat(scenario.expectedAbandonReason, ", got=").concat(event_1.labels.abandon_reason));
                                                    scenarioPass = false;
                                                }
                                                else {
                                                    console.log("  \u2713 ABANDONED event emitted with correct reason");
                                                }
                                            }
                                            else {
                                                console.log("  \u2717 No ABANDON event found");
                                                scenarioPass = false;
                                            }
                                        }
                                    }
                                    else {
                                        // Check RESUME_REEXEC_ATTEMPT event for budget labels
                                        if (fs.existsSync(eventsPath)) {
                                            content = fs.readFileSync(eventsPath, "utf8");
                                            lines = content.trim().split("\n");
                                            attemptEvents = lines.filter(function (line) {
                                                return line.includes('"type":"RESUME_REEXEC_ATTEMPT"');
                                            });
                                            if (attemptEvents.length > 0) {
                                                event_2 = JSON.parse(attemptEvents[attemptEvents.length - 1]);
                                                // Check budget action
                                                if (scenario.expectedBudgetAction) {
                                                    action = event_2.labels.resume_budget_action;
                                                    if (action !== scenario.expectedBudgetAction) {
                                                        console.log("  \u2717 Expected budget_action=".concat(scenario.expectedBudgetAction, ", got=").concat(action));
                                                        scenarioPass = false;
                                                    }
                                                    else {
                                                        console.log("  \u2713 budget_action=".concat(action));
                                                    }
                                                }
                                                // Check budget status labels
                                                if (scenario.expectedBudgetAttemptStatus) {
                                                    status_1 = event_2.labels.resume_budget_attempt_status;
                                                    if (status_1 !== scenario.expectedBudgetAttemptStatus) {
                                                        console.log("  \u2717 Expected budget_attempt_status=".concat(scenario.expectedBudgetAttemptStatus, ", got=").concat(status_1));
                                                        scenarioPass = false;
                                                    }
                                                    else {
                                                        console.log("  \u2713 budget_attempt_status=".concat(status_1));
                                                    }
                                                }
                                                if (scenario.expectedBudgetImmediateRateStatus) {
                                                    status_2 = event_2.labels.resume_budget_immediate_rate_status;
                                                    if (status_2 !== scenario.expectedBudgetImmediateRateStatus) {
                                                        console.log("  \u2717 Expected budget_immediate_rate_status=".concat(scenario.expectedBudgetImmediateRateStatus, ", got=").concat(status_2));
                                                        scenarioPass = false;
                                                    }
                                                    else {
                                                        console.log("  \u2713 budget_immediate_rate_status=".concat(status_2));
                                                    }
                                                }
                                                if (scenario.expectedBudgetFailedMarketRateStatus) {
                                                    status_3 = event_2.labels.resume_budget_failed_market_rate_status;
                                                    if (status_3 !== scenario.expectedBudgetFailedMarketRateStatus) {
                                                        console.log("  \u2717 Expected budget_failed_market_rate_status=".concat(scenario.expectedBudgetFailedMarketRateStatus, ", got=").concat(status_3));
                                                        scenarioPass = false;
                                                    }
                                                    else {
                                                        console.log("  \u2713 budget_failed_market_rate_status=".concat(status_3));
                                                    }
                                                }
                                                if (scenario.expectedBudgetOscCooldownStatus) {
                                                    status_4 = event_2.labels.resume_budget_osc_cooldown_status;
                                                    if (status_4 !== scenario.expectedBudgetOscCooldownStatus) {
                                                        console.log("  \u2717 Expected budget_osc_cooldown_status=".concat(scenario.expectedBudgetOscCooldownStatus, ", got=").concat(status_4));
                                                        scenarioPass = false;
                                                    }
                                                    else {
                                                        console.log("  \u2713 budget_osc_cooldown_status=".concat(status_4));
                                                    }
                                                }
                                                // Check override timing (if DEFER)
                                                if (scenario.expectedOverrideDelayClass) {
                                                    delayClass = event_2.labels.resume_delay_class;
                                                    if (delayClass !== scenario.expectedOverrideDelayClass) {
                                                        console.log("  \u2717 Expected delay_class=".concat(scenario.expectedOverrideDelayClass, ", got=").concat(delayClass));
                                                        scenarioPass = false;
                                                    }
                                                    else {
                                                        console.log("  \u2713 delay_class=".concat(delayClass, " (budget override)"));
                                                    }
                                                }
                                                if (scenario.expectedOverrideDelayOffsetLabel) {
                                                    delayOffset = event_2.labels.resume_delay_offset_label;
                                                    if (delayOffset !== scenario.expectedOverrideDelayOffsetLabel) {
                                                        console.log("  \u2717 Expected delay_offset_label=".concat(scenario.expectedOverrideDelayOffsetLabel, ", got=").concat(delayOffset));
                                                        scenarioPass = false;
                                                    }
                                                    else {
                                                        console.log("  \u2713 delay_offset_label=".concat(delayOffset, " (budget override)"));
                                                    }
                                                }
                                            }
                                            else {
                                                console.log("  \u2717 No RESUME_REEXEC_ATTEMPT event found");
                                                scenarioPass = false;
                                            }
                                        }
                                        else {
                                            console.log("  \u2717 Events file not found");
                                            scenarioPass = false;
                                        }
                                    }
                                    if (scenarioPass) {
                                        console.log("  \u2713 Scenario PASSED");
                                        passCount++;
                                    }
                                    else {
                                        console.log("  \u2717 Scenario FAILED");
                                        failCount++;
                                    }
                                    return [2 /*return*/];
                            }
                        });
                    };
                    _i = 0, scenarios_1 = scenarios;
                    _a.label = 1;
                case 1:
                    if (!(_i < scenarios_1.length)) return [3 /*break*/, 4];
                    scenario = scenarios_1[_i];
                    return [5 /*yield**/, _loop_1(scenario)];
                case 2:
                    _a.sent();
                    _a.label = 3;
                case 3:
                    _i++;
                    return [3 /*break*/, 1];
                case 4:
                    console.log("\n=== Test Summary ===");
                    console.log("Total scenarios: ".concat(scenarios.length));
                    console.log("Passed: ".concat(passCount));
                    console.log("Failed: ".concat(failCount));
                    if (failCount === 0) {
                        console.log("\n✓ All PR229 recovery budgeting tests PASSED!");
                    }
                    else {
                        console.log("\n\u2717 ".concat(failCount, " test(s) FAILED"));
                        process.exit(1);
                    }
                    console.log("\n=== AC Verification ===");
                    console.log("AC1: Attempt Budget (>=10 → ABANDON) - ✓");
                    console.log("AC2: IMMEDIATE Rate Limit (>=3/hour → DEFER) - ✓");
                    console.log("AC3: FAILED_MARKET Cap (>=2/hour → DEFER) - ✓");
                    console.log("AC4: Oscillation Cooldown (CHG_EXCEEDED → DEFER) - ✓");
                    console.log("AC5: Window Reset (>1 hour → counts reset) - ✓");
                    console.log("\n=== Test Complete ===");
                    return [2 /*return*/];
            }
        });
    });
}
testRecoveryBudgeting().catch(function (e) {
    console.error("Fatal error:", e);
    process.exit(1);
});
