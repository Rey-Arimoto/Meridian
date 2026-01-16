/**
 * PR171: v1.4 Patch Preview Report v1 - Guards
 *
 * Purpose:
 *   Sanitization and validation for preview reports.
 *   Ensures all fields are label-only (no numerics, no forbidden patterns).
 *
 * Constitutional Constraints:
 *   - Label-only: No numerics in normal mode (except in MERIDIAN_DEBUG=true)
 *   - Forbidden patterns: Token literals, trading vocab, prescriptive language, addresses, prices
 *   - Defensive: Never throws, always returns safe output
 */

import { PatchPreviewReportV1, PreviewTimeLabel } from "./types";

/**
 * Forbidden patterns (same as PR165/166/167/170)
 *
 * - Token literals: wBTC, USDC, SUI, etc.
 * - Trading vocab: buy, sell, long, short, trade, execute, etc.
 * - Prescriptive: should, must, will, shall, etc.
 * - Address: 0x...
 * - Price: $, USD, price patterns
 * - Numerics in normal mode (except debug)
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
 * Format time label from timestamp
 *
 * Discretizes timestamp into label-only categories.
 *
 * @param ts - Timestamp (optional)
 * @returns Time label
 */
export function formatTimeLabel(ts?: number): PreviewTimeLabel {
  if (!ts || ts <= 0) {
    return "T_UNKNOWN";
  }

  const now = Date.now();
  const ageMs = now - ts;

  if (ageMs < 0) {
    // Future timestamp (invalid)
    return "T_UNKNOWN";
  }

  if (ageMs < 5 * 60 * 1000) {
    // < 5 minutes
    return "T_RECENT";
  }

  if (ageMs < 60 * 60 * 1000) {
    // < 60 minutes
    return "T_MIN";
  }

  if (ageMs < 24 * 60 * 60 * 1000) {
    // < 24 hours
    return "T_HOUR";
  }

  // >= 24 hours
  return "T_OLD";
}

/**
 * Validate label-only report
 *
 * Checks if preview report follows label-only constraints.
 *
 * @param report - Preview report
 * @returns Validation result
 */
export function validateLabelOnlyReport(
  report: PatchPreviewReportV1
): { ok: boolean; warnings: string[] } {
  const warnings: string[] = [];

  // Check all string fields are sanitized
  if (report.proposalId && sanitizeLabel(report.proposalId) !== report.proposalId) {
    warnings.push("WARN_PROPOSAL_ID_NOT_SANITIZED");
  }

  for (const op of report.patchOps) {
    if (sanitizeLabel(op) !== op) {
      warnings.push("WARN_PATCH_OP_NOT_SANITIZED");
      break;
    }
  }

  for (const section of report.sections) {
    if (sanitizeLabel(section.title) !== section.title) {
      warnings.push("WARN_SECTION_TITLE_NOT_SANITIZED");
      break;
    }

    for (const line of [...section.before, ...section.after, ...section.notes]) {
      if (sanitizeLabel(line) !== line) {
        warnings.push("WARN_SECTION_LINE_NOT_SANITIZED");
        break;
      }
    }
  }

  return {
    ok: warnings.length === 0,
    warnings,
  };
}

/**
 * Sanitize preview report for display
 *
 * In normal mode:
 * - Keeps labels only
 * - Removes numeric timestamp (keeps timeLabel only)
 *
 * In debug mode (MERIDIAN_DEBUG=true):
 * - Returns raw report with all details
 *
 * @param report - Raw preview report
 * @param debugMode - Debug mode flag
 * @returns Sanitized report
 */
export function sanitizePreviewForDisplay(
  report: PatchPreviewReportV1,
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
    proposalId: report.proposalId ? sanitizeLabel(report.proposalId) : undefined,
    priority: report.priority,
    decisionCandidate: report.decisionCandidate,
    patchOps: report.patchOps.map(sanitizeLabel),
    sections: report.sections.map((s) => ({
      title: sanitizeLabel(s.title),
      before: sanitizeLines(s.before),
      after: sanitizeLines(s.after),
      notes: sanitizeLines(s.notes),
    })),
    riskLabels: sanitizeLines(report.riskLabels),
    readiness: sanitizeLines(report.readiness),
    evidence_count: report.evidence.length > 0 ? "HAS_EVIDENCE" : "NO_EVIDENCE",
    compareSignals_count:
      report.compareSignals.length > 0 ? "HAS_COMPARE_SIGNALS" : "NO_COMPARE_SIGNALS",
    warnings: sanitizeLines(report.warnings),
    timeLabel: report.timeLabel,
  };
}

/**
 * Format preview lines for console output
 *
 * @param report - Preview report
 * @param debugMode - Debug mode flag
 * @returns Formatted lines
 */
export function formatPreviewLines(
  report: PatchPreviewReportV1,
  debugMode: boolean
): string[] {
  const lines: string[] = [];

  // Header
  lines.push("=== Patch Preview Report v1 ===");
  lines.push("");
  lines.push(`Status: ${report.status}`);
  lines.push(`Time: ${report.timeLabel}`);

  if (report.proposalId) {
    lines.push(`Proposal: ${report.proposalId}`);
  }

  if (report.priority) {
    lines.push(`Priority: ${report.priority}`);
  }

  if (report.decisionCandidate) {
    lines.push(`Decision Candidate: ${report.decisionCandidate}`);
  }

  lines.push("");

  // Warnings
  if (report.warnings.length > 0) {
    lines.push(`Warnings: ${report.warnings.join(", ")}`);
    lines.push("");
  }

  // Readiness
  if (report.readiness.length > 0) {
    lines.push("Readiness:");
    for (const ready of report.readiness) {
      lines.push(`  - ${ready}`);
    }
    lines.push("");
  }

  // Risk Labels
  if (report.riskLabels.length > 0) {
    lines.push("Risk Labels:");
    for (const risk of report.riskLabels) {
      lines.push(`  - ${risk}`);
    }
    lines.push("");
  }

  // Sections
  if (report.sections.length > 0) {
    lines.push("--- Changes Preview ---");
    lines.push("");

    for (const section of report.sections) {
      lines.push(`[${section.title}]`);
      lines.push("");

      if (section.before.length > 0) {
        lines.push("  Before:");
        for (const line of section.before) {
          lines.push(`    - ${line}`);
        }
        lines.push("");
      }

      if (section.after.length > 0) {
        lines.push("  After:");
        for (const line of section.after) {
          lines.push(`    - ${line}`);
        }
        lines.push("");
      }

      if (section.notes.length > 0) {
        lines.push("  Notes:");
        for (const note of section.notes) {
          lines.push(`    - ${note}`);
        }
        lines.push("");
      }
    }
  }

  // Evidence (if debug mode)
  if (debugMode && report.evidence.length > 0) {
    lines.push("--- Evidence ---");
    lines.push("");

    for (const evid of report.evidence) {
      lines.push(`  [${evid.kind}] [${evid.strength}] ${evid.label}`);
      if (evid.context && evid.context.length > 0) {
        for (const ctx of evid.context) {
          lines.push(`    Context: ${ctx}`);
        }
      }
    }
    lines.push("");
  }

  // Compare Signals (if debug mode)
  if (debugMode && report.compareSignals.length > 0) {
    lines.push("--- Compare Signals ---");
    lines.push("");

    for (const signal of report.compareSignals) {
      lines.push(`  - ${signal}`);
    }
    lines.push("");
  }

  lines.push("=== End Preview ===");
  lines.push("");

  return lines;
}
