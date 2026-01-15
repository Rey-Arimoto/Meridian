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

import { ResumeState } from "../rebalance/types";

/**
 * State status (for read/write operations)
 */
export type StateStatus = "OK" | "STALE" | "ERROR";

/**
 * Meridian state v1 (persistent)
 */
export interface MeridianStateV1 {
  // Schema version
  version: "v1";

  // Last updated timestamp (internal numeric only)
  updatedAtTs: number;

  // Last known run outcome (label-only)
  lastRun?: {
    status: string; // COMPLETED / STOPPED / ERROR etc
    stopReason?: string; // StopReason label
    phaseLabel?: string;
    routeSelected?: string;
    templateId?: string;
    action?: string; // label-only
    warnings: string[];
  };

  // PR162: Resume state (if stopped)
  resumeState?: ResumeState;

  // PR156: HardStop state
  hardStop?: {
    active: boolean;
    reason?: string; // label-only
    untilTs?: number; // internal numeric
  };

  // PR158: Cooldown state
  cooldown?: {
    lastActionTs?: number; // internal numeric
  };

  // Heartbeat-ish health (label-only)
  health?: {
    oracle: "AVAILABLE" | "STALE" | "ERROR" | "UNKNOWN";
    route: "AVAILABLE" | "NONE" | "UNKNOWN";
    policy: "OK" | "DENY" | "UNKNOWN";
    notes: string[]; // label-only
  };

  // Warnings (label-only)
  warnings: string[];
}

/**
 * Create empty state (defensive default)
 */
export function createEmptyStateV1(nowTs: number = Date.now()): MeridianStateV1 {
  return {
    version: "v1",
    updatedAtTs: nowTs,
    warnings: [],
  };
}
