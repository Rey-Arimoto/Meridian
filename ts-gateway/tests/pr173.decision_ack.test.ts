/**
 * PR173: v1.4 Decision Acknowledgement + Reviewer Trace v1 - Tests
 *
 * Purpose:
 *   Verify decision acknowledgement record building, storage, and sanitization.
 *
 * Test Coverage:
 *   1. buildAck: minimal inputs (proposalId + decision) → AVAILABLE
 *   2. buildAck: decision missing → PARTIAL + RAT_UNAVAILABLE
 *   3. buildAck: malformed input → ERROR record returned (never throws)
 *   4. sanitize: forbidden numeric patterns removed from warnings
 *   5. sanitize: address-like patterns removed
 *   6. store: append + read roundtrip OK
 *   7. store: corrupted JSONL line skipped with warning
 *   8. cli formatter: output has no numerics (validateLabelOnly)
 *   9. checklist summary: PASS/FAIL/UNKNOWN rendered
 *   10. compare summary: IMPROVED/WORSENED labels included
 *   11. filter: readRecentDecisionAcks by proposalId works
 *   12. filter: by decision + reviewer works
 */

import { buildDecisionAckV1 } from "../src/decision/ack";
import { sanitizeDecisionLabel, formatAckLines } from "../src/decision/guards";
import {
  appendDecisionAckV1,
  readRecentDecisionAcksV1,
  getDecisionLogPath,
} from "../src/decision/store";
import { DecisionAckRecordV1 } from "../src/decision/types";
import * as fs from "fs";

