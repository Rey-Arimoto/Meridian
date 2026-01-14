/**
 * PR156: v1.4 Execution Simulation - Guards (READ-ONLY)
 *
 * Purpose:
 *   Validate that simulation output does not contain forbidden content.
 *   Constitutional enforcement layer for warnings/reasons.
 *
 * Constitutional Constraints:
 *   - No numeric values in warnings/reasons (internal calculations OK)
 *   - No prescriptive/trading vocabulary
 *   - No token literals in output strings
 *   - Label-only output
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
 * Forbidden token literals
 */
const FORBIDDEN_TOKEN_LITERALS = [
  "wBTC",
  "WBTC",
  "wbtc",
  "USDC",
  "usdc",
  "SUI",
  "sui",
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
export function containsTokenLiteral(str: string): boolean {
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
 * Numeric values should not appear in warnings/reasons.
 * Internal calculations can use numbers, but output must be label-only.
 */
export function containsNumericLike(str: string): boolean {
  // Match standalone numbers (not part of identifiers)
  const numericPattern = /\b\d+\.?\d*\b/;
  return numericPattern.test(str);
}

/**
 * Check if string contains prescriptive language
 *
 * @param str - String to check
 * @returns True if prescriptive language found
 */
export function containsPrescriptive(str: string): boolean {
  return containsForbiddenVocab(str);
}

/**
 * Validate label-only strings (comprehensive check)
 *
 * @param strings - Strings to validate
 * @returns Validated strings (sanitized if needed)
 *
 * This is the main validation function for warnings/reasons.
 * If validation fails, replaces with generic label.
 */
export function validateLabelOnlyStrings(strings: string[]): string[] {
  return strings.map((str) => {
    // Check all forbidden patterns
    if (containsForbiddenVocab(str)) {
      return "WARN_SANITIZED_VOCAB";
    }

    if (containsTokenLiteral(str)) {
      return "WARN_SANITIZED_TOKEN";
    }

    if (containsNumericLike(str)) {
      return "WARN_SANITIZED_NUMERIC";
    }

    // String is clean
    return str;
  });
}

/**
 * Sanitize warnings (defensive fallback)
 *
 * @param warnings - Warning strings
 * @returns Sanitized warnings
 *
 * If any warning contains forbidden content, replace with generic label.
 * This is a defensive fallback to prevent leaking forbidden content.
 */
export function sanitizeWarnings(warnings: string[]): string[] {
  return validateLabelOnlyStrings(warnings);
}

/**
 * Validate simulation output (check for violations)
 *
 * @param warnings - Warning strings
 * @param reasons - Reason strings
 * @returns Validation result
 *
 * Use this to check simulation output before returning.
 * Returns list of violations found.
 */
export function validateSimulationOutput(
  warnings: string[],
  reasons: string[]
): {
  valid: boolean;
  violations: string[];
} {
  const violations: string[] = [];

  // Check warnings
  for (const warning of warnings) {
    if (containsNumericLike(warning)) {
      violations.push("NUMERIC_IN_WARNING");
    }
    if (containsForbiddenVocab(warning)) {
      violations.push("FORBIDDEN_VOCAB_IN_WARNING");
    }
    if (containsTokenLiteral(warning)) {
      violations.push("TOKEN_LITERAL_IN_WARNING");
    }
  }

  // Check reasons (converted to strings for validation)
  for (const reason of reasons) {
    if (containsNumericLike(reason)) {
      violations.push("NUMERIC_IN_REASON");
    }
    if (containsForbiddenVocab(reason)) {
      violations.push("FORBIDDEN_VOCAB_IN_REASON");
    }
  }

  return {
    valid: violations.length === 0,
    violations,
  };
}
