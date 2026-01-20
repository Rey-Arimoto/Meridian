"use strict";
/**
 * PR163: v1.4 Supervisor State Types (READ-ONLY)
 *
 * Purpose:
 *   Define persistent state schema for 24/7 operational loop.
 *   State includes: ResumeState, HardStop, Cooldown, lastRun, health.
 *
 * Constitutional Constraints:
 *   - READ-ONLY: Fixed schema, no learning, no optimization
 *   - Label-only: All reasons/warnings/notes are labels
 *   - Numeric timestamps: Internal only, never in logs/output
 *   - Defensive: Unknown fields ignored (forward-compatible)
 */
Object.defineProperty(exports, "__esModule", { value: true });
exports.createEmptyStateV1 = createEmptyStateV1;
/**
 * Create empty state (defensive default)
 */
function createEmptyStateV1(nowTs) {
    if (nowTs === void 0) { nowTs = Date.now(); }
    return {
        version: "v1",
        updatedAtTs: nowTs,
        warnings: [],
    };
}
