/**
 * PR175: v1.4 Regression Guard v1 - Guards
 *
 * Purpose:
 *   Sanitize regression labels and format output.
 *   Similar to PR171/172/174 label-only policy.
 *
 * Constitutional Constraints:
 *   - Label-only: No token literals, addresses, or numeric-like patterns
 *   - Defensive: Never throws
 *   - Debug mode: MERIDIAN_DEBUG=true allows numerics in JSON
 */

import { RegressionReportV1, RegressionEvidence } from "./types";

/**
 * Forbidden patterns (token literals, addresses, trading vocab, etc.)
 */
const FORBIDDEN_PATTERNS = [
  /0x[a-fA-F0-9]{40}/g, // Ethereum-like addresses
  /[A-Z0-9]{32,}/g, // Long alphanumeric (API keys, tokens)
  /\b(buy|sell|long|short|market|limit)\b/gi, // Trading vocab
  /\b(execute|trade|swap|rebalance)\b/gi, // Action vocab
  /\b\d+(\.\d+)?\s*(USD|USDC|SUI|BTC|ETH)\b/gi, // Amounts with currencies
];

/**
 * Sanitize regression label
 *
 * @param label - Raw label
 * @returns Sanitized label
 */
export function sanitizeRegressionLabel(label: string): string {
  if (!label || typeof label !== "string") {
    return "LABEL_INVALID";
  }

  let sanitized = label;

  // Remove forbidden patterns
  for (const pattern of FORBIDDEN_PATTERNS) {
    sanitized = sanitized.replace(pattern, "REDACTED");
  }

  // Truncate if too long
  if (sanitized.length > 200) {
    sanitized = sanitized.slice(0, 200) + "...";
  }

  return sanitized;
}

/**
 * Check if debug mode is enabled
 *
 * @returns True if MERIDIAN_DEBUG=true
 */
export function isDebugMode(): boolean {
  return process.env.MERIDIAN_DEBUG === "true";
}

/**
 * Validate regression label-only (no numerics in normal mode)
 *
 * @param label - Label to validate
 * @param debugMode - Debug mode flag
 * @returns True if valid
 */
export function validateRegressionLabelOnly(
  label: string,
  debugMode: boolean
): boolean {
  if (!label || typeof label !== "string") {
    return false;
  }

  // In normal mode, reject numeric-like patterns
  if (!debugMode) {
    // Reject if contains isolated numbers (not part of label like "WIN_AFTER_SHORT")
    if (/\b\d+(\.\d+)?\b/.test(label)) {
      return false;
    }
  }

  // Always reject forbidden patterns
  for (const pattern of FORBIDDEN_PATTERNS) {
    if (pattern.test(label)) {
      return false;
    }
  }

  return true;
}

/**
 * Sanitize evidence for display
 *
 * @param evidence - Raw evidence
 * @param debugMode - Debug mode flag
 * @returns Sanitized evidence
 */
export function sanitizeEvidence(
  evidence: RegressionEvidence,
  debugMode: boolean
): RegressionEvidence {
  return {
    ...evidence,
    label: sanitizeRegressionLabel(evidence.label),
  };
}

/**
 * Sanitize regression report for display
 *
 * @param report - Raw report
 * @param debugMode - Debug mode flag
 * @returns Sanitized report
 */
export function sanitizeRegressionForDisplayV1(
  report: RegressionReportV1,
  debugMode: boolean
): Partial<RegressionReportV1> {
  const sanitized: Partial<RegressionReportV1> = {
    kind: report.kind,
    status: report.status,
    analysis: {
      ...report.analysis,
      evidence: report.analysis.evidence.map((e) =>
        sanitizeEvidence(e, debugMode)
      ),
      warnings: report.analysis.warnings.map(sanitizeRegressionLabel),
    },
    warnings: report.warnings.map(sanitizeRegressionLabel),
  };

  // In debug mode, include ts
  if (debugMode) {
    sanitized.ts = report.ts;
  }

  return sanitized;
}

/**
 * Format regression report as label-only lines
 *
 * @param report - Regression report
 * @param debugMode - Debug mode flag
 * @returns Formatted lines
 */
export function formatRegressionLinesV1(
  report: RegressionReportV1,
  debugMode: boolean
): string[] {
  const lines: string[] = [];

  // Header
  lines.push("=== Regression Report V1 ===");
  lines.push("");

  // Status
  lines.push(`Status: ${report.status}`);

  if (report.status === "ERROR" || report.status === "PARTIAL") {
    lines.push(`Warnings: ${report.warnings.join(", ")}`);
    return lines;
  }

  // Analysis
  const { analysis } = report;
  lines.push(`Proposal: ${analysis.proposalId}`);
  lines.push(`Decision: ${analysis.decision}`);
  lines.push(`Kind: ${analysis.kind}`);
  lines.push(`Strength: ${analysis.strength}`);
  lines.push(`Window: ${analysis.windowLabel}`);
  lines.push("");

  // Evidence (max 3)
  if (analysis.evidence.length > 0) {
    lines.push("Evidence:");
    const maxEvidence = 3;
    const evidenceToShow = analysis.evidence.slice(0, maxEvidence);

    for (const evid of evidenceToShow) {
      const sanitizedLabel = sanitizeRegressionLabel(evid.label);
      lines.push(
        `  - [${evid.kind}] ${sanitizedLabel} (${evid.strength})`
      );
    }

    if (analysis.evidence.length > maxEvidence) {
      lines.push(
        `  ... and ${analysis.evidence.length - maxEvidence} more`
      );
    }
    lines.push("");
  }

  // Warnings
  if (analysis.warnings.length > 0) {
    lines.push(`Warnings: ${analysis.warnings.join(", ")}`);
    lines.push("");
  }

  // Debug info
  if (debugMode) {
    lines.push(`Timestamp: ${report.ts}`);
    lines.push("");
  }

  return lines;
}
