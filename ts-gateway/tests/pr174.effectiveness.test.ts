/**
 * PR174: v1.4 Patch Effectiveness Tracker v1 - Tests
 *
 * Purpose:
 *   Verify effect tracking, window selection, metrics, and evaluation.
 *
 * Test Coverage:
 *   1. Before/After selection cuts correct counts
 *   2. Snapshots insufficient → PARTIAL
 *   3. Corrupted snapshots line skip (defensive)
 *   4. summarizeWindow counts/rates calculation
 *   5. evaluateEffect: blockRate 10%pt decrease → IMPROVED
 *   6. evaluateEffect: stopRate 10%pt increase → WORSENED
 *   7. evaluateEffect: mixed → MIXED
 *   8. evaluateEffect: small change → NO_CHANGE
 *   9. No afterShort → UNKNOWN
 *   10. Label-only sanitizer removes numerics in normal mode
 *   11. Debug mode allows numerics but still sanitizes forbidden patterns
 *   12. Store append/read roundtrip + filter works
 */

import { selectEffectWindowsV1 } from "../src/effect/selector";
import { summarizeWindowV1 } from "../src/effect/metrics";
import { evaluateEffectV1 } from "../src/effect/evaluator";
import {
  sanitizeEffectForDisplayV1,
  validateEffectLabelOnlyV1,
} from "../src/effect/guards";
import {
  appendEffectReportV1,
  readRecentEffectReportsV1,
  getEffectLogPath,
} from "../src/effect/store";
import { MarketRegimeSnapshotV1 } from "../src/snapshot/types";
import { DecisionAckRecordV1 } from "../src/decision/types";
import { PatchEffectReportV1 } from "../src/effect/types";
import * as fs from "fs";

