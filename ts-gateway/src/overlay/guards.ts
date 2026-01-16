/**
 * PR177: v1.4 Pre-Adoption Risk Overlay v1 - Guards
 *
 * Purpose:
 *   Sanitize overlay labels and format output.
 *   Similar to PR171/172/174/175/176 label-only policy.
 *
 * Constitutional Constraints:
 *   - Label-only: No token literals, addresses, or numeric-like patterns
 *   - Defensive: Never throws
 */

import { RiskOverlayV1, OverlayEvidence } from "./types";

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
 * Sanitize overlay label
 *
 * @param label - Raw label
 * @returns Sanitized label
 */
export function sanitizeOverlayLabel(label: string): string {
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
 * Validate overlay label-only (no numerics in normal mode)
 *
 * @param label - Label to validate
 * @returns True if valid
 */
export function validateOverlayLabelOnly(label: string): boolean {
  if (!label || typeof label !== "string") {
    return false;
  }

  // Reject if contains large isolated numbers (not part of label like "P0_")
  if (/\b\d{3,}\b/.test(label)) {
    return false;
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
 * @returns Sanitized evidence
 */
export function sanitizeEvidence(
  evidence: OverlayEvidence
): OverlayEvidence {
  return {
    ...evidence,
    label: sanitizeOverlayLabel(evidence.label),
  };
}

/**
 * Sanitize risk overlay for display
 *
 * @param overlay - Raw overlay
 * @returns Sanitized overlay
 */
export function sanitizeRiskOverlayV1(
  overlay: RiskOverlayV1
): RiskOverlayV1 {
  return {
    ...overlay,
    risks: overlay.risks.map((r) => ({
      ...r,
      label: sanitizeOverlayLabel(r.label),
    })),
    evidence: overlay.evidence.map(sanitizeEvidence),
    warnings: overlay.warnings.map(sanitizeOverlayLabel),
  };
}
