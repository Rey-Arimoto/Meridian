"use strict";
/**
 * PR164: v1.4 Telemetry Guards (READ-ONLY)
 *
 * Purpose:
 *   Ensure telemetry events are label-only (no numerics, no sensitive data).
 *
 * Constitutional Constraints:
 *   - Label-only: No numerics, no token literals, no trading vocab, no prescriptive
 *   - Defensive: Never throws, returns sanitized copy
 *   - Safe defaults: Forbidden values → "REDACTED"
 */
var __assign = (this && this.__assign) || function () {
    __assign = Object.assign || function(t) {
        for (var s, i = 1, n = arguments.length; i < n; i++) {
            s = arguments[i];
            for (var p in s) if (Object.prototype.hasOwnProperty.call(s, p))
                t[p] = s[p];
        }
        return t;
    };
    return __assign.apply(this, arguments);
};
Object.defineProperty(exports, "__esModule", { value: true });
exports.containsForbiddenPatterns = containsForbiddenPatterns;
exports.sanitizeLabelValue = sanitizeLabelValue;
exports.validateEventV1 = validateEventV1;
exports.formatTimestampLabel = formatTimestampLabel;
exports.formatLabelOnlyLine = formatLabelOnlyLine;
exports.containsNumericPatterns = containsNumericPatterns;
/**
 * Forbidden patterns (extended from PR154/155/156)
 */
var FORBIDDEN_PATTERNS = {
    // Token literals
    tokens: /\b(wBTC|WBTC|BTC|USDC|SUI|ETH|SOL)\b/gi,
    // Trading vocabulary
    trading: /\b(swap|buy|sell|execute|sign|transfer|approve|allowance|spend)\b/gi,
    // Prescriptive vocabulary
    prescriptive: /\b(should|must|need|recommend|advise|suggest|ought)\b/gi,
    // Numeric patterns
    numeric: /(\d+\.\d+|\d{4,}|\$\d+|\d+%|0x[0-9a-fA-F]+)/g,
};
/**
 * Check if value contains forbidden patterns
 *
 * @param value - Value to check
 * @returns True if contains forbidden patterns
 */
function containsForbiddenPatterns(value) {
    return Object.values(FORBIDDEN_PATTERNS).some(function (pattern) { return pattern.test(value); });
}
/**
 * Sanitize label value (replace forbidden with "REDACTED")
 *
 * @param value - Label value to sanitize
 * @returns Sanitized value
 */
function sanitizeLabelValue(value) {
    var sanitized = value;
    // Replace each forbidden pattern
    for (var _i = 0, _a = Object.values(FORBIDDEN_PATTERNS); _i < _a.length; _i++) {
        var pattern = _a[_i];
        sanitized = sanitized.replace(pattern, "REDACTED");
    }
    // If still contains issues, redact entirely
    if (containsForbiddenPatterns(sanitized)) {
        return "REDACTED";
    }
    return sanitized;
}
/**
 * Validate and sanitize event (defensive)
 *
 * @param event - Event to validate
 * @returns Sanitized event
 */
function validateEventV1(event) {
    try {
        var sanitizedLabels = {};
        // Sanitize labels
        for (var _i = 0, _a = Object.entries(event.labels); _i < _a.length; _i++) {
            var _b = _a[_i], key = _b[0], value = _b[1];
            if (value === undefined) {
                sanitizedLabels[key] = undefined;
                continue;
            }
            sanitizedLabels[key] = sanitizeLabelValue(value);
        }
        // Sanitize warnings
        var sanitizedWarnings = event.warnings.map(sanitizeLabelValue);
        return __assign(__assign({}, event), { labels: sanitizedLabels, warnings: sanitizedWarnings });
    }
    catch (error) {
        // Defensive: Return minimal safe event
        return {
            v: "v1",
            ts: event.ts || Date.now(),
            level: "ERROR",
            type: "ERROR",
            labels: {},
            warnings: ["WARN_EVENT_VALIDATION_ERROR"],
        };
    }
}
/**
 * Format timestamp as label (no numeric output)
 *
 * @param ts - Timestamp (epoch ms)
 * @param nowTs - Current timestamp (optional)
 * @returns Time label (T_RECENT / T_OLD / T_UNKNOWN)
 */
function formatTimestampLabel(ts, nowTs) {
    try {
        var now = nowTs || Date.now();
        var ageMs = now - ts;
        if (ageMs < 0) {
            return "T_FUTURE"; // Clock skew
        }
        if (ageMs < 60000) {
            return "T_RECENT"; // < 1 minute
        }
        if (ageMs < 3600000) {
            return "T_HOUR"; // < 1 hour
        }
        if (ageMs < 86400000) {
            return "T_DAY"; // < 1 day
        }
        return "T_OLD"; // > 1 day
    }
    catch (error) {
        return "T_UNKNOWN";
    }
}
/**
 * Format event as label-only line (for CLI display)
 *
 * @param event - Event to format
 * @returns Label-only string (no numerics)
 */
function formatLabelOnlyLine(event) {
    try {
        var timeLabel = formatTimestampLabel(event.ts);
        var level = event.level.padEnd(5);
        var type = event.type.padEnd(20);
        // Format labels (key=value pairs)
        var labelPairs = [];
        for (var _i = 0, _a = Object.entries(event.labels); _i < _a.length; _i++) {
            var _b = _a[_i], key = _b[0], value = _b[1];
            if (value !== undefined) {
                labelPairs.push("".concat(key, "=").concat(value));
            }
        }
        var labelsStr = labelPairs.length > 0 ? labelPairs.join(" ") : "";
        var warningsStr = event.warnings.length > 0 ? "[".concat(event.warnings.join(", "), "]") : "";
        // Combine parts
        var parts = [
            "[".concat(timeLabel, "]"),
            "[".concat(level, "]"),
            "[".concat(type, "]"),
            labelsStr,
            warningsStr,
        ].filter(function (p) { return p !== "" && p !== "[]"; });
        return parts.join(" ");
    }
    catch (error) {
        return "[ERROR] WARN_FORMAT_ERROR";
    }
}
/**
 * Check if line contains any numeric patterns (for validation)
 *
 * @param line - Line to check
 * @returns True if contains numeric patterns
 */
function containsNumericPatterns(line) {
    var numericPattern = /(\d+\.\d+|\d{4,}|\$\d+|\d+%|0x[0-9a-fA-F]+)/;
    return numericPattern.test(line);
}
