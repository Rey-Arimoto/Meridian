/**
 * PR181: v1.4 Observe 1s Loop + Chunk 10s + Immediate STOP v1 - Guards
 *
 * Purpose:
 *   Sanitize observe loop output to enforce label-only.
 *
 * Constitutional Constraints:
 *   - Label-only: No numerics, addresses, tokens, trading vocab
 *   - Defensive: Never throws
 */

import { TimeLabel } from "./types";

/**
 * Forbidden patterns
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

/**
 * Format time label
 *
 * @param ts - Epoch ms (optional)
 * @returns Time label
 */
export function formatTimeLabel(ts?: number): TimeLabel {
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
