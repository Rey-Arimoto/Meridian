/**
 * PR155: v1.4 Price Oracle Integration - Guards (READ-ONLY)
 *
 * Purpose:
 *   Validate that oracle output does not contain forbidden content.
 *   Constitutional enforcement layer for oracle warnings/logs.
 *
 * Constitutional Constraints:
 *   - No numeric values in warnings/logs (internal calculations OK)
 *   - No prescriptive/trading vocabulary
 *   - No token literals in output strings
 *   - No addresses in output strings
 */

/**
 * Forbidden prescriptive/trading vocabulary
 */
const FORBIDDEN_VOCAB = [
  "should",
  "must",
  "recommend",
  "suggest",
  "advise",
  "buy",
  "sell",
  "trade",
  "execute",
  "swap",
  "position",
  "long",
  "short",
  "enter",
  "exit",
];

/**
 * Check if string contains forbidden vocabulary
 *
 * @param str - String to check
 * @returns True if forbidden vocab found
 */
export function containsForbiddenVocab(str: string): boolean {
  const lowerStr = str.toLowerCase();

  for (const word of FORBIDDEN_VOCAB) {
    if (lowerStr.includes(word)) {
      return true;
    }
  }

  return false;
}

/**
 * Check if string contains numeric values
 *
 * @param str - String to check
 * @returns True if numeric values found
 *
 * Numeric values should not appear in warnings/logs.
 * Internal calculations can use numbers, but output must be label-only.
 */
export function containsNumericValue(str: string): boolean {
  // Match standalone numbers (not part of identifiers)
  const numericPattern = /\b\d+\.?\d*\b/;
  return numericPattern.test(str);
}

/**
 * Validate warning string (comprehensive check)
 *
 * @param str - Warning string to validate
 * @returns Validation result with errors
 *
 * Use this to validate all warning strings before adding to OracleResult.
 */
export function validateWarningString(str: string): {
  valid: boolean;
  errors: string[];
} {
  const errors: string[] = [];

  if (containsForbiddenVocab(str)) {
    errors.push("FORBIDDEN_VOCAB");
  }

  if (containsNumericValue(str)) {
    errors.push("NUMERIC_VALUE");
  }

  return {
    valid: errors.length === 0,
    errors,
  };
}

/**
 * Sanitize warning string (defensive fallback)
 *
 * @param str - Warning string
 * @returns Sanitized string or generic label
 *
 * If validation fails, return a generic label instead of the original string.
 * This is a defensive fallback to prevent leaking forbidden content.
 */
export function sanitizeWarning(str: string): string {
  const validation = validateWarningString(str);

  if (validation.valid) {
    return str;
  }

  // Return generic label if validation fails
  return "ORACLE_WARNING";
}
