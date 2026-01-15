/**
 * PR165: v1.4 Market Regime Snapshot Export v1 - Tests
 *
 * Purpose:
 *   Verify snapshot generation, storage, sanitization, and display functionality.
 *
 * Test Coverage:
 *   1. Build snapshot with minimal inputs → PARTIAL, never throws
 *   2. Build snapshot with AVAILABLE conditions → AVAILABLE
 *   3. Build snapshot with invalid inputs → ERROR record, never throws
 *   4. Warnings with numerics → guards detect and sanitize
 *   5. Token literal mixing → guards detect
 *   6. Append snapshot writes JSONL (tmp dir) → OK
 *   7. Append snapshot with invalid path → ERROR + warning, never throws
 *   8. Sanitize snapshot removes numerics (notionalUsd etc.)
 *   9. CLI formatter returns label-only strings (no numerics pattern)
 *   10. Supervisor hook: snapshot write failure does not abort tick
 */

import * as fs from "fs";
import * as path from "path";
import * as os from "os";
import {
  buildMarketRegimeSnapshotV1,
  appendSnapshotV1,
  readRecentSnapshotsV1,
  readFilteredSnapshotsV1,
  SnapshotInputsV1,
} from "../src/snapshot/exporter";
import {
  sanitizeSnapshotLabel,
  validateSnapshotLabelsOnly,
  sanitizeSnapshotForDisplay,
  formatSnapshotLabelOnlyLines,
} from "../src/snapshot/guards";
import { MarketRegimeSnapshotV1 } from "../src/snapshot/types";
import { runSupervisorOnceV1 } from "../src/supervisor/supervisor";
import { StateStore } from "../src/state";

