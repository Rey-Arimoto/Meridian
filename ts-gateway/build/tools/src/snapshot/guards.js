"use strict";
/**
 * PR165: v1.4 Market Regime Snapshot Export v1 - Guards
 *
 * Purpose:
 *   Sanitize and validate snapshot labels/warnings to prevent:
 *   - Token literals (wBTC, USDC, SUI, etc.)
 *   - Trading vocabulary (buy, sell, swap, execute, sign, transfer)
 *   - Prescriptive language (should, must, recommend)
 *   - Numeric/address patterns (0x..., prices, amounts)
 *
 * Constitutional Constraints:
 *   - Numerics allowed in saved files (for analysis)
 *   - Numerics FORBIDDEN in CLI/telemetry display
 *   - Always sanitize warnings/labels before display
 */
Object.defineProperty(exports, "__esModule", { value: true });
exports.sanitizeSnapshotLabel = sanitizeSnapshotLabel;
exports.validateSnapshotLabelsOnly = validateSnapshotLabelsOnly;
exports.formatSnapshotTimeLabel = formatSnapshotTimeLabel;
exports.sanitizeSnapshotForDisplay = sanitizeSnapshotForDisplay;
exports.formatSnapshotLabelOnlyLines = formatSnapshotLabelOnlyLines;
/**
 * Forbidden patterns (same as PR164 telemetry guards)
 */
var FORBIDDEN_PATTERNS = [
    // Token literals
    /\bwBTC\b/gi,
    /\bUSDC\b/gi,
    /\bSUI\b/gi,
    /\btoken\b/gi,
    // Trading vocabulary
    /\bbuy\b/gi,
    /\bsell\b/gi,
    /\bswap\b/gi,
    /\btrade\b/gi,
    /\bexecute\b/gi,
    /\bsign\b/gi,
    /\btransfer\b/gi,
    // Prescriptive language
    /\bshould\b/gi,
    /\bmust\b/gi,
    /\brecommend\b/gi,
    /\badvise\b/gi,
    // Address patterns
    /0x[a-fA-F0-9]{40}/g,
    /0x[a-fA-F0-9]{64}/g,
    // Price-like patterns (decimal numbers)
    /\b\d+\.\d+\b/g,
];
/**
 * Sanitize a single label value
 *
 * @param value - Label value to sanitize
 * @returns Sanitized value (REDACTED if forbidden pattern found)
 */
function sanitizeSnapshotLabel(value) {
    if (!value)
        return value;
    for (var _i = 0, FORBIDDEN_PATTERNS_1 = FORBIDDEN_PATTERNS; _i < FORBIDDEN_PATTERNS_1.length; _i++) {
        var pattern = FORBIDDEN_PATTERNS_1[_i];
        if (pattern.test(value)) {
            return "REDACTED";
        }
    }
    return value;
}
/**
 * Validate snapshot labels (check for forbidden patterns)
 *
 * @param snapshot - Snapshot to validate
 * @returns Validation result with warnings
 */
function validateSnapshotLabelsOnly(snapshot) {
    var warnings = [];
    var ok = true;
    // Check warnings array
    for (var _i = 0, _a = snapshot.warnings; _i < _a.length; _i++) {
        var warning = _a[_i];
        for (var _b = 0, FORBIDDEN_PATTERNS_2 = FORBIDDEN_PATTERNS; _b < FORBIDDEN_PATTERNS_2.length; _b++) {
            var pattern = FORBIDDEN_PATTERNS_2[_b];
            if (pattern.test(warning)) {
                warnings.push("WARN_SNAPSHOT_WARNING_SANITIZED");
                ok = false;
                break;
            }
        }
    }
    // Check labels
    var labelValues = Object.values(snapshot.labels);
    for (var _c = 0, labelValues_1 = labelValues; _c < labelValues_1.length; _c++) {
        var labelValue = labelValues_1[_c];
        if (typeof labelValue === "string") {
            for (var _d = 0, FORBIDDEN_PATTERNS_3 = FORBIDDEN_PATTERNS; _d < FORBIDDEN_PATTERNS_3.length; _d++) {
                var pattern = FORBIDDEN_PATTERNS_3[_d];
                if (pattern.test(labelValue)) {
                    warnings.push("WARN_SNAPSHOT_LABEL_SANITIZED");
                    ok = false;
                    break;
                }
            }
        }
    }
    return { ok: ok, warnings: warnings };
}
/**
 * Format timestamp as label (for CLI display)
 *
 * @param ts - Timestamp (epoch ms)
 * @returns Time label (T_RECENT / T_MIN / T_HOUR / T_OLD)
 */
