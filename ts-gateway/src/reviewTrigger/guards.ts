/**
 * PR178: v1.4 Manual Review Trigger Hook v1 - Guards
 *
 * Purpose:
 *   Sanitize trigger warnings to ensure label-only output.
 *
 * Constitutional Constraints:
 *   - Label-only: No token literals, addresses, or numeric-like patterns
 *   - Defensive: Never throws
 */

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
 * Sanitize trigger warning
 *
 * @param warning - Raw warning
 * @returns Sanitized warning
 */
export function sanitizeTriggerWarning(warning: string): string {
  if (!warning || typeof warning !== "string") {
    return "WARNING_INVALID";
  }

  let sanitized = warning;

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
 * Sanitize trigger warnings array
 *
 * @param warnings - Raw warnings
 * @returns Sanitized warnings
 */
export function sanitizeTriggerWarnings(warnings: string[]): string[] {
  if (!Array.isArray(warnings)) {
    return [];
  }

  return warnings.map(sanitizeTriggerWarning);
}