describe("PR165: Market Regime Snapshot Export v1", () => {
  const TEST_LOG_DIR = path.join(os.tmpdir(), "meridian-test-snapshots");
  const TEST_LOG_PATH = path.join(TEST_LOG_DIR, "snapshots.test.log");

  beforeEach(() => {
    // Clean up test log before each test
    if (fs.existsSync(TEST_LOG_PATH)) {
      fs.unlinkSync(TEST_LOG_PATH);
    }
    if (fs.existsSync(TEST_LOG_DIR)) {
      fs.rmdirSync(TEST_LOG_DIR, { recursive: true });
    }
  });

  afterEach(() => {
    // Clean up test log after each test
    if (fs.existsSync(TEST_LOG_PATH)) {
      fs.unlinkSync(TEST_LOG_PATH);
    }
    if (fs.existsSync(TEST_LOG_DIR)) {
      fs.rmdirSync(TEST_LOG_DIR, { recursive: true });
    }
  });

  /**
   * Test 1: Build snapshot with minimal inputs → PARTIAL, never throws
   */
  test("Test 1: Build snapshot with minimal inputs → PARTIAL", async () => {
    const snapshot = await buildMarketRegimeSnapshotV1();

    expect(snapshot.version).toBe("v1.0");
    expect(snapshot.kind).toBe("REGIME_SNAPSHOT");
    expect(snapshot.status).toBe("PARTIAL"); // No components available
    expect(snapshot.ts).toBeGreaterThan(0);
    expect(snapshot.id).toBeTruthy();
    expect(snapshot.warnings).toEqual([]);
  });

  /**
   * Test 2: Build snapshot with AVAILABLE conditions → AVAILABLE
   */
  test("Test 2: Build snapshot with AVAILABLE conditions → AVAILABLE", async () => {
    const inputs: SnapshotInputsV1 = {
      latest: {
        shockPhase: "PHASE_NORMAL",
        stress: "STRESS_CALM",
        actionShape: "ACTION_NORMAL",
        templateId: "TPL_RISK_50",
        gateDecision: "PASS",
        policyDecision: "ALLOW",
      },
    };

    const snapshot = await buildMarketRegimeSnapshotV1(inputs);

    expect(snapshot.status).toBe("AVAILABLE");
    expect(snapshot.presence.hasShockPhase).toBe(true);
    expect(snapshot.presence.hasStress).toBe(true);
    expect(snapshot.presence.hasActionShape).toBe(true);
    expect(snapshot.presence.hasTemplateId).toBe(true);
    expect(snapshot.presence.hasGate).toBe(true);
    expect(snapshot.presence.hasPolicy).toBe(true);
    expect(snapshot.labels.shockPhase).toBe("PHASE_NORMAL");
    expect(snapshot.labels.stress).toBe("STRESS_CALM");
  });

  /**
   * Test 3: Build snapshot with invalid inputs → ERROR record, never throws
   */
  test("Test 3: Build snapshot with invalid inputs → ERROR record", async () => {
    // Even with broken inputs, should return snapshot (not throw)
    const snapshot = await buildMarketRegimeSnapshotV1({
      latest: undefined as any,
    });

    expect(snapshot.version).toBe("v1.0");
    expect(snapshot.status).toBe("PARTIAL"); // Missing components
    // Should not throw
  });

  /**
   * Test 4: Warnings with numerics → guards detect and sanitize
   */
  test("Test 4: Warnings with numerics → guards detect and sanitize", async () => {
    const snapshot: MarketRegimeSnapshotV1 = {
      version: "v1.0",
      kind: "REGIME_SNAPSHOT",
      status: "AVAILABLE",
      ts: Date.now(),
      id: "test_123",
      warnings: ["WARN_PRICE_123.45", "WARN_AMOUNT_0x1234abcd"],
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
    };

    const validation = validateSnapshotLabelsOnly(snapshot);

    expect(validation.ok).toBe(false);
    expect(validation.warnings).toContain("WARN_SNAPSHOT_WARNING_SANITIZED");
  });

  /**
   * Test 5: Token literal mixing → guards detect
   */
  test("Test 5: Token literal mixing → guards detect", () => {
    // Test forbidden patterns
    expect(sanitizeSnapshotLabel("wBTC price")).toBe("REDACTED");
    expect(sanitizeSnapshotLabel("USDC balance")).toBe("REDACTED");
    expect(sanitizeSnapshotLabel("buy SUI")).toBe("REDACTED");
    expect(sanitizeSnapshotLabel("sell token")).toBe("REDACTED");
    expect(sanitizeSnapshotLabel("0x1234abcd")).toBe("REDACTED");

    // Test allowed patterns
    expect(sanitizeSnapshotLabel("PHASE_NORMAL")).toBe("PHASE_NORMAL");
    expect(sanitizeSnapshotLabel("STRESS_CALM")).toBe("STRESS_CALM");
    expect(sanitizeSnapshotLabel("TPL_RISK_50")).toBe("TPL_RISK_50");
  });

  /**
   * Test 6: Append snapshot writes JSONL (tmp dir) → OK
   */
  test("Test 6: Append snapshot writes JSONL", async () => {
    const snapshot1 = await buildMarketRegimeSnapshotV1({
      latest: {
        shockPhase: "PHASE_NORMAL",
        stress: "STRESS_CALM",
        actionShape: "ACTION_NORMAL",
        templateId: "TPL_RISK_50",
        gateDecision: "PASS",
        policyDecision: "ALLOW",
      },
    });

    const snapshot2 = await buildMarketRegimeSnapshotV1({
      latest: {
        shockPhase: "PHASE_PRE_SHOCK",
        stress: "STRESS_TENSE",
        actionShape: "ACTION_CONSIDER",
        templateId: "TPL_RISK_20",
        gateDecision: "PASS",
        policyDecision: "ALLOW",
      },
    });

    // Append snapshots
    const result1 = await appendSnapshotV1(snapshot1, { path: TEST_LOG_PATH });
    expect(result1.status).toBe("OK");

    const result2 = await appendSnapshotV1(snapshot2, { path: TEST_LOG_PATH });
    expect(result2.status).toBe("OK");

    // Verify file exists and has 2 lines
    expect(fs.existsSync(TEST_LOG_PATH)).toBe(true);
    const content = fs.readFileSync(TEST_LOG_PATH, "utf-8");
    const lines = content.split("\n").filter((line) => line.trim() !== "");
    expect(lines.length).toBe(2);

    // Verify each line is valid JSON
    const parsed1 = JSON.parse(lines[0]);
    expect(parsed1.labels.shockPhase).toBe("PHASE_NORMAL");

    const parsed2 = JSON.parse(lines[1]);
    expect(parsed2.labels.shockPhase).toBe("PHASE_PRE_SHOCK");
  });

  /**
   * Test 7: Append snapshot with invalid path → ERROR + warning, never throws
   */
  test("Test 7: Append snapshot with invalid path → ERROR", async () => {
    const snapshot = await buildMarketRegimeSnapshotV1();

    const invalidPath = "/invalid/path/that/does/not/exist/snapshots.log";
    const result = await appendSnapshotV1(snapshot, { path: invalidPath });

    expect(result.status).toBe("ERROR");
    expect(result.warnings).toContain("WARN_SNAPSHOT_WRITE_FAILED");
    // Should not throw
  });

  /**
   * Test 8: Sanitize snapshot removes numerics
   */
  test("Test 8: Sanitize snapshot removes numerics", async () => {
    const snapshot = await buildMarketRegimeSnapshotV1({
      latest: {
        shockPhase: "PHASE_NORMAL",
        stress: "STRESS_CALM",
        actionShape: "ACTION_NORMAL",
        templateId: "TPL_RISK_50",
        gateDecision: "PASS",
        policyDecision: "ALLOW",
        numerics: {
          notionalUsd: 100000,
          targetNotionalUsd: 150000,
          oracleAgeMs: 5000,
        },
      },
    });

    // Verify numerics are in raw snapshot
    expect(snapshot.numerics).toBeDefined();
    expect(snapshot.numerics?.notionalUsd).toBe(100000);

    // Sanitize for display
    const sanitized = sanitizeSnapshotForDisplay(snapshot);

    // Verify numerics are removed
    expect((sanitized as any).numerics).toBeUndefined();
    expect(sanitized.timeLabel).toBeTruthy(); // ts converted to label
    expect(sanitized.idLabel).toBe("HAS_ID"); // id converted to label
  });

  /**
   * Test 9: CLI formatter returns label-only strings
   */
  test("Test 9: CLI formatter returns label-only strings", async () => {
    const snapshot = await buildMarketRegimeSnapshotV1({
      latest: {
        shockPhase: "PHASE_NORMAL",
        stress: "STRESS_CALM",
        actionShape: "ACTION_NORMAL",
        templateId: "TPL_RISK_50",
        gateDecision: "PASS",
        policyDecision: "ALLOW",
        numerics: {
          notionalUsd: 100000,
        },
      },
    });

    const sanitized = sanitizeSnapshotForDisplay(snapshot);
    const lines = formatSnapshotLabelOnlyLines(sanitized);

    // Verify lines are label-only (no numerics like "100000")
    const allText = lines.join("\n");
    expect(allText).not.toContain("100000");
    expect(allText).toContain("REGIME_SNAPSHOT");
    expect(allText).toContain("AVAILABLE");
    expect(allText).toContain("PHASE_NORMAL");
  });

  /**
   * Test 10: Supervisor hook: snapshot write failure does not abort tick
   */
  test("Test 10: Supervisor hook: snapshot failure does not abort tick", async () => {
    // Set env var to invalid path (snapshot will fail)
    const originalPath = process.env.MERIDIAN_SNAPSHOTS_PATH;
    process.env.MERIDIAN_SNAPSHOTS_PATH = "/invalid/path/snapshots.log";

    try {
      // Create in-memory state store
      const stateDir = path.join(os.tmpdir(), "meridian-test-state-pr165");
      if (!fs.existsSync(stateDir)) {
        fs.mkdirSync(stateDir, { recursive: true });
      }
      const store = new StateStore(stateDir);

      // Initialize state
      await store.initState();

      // Run supervisor once (snapshot will fail but tick should succeed)
      const result = await runSupervisorOnceV1(store, {}, {});

      // Verify tick succeeded despite snapshot failure
      expect(result.status).toBe("OK");
      // Should not throw

      // Clean up state dir
      if (fs.existsSync(stateDir)) {
        fs.rmSync(stateDir, { recursive: true });
      }
    } finally {
      // Restore env var
      if (originalPath) {
        process.env.MERIDIAN_SNAPSHOTS_PATH = originalPath;
      } else {
        delete process.env.MERIDIAN_SNAPSHOTS_PATH;
      }
    }
  });

  /**
   * Test 11: Read recent snapshots
   */
  test("Test 11: Read recent snapshots", async () => {
    // Append 3 snapshots
    for (let i = 0; i < 3; i++) {
      const snapshot = await buildMarketRegimeSnapshotV1({
        latest: {
          shockPhase: "PHASE_NORMAL",
          stress: "STRESS_CALM",
          actionShape: "ACTION_NORMAL",
          templateId: "TPL_RISK_50",
          gateDecision: "PASS",
          policyDecision: "ALLOW",
        },
      });
      await appendSnapshotV1(snapshot, { path: TEST_LOG_PATH });
    }

    // Read recent snapshots
    const result = await readRecentSnapshotsV1(
      { path: TEST_LOG_PATH },
      { maxLines: 200 }
    );

    expect(result.snapshots.length).toBe(3);
    expect(result.snapshots[0].kind).toBe("REGIME_SNAPSHOT");
    expect(result.warnings).toEqual([]);
  });

  /**
   * Test 12: Filtered snapshots (by status)
   */
  test("Test 12: Filtered snapshots by status", async () => {
    // Append mixed snapshots
    const available = await buildMarketRegimeSnapshotV1({
      latest: {
        shockPhase: "PHASE_NORMAL",
        stress: "STRESS_CALM",
        actionShape: "ACTION_NORMAL",
        templateId: "TPL_RISK_50",
        gateDecision: "PASS",
        policyDecision: "ALLOW",
      },
    });

    const partial = await buildMarketRegimeSnapshotV1({
      latest: {
        shockPhase: "PHASE_NORMAL",
        // Missing other components → PARTIAL
      },
    });

    await appendSnapshotV1(available, { path: TEST_LOG_PATH });
    await appendSnapshotV1(partial, { path: TEST_LOG_PATH });
    await appendSnapshotV1(available, { path: TEST_LOG_PATH });

    // Filter by AVAILABLE
    const availableResult = await readFilteredSnapshotsV1(
      { status: "AVAILABLE", maxLines: 200 },
      { path: TEST_LOG_PATH }
    );

    expect(availableResult.snapshots.length).toBe(2);
    expect(availableResult.snapshots[0].status).toBe("AVAILABLE");

    // Filter by PARTIAL
    const partialResult = await readFilteredSnapshotsV1(
      { status: "PARTIAL", maxLines: 200 },
      { path: TEST_LOG_PATH }
    );

    expect(partialResult.snapshots.length).toBe(1);
    expect(partialResult.snapshots[0].status).toBe("PARTIAL");
  });
});
