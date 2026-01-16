/**
 * PR180: v1.4 Spec Change Digest v1 - Guards
 *
 * Purpose:
 *   Sanitize digest output to enforce label-only.
 *
 * Constitutional Constraints:
 *   - Label-only: No token literals, addresses, numerics, timestamps, trading vocab
 *   - Defensive: Never throws
 */

import { SpecChangeDigestV1, DigestTimeLabel } from "./types";

/**
 * Forbidden patterns (token literals, addresses, numerics, trading vocab)
 */
const FORBIDDEN_PATTERNS = [
  /0x[a-fA-F0-9]{40}/g, // Ethereum-like addresses
  /[A-Z0-9]{32,}/g, // Long alphanumeric (API keys, tokens)
  /\b(buy|sell|long|short|market|limit)\b/gi, // Trading vocab
  /\b(execute|trade|swap|rebalance)\b/gi, // Action vocab
  /\b\d+(\.\d+)?\s*(USD|USDC|SUI|BTC|ETH|wBTC)\b/gi, // Amounts with currencies
  /\b(must|should|will|shall)\b/gi, // Prescriptive terms
  /\b\d{1,10}(\.\d+)?\b/g, // Standalone numbers
  /\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}/g, // ISO timestamps
];

/**
 * Sanitize label string
 *
 * @param input - Raw string
 * @returns Sanitized label
 */
export function sanitizeLabel(input: string): string {
  if (!input || typeof input !== "string") {
    return "LABEL_INVALID";
  }

  let sanitized = input;

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
 * Format time label
 *
 * @param ts - Epoch ms (optional)
 * @returns Time label
 */
export function formatTimeLabel(ts?: number): DigestTimeLabel {
  if (!ts || typeof ts !== "number") {
    return "T_UNKNOWN";
  }

  const now = Date.now();
  const diff = now - ts;

  if (diff < 0) {
    return "T_UNKNOWN"; // Future timestamp
  } else if (diff < 60 * 1000) {
    return "T_RECENT"; // < 1 minute
  } else if (diff < 60 * 60 * 1000) {
    return "T_MIN"; // < 1 hour
  } else if (diff < 24 * 60 * 60 * 1000) {
    return "T_HOUR"; // < 24 hours
  } else {
    return "T_OLD"; // >= 24 hours
  }
}

/**
 * Validate digest is label-only
 *
 * @param report - Digest report
 * @returns Validation result
 */
export function validateDigestLabelOnly(
  report: SpecChangeDigestV1
): { ok: boolean; warnings: string[] } {
  const warnings: string[] = [];

  // Check all string arrays for forbidden patterns
  const fieldsToCheck: (keyof SpecChangeDigestV1)[] = [
    "headline",
    "why",
    "what",
    "risks",
    "checklist",
    "rationale",
    "warnings",
  ];

  for (const field of fieldsToCheck) {
    const value = report[field];

    if (Array.isArray(value)) {
      for (const item of value) {
        if (typeof item === "string") {
          // Check for forbidden patterns
          for (const pattern of FORBIDDEN_PATTERNS) {
            if (pattern.test(item)) {
              warnings.push(`WARN_FORBIDDEN_PATTERN_IN_${field.toUpperCase()}`);
              break;
            }
          }
        }
      }
    }
  }

  return {
    ok: warnings.length === 0,
    warnings,
  };
}

/**
 * Sanitize string array
 *
 * @param arr - String array
 * @returns Sanitized array
 */
export function sanitizeStringArray(arr: string[]): string[] {
  if (!Array.isArray(arr)) {
    return [];
  }

  return arr.map(sanitizeLabel);
}
