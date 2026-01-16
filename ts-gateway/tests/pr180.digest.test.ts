/**
 * PR180: v1.4 Spec Change Digest v1 - Tests
 *
 * Purpose:
 *   Verify digest generation, sanitization, and storage.
 *
 * Test Coverage:
 *   1. Empty input → PARTIAL + warnings (no throw)
 *   2. PatchOps 3つまで抽出（順序保持）
 *   3. Preview evidence STRONG優先で最大3
 *   4. Risks: NOT_ALLOWED があれば必ず RISK_PATCH_NOT_ALLOWED_PRESENT
 *   5. Review checklist FAIL があると RISK_CHECKLIST_FAIL_PRESENT
 *   6. SuggestedNext: CANDIDATE_ADOPT→ACK_OK
 *   7. Sanitize: 数値混入ラベルが REDACT される
 *   8. Sanitize: トークン/アドレスっぽい文字列が REDACT
 *   9. Store append/read roundtrip
 *   10. Store: 壊れた行をスキップして読み続ける
 *   11. CLI format: label-only lines 出力（数字が出ない）
 *   12. Defensive: 内部で例外相当の入力でもERRORに落ちつつレポート返却
 */

import * as fs from "fs";
import * as path from "path";
import * as os from "os";
import { buildSpecChangeDigestV1 } from "../src/digest/digester";
import { appendDigestV1, readRecentDigestsV1 } from "../src/digest/store";
import { sanitizeLabel, validateDigestLabelOnly } from "../src/digest/guards";
import { DigestInputV1, SpecChangeDigestV1 } from "../src/digest/types";