describe("PR173: Decision Acknowledgement + Reviewer Trace", () => {
  /**
   * Test 1: buildAck with minimal inputs → AVAILABLE
   */
  test("Test 1: Minimal inputs produce AVAILABLE record", () => {
    const ackRecord = buildDecisionAckV1({
      proposalId: "P0_TEST_MINIMAL",
      decisionResult: {
        decision: "ADOPT",
      },
    });

    expect(ackRecord.kind).toBe("DECISION_ACK_V1");
    expect(ackRecord.status).toBe("AVAILABLE");
    expect(ackRecord.refs.proposalId).toBe("P0_TEST_MINIMAL");
    expect(ackRecord.rationale.decision).toBe("ADOPT");
  });

  /**
   * Test 2: buildAck with decision missing → PARTIAL
   */
  test("Test 2: Missing decision produces PARTIAL record", () => {
    const ackRecord = buildDecisionAckV1({
      proposalId: "P0_TEST_PARTIAL",
      // No decisionResult, no reviewReport
    });

    expect(ackRecord.status).toBe("PARTIAL");
    expect(ackRecord.rationale.decision).toBe("UNKNOWN");
    expect(ackRecord.rationale.rationaleLabels).toContain("RAT_UNAVAILABLE");
    expect(ackRecord.warnings).toContain("WARN_DECISION_UNKNOWN");
  });

  /**
   * Test 3: buildAck with malformed input → ERROR (never throws)
   */
  test("Test 3: Malformed input doesn't throw", () => {
    // Should not throw
    expect(() => {
      buildDecisionAckV1({
        proposalId: undefined,
        decisionResult: undefined,
        previewReport: { corrupted: "data" } as any,
      });
    }).not.toThrow();

    // Should return ERROR or PARTIAL status
    const ackRecord = buildDecisionAckV1({
      proposalId: undefined,
    });

    expect(ackRecord.kind).toBe("DECISION_ACK_V1");
    expect(["ERROR", "PARTIAL"]).toContain(ackRecord.status);
  });

  /**
   * Test 4: Sanitize forbidden numeric patterns
   */
  test("Test 4: Forbidden numeric patterns sanitized", () => {
    // Price patterns
    expect(sanitizeDecisionLabel("$100 threshold")).toBe("REDACTED");
    expect(sanitizeDecisionLabel("500 USD limit")).toBe("REDACTED");

    // Token literals
    expect(sanitizeDecisionLabel("wBTC balance")).toBe("REDACTED");
    expect(sanitizeDecisionLabel("USDC amount")).toBe("REDACTED");

    // Allowed
    expect(sanitizeDecisionLabel("P0_TEST")).toBe("P0_TEST");
    expect(sanitizeDecisionLabel("CANDIDATE_ADOPT")).toBe("CANDIDATE_ADOPT");
  });

  /**
   * Test 5: Sanitize address-like patterns
   */
  test("Test 5: Address patterns sanitized", () => {
    // Address pattern
    expect(sanitizeDecisionLabel("0x1234abcd5678ef90")).toBe("REDACTED");
    expect(sanitizeDecisionLabel("Address: 0xdeadbeef12345678")).toBe(
      "REDACTED"
    );

    // Allowed
    expect(sanitizeDecisionLabel("EVIDENCE_STRONG")).toBe("EVIDENCE_STRONG");
    expect(sanitizeDecisionLabel("CHECK_NO_WORSENING_SIGNAL")).toBe(
      "CHECK_NO_WORSENING_SIGNAL"
    );
  });

  /**
   * Test 6: Store append + read roundtrip
   */
  test("Test 6: Store append and read roundtrip works", () => {
    const ackRecord = buildDecisionAckV1({
      proposalId: "P0_TEST_STORE",
      reviewer: "HUMAN_PRIMARY",
      source: "CLI_ADOPT",
      decisionResult: {
        decision: "ADOPT",
      },
    });

    // Append to store
    const { status } = appendDecisionAckV1(ackRecord);
    expect(status).toBe("OK");

    // Read back
    const { records, warnings } = readRecentDecisionAcksV1({ tail: 10 });

    // Should find at least one record
    expect(records.length).toBeGreaterThan(0);

    // Should find our record (most recent)
    const found = records.find((r) => r.refs.proposalId === "P0_TEST_STORE");
    expect(found).toBeDefined();
    expect(found?.reviewer).toBe("HUMAN_PRIMARY");
    expect(found?.rationale.decision).toBe("ADOPT");
  });

  /**
   * Test 7: Store corrupted JSONL line skipped
   */
  test("Test 7: Corrupted JSONL line skipped with warning", () => {
    const logPath = getDecisionLogPath();

    // Append corrupted line
    fs.appendFileSync(logPath, "{ invalid json\n", "utf-8");

    // Read should skip corrupt line and warn
    const { records, warnings } = readRecentDecisionAcksV1({ tail: 100 });

    expect(warnings).toContain("WARN_CORRUPT_DECISION_LINE");
  });

  /**
   * Test 8: CLI formatter produces label-only output
   */
  test("Test 8: Formatter output has no raw numerics", () => {
    const ackRecord = buildDecisionAckV1({
      proposalId: "P0_TEST_FORMAT",
      decisionResult: {
        decision: "ADOPT",
      },
    });

    const lines = formatAckLines(ackRecord, false); // Normal mode (no debug)

    // Should not contain raw timestamp (13-digit number)
    const hasRawTimestamp = lines.some((line) => /\d{13}/.test(line));
    expect(hasRawTimestamp).toBe(false);

    // Should contain time label
    const hasTimeLabel = lines.some((line) =>
      /T_(RECENT|MIN|HOUR|OLD|UNKNOWN)/.test(line)
    );
    expect(hasTimeLabel).toBe(true);
  });

  /**
   * Test 9: Checklist summary rendered correctly
   */
  test("Test 9: Checklist summary PASS/FAIL/UNKNOWN rendered", () => {
    const ackRecord = buildDecisionAckV1({
      proposalId: "P0_TEST_CHECKLIST",
      reviewReport: {
        checklist: [
          {
            id: "CHECK_NO_NOT_ALLOWED_PATCH",
            label: "No safety-reducing patches",
            status: "PASS",
          },
          {
            id: "CHECK_HAS_EVIDENCE",
            label: "Supporting evidence present",
            status: "FAIL",
          },
          {
            id: "CHECK_SCOPE_NOT_MULTI",
            label: "Change scope limited",
            status: "UNKNOWN",
          },
        ],
      },
      decisionResult: {
        decision: "HOLD",
      },
    });

    // Should have checklist summary
    expect(ackRecord.rationale.checklistSummary.length).toBeGreaterThan(0);

    // Should contain PASS/FAIL/UNKNOWN
    const summary = ackRecord.rationale.checklistSummary.join(" ");
    expect(summary).toContain("PASS");
    expect(summary).toContain("FAIL");
    expect(summary).toContain("UNKNOWN");
  });

  /**
   * Test 10: Compare summary includes IMPROVED/WORSENED labels
   */
  test("Test 10: Compare summary includes IMPROVED/WORSENED", () => {
    const ackRecord = buildDecisionAckV1({
      proposalId: "P0_TEST_COMPARE",
      previewReport: {
        compareSignals: [
          "IMPROVED_BLOCK_DOMINANCE",
          "SIGNAL_WORSENED_PASS_RATIO",
          "NO_WORSENING",
        ],
      },
      decisionResult: {
        decision: "HOLD",
      },
    });

    // Should have compare summary
    const compareSummary = ackRecord.rationale.compareSummary;
    expect(compareSummary.length).toBeGreaterThan(0);

    // Should include signals (max 3)
    expect(compareSummary).toContain("IMPROVED_BLOCK_DOMINANCE");
    expect(compareSummary).toContain("SIGNAL_WORSENED_PASS_RATIO");
    expect(compareSummary).toContain("NO_WORSENING");
  });

  /**
   * Test 11: Filter by proposalId works
   */
  test("Test 11: Filter by proposalId works", () => {
    // Create two different acks
    const ack1 = buildDecisionAckV1({
      proposalId: "P0_FILTER_TEST_A",
      decisionResult: { decision: "ADOPT" },
    });

    const ack2 = buildDecisionAckV1({
      proposalId: "P0_FILTER_TEST_B",
      decisionResult: { decision: "HOLD" },
    });

    appendDecisionAckV1(ack1);
    appendDecisionAckV1(ack2);

    // Filter by proposalId
    const { records } = readRecentDecisionAcksV1({
      proposalId: "P0_FILTER_TEST_A",
      tail: 100,
    });

    // Should only find ack1
    const foundA = records.find((r) => r.refs.proposalId === "P0_FILTER_TEST_A");
    const foundB = records.find((r) => r.refs.proposalId === "P0_FILTER_TEST_B");

    expect(foundA).toBeDefined();
    expect(foundB).toBeUndefined();
  });

  /**
   * Test 12: Filter by decision + reviewer works
   */
  test("Test 12: Filter by decision and reviewer works", () => {
    // Create acks with different decisions and reviewers
    const ack1 = buildDecisionAckV1({
      proposalId: "P0_FILTER_COMBO_1",
      reviewer: "HUMAN_PRIMARY",
      decisionResult: { decision: "ADOPT" },
    });

    const ack2 = buildDecisionAckV1({
      proposalId: "P0_FILTER_COMBO_2",
      reviewer: "AUTO_ASSISTED",
      decisionResult: { decision: "HOLD" },
    });

    const ack3 = buildDecisionAckV1({
      proposalId: "P0_FILTER_COMBO_3",
      reviewer: "HUMAN_PRIMARY",
      decisionResult: { decision: "HOLD" },
    });

    appendDecisionAckV1(ack1);
    appendDecisionAckV1(ack2);
    appendDecisionAckV1(ack3);

    // Filter by decision=HOLD + reviewer=HUMAN_PRIMARY
    const { records } = readRecentDecisionAcksV1({
      decision: "HOLD",
      reviewer: "HUMAN_PRIMARY",
      tail: 100,
    });

    // Should only find ack3
    const found1 = records.find((r) => r.refs.proposalId === "P0_FILTER_COMBO_1");
    const found2 = records.find((r) => r.refs.proposalId === "P0_FILTER_COMBO_2");
    const found3 = records.find((r) => r.refs.proposalId === "P0_FILTER_COMBO_3");

    expect(found1).toBeUndefined(); // ADOPT (not HOLD)
    expect(found2).toBeUndefined(); // AUTO_ASSISTED (not HUMAN_PRIMARY)
    expect(found3).toBeDefined(); // HOLD + HUMAN_PRIMARY ✓
  });
});
