/**
 * PR172: v1.4 Patch Review Checklist + Decision Rationale v1 - Guards
 *
 * Purpose:
 *   Sanitization and validation for review reports.
 *   Ensures all fields are label-only (no numerics, no forbidden patterns).
 *
 * Constitutional Constraints:
 *   - Label-only: No numerics in normal mode (except in MERIDIAN_DEBUG=true)
 *   - Forbidden patterns: Token literals, trading vocab, prescriptive language, addresses, prices
 *   - Defensive: Never throws, always returns safe output
 */

import { PatchReviewReportV1 } from "./types";

/**
 * Forbidden patterns (same as PR165/166/167/170/171)
 */
const FORBIDDEN_PATTERNS = [
  // Token literals
  /\bwBTC\b/i,
  /\bUSDC\b/i,
  /\bUSDT\b/i,
  /\bSUI\b/i,
  /\bETH\b/i,
  /\bBTC\b/i,
  // Trading vocab
  /\bbuy\b/i,
  /\bsell\b/i,
  /\blong\b/i,
  /\bshort\b/i,
  /\btrade\b/i,
  /\bexecute\b/i,
  /\border\b/i,
  /\bposition\b/i,
  // Prescriptive
  /\bshould\b/i,
  /\bmust\b/i,
  /\bwill\b/i,
  /\bshall\b/i,
  /\brecommend\b/i,
  /\badvise\b/i,
  // Address
  /0x[a-fA-F0-9]{8,}/,
  // Price
  /\$\d+/,
  /\d+\s*USD/i,
  /\bprice\b/i,
];

/**
 * Check if debug mode is enabled
 *
 * @returns True if MERIDIAN_DEBUG=true
 */
export function isDebugMode(): boolean {
  return process.env.MERIDIAN_DEBUG === "true";
}

/**
 * Sanitize label
 *
 * Removes forbidden patterns and replaces with "REDACTED".
 *
 * @param value - Label value
 * @returns Sanitized label
 */
export function sanitizeLabel(value: string): string {
  if (typeof value !== "string") {
    return "REDACTED";
  }

  for (const pattern of FORBIDDEN_PATTERNS) {
    if (pattern.test(value)) {
      return "REDACTED";
    }
  }

  return value;
}

/**
 * Sanitize lines array
 *
 * @param lines - Array of labels
 * @returns Sanitized array
 */
export function sanitizeLines(lines: string[]): string[] {
  return lines.map(sanitizeLabel);
}

/**
 * Validate checklist label-only
 *
 * Checks if checklist items follow label-only constraints.
 *
 * @param checklist - Review checklist
 * @returns Validation result
 */
export function validateChecklistLabelOnly(
  checklist: any[]
): { ok: boolean; warnings: string[] } {
  const warnings: string[] = [];

  for (const item of checklist) {
    if (item.id && sanitizeLabel(item.id) !== item.id) {
      warnings.push("WARN_CHECKLIST_ID_NOT_SANITIZED");
      break;
    }

    if (item.label && sanitizeLabel(item.label) !== item.label) {
      warnings.push("WARN_CHECKLIST_LABEL_NOT_SANITIZED");
      break;
    }

    if (item.detail && sanitizeLabel(item.detail) !== item.detail) {
      warnings.push("WARN_CHECKLIST_DETAIL_NOT_SANITIZED");
      break;
    }
  }

  return {
    ok: warnings.length === 0,
    warnings,
  };
}

/**
 * Validate rationale label-only
 *
 * Checks if rationale follows label-only constraints.
 *
 * @param rationale - Decision rationale
 * @returns Validation result
 */
export function validateRationaleLabelOnly(
  rationale: any
): { ok: boolean; warnings: string[] } {
  const warnings: string[] = [];

  if (
    rationale.decisionCandidate &&
    sanitizeLabel(rationale.decisionCandidate) !== rationale.decisionCandidate
  ) {
    warnings.push("WARN_RATIONALE_DECISION_NOT_SANITIZED");
  }

  for (const reason of rationale.reasons || []) {
    if (sanitizeLabel(reason) !== reason) {
      warnings.push("WARN_RATIONALE_REASON_NOT_SANITIZED");
      break;
    }
  }

  return {
    ok: warnings.length === 0,
    warnings,
  };
}

/**
 * Sanitize review report for display
 *
 * In normal mode:
 * - Keeps labels only
 * - Removes numeric timestamp (keeps status only)
 *
 * In debug mode (MERIDIAN_DEBUG=true):
 * - Returns raw report with all details
 *
 * @param report - Raw review report
 * @param debugMode - Debug mode flag
 * @returns Sanitized report
 */
export function sanitizeReviewForDisplay(
  report: PatchReviewReportV1,
  debugMode: boolean
): any {
  if (debugMode) {
    // Debug mode: Return raw report
    return report;
  }

  // Normal mode: Label-only
  return {
    kind: report.kind,
    status: report.status,
    checklist: report.checklist.map((item) => ({
      id: sanitizeLabel(item.id),
      label: sanitizeLabel(item.label),
      status: item.status,
      detail: item.detail ? sanitizeLabel(item.detail) : undefined,
    })),
    rationale: {
      decisionCandidate: report.rationale.decisionCandidate,
      reasons: sanitizeLines(report.rationale.reasons),
    },
    warnings: sanitizeLines(report.warnings),
  };
}

/**
 * Format review lines for console output
 *
 * @param report - Review report
 * @param debugMode - Debug mode flag
 * @returns Formatted lines
 */
export function formatReviewLines(
  report: PatchReviewReportV1,
  debugMode: boolean
): string[] {
  const lines: string[] = [];

  // Header
  lines.push("=== Patch Review Report v1 ===");
  lines.push("");
  lines.push(`Status: ${report.status}`);

  if (report.warnings.length > 0) {
    lines.push(`Warnings: ${report.warnings.join(", ")}`);
  }

  lines.push("");

  // Checklist
  lines.push("--- Review Checklist ---");
  lines.push("");

  for (const item of report.checklist) {
    const statusSymbol =
      item.status === "PASS" ? "✓" : item.status === "FAIL" ? "✗" : "?";
    lines.push(`${statusSymbol} [${item.status}] ${item.label}`);

    if (item.detail && debugMode) {
      lines.push(`    Detail: ${item.detail}`);
    }
  }

  lines.push("");

  // Decision Rationale
  lines.push("--- Decision Rationale ---");
  lines.push("");
  lines.push(`Suggested Decision: ${report.rationale.decisionCandidate}`);
  lines.push("");
  lines.push("Reasons:");

  for (const reason of report.rationale.reasons) {
    lines.push(`  - ${reason}`);
  }

  lines.push("");

  lines.push("=== End Review ===");
  lines.push("");

  return lines;
}