describe("PR180: Spec Change Digest", () => {
  let tmpDir: string;
  let digestLog: string;

  beforeEach(() => {
    // Create temp directory for test logs
    tmpDir = fs.mkdtempSync(path.join(os.tmpdir(), "pr180-test-"));
    digestLog = path.join(tmpDir, "digests.log");
  });

  afterEach(() => {
    // Clean up temp directory
    if (fs.existsSync(tmpDir)) {
      fs.rmSync(tmpDir, { recursive: true, force: true });
    }
  });

  /**
   * Test 1: Empty input → PARTIAL + warnings (no throw)
   */
  test("Test 1: Empty input returns PARTIAL without throwing", () => {
    const input: DigestInputV1 = {};

    const result = buildSpecChangeDigestV1(input);

    expect(result).toBeDefined();
    expect(result.status).toBe("PARTIAL");
    expect(result.warnings).toContain("WARN_MISSING_KEY_COMPONENTS");
  });

  /**
   * Test 2: PatchOps 3つまで抽出（順序保持）
   */
  test("Test 2: Extracts max 3 patch ops preserving order", () => {
    const input: DigestInputV1 = {
      patchPlan: {
        patchOps: [
          { kind: "PATCH_GATE_ORDER", label: "Gate order patch" },
          { kind: "PATCH_PHASE_POLICY", label: "Phase policy patch" },
          { kind: "PATCH_ORACLE_TIMEOUT", label: "Oracle timeout patch" },
          { kind: "PATCH_SLIPPAGE", label: "Slippage patch" },
        ],
      },
    };

    const result = buildSpecChangeDigestV1(input);

    expect(result.what.length).toBe(3);
    expect(result.what[0]).toBe("PATCH_GATE_ORDER");
    expect(result.what[1]).toBe("PATCH_PHASE_POLICY");
    expect(result.what[2]).toBe("PATCH_ORACLE_TIMEOUT");
  });

  /**
   * Test 3: Preview evidence STRONG優先で最大3
   */
  test("Test 3: Extracts max 3 STRONG/MEDIUM evidence", () => {
    const input: DigestInputV1 = {
      preview: {
        evidence: [
          { kind: "EVIDENCE_ORACLE", strength: "STRONG", label: "EVIDENCE_ORACLE_DOMINANT" },
          { kind: "EVIDENCE_GATE", strength: "MEDIUM", label: "EVIDENCE_GATE_BLOCK" },
          { kind: "EVIDENCE_PHASE", strength: "STRONG", label: "EVIDENCE_PHASE_SHIFT" },
          { kind: "EVIDENCE_WEAK", strength: "WEAK", label: "EVIDENCE_WEAK_SIGNAL" },
        ],
      },
    };

    const result = buildSpecChangeDigestV1(input);

    expect(result.why.length).toBe(3);
    expect(result.why).toContain("EVIDENCE_ORACLE_DOMINANT");
    expect(result.why).toContain("EVIDENCE_GATE_BLOCK");
    expect(result.why).toContain("EVIDENCE_PHASE_SHIFT");
    expect(result.why).not.toContain("EVIDENCE_WEAK_SIGNAL");
  });

  /**
   * Test 4: Risks: NOT_ALLOWED があれば必ず RISK_PATCH_NOT_ALLOWED_PRESENT
   */
  test("Test 4: Detects NOT_ALLOWED patch as risk", () => {
    const input: DigestInputV1 = {
      patchPlan: {
        patchOps: [
          { kind: "PATCH_GATE_ORDER", label: "Gate order patch" },
          { kind: "NOT_ALLOWED", label: "Not allowed patch" },
        ],
      },
    };

    const result = buildSpecChangeDigestV1(input);

    expect(result.risks).toContain("RISK_PATCH_NOT_ALLOWED_PRESENT");
  });

  /**
   * Test 5: Review checklist FAIL があると RISK_CHECKLIST_FAIL_PRESENT
   */
  test("Test 5: Detects checklist FAIL as risk", () => {
    const input: DigestInputV1 = {
      review: {
        checklist: [
          { id: "CHECK_EVIDENCE", status: "PASS" },
          { id: "CHECK_REGRESSION", status: "FAIL" },
          { id: "CHECK_INTERACTION", status: "PASS" },
        ],
      },
    };

    const result = buildSpecChangeDigestV1(input);

    expect(result.risks).toContain("RISK_CHECKLIST_FAIL_PRESENT");
  });

  /**
   * Test 6: SuggestedNext: CANDIDATE_ADOPT→ACK_OK
   */
  test("Test 6: Maps CANDIDATE_ADOPT to ACK_OK", () => {
    const input: DigestInputV1 = {
      review: {
        decision: "CANDIDATE_ADOPT",
      },
    };

    const result = buildSpecChangeDigestV1(input);

    expect(result.suggestedNext).toBe("ACK_OK");
  });

  /**
   * Test 7: Sanitize: 数値混入ラベルが REDACT される
   */
  test("Test 7: Sanitizes numeric values", () => {
    const input = "Spec version 123 with 456 USDC allocation";
    const sanitized = sanitizeLabel(input);

    expect(sanitized).toContain("REDACTED");
    expect(sanitized).not.toContain("123");
    expect(sanitized).not.toContain("456");
    expect(sanitized).not.toContain("USDC");
  });

  /**
   * Test 8: Sanitize: トークン/アドレスっぽい文字列が REDACT
   */
  test("Test 8: Sanitizes addresses and tokens", () => {
    const input1 = "Address 0x1234567890123456789012345678901234567890 used";
    const sanitized1 = sanitizeLabel(input1);
    expect(sanitized1).toContain("REDACTED");
    expect(sanitized1).not.toContain("0x1234");

    const input2 = "Buy 50 wBTC at market price";
    const sanitized2 = sanitizeLabel(input2);
    expect(sanitized2).toContain("REDACTED");
    expect(sanitized2).not.toContain("50");
    expect(sanitized2).not.toContain("wBTC");
  });

  /**
   * Test 9: Store append/read roundtrip
   */
  test("Test 9: Store append and read roundtrip works", async () => {
    const input: DigestInputV1 = {
      specLock: {
        status: "ACTIVE_OK",
        hasActiveSpec: true,
      },
      preview: {
        status: "AVAILABLE",
      },
    };

    const digest = buildSpecChangeDigestV1(input);
    const appendResult = await appendDigestV1(digest, digestLog);

    expect(appendResult.ok).toBe(true);

    const readResult = await readRecentDigestsV1({ tail: 10 }, digestLog);

    expect(readResult.items.length).toBe(1);
    expect(readResult.items[0].status).toBe(digest.status);
    expect(readResult.items[0].headline).toEqual(digest.headline);
  });

  /**
   * Test 10: Store: 壊れた行をスキップして読み続ける
   */
  test("Test 10: Store skips corrupted lines gracefully", async () => {
    // Write corrupted line
    fs.writeFileSync(digestLog, "{ invalid json }\n", "utf8");

    // Write valid digest
    const input: DigestInputV1 = {
      specLock: { status: "ACTIVE_OK" },
    };
    const digest = buildSpecChangeDigestV1(input);
    await appendDigestV1(digest, digestLog);

    // Read should skip corrupted line
    const readResult = await readRecentDigestsV1({ tail: 10 }, digestLog);

    expect(readResult.items.length).toBe(1);
    expect(readResult.warnings).toContain("WARN_CORRUPT_LINE_SKIPPED");
  });

  /**
   * Test 11: CLI format: label-only lines 出力（数字が出ない）
   */
  test("Test 11: Digest output is label-only", () => {
    const input: DigestInputV1 = {
      patchPlan: {
        patchOps: [{ kind: "PATCH_GATE_ORDER", label: "Gate order" }],
      },
      preview: {
        evidence: [
          { kind: "EVIDENCE_ORACLE", strength: "STRONG", label: "EVIDENCE_LABEL" },
        ],
      },
    };

    const result = buildSpecChangeDigestV1(input);

    // Check headline
    for (const item of result.headline) {
      expect(item).not.toMatch(/\d{3,}/); // No long numbers
      expect(item).not.toMatch(/0x[a-fA-F0-9]{40}/); // No addresses
    }

    // Check what
    for (const item of result.what) {
      expect(item).not.toMatch(/\d{3,}/);
    }

    // Check why
    for (const item of result.why) {
      expect(item).not.toMatch(/\d{3,}/);
    }
  });

  /**
   * Test 12: Defensive: 内部で例外相当の入力でもERRORに落ちつつレポート返却
   */
  test("Test 12: Handles malformed input defensively", () => {
    // Null/undefined inputs
    const input1: DigestInputV1 = {
      patchPlan: {
        patchOps: undefined as any,
      },
    };

    const result1 = buildSpecChangeDigestV1(input1);
    expect(result1).toBeDefined();
    expect(result1.status).toBeDefined();

    // Malformed evidence
    const input2: DigestInputV1 = {
      preview: {
        evidence: [
          { kind: undefined, strength: undefined, label: undefined } as any,
        ],
      },
    };

    const result2 = buildSpecChangeDigestV1(input2);
    expect(result2).toBeDefined();
    expect(result2.status).toBeDefined();
  });

  /**
   * Test 13: Validation detects forbidden patterns
   */
  test("Test 13: Validation catches forbidden patterns", () => {
    const badDigest: SpecChangeDigestV1 = {
      status: "AVAILABLE",
      time: "T_RECENT",
      headline: ["PENDING_ACK", "Amount 1000 USDC"],
      why: [],
      what: [],
      risks: [],
      checklist: [],
      rationale: [],
      suggestedNext: "ACK_OK",
      refs: {
        hasSpecLock: false,
        hasPatchPlan: false,
        hasPreview: false,
        hasReview: false,
        hasDecisionAck: false,
        hasEffect: false,
        hasAttribution: false,
        hasEvidenceLinked: false,
      },
      warnings: [],
    };

    const validation = validateDigestLabelOnly(badDigest);
    expect(validation.ok).toBe(false);
    expect(validation.warnings.length).toBeGreaterThan(0);
  });

  /**
   * Test 14: Refs are correctly populated
   */
  test("Test 14: Refs are correctly populated based on input", () => {
    const input: DigestInputV1 = {
      specLock: { status: "ACTIVE_OK" },
      patchPlan: { patchOps: [] },
      preview: { status: "AVAILABLE", evidence: [{ kind: "TEST" }] },
      review: { status: "AVAILABLE" },
      decisionAck: { decision: "ADOPT" },
      effect: { status: "TRACKED" },
      attribution: { bottlenecks: [] },
    };

    const result = buildSpecChangeDigestV1(input);

    expect(result.refs.hasSpecLock).toBe(true);
    expect(result.refs.hasPatchPlan).toBe(true);
    expect(result.refs.hasPreview).toBe(true);
    expect(result.refs.hasReview).toBe(true);
    expect(result.refs.hasDecisionAck).toBe(true);
    expect(result.refs.hasEffect).toBe(true);
    expect(result.refs.hasAttribution).toBe(true);
    expect(result.refs.hasEvidenceLinked).toBe(true);
  });
});
