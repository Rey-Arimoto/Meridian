/**
 * PR176: v1.4 Change Interaction Detector v1 - Guards
 *
 * Purpose:
 *   Sanitize interaction labels and format output.
 *   Similar to PR171/172/174/175 label-only policy.
 *
 * Constitutional Constraints:
 *   - Label-only: No token literals, addresses, or numeric-like patterns
 *   - Defensive: Never throws
 *   - Debug mode: MERIDIAN_DEBUG=true allows numerics in JSON
 */

import { InteractionReportV1, InteractionEvidence } from "./types";

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
 * Sanitize interaction label
 *
 * @param label - Raw label
 * @returns Sanitized label
 */
export function sanitizeInteractionLabel(label: string): string {
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
 * Validate interaction label-only (no numerics in normal mode)
 *
 * @param label - Label to validate
 * @param debugMode - Debug mode flag
 * @returns True if valid
 */
export function validateInteractionLabelOnly(
  label: string,
  debugMode: boolean
): boolean {
  if (!label || typeof label !== "string") {
    return false;
  }

  // In normal mode, reject numeric-like patterns
  if (!debugMode) {
    // Reject if contains isolated numbers (not part of label like "WITHIN_2")
    if (/\b\d{2,}\b/.test(label)) {
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
  evidence: InteractionEvidence,
  debugMode: boolean
): InteractionEvidence {
  return {
    ...evidence,
    label: sanitizeInteractionLabel(evidence.label),
  };
}

/**
 * Sanitize interaction report for display
 *
 * @param report - Raw report
 * @param debugMode - Debug mode flag
 * @returns Sanitized report
 */
export function sanitizeInteractionForDisplayV1(
  report: InteractionReportV1,
  debugMode: boolean
): Partial<InteractionReportV1> {
  const sanitized: Partial<InteractionReportV1> = {
    kind: report.kind,
    status: report.status,
    primaryProposalId: report.primaryProposalId,
    secondaryProposalId: report.secondaryProposalId,
    primaryDecision: report.primaryDecision,
    secondaryDecision: report.secondaryDecision,
    interaction: report.interaction,
    interactionKind: report.interactionKind,
    strength: report.strength,
    window: report.window,
    timeLabel: report.timeLabel,
    evidence: report.evidence.map((e) => sanitizeEvidence(e, debugMode)),
    warnings: report.warnings.map(sanitizeInteractionLabel),
  };

  // In debug mode, include ts
  if (debugMode) {
    sanitized.ts = report.ts;
  }

  return sanitized;
}

/**
 * Format interaction report as label-only lines
 *
 * @param report - Interaction report
 * @param debugMode - Debug mode flag
 * @returns Formatted lines
 */
export function formatInteractionLinesV1(
  report: InteractionReportV1,
  debugMode: boolean
): string[] {
  const lines: string[] = [];

  // Header
  lines.push("=== Interaction Report V1 ===");
  lines.push("");

  // Status
  lines.push(`Status: ${report.status}`);

  if (report.status === "ERROR" || report.status === "PARTIAL") {
    lines.push(`Warnings: ${report.warnings.join(", ")}`);
    return lines;
  }

  // Proposals
  lines.push(`Primary: ${report.primaryProposalId || "UNKNOWN"}`);
  lines.push(`Secondary: ${report.secondaryProposalId || "UNKNOWN"}`);
  lines.push("");

  // Decisions
  if (report.primaryDecision) {
    lines.push(`Primary Decision: ${report.primaryDecision}`);
  }
  if (report.secondaryDecision) {
    lines.push(`Secondary Decision: ${report.secondaryDecision}`);
  }
  lines.push("");

  // Interaction analysis
  lines.push(`Interaction: ${report.interaction}`);
  lines.push(`Kind: ${report.interactionKind}`);
  lines.push(`Strength: ${report.strength}`);
  lines.push(`Window: ${report.window}`);
  lines.push(`Time: ${report.timeLabel}`);
  lines.push("");

  // Evidence (max 3)
  if (report.evidence.length > 0) {
    lines.push("Evidence:");
    const evidenceToShow = report.evidence.slice(0, 3);

    for (const evid of evidenceToShow) {
      const sanitizedLabel = sanitizeInteractionLabel(evid.label);
      lines.push(
        `  - [${evid.kind}] ${sanitizedLabel} (${evid.strength})`
      );
    }

    if (report.evidence.length > 3) {
      lines.push(
        `  ... and ${report.evidence.length - 3} more`
      );
    }
    lines.push("");
  }

  // Warnings
  if (report.warnings.length > 0) {
    lines.push(`Warnings: ${report.warnings.join(", ")}`);
    lines.push("");
  }

  // Debug info
  if (debugMode) {
    lines.push(`Timestamp: ${report.ts}`);
    lines.push("");
  }

  return lines;
}
