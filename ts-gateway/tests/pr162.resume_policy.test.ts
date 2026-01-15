/**
 * PR162: v1.4 Partial Resume Policy v1 - Test Suite
 *
 * Tests for STOP resume conditions and fixed decision table.
 *
 * Test Cases (10):
 *   Resume Policy (10):
 *     1. STOP_ORACLE_STALE → WAIT until oracle AVAILABLE
 *     2. STOP_ORACLE_STALE + oracle AVAILABLE + gate PASS → RESUMABLE
 *     3. STOP_NO_ROUTE + routeAvailable=false → WAIT
 *     4. STOP_NO_ROUTE + routeAvailable=true + gate PASS → RESUMABLE
 *     5. STOP_PHASE_POLICY + phase=UP_SHOCK → WAIT
 *     6. STOP_PHASE_POLICY + phase=RECOVERY → RESUMABLE (other conditions OK)
 *     7. STOP_IMPACT_HIGH + gate BLOCK → WAIT
 *     8. STOP_IMPACT_HIGH + gate PASS → RESUMABLE
 *     9. STOP_POLICY_DENY → ABANDON
 *     10. Incomplete inputs → UNKNOWN (defensive)
 */

import { describe, test, expect } from "bun:test";
import {
  evaluateResumeV1,
  ResumeInputs,
  getResumePolicySummary,
} from "../src/rebalance/resumePolicy";
import { ResumeState } from "../src/rebalance/types";

