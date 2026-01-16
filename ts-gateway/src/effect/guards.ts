/**
 * PR174: v1.4 Patch Effectiveness Tracker v1 - Guards
 *
 * Purpose:
 *   Sanitization and validation for effect reports.
 *   Ensures label-only display in normal mode, allows numerics in debug mode.
 *
 * Constitutional Constraints:
 *   - Label-only: No numerics in normal mode (except in MERIDIAN_DEBUG=true)
 *   - Forbidden patterns: Token literals, trading vocab, addresses, prices
 *   - Defensive: Never throws, always returns safe output
 */

import { PatchEffectReportV1, EffectWindowSummary } from "./types";

/**
 * Forbidden patterns (same as PR165/166/167/170/171/172/173)
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
 * Sanitize effect label
 *
 * Removes forbidden patterns and replaces with "REDACTED".
 *
 * @param value - Label value
 * @returns Sanitized label
 */
export function sanitizeEffectLabel(value: string): string {
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
  return lines.map(sanitizeEffectLabel);
}

/**
 * Validate effect label-only
 *
 * Checks if effect report follows label-only constraints in normal mode.
 *
 * @param report - Effect report
 * @returns Validation result
 */
export function validateEffectLabelOnlyV1(
  report: PatchEffectReportV1
): { ok: boolean; warnings: string[] } {
  const warnings: string[] = [];

  // Check rationale
  for (const label of report.rationale || []) {
    if (sanitizeEffectLabel(label) !== label) {
      warnings.push("WARN_RATIONALE_NOT_SANITIZED");
      break;
    }
  }

  // Check compare signals
  for (const label of [
    ...report.compare.improved,
    ...report.compare.worsened,
    ...report.compare.unchanged,
    ...report.compare.unavailable,
  ]) {
    if (sanitizeEffectLabel(label) !== label) {
      warnings.push("WARN_COMPARE_SIGNAL_NOT_SANITIZED");
      break;
    }
  }

  // Check warnings
  for (const label of report.warnings || []) {
    if (sanitizeEffectLabel(label) !== label) {
      warnings.push("WARN_WARNING_NOT_SANITIZED");
      break;
    }
  }

  return {
    ok: warnings.length === 0,
    warnings,
  };
}

/**
 * Sanitize effect report for display
 *
 * In normal mode:
 * - Removes numeric counts and rates
 * - Keeps only labels
 *
 * In debug mode (MERIDIAN_DEBUG=true):
 * - Returns raw report with all numerics
 *
 * @param report - Raw effect report
 * @param debugMode - Debug mode flag
 * @returns Sanitized report
 */
export function sanitizeEffectForDisplayV1(
  report: PatchEffectReportV1,
  debugMode: boolean
): any {
  if (debugMode) {
    // Debug mode: Return raw report (but still sanitize forbidden patterns)
    return report;
  }

  // Normal mode: Label-only (no counts/rates/ts)
  return {
    kind: report.kind,
    status: report.status,
    decisionAckRef: report.decisionAckRef,
    windows: report.windows.map((window) => ({
      window: window.window,
      status: window.status,
      // NO counts/rates in normal mode
      tops: window.tops,
      confusionSignals: sanitizeLines(window.confusionSignals),
      bottlenecks: sanitizeLines(window.bottlenecks),
      warnings: sanitizeLines(window.warnings),
    })),
    compare: {
      improved: sanitizeLines(report.compare.improved),
      worsened: sanitizeLines(report.compare.worsened),
      unchanged: sanitizeLines(report.compare.unchanged),
      unavailable: sanitizeLines(report.compare.unavailable),
    },
    effectDecision: report.effectDecision,
    rationale: sanitizeLines(report.rationale),
    warnings: sanitizeLines(report.warnings),
    // NO ts in normal mode
  };
}

/**
 * Format effect lines for console output (label-only)
 *
 * @param report - Effect report
 * @param debugMode - Debug mode flag
 * @returns Formatted lines
 */
export function formatEffectLabelOnlyLinesV1(
  report: PatchEffectReportV1,
  debugMode: boolean
): string[] {
  const lines: string[] = [];

  // Header
  lines.push("=== Patch Effect Report v1 ===");
  lines.push("");
  lines.push(`Status: ${report.status}`);
  lines.push(`Effect Decision: ${report.effectDecision}`);
  lines.push("");

  // Decision Ack Reference
  if (report.decisionAckRef.proposalId) {
    lines.push(`Proposal: ${report.decisionAckRef.proposalId}`);
  }
  if (report.decisionAckRef.decision) {
    lines.push(`Original Decision: ${report.decisionAckRef.decision}`);
  }
  if (report.decisionAckRef.reviewerKind) {
    lines.push(`Reviewer: ${report.decisionAckRef.reviewerKind}`);
  }
  if (report.decisionAckRef.timeLabel) {
    lines.push(`Time: ${report.decisionAckRef.timeLabel}`);
  }
  lines.push("");

  // Windows
  lines.push("--- Time Windows ---");
  lines.push("");

  for (const window of report.windows) {
    lines.push(`Window: ${window.window} (${window.status})`);

    if (debugMode) {
      // Debug mode: Show counts and rates
      lines.push(
        `  Counts: ${window.counts.nSnapshots} snapshots, ` +
          `${window.counts.nGatePass} pass, ${window.counts.nGateBlock} block, ` +
          `${window.counts.nStop} stop`
      );
      if (window.rates.passRate !== undefined) {
        lines.push(
          `  Rates: pass=${(window.rates.passRate * 100).toFixed(1)}%, ` +
            `block=${((window.rates.blockRate || 0) * 100).toFixed(1)}%, ` +
            `stop=${((window.rates.stopRate || 0) * 100).toFixed(1)}%`
        );
      }
    }

    // Top labels (always show)
    if (window.tops.topPhase) {
      lines.push(`  Top Phase: ${window.tops.topPhase}`);
    }
    if (window.tops.topBlockReason) {
      lines.push(`  Top Block Reason: ${window.tops.topBlockReason}`);
    }

    // Confusion signals
    if (window.confusionSignals.length > 0) {
      lines.push(`  Confusion: ${window.confusionSignals.join(", ")}`);
    }

    // Bottlenecks
    if (window.bottlenecks.length > 0) {
      lines.push(`  Bottlenecks: ${window.bottlenecks.join(", ")}`);
    }

    lines.push("");
  }

  // Compare
  lines.push("--- Comparison ---");
  lines.push("");

  if (report.compare.improved.length > 0) {
    lines.push(`Improved: ${report.compare.improved.join(", ")}`);
  }
  if (report.compare.worsened.length > 0) {
    lines.push(`Worsened: ${report.compare.worsened.join(", ")}`);
  }
  if (report.compare.unchanged.length > 0) {
    lines.push(`Unchanged: ${report.compare.unchanged.join(", ")}`);
  }
  if (report.compare.unavailable.length > 0) {
    lines.push(`Unavailable: ${report.compare.unavailable.join(", ")}`);
  }

  lines.push("");

  // Rationale
  lines.push("--- Rationale ---");
  lines.push("");

  for (const reason of report.rationale) {
    lines.push(`  - ${reason}`);
  }

  lines.push("");

  // Warnings
  if (report.warnings.length > 0) {
    lines.push(`Warnings: ${report.warnings.join(", ")}`);
    lines.push("");
  }

  lines.push("=== End Report ===");
  lines.push("");

  return lines;
}
