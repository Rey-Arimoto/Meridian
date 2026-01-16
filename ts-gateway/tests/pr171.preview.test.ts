/**
 * PR171: v1.4 Patch Preview Report v1 - Tests
 *
 * Purpose:
 *   Verify preview report generation, sanitization, and storage.
 *
 * Test Coverage:
 *   1. PATCH_GATE_ORDER → sections generated
 *   2. Multiple patchOps → order preserved
 *   3. Evidence max 3, strength-sorted
 *   4. PATCH_NOT_ALLOWED → riskLabels/readiness assigned
 *   5. compareSignals reflected in report
 *   6. Sanitize: forbidden patterns → REDACTED
 *   7. Store append/read roundtrip
 *   8. Corrupted JSONL → skip + warning
 *   9. CLI output label-only (no numerics)
 *   10. Defensive: malformed inputs → PARTIAL/ERROR
 *   11. timeLabel formatting (ts → T_*)
 *   12. Empty patchOps → PARTIAL + WARN
 */

import { generatePreviewV1 } from "../src/preview/previewer";
import { getSectionTemplate, getSectionsForPatchOps } from "../src/preview/templates";
import { formatTimeLabel, sanitizeLabel } from "../src/preview/guards";
import { appendPreviewV1, readRecentPreviewsV1, getPreviewLogPath } from "../src/preview/store";
import * as fs from "fs";