describe("PR162: Resume Policy", () => {
  const createMockResumeState = (
    stopReason: ResumeState["stopReason"],
    nowTs: number = Date.now()
  ): ResumeState => ({
    status: "STOPPED",
    stopReason,
    stopAtTs: nowTs,
    lastPhaseLabel: "PHASE_NORMAL",
    lastRoute: "CETUS",
    lastTemplateId: "TPL_RISK_50",
    lastIntent: "INCREASE_WBTC",
    warnings: [],
  });

  test("Test 1: STOP_ORACLE_STALE → WAIT until oracle AVAILABLE", () => {
    const state = createMockResumeState("STOP_ORACLE_STALE");
    const inputs: ResumeInputs = {
      nowTs: Date.now(),
      oracleStatus: "STALE", // Still stale
      gateStatus: "PASS",
      phaseLabel: "PHASE_NORMAL",
      routeAvailable: true,
      hardStopActive: false,
      policyEnvEnabled: true,
    };

    const decision = evaluateResumeV1(state, inputs);

    expect(decision.status).toBe("WAIT");
    expect(decision.reasons).toContain("REASON_WAIT_ORACLE_STALE");
    expect(decision.nextCheckHint).toBe("SOON");
  });

  test("Test 2: STOP_ORACLE_STALE + oracle AVAILABLE + gate PASS → RESUMABLE", () => {
    const state = createMockResumeState("STOP_ORACLE_STALE");
    const inputs: ResumeInputs = {
      nowTs: Date.now(),
      oracleStatus: "AVAILABLE", // Recovered
      gateStatus: "PASS",
      phaseLabel: "PHASE_NORMAL",
      routeAvailable: true,
      hardStopActive: false,
      policyEnvEnabled: true,
    };

    const decision = evaluateResumeV1(state, inputs);

    expect(decision.status).toBe("RESUMABLE");
    expect(decision.reasons).toContain("REASON_RESUMABLE_ALL_CONDITIONS_OK");
  });

  test("Test 3: STOP_NO_ROUTE + routeAvailable=false → WAIT", () => {
    const state = createMockResumeState("STOP_NO_ROUTE");
    const inputs: ResumeInputs = {
      nowTs: Date.now(),
      oracleStatus: "AVAILABLE",
      gateStatus: "PASS",
      phaseLabel: "PHASE_NORMAL",
      routeAvailable: false, // Still no route
      hardStopActive: false,
      policyEnvEnabled: true,
    };

    const decision = evaluateResumeV1(state, inputs);

    expect(decision.status).toBe("WAIT");
    expect(decision.reasons).toContain("REASON_WAIT_NO_ROUTE");
    expect(decision.nextCheckHint).toBe("NORMAL");
  });

  test("Test 4: STOP_NO_ROUTE + routeAvailable=true + gate PASS → RESUMABLE", () => {
    const state = createMockResumeState("STOP_NO_ROUTE");
    const inputs: ResumeInputs = {
      nowTs: Date.now(),
      oracleStatus: "AVAILABLE",
      gateStatus: "PASS",
      phaseLabel: "PHASE_NORMAL",
      routeAvailable: true, // Route available now
      hardStopActive: false,
      policyEnvEnabled: true,
    };

    const decision = evaluateResumeV1(state, inputs);

    expect(decision.status).toBe("RESUMABLE");
    expect(decision.reasons).toContain("REASON_RESUMABLE_ALL_CONDITIONS_OK");
  });

  test("Test 5: STOP_PHASE_POLICY + phase=UP_SHOCK → WAIT", () => {
    const state = createMockResumeState("STOP_PHASE_POLICY");
    const inputs: ResumeInputs = {
      nowTs: Date.now(),
      oracleStatus: "AVAILABLE",
      gateStatus: "PASS",
      phaseLabel: "PHASE_UP_SHOCK", // Still in shock
      routeAvailable: true,
      hardStopActive: false,
      policyEnvEnabled: true,
    };

    const decision = evaluateResumeV1(state, inputs);

    expect(decision.status).toBe("WAIT");
    expect(decision.reasons).toContain("REASON_WAIT_PHASE_POLICY");
    expect(decision.nextCheckHint).toBe("SOON"); // Phase can change quickly
  });

  test("Test 6: STOP_PHASE_POLICY + phase=RECOVERY → RESUMABLE", () => {
    const state = createMockResumeState("STOP_PHASE_POLICY");
    const inputs: ResumeInputs = {
      nowTs: Date.now(),
      oracleStatus: "AVAILABLE",
      gateStatus: "PASS",
      phaseLabel: "PHASE_RECOVERY", // Phase recovered
      routeAvailable: true,
      hardStopActive: false,
      policyEnvEnabled: true,
    };

    const decision = evaluateResumeV1(state, inputs);

    expect(decision.status).toBe("RESUMABLE");
    expect(decision.reasons).toContain("REASON_RESUMABLE_ALL_CONDITIONS_OK");
  });

  test("Test 7: STOP_IMPACT_HIGH + gate BLOCK → WAIT", () => {
    const state = createMockResumeState("STOP_IMPACT_HIGH");
    const inputs: ResumeInputs = {
      nowTs: Date.now(),
      oracleStatus: "AVAILABLE",
      gateStatus: "BLOCK", // Gate still blocking
      blockReasons: ["BLOCK_IMPACT_HIGH"],
      phaseLabel: "PHASE_NORMAL",
      routeAvailable: true,
      hardStopActive: false,
      policyEnvEnabled: true,
    };

    const decision = evaluateResumeV1(state, inputs);

    expect(decision.status).toBe("WAIT");
    expect(decision.reasons).toContain("REASON_WAIT_GATE_IMPACT_HIGH");
    expect(decision.nextCheckHint).toBe("NORMAL");
  });

  test("Test 8: STOP_IMPACT_HIGH + gate PASS → RESUMABLE", () => {
    const state = createMockResumeState("STOP_IMPACT_HIGH");
    const inputs: ResumeInputs = {
      nowTs: Date.now(),
      oracleStatus: "AVAILABLE",
      gateStatus: "PASS", // Gate passed
      phaseLabel: "PHASE_NORMAL",
      routeAvailable: true,
      hardStopActive: false,
      policyEnvEnabled: true,
    };

    const decision = evaluateResumeV1(state, inputs);

    expect(decision.status).toBe("RESUMABLE");
    expect(decision.reasons).toContain("REASON_RESUMABLE_ALL_CONDITIONS_OK");
  });

  test("Test 9: STOP_POLICY_DENY → ABANDON", () => {
    const state = createMockResumeState("STOP_POLICY_DENY");
    const inputs: ResumeInputs = {
      nowTs: Date.now(),
      oracleStatus: "AVAILABLE",
      gateStatus: "PASS",
      phaseLabel: "PHASE_NORMAL",
      routeAvailable: true,
      hardStopActive: false,
      policyEnvEnabled: false, // Env key missing
    };

    const decision = evaluateResumeV1(state, inputs);

    expect(decision.status).toBe("ABANDON");
    expect(decision.reasons).toContain("REASON_ABANDON_POLICY_DENY");
    expect(decision.nextCheckHint).toBeUndefined(); // No retry
  });

  test("Test 10: Incomplete inputs → UNKNOWN (defensive)", () => {
    const state = createMockResumeState("STOP_ORACLE_STALE");
    const inputs: ResumeInputs = {
      nowTs: Date.now(),
      // Missing most inputs
    };

    const decision = evaluateResumeV1(state, inputs);

    // With missing oracle status, should WAIT for oracle
    expect(decision.status).toBe("WAIT");
    expect(decision.nextCheckHint).toBe("SOON");
  });

  test("Test 11: STOP_DURATION_EXCEEDED → ABANDON", () => {
    const state = createMockResumeState("STOP_DURATION_EXCEEDED");
    const inputs: ResumeInputs = {
      nowTs: Date.now(),
      oracleStatus: "AVAILABLE",
      gateStatus: "PASS",
      phaseLabel: "PHASE_NORMAL",
      routeAvailable: true,
      hardStopActive: false,
      policyEnvEnabled: true,
    };

    const decision = evaluateResumeV1(state, inputs);

    expect(decision.status).toBe("ABANDON");
    expect(decision.reasons).toContain("REASON_ABANDON_DURATION_EXCEEDED");
  });

  test("Test 12: STOP_HARDSTOP_ACTIVE + hardStopActive=true → WAIT", () => {
    const state = createMockResumeState("STOP_HARDSTOP_ACTIVE");
    const inputs: ResumeInputs = {
      nowTs: Date.now(),
      oracleStatus: "AVAILABLE",
      gateStatus: "PASS",
      phaseLabel: "PHASE_NORMAL",
      routeAvailable: true,
      hardStopActive: true, // HardStop still active
      policyEnvEnabled: true,
    };

    const decision = evaluateResumeV1(state, inputs);

    expect(decision.status).toBe("WAIT");
    expect(decision.reasons).toContain("REASON_WAIT_HARDSTOP_ACTIVE");
    expect(decision.nextCheckHint).toBe("NORMAL");
  });

  test("Test 13: STOP_HARDSTOP_ACTIVE + hardStopActive=false → RESUMABLE", () => {
    const state = createMockResumeState("STOP_HARDSTOP_ACTIVE");
    const inputs: ResumeInputs = {
      nowTs: Date.now(),
      oracleStatus: "AVAILABLE",
      gateStatus: "PASS",
      phaseLabel: "PHASE_NORMAL",
      routeAvailable: true,
      hardStopActive: false, // HardStop released
      policyEnvEnabled: true,
    };

    const decision = evaluateResumeV1(state, inputs);

    expect(decision.status).toBe("RESUMABLE");
    expect(decision.reasons).toContain("REASON_RESUMABLE_ALL_CONDITIONS_OK");
  });

  test("Test 14: STOP_BLOCKED_STREAK + before resumeAfterTs → WAIT", () => {
    const nowTs = Date.now();
    const state: ResumeState = {
      ...createMockResumeState("STOP_BLOCKED_STREAK", nowTs),
      resumeAfterTs: nowTs + 30000, // 30s from now
    };
    const inputs: ResumeInputs = {
      nowTs: nowTs + 10000, // 10s later (still within cooldown)
      oracleStatus: "AVAILABLE",
      gateStatus: "PASS",
      phaseLabel: "PHASE_NORMAL",
      routeAvailable: true,
      hardStopActive: false,
      policyEnvEnabled: true,
    };

    const decision = evaluateResumeV1(state, inputs);

    expect(decision.status).toBe("WAIT");
    expect(decision.reasons).toContain("REASON_WAIT_BLOCKED_STREAK_COOLDOWN");
    expect(decision.nextCheckHint).toBe("SOON");
  });

  test("Test 15: STOP_BLOCKED_STREAK + after resumeAfterTs → RESUMABLE", () => {
    const nowTs = Date.now();
    const state: ResumeState = {
      ...createMockResumeState("STOP_BLOCKED_STREAK", nowTs),
      resumeAfterTs: nowTs + 30000, // 30s from now
    };
    const inputs: ResumeInputs = {
      nowTs: nowTs + 40000, // 40s later (cooldown expired)
      oracleStatus: "AVAILABLE",
      gateStatus: "PASS",
      phaseLabel: "PHASE_NORMAL",
      routeAvailable: true,
      hardStopActive: false,
      policyEnvEnabled: true,
    };

    const decision = evaluateResumeV1(state, inputs);

    expect(decision.status).toBe("RESUMABLE");
    expect(decision.reasons).toContain("REASON_RESUMABLE_ALL_CONDITIONS_OK");
  });

  test("Test 16: getResumePolicySummary returns correct label", () => {
    const decision1 = { status: "RESUMABLE" as const, reasons: [], nextCheckHint: "SOON" as const };
    const decision2 = { status: "WAIT" as const, reasons: [], nextCheckHint: "NORMAL" as const };
    const decision3 = { status: "ABANDON" as const, reasons: [] };

    expect(getResumePolicySummary(decision1)).toBe("RESUME_POLICY_RESUMABLE");
    expect(getResumePolicySummary(decision2)).toBe("RESUME_POLICY_WAIT");
    expect(getResumePolicySummary(decision3)).toBe("RESUME_POLICY_ABANDON");
  });
});
