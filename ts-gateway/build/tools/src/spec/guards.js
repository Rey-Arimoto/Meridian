"use strict";
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
Object.defineProperty(exports, "__esModule", { value: true });
exports.sanitizeLabel = sanitizeLabel;
exports.validateLabelOnly = validateLabelOnly;
exports.sanitizeWarnings = sanitizeWarnings;
exports.buildLabelWarning = buildLabelWarning;
/**
 * Forbidden patterns (addresses, tokens, trading vocab, prescriptive terms)
 */
var FORBIDDEN_PATTERNS = [
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
function sanitizeLabel(input) {
    if (!input || typeof input !== "string") {
        return "LABEL_INVALID";
    }
    var sanitized = input;
    // Remove forbidden patterns
    for (var _i = 0, FORBIDDEN_PATTERNS_1 = FORBIDDEN_PATTERNS; _i < FORBIDDEN_PATTERNS_1.length; _i++) {
        var pattern = FORBIDDEN_PATTERNS_1[_i];
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
function validateLabelOnly(input) {
    if (!input || typeof input !== "string") {
        return false;
    }
    // Check for forbidden patterns
    for (var _i = 0, FORBIDDEN_PATTERNS_2 = FORBIDDEN_PATTERNS; _i < FORBIDDEN_PATTERNS_2.length; _i++) {
        var pattern = FORBIDDEN_PATTERNS_2[_i];
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
function sanitizeWarnings(arr) {
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
function buildLabelWarning(code) {
    if (!code || typeof code !== "string") {
        return "WARN_UNKNOWN";
    }
    // Ensure code is uppercase and underscore-separated
    var normalized = code.toUpperCase().replace(/[^A-Z0-9_]/g, "_");
    return normalized || "WARN_UNKNOWN";
}
