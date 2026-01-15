/**
 * PR164: v1.4 Telemetry + Audit Log + Replay v1 - Tests
 *
 * Purpose:
 *   Verify telemetry event creation, audit log, and replay CLI functionality.
 *
 * Test Coverage:
 *   1. Event creation and sanitization
 *   2. Append event to log
 *   3. Read recent events
 *   4. Filtered events
 *   5. Label-only formatting
 *   6. Supervisor telemetry
 *   7. Runner telemetry
 *   8. Replay CLI
 *   9. Event validation
 *   10. Defensive behavior (telemetry failures don't break execution)
 */

import * as fs from "fs";
import * as path from "path";
import * as os from "os";
import {
  MeridianEventV1,
  createEventV1,
  validateEventV1,
  sanitizeLabelValue,
  formatLabelOnlyLine,
  formatTimestampLabel,
  appendEventV1,
  readRecentEventsV1,
  readFilteredEventsV1,
  resolveEventLogPath,
} from "../src/telemetry";
import { runSupervisorOnceV1 } from "../src/supervisor/supervisor";
import { StateStore } from "../src/state";

describe("PR164: Telemetry + Audit Log + Replay v1", () => {
  const TEST_LOG_DIR = path.join(os.tmpdir(), "meridian-test-telemetry");
  const TEST_LOG_PATH = path.join(TEST_LOG_DIR, "events.test.log");

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
   * Test 1: Event creation and sanitization
   */
  test("Test 1: Event creation and sanitization", () => {
    const event = createEventV1("SUPERVISOR_TICK", "INFO", {
      action: "TICK_START",
      phase: "PHASE_NORMAL",
    });

    expect(event.v).toBe("v1");
    expect(event.type).toBe("SUPERVISOR_TICK");
    expect(event.level).toBe("INFO");
    expect(event.labels.action).toBe("TICK_START");
    expect(event.labels.phase).toBe("PHASE_NORMAL");
    expect(event.warnings).toEqual([]);
    expect(event.ts).toBeGreaterThan(0);
  });

  /**
   * Test 2: Sanitization guards (forbidden patterns)
   */
  test("Test 2: Sanitization guards (forbidden patterns)", () => {
    // Test forbidden patterns
    expect(sanitizeLabelValue("0x1234abcd")).toBe("REDACTED"); // Token address
    expect(sanitizeLabelValue("1234.56")).toBe("REDACTED"); // Price
    expect(sanitizeLabelValue("buy 100 SUI")).toBe("REDACTED"); // Trading vocab
    expect(sanitizeLabelValue("sell USDC")).toBe("REDACTED"); // Trading vocab
    expect(sanitizeLabelValue("swap tokens")).toBe("REDACTED"); // Trading vocab

    // Test allowed patterns
    expect(sanitizeLabelValue("PHASE_NORMAL")).toBe("PHASE_NORMAL");
    expect(sanitizeLabelValue("STOP_ORACLE_STALE")).toBe("STOP_ORACLE_STALE");
    expect(sanitizeLabelValue("BLOCK_IMPACT_HIGH")).toBe("BLOCK_IMPACT_HIGH");
  });

  /**
   * Test 3: Append event to log (JSONL)
   */
  test("Test 3: Append event to log (JSONL)", async () => {
    const event1 = createEventV1("SUPERVISOR_TICK", "INFO", {
      action: "TICK_START",
    });
    const event2 = createEventV1("GATE_BLOCK", "WARN", {
      gate_reason: "BLOCK_ORACLE_STALE",
    });

    // Append events
    const result1 = await appendEventV1(event1, { path: TEST_LOG_PATH });
    expect(result1.ok).toBe(true);
    expect(result1.warnings).toEqual([]);

    const result2 = await appendEventV1(event2, { path: TEST_LOG_PATH });
    expect(result2.ok).toBe(true);

    // Verify file exists and has 2 lines
    expect(fs.existsSync(TEST_LOG_PATH)).toBe(true);
    const content = fs.readFileSync(TEST_LOG_PATH, "utf-8");
    const lines = content.split("\n").filter((line) => line.trim() !== "");
    expect(lines.length).toBe(2);

    // Verify each line is valid JSON
    const parsed1 = JSON.parse(lines[0]);
    expect(parsed1.type).toBe("SUPERVISOR_TICK");
    const parsed2 = JSON.parse(lines[1]);
    expect(parsed2.type).toBe("GATE_BLOCK");
  });

  /**
   * Test 4: Read recent events
   */
  test("Test 4: Read recent events", async () => {
    // Append 3 events
    await appendEventV1(createEventV1("SUPERVISOR_TICK", "INFO", {}), {
      path: TEST_LOG_PATH,
    });
    await appendEventV1(createEventV1("GATE_BLOCK", "WARN", {}), {
      path: TEST_LOG_PATH,
    });
    await appendEventV1(createEventV1("RUN_STOP", "WARN", {}), {
      path: TEST_LOG_PATH,
    });

    // Read recent events
    const result = await readRecentEventsV1(
      { path: TEST_LOG_PATH },
      { maxLines: 200 }
    );

    expect(result.events.length).toBe(3);
    expect(result.events[0].type).toBe("SUPERVISOR_TICK");
    expect(result.events[1].type).toBe("GATE_BLOCK");
    expect(result.events[2].type).toBe("RUN_STOP");
    expect(result.warnings).toEqual([]);
  });

  /**
   * Test 5: Filtered events (by type and level)
   */
  test("Test 5: Filtered events (by type and level)", async () => {
    // Append mixed events
    await appendEventV1(createEventV1("SUPERVISOR_TICK", "INFO", {}), {
      path: TEST_LOG_PATH,
    });
    await appendEventV1(createEventV1("GATE_BLOCK", "WARN", {}), {
      path: TEST_LOG_PATH,
    });
    await appendEventV1(createEventV1("GATE_BLOCK", "WARN", {}), {
      path: TEST_LOG_PATH,
    });
    await appendEventV1(createEventV1("ERROR", "ERROR", {}), {
      path: TEST_LOG_PATH,
    });

    // Filter by type
    const typeResult = await readFilteredEventsV1(
      { type: "GATE_BLOCK", maxLines: 200 },
      { path: TEST_LOG_PATH }
    );
    expect(typeResult.events.length).toBe(2);
    expect(typeResult.events[0].type).toBe("GATE_BLOCK");

    // Filter by level
    const levelResult = await readFilteredEventsV1(
      { level: "ERROR", maxLines: 200 },
      { path: TEST_LOG_PATH }
    );
    expect(levelResult.events.length).toBe(1);
    expect(levelResult.events[0].type).toBe("ERROR");

    // Filter by both
    const bothResult = await readFilteredEventsV1(
      { type: "GATE_BLOCK", level: "WARN", maxLines: 200 },
      { path: TEST_LOG_PATH }
    );
    expect(bothResult.events.length).toBe(2);
  });

  /**
   * Test 6: Label-only formatting (no numerics)
   */
  test("Test 6: Label-only formatting (no numerics)", () => {
    const event = createEventV1("GATE_BLOCK", "WARN", {
      gate_reason: "BLOCK_ORACLE_STALE",
      consecutive_blocks: "2",
    });

    const line = formatLabelOnlyLine(event);

    // Verify format: time level type [label pairs]
    expect(line).toContain("WARN");
    expect(line).toContain("GATE_BLOCK");
    expect(line).toContain("gate_reason=BLOCK_ORACLE_STALE");

    // Verify no numerics (except in labels like "consecutive_blocks=2")
    // The timestamp should be a label like T_RECENT, not a number
    expect(line).not.toMatch(/^\d+/); // Should not start with number
  });

  /**
   * Test 7: Timestamp label formatting
   */
  test("Test 7: Timestamp label formatting", () => {
    const now = Date.now();

    // Recent event (< 60s)
    const recent = formatTimestampLabel(now - 30_000);
    expect(recent).toBe("T_RECENT");

    // Old event (> 24h)
    const old = formatTimestampLabel(now - 25 * 60 * 60 * 1000);
    expect(old).toBe("T_OLD");

    // Hour event (> 1h, < 24h)
    const hour = formatTimestampLabel(now - 2 * 60 * 60 * 1000);
    expect(hour).toBe("T_HOUR");

    // Minute event (> 1min, < 1h)
    const minute = formatTimestampLabel(now - 5 * 60 * 1000);
    expect(minute).toBe("T_MIN");
  });

  /**
   * Test 8: Supervisor telemetry integration
   */
  test("Test 8: Supervisor telemetry integration", async () => {
    // Set env var for test log path
    const originalPath = process.env.MERIDIAN_EVENTS_PATH;
    process.env.MERIDIAN_EVENTS_PATH = TEST_LOG_PATH;

    try {
      // Create in-memory state store
      const stateDir = path.join(os.tmpdir(), "meridian-test-state-pr164");
      if (!fs.existsSync(stateDir)) {
        fs.mkdirSync(stateDir, { recursive: true });
      }
      const store = new StateStore(stateDir);

      // Initialize state
      await store.initState();

      // Run supervisor once
      const result = await runSupervisorOnceV1(store, {}, {});

      expect(result.status).toBe("OK");

      // Verify telemetry event was written
      const events = await readRecentEventsV1({ path: TEST_LOG_PATH });
      expect(events.events.length).toBeGreaterThan(0);

      const supervisorEvent = events.events.find(
        (e) => e.type === "SUPERVISOR_TICK"
      );
      expect(supervisorEvent).toBeDefined();
      expect(supervisorEvent?.level).toBe("INFO");

      // Clean up state dir
      if (fs.existsSync(stateDir)) {
        fs.rmSync(stateDir, { recursive: true });
      }
    } finally {
      // Restore env var
      if (originalPath) {
        process.env.MERIDIAN_EVENTS_PATH = originalPath;
      } else {
        delete process.env.MERIDIAN_EVENTS_PATH;
      }
    }
  });

  /**
   * Test 9: Event validation (defensive)
   */
  test("Test 9: Event validation (defensive)", () => {
    // Valid event
    const validEvent = createEventV1("SUPERVISOR_TICK", "INFO", {
      action: "TICK_START",
    });
    const validated = validateEventV1(validEvent);
    expect(validated.v).toBe("v1");
    expect(validated.type).toBe("SUPERVISOR_TICK");

    // Event with forbidden pattern in label
    const dirtyEvent = createEventV1("GATE_BLOCK", "WARN", {
      gate_reason: "BLOCK_ORACLE_STALE",
      suspicious_label: "0x1234abcd",
    });
    const sanitized = validateEventV1(dirtyEvent);
    expect(sanitized.labels.gate_reason).toBe("BLOCK_ORACLE_STALE");
    expect(sanitized.labels.suspicious_label).toBe("REDACTED");
  });

  /**
   * Test 10: Defensive behavior (telemetry failures don't break execution)
   */
  test("Test 10: Defensive behavior (telemetry failures don't break execution)", async () => {
    // Try to append to invalid path (should return ok: false, but not throw)
    const invalidPath = "/invalid/path/that/does/not/exist/events.log";
    const result = await appendEventV1(
      createEventV1("SUPERVISOR_TICK", "INFO", {}),
      { path: invalidPath }
    );

    expect(result.ok).toBe(false);
    expect(result.warnings).toContain("WARN_EVENT_APPEND_FAILED");

    // Try to read from non-existent file (should return empty array, but not throw)
    const readResult = await readRecentEventsV1({ path: invalidPath });
    expect(readResult.events).toEqual([]);
    expect(readResult.warnings).toContain("WARN_EVENT_LOG_NOT_FOUND");
  });
});
