/**
 * PR174: v1.4 Patch Effectiveness Tracker v1 - Window Selector
 *
 * Purpose:
 *   Select Before/After snapshot windows based on DecisionAck timestamp.
 *
 * Constitutional Constraints:
 *   - READ-ONLY: Selection only (no modification)
 *   - Fixed rules: Fixed window sizes
 *   - Defensive: Never throws, returns PARTIAL if insufficient data
 */

import { MarketRegimeSnapshotV1 } from "../snapshot/types";
import { DecisionAckRecordV1 } from "../decision/types";
import { EffectWindowConfig } from "./types";

/**
 * Selected Windows
 *
 * Result of window selection with warnings.
 */
export interface SelectedWindows {
  /**
   * Snapshots before ack
   */
  before: MarketRegimeSnapshotV1[];

  /**
   * Snapshots in short-term after window
   */
  afterShort: MarketRegimeSnapshotV1[];

  /**
   * Snapshots in medium-term after window
   */
  afterMedium: MarketRegimeSnapshotV1[];

  /**
   * Snapshots in long-term after window
   */
  afterLong: MarketRegimeSnapshotV1[];

  /**
   * Warnings (label-only)
   */
  warnings: string[];
}

/**
 * Default window config
 */
const DEFAULT_WINDOW_CONFIG: EffectWindowConfig = {
  beforeTail: 120,
  afterShort: 60,
  afterMedium: 180,
  afterLong: 600,
};

/**
 * Select effect windows v1
 *
 * Selects Before/After snapshot windows based on ack timestamp.
 *
 * Algorithm:
 * 1. Find ack timestamp (ts field from DecisionAckRecordV1)
 * 2. Split snapshots into Before (ts < ack) and After (ts >= ack)
 * 3. Take last N snapshots from Before
 * 4. Take first N snapshots from After for each window
 * 5. Return PARTIAL if insufficient snapshots
 *
 * @param snapshots - All snapshots (sorted by timestamp)
 * @param ack - Decision ack record
 * @param cfg - Window config (optional)
 * @returns Selected windows
 */
export function selectEffectWindowsV1(
  snapshots: MarketRegimeSnapshotV1[],
  ack: DecisionAckRecordV1,
  cfg?: Partial<EffectWindowConfig>
): SelectedWindows {
  const warnings: string[] = [];
  const config: EffectWindowConfig = {
    ...DEFAULT_WINDOW_CONFIG,
    ...cfg,
  };

  try {
    // Get ack timestamp
    const ackTs = ack.ts;

    if (!ackTs || ackTs === 0) {
      warnings.push("WARN_ACK_TIMESTAMP_MISSING");
      return {
        before: [],
        afterShort: [],
        afterMedium: [],
        afterLong: [],
        warnings,
      };
    }

    // Split snapshots into Before and After
    const beforeSnapshots: MarketRegimeSnapshotV1[] = [];
    const afterSnapshots: MarketRegimeSnapshotV1[] = [];

    for (const snapshot of snapshots) {
      if (!snapshot.ts || snapshot.ts === 0) {
        warnings.push("WARN_SNAPSHOT_TIMESTAMP_MISSING");
        continue;
      }

      if (snapshot.ts < ackTs) {
        beforeSnapshots.push(snapshot);
      } else {
        afterSnapshots.push(snapshot);
      }
    }

    // Sort snapshots by timestamp
    beforeSnapshots.sort((a, b) => a.ts - b.ts);
    afterSnapshots.sort((a, b) => a.ts - b.ts);

    // Select Before window (last N snapshots before ack)
    const before = beforeSnapshots.slice(-config.beforeTail);

    if (before.length < config.beforeTail) {
      warnings.push("WARN_BEFORE_WINDOW_INSUFFICIENT");
    }

    // Select After windows
    const afterShort = afterSnapshots.slice(0, config.afterShort);
    const afterMedium = afterSnapshots.slice(0, config.afterMedium);
    const afterLong = afterSnapshots.slice(0, config.afterLong);

    if (afterShort.length < config.afterShort) {
      warnings.push("WARN_AFTER_SHORT_INSUFFICIENT");
    }
    if (afterMedium.length < config.afterMedium) {
      warnings.push("WARN_AFTER_MEDIUM_INSUFFICIENT");
    }
    if (afterLong.length < config.afterLong) {
      warnings.push("WARN_AFTER_LONG_INSUFFICIENT");
    }

    return {
      before,
      afterShort,
      afterMedium,
      afterLong,
      warnings,
    };
  } catch (error) {
    // Defensive: Return empty windows with error warning
    warnings.push("WARN_WINDOW_SELECTION_ERROR");

    return {
      before: [],
      afterShort: [],
      afterMedium: [],
      afterLong: [],
      warnings,
    };
  }
}
