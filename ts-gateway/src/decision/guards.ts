/**
 * PR173: v1.4 Decision Acknowledgement + Reviewer Trace v1 - Guards
 *
 * Purpose:
 *   Sanitization and validation for decision acknowledgement records.
 *   Ensures all fields are label-only (no numerics, no forbidden patterns).
 *
 * Constitutional Constraints:
 *   - Label-only: No numerics in display mode (except in MERIDIAN_DEBUG=true)
 *   - Forbidden patterns: Token literals, trading vocab, prescriptive language, addresses, prices
 *   - Defensive: Never throws, always returns safe output
 */

import { DecisionAckRecordV1, TimeLabel } from "./types";

/**
 * Forbidden patterns (same as PR165/166/167/170/171/172)
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
 * Sanitize decision label
 *
 * Removes forbidden patterns and replaces with "REDACTED".
 *
 * @param value - Label value
 * @returns Sanitized label
 */
export function sanitizeDecisionLabel(value: string): string {
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
  return lines.map(sanitizeDecisionLabel);
}

/**
 * Format time label
 *
 * Converts numeric timestamp to discretized time label.
 *
 * @param ts - Timestamp (milliseconds)
 * @returns Time label
 */
export function formatTimeLabel(ts: number | undefined): TimeLabel {
  if (!ts || ts === 0) {
    return "T_UNKNOWN";
  }

  const now = Date.now();
  const diffMs = now - ts;

  // < 5 minutes
  if (diffMs < 5 * 60 * 1000) {
    return "T_RECENT";
  }

  // < 60 minutes
  if (diffMs < 60 * 60 * 1000) {
    return "T_MIN";
  }

  // < 24 hours
  if (diffMs < 24 * 60 * 60 * 1000) {
    return "T_HOUR";
  }

  // >= 24 hours
  return "T_OLD";
}

/**
 * Validate ack label-only
 *
 * Checks if acknowledgement record follows label-only constraints.
 * Returns warnings for violations (does not mutate record).
 *
 * @param rec - Decision ack record
 * @returns Array of warning labels
 */
export function validateAckLabelOnly(rec: DecisionAckRecordV1): string[] {
  const warnings: string[] = [];

  // Check rationale labels
  for (const label of rec.rationale.rationaleLabels || []) {
    if (sanitizeDecisionLabel(label) !== label) {
      warnings.push("WARN_RATIONALE_LABEL_NOT_SANITIZED");
      break;
    }
  }

  // Check checklist summary
  for (const label of rec.rationale.checklistSummary || []) {
    if (sanitizeDecisionLabel(label) !== label) {
      warnings.push("WARN_CHECKLIST_SUMMARY_NOT_SANITIZED");
      break;
    }
  }

  // Check evidence summary
  for (const label of rec.rationale.evidenceSummary || []) {
    if (sanitizeDecisionLabel(label) !== label) {
      warnings.push("WARN_EVIDENCE_SUMMARY_NOT_SANITIZED");
      break;
    }
  }

  // Check compare summary
  for (const label of rec.rationale.compareSummary || []) {
    if (sanitizeDecisionLabel(label) !== label) {
      warnings.push("WARN_COMPARE_SUMMARY_NOT_SANITIZED");
      break;
    }
  }

  // Check warnings
  for (const label of rec.warnings || []) {
    if (sanitizeDecisionLabel(label) !== label) {
      warnings.push("WARN_WARNING_NOT_SANITIZED");
      break;
    }
  }

  return warnings;
}

/**
 * Sanitize ack record for display
 *
 * In normal mode:
 * - Keeps labels only
 * - Removes numeric timestamp (uses timeLabel only)
 *
 * In debug mode (MERIDIAN_DEBUG=true):
 * - Returns raw record with all details
 *
 * @param rec - Raw ack record
 * @param debugMode - Debug mode flag
 * @returns Sanitized record
 */
export function sanitizeAckForDisplay(
  rec: DecisionAckRecordV1,
  debugMode: boolean
): any {
  if (debugMode) {
    // Debug mode: Return raw record
    return rec;
  }

  // Normal mode: Label-only (no ts)
  return {
    kind: rec.kind,
    status: rec.status,
    timeLabel: rec.timeLabel,
    reviewer: rec.reviewer,
    source: rec.source,
    refs: {
      proposalId: rec.refs.proposalId,
      previewId: rec.refs.previewId,
      reviewId: rec.refs.reviewId,
      patchPlanId: rec.refs.patchPlanId,
    },
    rationale: {
      decision: rec.rationale.decision,
      rationaleLabels: sanitizeLines(rec.rationale.rationaleLabels),
      checklistSummary: sanitizeLines(rec.rationale.checklistSummary),
      evidenceSummary: sanitizeLines(rec.rationale.evidenceSummary),
      compareSummary: sanitizeLines(rec.rationale.compareSummary),
    },
    warnings: sanitizeLines(rec.warnings),
  };
}

/**
 * Format ack lines for console output
 *
 * @param rec - Decision ack record
 * @param debugMode - Debug mode flag
 * @returns Formatted lines
 */
export function formatAckLines(
  rec: DecisionAckRecordV1,
  debugMode: boolean
): string[] {
  const lines: string[] = [];

  // Header
  lines.push(`${rec.kind} ${rec.status} ${rec.timeLabel}`);
  lines.push(`REVIEWER ${rec.reviewer} SOURCE ${rec.source}`);

  // References
  if (rec.refs.proposalId) {
    lines.push(`PROPOSAL ${rec.refs.proposalId}`);
  }
  if (rec.refs.previewId) {
    lines.push(`PREVIEW ${rec.refs.previewId}`);
  }
  if (rec.refs.reviewId) {
    lines.push(`REVIEW ${rec.refs.reviewId}`);
  }
  if (rec.refs.patchPlanId) {
    lines.push(`PATCHPLAN ${rec.refs.patchPlanId}`);
  }

  // Decision
  lines.push(`DECISION ${rec.rationale.decision}`);

  // Rationale labels
  if (rec.rationale.rationaleLabels.length > 0) {
    lines.push(`RATIONALE ${rec.rationale.rationaleLabels.join(", ")}`);
  }

  // Checklist summary
  if (rec.rationale.checklistSummary.length > 0) {
    lines.push(`CHECKLIST ${rec.rationale.checklistSummary.join(", ")}`);
  }

  // Evidence summary
  if (rec.rationale.evidenceSummary.length > 0) {
    lines.push(`EVIDENCE ${rec.rationale.evidenceSummary.join(", ")}`);
  }

  // Compare summary
  if (rec.rationale.compareSummary.length > 0) {
    lines.push(`COMPARE ${rec.rationale.compareSummary.join(", ")}`);
  }

  // Warnings
  if (rec.warnings.length > 0) {
    lines.push(`WARNINGS ${rec.warnings.join(", ")}`);
  } else {
    lines.push("WARNINGS NONE");
  }

  // Debug mode: Show timestamp
  if (debugMode && rec.ts) {
    lines.push(`DEBUG_TS ${rec.ts}`);
  }

  lines.push("---");
  lines.push("");

  return lines;
}
