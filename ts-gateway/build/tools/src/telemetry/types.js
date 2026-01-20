"use strict";
/**
 * PR164: v1.4 Telemetry Types (READ-ONLY)
 *
 * Purpose:
 *   Define event types for append-only audit log.
 *   Events record "what happened" (facts), not predictions or instructions.
 *
 * Constitutional Constraints:
 *   - READ-ONLY: Record facts only, no learning, no optimization, no prediction
 *   - Label-only: All labels/warnings are strings, no numerics in display
 *   - Numeric timestamps: Internal only (ts field), never in labels/warnings
 *   - Defensive: Never throws, handles malformed events gracefully
 */
Object.defineProperty(exports, "__esModule", { value: true });
exports.createEventV1 = createEventV1;
/**
 * Create empty event (helper)
 */
function createEventV1(type, level, labels, warnings) {
    if (level === void 0) { level = "INFO"; }
    if (labels === void 0) { labels = {}; }
    if (warnings === void 0) { warnings = []; }
    return {
        v: "v1",
        ts: Date.now(),
        level: level,
        type: type,
        labels: labels,
        warnings: warnings,
    };
}