function formatSnapshotTimeLabel(ts) {
    var now = Date.now();
    var ageMs = now - ts;
    if (ageMs < 60000) {
        // < 1 min
        return "T_RECENT";
    }
    else if (ageMs < 60 * 60000) {
        // < 1 hour
        return "T_MIN";
    }
    else if (ageMs < 24 * 60 * 60000) {
        // < 24 hours
        return "T_HOUR";
    }
    else {
        return "T_OLD";
    }
}
/**
 * Sanitize snapshot for display (remove/mask numerics)
 *
 * Purpose:
 *   Remove numerics field and convert ts/id to labels for CLI/telemetry display.
 *
 * @param snapshot - Raw snapshot
 * @returns Sanitized snapshot (label-only)
 */
function sanitizeSnapshotForDisplay(snapshot) {
    // Sanitize labels
    var sanitizedLabels = {};
    for (var _i = 0, _a = Object.entries(snapshot.labels); _i < _a.length; _i++) {
        var _b = _a[_i], key = _b[0], value = _b[1];
        if (typeof value === "string") {
            sanitizedLabels[key] = sanitizeSnapshotLabel(value);
        }
    }
    // Sanitize warnings
    var sanitizedWarnings = snapshot.warnings.map(sanitizeSnapshotLabel);
    return {
        version: snapshot.version,
        kind: snapshot.kind,
        status: snapshot.status,
        timeLabel: formatSnapshotTimeLabel(snapshot.ts),
        idLabel: snapshot.id ? "HAS_ID" : "NO_ID",
        warnings: sanitizedWarnings,
        presence: snapshot.presence,
        labels: sanitizedLabels,
        // numerics field is REMOVED (not included in sanitized output)
    };
}
/**
 * Format sanitized snapshot as CLI lines (label-only)
 *
 * @param sanitized - Sanitized snapshot
 * @returns Formatted string lines
 */
function formatSnapshotLabelOnlyLines(sanitized) {
    var lines = [];
    // Header
    lines.push("".concat(sanitized.timeLabel, " ").concat(sanitized.kind, " ").concat(sanitized.status));
    // ID
    lines.push("  ID: ".concat(sanitized.idLabel));
    // Presence (show major flags only)
    var presenceFlags = [
        sanitized.presence.hasShockPhase ? "SHOCK_PHASE" : null,
        sanitized.presence.hasStress ? "STRESS" : null,
        sanitized.presence.hasActionShape ? "ACTION" : null,
        sanitized.presence.hasTemplateId ? "TEMPLATE" : null,
        sanitized.presence.hasRoute ? "ROUTE" : null,
        sanitized.presence.hasGate ? "GATE" : null,
        sanitized.presence.hasPolicy ? "POLICY" : null,
        sanitized.presence.hasHardStop ? "HARDSTOP" : null,
    ]
        .filter(function (f) { return f !== null; })
        .join(", ");
    lines.push("  Presence: ".concat(presenceFlags || "NONE"));
    // Labels (show non-empty only)
    var labelPairs = [];
    for (var _i = 0, _a = Object.entries(sanitized.labels); _i < _a.length; _i++) {
        var _b = _a[_i], key = _b[0], value = _b[1];
        if (value) {
            labelPairs.push("".concat(key, "=").concat(value));
        }
    }
    if (labelPairs.length > 0) {
        lines.push("  Labels: ".concat(labelPairs.join(", ")));
    }
    // Warnings
    if (sanitized.warnings.length > 0) {
        lines.push("  Warnings: ".concat(sanitized.warnings.join(", ")));
    }
    return lines;
}
