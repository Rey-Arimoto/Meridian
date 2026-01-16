/**
 * PR179: v1.4 Spec Version Lock + Human ACK Gate v1 - Guards
 *
 * Purpose:
 *   Sanitize spec warnings and reasons to enforce label-only output.
 *
 * Constitutional Constraints:
 *   - Label-only: No numeric literals, addresses, token names, or trading vocab
 *   - Defensive: Never throws
 */

/**
 * Forbidden patterns (addresses, tokens, trading vocab, prescriptive terms)
 */
const FORBIDDEN_PATTERNS = [
  /0x[a-fA-F0-9]{40}/g, // Ethereum-like addresses
  /[A-Z0-9]{32,}/g, // Long alphanumeric (API keys, tokens)
  /\b(buy|sell|long|short|market|limit)\b/gi, // Trading vocab
  /\b(execute|trade|swap|rebalance)\b/gi, // Action vocab
  /\b\d+(\.\d+)?\s*(USD|USDC|SUI|BTC|ETH|wBTC)\b/gi, // Amounts with currencies
  /\b(must|should|will|shall)\b/gi, // Prescriptive terms
  /\b\d{1,10}(\.\d+)?\b/g, // Standalone numbers
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
 * Validate if input is label-only
 *
 * @param input - String to validate
 * @returns True if label-only
 */
export function validateLabelOnly(input: string): boolean {
  if (!input || typeof input !== "string") {
    return false;
  }

  // Check for forbidden patterns
  for (const pattern of FORBIDDEN_PATTERNS) {
    if (pattern.test(input)) {
      return false;
    }
  }

  return true;
}

/**
 * Sanitize warnings array
 *
 * @param arr - Raw warnings
 * @returns Sanitized warnings
 */
export function sanitizeWarnings(arr: string[]): string[] {
  if (!Array.isArray(arr)) {
    return [];
  }

  return arr.map(sanitizeLabel);
}

/**
 * Build label warning from code
 *
 * @param code - Warning code
 * @returns Label warning
 */
export function buildLabelWarning(code: string): string {
  if (!code || typeof code !== "string") {
    return "WARN_UNKNOWN";
  }

  // Ensure code is uppercase and underscore-separated
  const normalized = code.toUpperCase().replace(/[^A-Z0-9_]/g, "_");

  return normalized || "WARN_UNKNOWN";
}