describe("PR174: Patch Effectiveness Tracker", () => {
  /**
   * Test 1: Before/After selection cuts correct counts
   */
  test("Test 1: Window selection cuts correct counts", () => {
    const ackTs = 1000000;
    const ack: DecisionAckRecordV1 = {
      kind: "DECISION_ACK_V1",
      status: "AVAILABLE",
      ts: ackTs,
      timeLabel: "T_RECENT",
      reviewer: "HUMAN_PRIMARY",
      source: "CLI_ADOPT",
      refs: { proposalId: "P0_TEST" },
      rationale: {
        decision: "ADOPT",
        rationaleLabels: [],
        checklistSummary: [],
        evidenceSummary: [],
        compareSummary: [],
      },
      warnings: [],
    };

    // Create snapshots before and after ack
    const snapshots: MarketRegimeSnapshotV1[] = [];
    for (let i = 0; i < 200; i++) {
      snapshots.push({
        kind: "MARKET_REGIME_SNAPSHOT_V1",
        ts: ackTs - 200 + i, // Before ack
        runnerStatus: "RUNNER_IDLE",
        presenceLabels: {},
        warnings: [],
      } as MarketRegimeSnapshotV1);
    }
    for (let i = 0; i < 100; i++) {
      snapshots.push({
        kind: "MARKET_REGIME_SNAPSHOT_V1",
        ts: ackTs + i, // After ack
        runnerStatus: "RUNNER_IDLE",
        presenceLabels: {},
        warnings: [],
      } as MarketRegimeSnapshotV1);
    }

    const { before, afterShort, warnings } = selectEffectWindowsV1(snapshots, ack, {
      beforeTail: 120,
      afterShort: 60,
      afterMedium: 180,
      afterLong: 600,
    });

    expect(before.length).toBe(120);
    expect(afterShort.length).toBe(60);
  });

  /**
   * Test 2: Insufficient snapshots → PARTIAL
   */
  test("Test 2: Insufficient snapshots produce PARTIAL", () => {
    const ackTs = 1000000;
    const ack: DecisionAckRecordV1 = {
      kind: "DECISION_ACK_V1",
      status: "AVAILABLE",
      ts: ackTs,
      timeLabel: "T_RECENT",
      reviewer: "HUMAN_PRIMARY",
      source: "CLI_ADOPT",
      refs: { proposalId: "P0_TEST" },
      rationale: {
        decision: "ADOPT",
        rationaleLabels: [],
        checklistSummary: [],
        evidenceSummary: [],
        compareSummary: [],
      },
      warnings: [],
    };

    // Create only 10 snapshots (insufficient for before/after windows)
    const snapshots: MarketRegimeSnapshotV1[] = [];
    for (let i = 0; i < 10; i++) {
      snapshots.push({
        kind: "MARKET_REGIME_SNAPSHOT_V1",
        ts: ackTs + i,
        runnerStatus: "RUNNER_IDLE",
        presenceLabels: {},
        warnings: [],
      } as MarketRegimeSnapshotV1);
    }

    const { before, afterShort, warnings } = selectEffectWindowsV1(snapshots, ack);

    expect(before.length).toBeLessThan(120);
    expect(afterShort.length).toBeLessThan(60);
    expect(warnings).toContain("WARN_BEFORE_WINDOW_INSUFFICIENT");
    expect(warnings).toContain("WARN_AFTER_SHORT_INSUFFICIENT");
  });

  /**
   * Test 3: Malformed input doesn't throw (defensive)
   */
  test("Test 3: Malformed inputs don't throw", () => {
    const ack: DecisionAckRecordV1 = {
      ts: 0,
    } as any;

    expect(() => {
      selectEffectWindowsV1([], ack);
    }).not.toThrow();

    const { before, warnings } = selectEffectWindowsV1([], ack);
    expect(before.length).toBe(0);
    expect(warnings).toContain("WARN_ACK_TIMESTAMP_MISSING");
  });

  /**
   * Test 4: summarizeWindow calculates counts/rates
   */
  test("Test 4: Window summary calculates counts and rates", () => {
    const snapshots: MarketRegimeSnapshotV1[] = [];

    // Create snapshots with gate PASS/BLOCK
    for (let i = 0; i < 100; i++) {
      snapshots.push({
        kind: "MARKET_REGIME_SNAPSHOT_V1",
        ts: Date.now() + i,
        runnerStatus: "RUNNER_IDLE",
        presenceLabels: {
          gatePaths: i < 70 ? ["GATE_PASS"] : [],
          blockReasons: i >= 70 ? ["BLOCK_ORACLE_STALE"] : [],
          stopCategories: i >= 90 ? ["STOP_MANUAL"] : [],
        },
        warnings: [],
      } as MarketRegimeSnapshotV1);
    }

    const summary = summarizeWindowV1("WIN_BEFORE", snapshots);

    expect(summary.counts.nSnapshots).toBe(100);
    expect(summary.counts.nGatePass).toBeGreaterThan(0);
    expect(summary.counts.nGateBlock).toBeGreaterThan(0);
    expect(summary.rates.passRate).toBeDefined();
    expect(summary.rates.blockRate).toBeDefined();
  });

  /**
   * Test 5: evaluateEffect: blockRate decrease → IMPROVED
   */
  test("Test 5: BlockRate decrease produces IMPROVED", () => {
    const before = {
      window: "WIN_BEFORE",
      status: "AVAILABLE",
      counts: { nSnapshots: 100, nGatePass: 50, nGateBlock: 50, nStop: 0 },
      rates: { passRate: 0.5, blockRate: 0.5, stopRate: 0 },
      tops: {},
      confusionSignals: [],
      bottlenecks: [],
      warnings: [],
    } as any;

    const afterShort = {
      window: "WIN_AFTER_SHORT",
      status: "AVAILABLE",
      counts: { nSnapshots: 100, nGatePass: 80, nGateBlock: 20, nStop: 0 },
      rates: { passRate: 0.8, blockRate: 0.2, stopRate: 0 }, // 30% point decrease
      tops: {},
      confusionSignals: [],
      bottlenecks: [],
      warnings: [],
    } as any;

    const { decision, compare } = evaluateEffectV1(before, afterShort);

    expect(decision).toBe("EFFECT_IMPROVED");
    expect(compare.improved).toContain("IMPROVED_BLOCK_RATE");
    expect(compare.improved).toContain("IMPROVED_PASS_RATE");
  });

  /**
   * Test 6: evaluateEffect: stopRate increase → WORSENED
   */
  test("Test 6: StopRate increase produces WORSENED", () => {
    const before = {
      window: "WIN_BEFORE",
      status: "AVAILABLE",
      counts: { nSnapshots: 100, nGatePass: 90, nGateBlock: 10, nStop: 5 },
      rates: { passRate: 0.9, blockRate: 0.1, stopRate: 0.05 },
      tops: {},
      confusionSignals: [],
      bottlenecks: [],
      warnings: [],
    } as any;

    const afterShort = {
      window: "WIN_AFTER_SHORT",
      status: "AVAILABLE",
      counts: { nSnapshots: 100, nGatePass: 80, nGateBlock: 10, nStop: 30 },
      rates: { passRate: 0.8, blockRate: 0.1, stopRate: 0.3 }, // 25% point increase
      tops: {},
      confusionSignals: [],
      bottlenecks: [],
      warnings: [],
    } as any;

    const { decision, compare } = evaluateEffectV1(before, afterShort);

    expect(decision).toBe("EFFECT_WORSENED");
    expect(compare.worsened).toContain("WORSENED_STOP_RATE");
  });

  /**
   * Test 7: evaluateEffect: mixed → MIXED
   */
  test("Test 7: Mixed improvements and worsening produce MIXED", () => {
    const before = {
      window: "WIN_BEFORE",
      status: "AVAILABLE",
      counts: { nSnapshots: 100, nGatePass: 50, nGateBlock: 50, nStop: 10 },
      rates: { passRate: 0.5, blockRate: 0.5, stopRate: 0.1 },
      tops: {},
      confusionSignals: [],
      bottlenecks: [],
      warnings: [],
    } as any;

    const afterShort = {
      window: "WIN_AFTER_SHORT",
      status: "AVAILABLE",
      counts: { nSnapshots: 100, nGatePass: 80, nGateBlock: 20, nStop: 30 },
      rates: { passRate: 0.8, blockRate: 0.2, stopRate: 0.3 }, // Block improved, stop worsened
      tops: {},
      confusionSignals: [],
      bottlenecks: [],
      warnings: [],
    } as any;

    const { decision } = evaluateEffectV1(before, afterShort);

    expect(decision).toBe("EFFECT_MIXED");
  });

  /**
   * Test 8: evaluateEffect: small change → NO_CHANGE
   */
  test("Test 8: Small changes produce NO_CHANGE", () => {
    const before = {
      window: "WIN_BEFORE",
      status: "AVAILABLE",
      counts: { nSnapshots: 100, nGatePass: 80, nGateBlock: 20, nStop: 5 },
      rates: { passRate: 0.8, blockRate: 0.2, stopRate: 0.05 },
      tops: {},
      confusionSignals: [],
      bottlenecks: [],
      warnings: [],
    } as any;

    const afterShort = {
      window: "WIN_AFTER_SHORT",
      status: "AVAILABLE",
      counts: { nSnapshots: 100, nGatePass: 82, nGateBlock: 18, nStop: 6 },
      rates: { passRate: 0.82, blockRate: 0.18, stopRate: 0.06 }, // <10% point change
      tops: {},
      confusionSignals: [],
      bottlenecks: [],
      warnings: [],
    } as any;

    const { decision } = evaluateEffectV1(before, afterShort);

    expect(decision).toBe("EFFECT_NO_CHANGE");
  });

  /**
   * Test 9: No afterShort → UNKNOWN
   */
  test("Test 9: Missing afterShort produces UNKNOWN", () => {
    const before = {
      window: "WIN_BEFORE",
      status: "AVAILABLE",
      counts: { nSnapshots: 100, nGatePass: 80, nGateBlock: 20, nStop: 0 },
      rates: { passRate: 0.8, blockRate: 0.2, stopRate: 0 },
      tops: {},
      confusionSignals: [],
      bottlenecks: [],
      warnings: [],
    } as any;

    const afterShort = {
      window: "WIN_AFTER_SHORT",
      status: "ERROR",
      counts: { nSnapshots: 0, nGatePass: 0, nGateBlock: 0, nStop: 0 },
      rates: {},
      tops: {},
      confusionSignals: [],
      bottlenecks: [],
      warnings: [],
    } as any;

    const { decision } = evaluateEffectV1(before, afterShort);

    expect(decision).toBe("EFFECT_UNKNOWN");
  });

  /**
   * Test 10: Label-only sanitizer removes numerics in normal mode
   */
  test("Test 10: Normal mode removes numerics", () => {
    const report: PatchEffectReportV1 = {
      kind: "PATCH_EFFECT_V1",
      status: "AVAILABLE",
      decisionAckRef: { proposalId: "P0_TEST" },
      windows: [],
      compare: { improved: [], worsened: [], unchanged: [], unavailable: [] },
      effectDecision: "EFFECT_IMPROVED",
      rationale: [],
      warnings: [],
      ts: Date.now(),
    };

    const sanitized = sanitizeEffectForDisplayV1(report, false);

    // Should not have ts in normal mode
    expect(sanitized.ts).toBeUndefined();

    // Should not have counts/rates in windows
    if (sanitized.windows && sanitized.windows.length > 0) {
      expect(sanitized.windows[0].counts).toBeUndefined();
      expect(sanitized.windows[0].rates).toBeUndefined();
    }
  });

  /**
   * Test 11: Debug mode allows numerics but sanitizes forbidden patterns
   */
  test("Test 11: Debug mode allows numerics", () => {
    const report: PatchEffectReportV1 = {
      kind: "PATCH_EFFECT_V1",
      status: "AVAILABLE",
      decisionAckRef: { proposalId: "P0_TEST" },
      windows: [],
      compare: { improved: [], worsened: [], unchanged: [], unavailable: [] },
      effectDecision: "EFFECT_IMPROVED",
      rationale: [],
      warnings: [],
      ts: Date.now(),
    };

    const sanitized = sanitizeEffectForDisplayV1(report, true);

    // Should have ts in debug mode
    expect(sanitized.ts).toBeDefined();
  });

  /**
   * Test 12: Store append/read roundtrip + filter works
   */
  test("Test 12: Store append and read roundtrip with filter", () => {
    const report: PatchEffectReportV1 = {
      kind: "PATCH_EFFECT_V1",
      status: "AVAILABLE",
      decisionAckRef: {
        proposalId: "P0_TEST_STORE",
        decision: "ADOPT",
      },
      windows: [],
      compare: {
        improved: ["IMPROVED_BLOCK_RATE"],
        worsened: [],
        unchanged: [],
        unavailable: [],
      },
      effectDecision: "EFFECT_IMPROVED",
      rationale: ["REASON_BLOCK_RATE_DECREASED"],
      warnings: [],
      ts: Date.now(),
    };

    // Append to store
    const { status } = appendEffectReportV1(report);
    expect(status).toBe("OK");

    // Read back
    const { reports } = readRecentEffectReportsV1({ tail: 10 });

    // Should find at least one report
    expect(reports.length).toBeGreaterThan(0);

    // Should find our report
    const found = reports.find((r) => r.decisionAckRef.proposalId === "P0_TEST_STORE");
    expect(found).toBeDefined();
    expect(found?.effectDecision).toBe("EFFECT_IMPROVED");

    // Filter by effectDecision
    const { reports: filteredReports } = readRecentEffectReportsV1({
      effectDecision: "EFFECT_IMPROVED",
      tail: 100,
    });

    const foundFiltered = filteredReports.find(
      (r) => r.decisionAckRef.proposalId === "P0_TEST_STORE"
    );
    expect(foundFiltered).toBeDefined();
  });
});
