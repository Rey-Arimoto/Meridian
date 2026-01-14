/**
 * PR154: v1.4 Observation Labeler - Guards (READ-ONLY)
 *
 * Purpose:
 *   Validate that output labels do not contain forbidden vocabulary.
 *   Constitutional enforcement layer.
 *
 * Constitutional Constraints:
 *   - No prescriptive/trading vocabulary (buy/sell/trade/recommend/should/must)
 *   - No token names/literals in output
 *   - No addresses/numerics in output strings
 *   - Labels are boolean | "UNKNOWN" only
 *
 * Note: This is a defensive layer. If properly implemented,
 * these guards should never trigger in production.
 */

/**
 * Forbidden prescriptive/trading vocabulary
 *
 * These words must not appear in any output string
 * (labels, diagnostics, warnings, etc.)
 */
const FORBIDDEN_VOCAB = [
  // Prescriptive
  "should",
  "must",
  "recommend",
  "suggest",
  "advise",

  // Trading instructions
  "buy",
  "sell",
  "trade",
  "execute",
  "swap",
  "position",

  // Directional instructions
  "long",
  "short",
  "enter",
  "exit",
];

/**
 * Forbidden token literals
 *
 * Token names/symbols must not appear in output strings.
 * (Internal code can use these, but not in output.)
 */
const FORBIDDEN_TOKEN_LITERALS = [
  "wBTC",
  "WBTC",
  "wbtc",
  "USDC",
  "usdc",
  "SUI",
  "sui",
  "BTC",
  "btc",
  "Bitcoin",
  "bitcoin",
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
 * Check if string contains forbidden token literals
 *
 * @param str - String to check
 * @returns True if forbidden token literal found
 */
export function containsForbiddenTokenLiteral(str: string): boolean {
  for (const token of FORBIDDEN_TOKEN_LITERALS) {
    if (str.includes(token)) {
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
 * Note: This checks for standalone numbers, not numbers within words.
 * Examples:
 *   "price is 45000" → true (forbidden)
 *   "l2_min_depth" → false (allowed)
 */
export function containsNumericValue(str: string): boolean {
  // Match standalone numbers (not part of identifiers)
  const numericPattern = /\b\d+\.?\d*\b/;
  return numericPattern.test(str);
}

/**
 * Check if string contains address-like patterns
 *
 * @param str - String to check
 * @returns True if address pattern found
 *
 * Checks for:
 *   - Hex addresses (0x...)
 *   - Long alphanumeric strings (likely addresses)
 */
export function containsAddressPattern(str: string): boolean {
  // Check for hex addresses
  if (/0x[a-fA-F0-9]{10,}/.test(str)) {
    return true;
  }

  // Check for long alphanumeric strings (>20 chars, likely address)
  if (/[a-zA-Z0-9]{20,}/.test(str)) {
    return true;
  }

  return false;
}

/**
 * Validate output string (comprehensive check)
 *
 * @param str - String to validate
 * @returns Validation result with errors
 *
 * This is the main validation function. Use this to check
 * any output strings (diagnostics, warnings, etc.)
 */
export function validateOutputString(str: string): {
  valid: boolean;
  errors: string[];
} {
  const errors: string[] = [];

  if (containsForbiddenVocab(str)) {
    errors.push("FORBIDDEN_VOCAB");
  }

  if (containsForbiddenTokenLiteral(str)) {
    errors.push("FORBIDDEN_TOKEN_LITERAL");
  }

  if (containsNumericValue(str)) {
    errors.push("NUMERIC_VALUE");
  }

  if (containsAddressPattern(str)) {
    errors.push("ADDRESS_PATTERN");
  }

  return {
    valid: errors.length === 0,
    errors,
  };
}

/**
 * Validate label value (strict check)
 *
 * @param value - Label value to check
 * @returns True if valid label value
 *
 * Labels must be boolean | "UNKNOWN" only.
 */
export function isValidLabelValue(
  value: any
): value is boolean | "UNKNOWN" {
  return (
    typeof value === "boolean" ||
    value === "UNKNOWN"
  );
}