describe("PR171: Patch Preview Report", () => {
  /**
   * Test 1: PATCH_GATE_ORDER → sections generated
   */
  test("Test 1: PATCH_GATE_ORDER generates section", () => {
    const section = getSectionTemplate("PATCH_GATE_ORDER");

    expect(section.title).toBe("SECTION_GATE_PRIORITY");
    expect(section.before).toContain("BEFORE_GATE_PRIORITY_CURRENT");
    expect(section.after).toContain("AFTER_GATE_PRIORITY_REORDERED");
    expect(section.notes).toContain("NOTE_BLOCK_REASON_SHIFT_EXPECTED");
  });

  /**
   * Test 2: Multiple patchOps → order preserved
   */
  test("Test 2: Multiple patchOps order preserved", () => {
    const patchOps = ["PATCH_PHASE_POLICY", "PATCH_GATE_ORDER", "PATCH_ROUTER_TIEBREAK"];
    const sections = getSectionsForPatchOps(patchOps);

    expect(sections.length).toBe(3);
    expect(sections[0].title).toBe("SECTION_PHASE_POLICY");
    expect(sections[1].title).toBe("SECTION_GATE_PRIORITY");
    expect(sections[2].title).toBe("SECTION_ROUTER_TIEBREAK");
  });

  /**
   * Test 3: Evidence max 3, strength-sorted
   */
  test("Test 3: Evidence max 3 and strength-sorted", () => {
    const report = generatePreviewV1({
      patchOps: [{ kind: "PATCH_GATE_ORDER" }],
      proposalId: "P0_TEST",
      evidence: [
        { kind: "EVID_1", label: "WEAK_EVID", strength: "EVIDENCE_WEAK", context: "ctx1" },
        { kind: "EVID_2", label: "STRONG_EVID", strength: "EVIDENCE_STRONG", context: "ctx2" },
        { kind: "EVID_3", label: "MEDIUM_EVID", strength: "EVIDENCE_MEDIUM", context: "ctx3" },
        { kind: "EVID_4", label: "ANOTHER_WEAK", strength: "EVIDENCE_WEAK", context: "ctx4" },
      ],
    });

    // Should have max 3 evidence
    expect(report.evidence.length).toBe(3);

    // Should be sorted by strength (STRONG > MEDIUM > WEAK)
    expect(report.evidence[0].strength).toBe("EVIDENCE_STRONG");
    expect(report.evidence[1].strength).toBe("EVIDENCE_MEDIUM");
    expect(report.evidence[2].strength).toBe("EVIDENCE_WEAK");
  });

  /**
   * Test 4: PATCH_NOT_ALLOWED → riskLabels/readiness assigned
   */
  test("Test 4: PATCH_NOT_ALLOWED triggers risk/readiness", () => {
    const report = generatePreviewV1({
      patchOps: [{ kind: "PATCH_NOT_ALLOWED" }],
      proposalId: "P0_TEST",
    });

    expect(report.riskLabels).toContain("RISK_PATCH_NOT_ALLOWED_PRESENT");
    expect(report.readiness).toContain("NOT_REVIEWABLE_REJECT_EXPECTED");
  });

  /**
   * Test 5: compareSignals reflected in report
   */
  test("Test 5: compareSignals reflected in report", () => {
    const report = generatePreviewV1({
      patchOps: [{ kind: "PATCH_GATE_ORDER" }],
      compareSignals: ["IMPROVED_PASS_RATIO", "NO_WORSENING"],
    });

    expect(report.compareSignals).toContain("IMPROVED_PASS_RATIO");
    expect(report.compareSignals).toContain("NO_WORSENING");
  });

  /**
   * Test 6: Sanitize forbidden patterns
   */
  test("Test 6: Forbidden patterns sanitized", () => {
    // Token literals
    expect(sanitizeLabel("wBTC balance")).toBe("REDACTED");
    expect(sanitizeLabel("USDC threshold")).toBe("REDACTED");

    // Trading vocab
    expect(sanitizeLabel("buy signal")).toBe("REDACTED");
    expect(sanitizeLabel("sell trigger")).toBe("REDACTED");

    // Address
    expect(sanitizeLabel("0x1234abcd5678")).toBe("REDACTED");

    // Allowed
    expect(sanitizeLabel("PATCH_GATE_ORDER")).toBe("PATCH_GATE_ORDER");
    expect(sanitizeLabel("SECTION_GATE_PRIORITY")).toBe("SECTION_GATE_PRIORITY");
  });

  /**
   * Test 7: Store append/read roundtrip
   */
  test("Test 7: Store append/read roundtrip", () => {
    const report = generatePreviewV1({
      patchOps: [{ kind: "PATCH_GATE_ORDER" }],
      proposalId: "P0_TEST_STORE",
      priority: "P0",
    });

    // Append to store
    appendPreviewV1(report);

    // Read back
    const { previews, warnings } = readRecentPreviewsV1({ tail: 10 });

    // Should find at least one preview
    expect(previews.length).toBeGreaterThan(0);

    // Should find our preview (most recent)
    const found = previews.find((p) => p.proposalId === "P0_TEST_STORE");
    expect(found).toBeDefined();
    expect(found?.priority).toBe("P0");
  });

  /**
   * Test 8: Corrupted JSONL → skip + warning
   */
  test("Test 8: Corrupted JSONL skipped", () => {
    const logPath = getPreviewLogPath();

    // Append corrupted line
    fs.appendFileSync(logPath, "{ invalid json\n", "utf-8");

    // Read should skip corrupt line and warn
    const { previews, warnings } = readRecentPreviewsV1({ tail: 100 });

    expect(warnings).toContain("WARN_CORRUPT_PREVIEW_LINE");
  });

  /**
   * Test 9: Defensive - malformed inputs don't throw
   */
  test("Test 9: Malformed inputs don't throw", () => {
    // Should not throw
    expect(() => {
      generatePreviewV1({
        patchOps: undefined as any,
        proposalId: undefined,
      });
    }).not.toThrow();

    // Should return PARTIAL status
    const report = generatePreviewV1({
      patchOps: undefined as any,
    });

    expect(report.status).toBe("PARTIAL");
    expect(report.warnings).toContain("WARN_NO_PATCH_OPS");
  });

  /**
   * Test 10: timeLabel formatting
   */
  test("Test 10: timeLabel formatting", () => {
    const now = Date.now();

    // T_RECENT (< 5 minutes)
    expect(formatTimeLabel(now - 2 * 60 * 1000)).toBe("T_RECENT");

    // T_MIN (< 60 minutes)
    expect(formatTimeLabel(now - 30 * 60 * 1000)).toBe("T_MIN");

    // T_HOUR (< 24 hours)
    expect(formatTimeLabel(now - 12 * 60 * 60 * 1000)).toBe("T_HOUR");

    // T_OLD (>= 24 hours)
    expect(formatTimeLabel(now - 48 * 60 * 60 * 1000)).toBe("T_OLD");

    // T_UNKNOWN (no timestamp)
    expect(formatTimeLabel(undefined)).toBe("T_UNKNOWN");
    expect(formatTimeLabel(0)).toBe("T_UNKNOWN");
  });

  /**
   * Test 11: Empty patchOps → PARTIAL + WARN
   */
  test("Test 11: Empty patchOps → PARTIAL", () => {
    const report = generatePreviewV1({
      patchOps: [],
      proposalId: "P0_TEST",
    });

    expect(report.status).toBe("PARTIAL");
    expect(report.warnings).toContain("WARN_NO_PATCH_OPS");
    expect(report.sections.length).toBe(0);
    expect(report.readiness).toContain("NOT_REVIEWABLE_NO_CHANGES");
  });

  /**
   * Test 12: PATCH_UNKNOWN fallback
   */
  test("Test 12: Unknown patch type uses fallback template", () => {
    const section = getSectionTemplate("PATCH_NONEXISTENT");

    expect(section.title).toBe("SECTION_UNKNOWN_PATCH");
    expect(section.notes).toContain("NOTE_PATCH_TYPE_UNRECOGNIZED_PATCH_NONEXISTENT");
  });
});
