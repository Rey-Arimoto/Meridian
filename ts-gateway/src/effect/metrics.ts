/**
 * PR174: v1.4 Patch Effectiveness Tracker v1 - Metrics
 *
 * Purpose:
 *   Calculate fixed metrics for each time window.
 *   Measures operational health (gate pass/block, stops, etc.).
 *
 * Constitutional Constraints:
 *   - READ-ONLY: Calculation only (no modification)
 *   - Fixed rules: Fixed metric definitions
 *   - Defensive: Never throws, handles missing data gracefully
 */

import { MarketRegimeSnapshotV1 } from "../snapshot/types";
import {
  EffectWindowSummary,
  WindowLabel,
  EffectStatus,
  EffectCounts,
  EffectRates,
  EffectTopLabels,
} from "./types";

/**
 * Count occurrences of label values
 *
 * @param snapshots - Snapshots to count
 * @param field - Field name
 * @returns Label → count map
 */
function countLabelValues(
  snapshots: MarketRegimeSnapshotV1[],
  field: keyof MarketRegimeSnapshotV1["labels"]
): Map<string, number> {
  const counts = new Map<string, number>();

  for (const snapshot of snapshots) {
    if (!snapshot.labels) {
      continue;
    }

    const label = snapshot.labels[field];
    if (!label || typeof label !== "string") {
      continue;
    }

    counts.set(label, (counts.get(label) || 0) + 1);
  }

  return counts;
}

/**
 * Get top label from counts
 *
 * @param counts - Label → count map
 * @returns Most common label
 */
function getTopLabel(counts: Map<string, number>): string | undefined {
  let topLabel: string | undefined;
  let maxCount = 0;

  for (const [label, count] of counts.entries()) {
    if (count > maxCount) {
      maxCount = count;
      topLabel = label;
    }
  }

  return topLabel;
}

/**
 * Summarize window v1
 *
 * Calculates fixed metrics for one time window.
 *
 * Metrics:
 * - Counts: nSnapshots, nGatePass, nGateBlock, nStop
 * - Rates: passRate, blockRate, stopRate
 * - Tops: topPhase, topTemplate, topBlockReason, topStopCategory
 * - Confusion signals: (optional, from PR166 patterns)
 *
 * @param window - Window label
 * @param snaps - Snapshots in window
 * @returns Window summary
 */
export function summarizeWindowV1(
  window: WindowLabel,
  snaps: MarketRegimeSnapshotV1[]
): EffectWindowSummary {
  const warnings: string[] = [];

  try {
    // 1. Count snapshots
    const nSnapshots = snaps.length;

    if (nSnapshots === 0) {
      warnings.push("WARN_WINDOW_EMPTY");

      return {
        window,
        status: "PARTIAL",
        counts: {
          nSnapshots: 0,
          nGatePass: 0,
          nGateBlock: 0,
          nStop: 0,
        },
        rates: {},
        tops: {},
        confusionSignals: [],
        bottlenecks: [],
        warnings,
      };
    }

    // 2. Count gate PASS/BLOCK
    let nGatePass = 0;
    let nGateBlock = 0;

    for (const snapshot of snaps) {
      if (!snapshot.labels) {
        continue;
      }

      // Check for GATE_PASS
      if (snapshot.labels.gateDecision === "PASS") {
        nGatePass++;
      }

      // Check for GATE_BLOCK
      if (snapshot.labels.gateDecision === "BLOCK") {
        nGateBlock++;
      }
    }

    // 3. Count STOP
    let nStop = 0;

    for (const snapshot of snaps) {
      if (!snapshot.labels) {
        continue;
      }

      // Check for STOP (hardStop or cooldown active)
      if (snapshot.labels.hardStop === "ACTIVE") {
        nStop++;
      }
    }

    // 4. Calculate rates
    const passRate = nSnapshots > 0 ? nGatePass / nSnapshots : undefined;
    const blockRate = nSnapshots > 0 ? nGateBlock / nSnapshots : undefined;
    const stopRate = nSnapshots > 0 ? nStop / nSnapshots : undefined;

    // 5. Get top labels
    const phaseCounts = countLabelValues(snaps, "shockPhase");
    const templateCounts = countLabelValues(snaps, "templateId");
    const blockReasonCounts = countLabelValues(snaps, "blockReason");
    const stopCategoryCounts = new Map<string, number>(); // Not available in current schema

    const tops: EffectTopLabels = {
      topPhase: getTopLabel(phaseCounts),
      topTemplate: getTopLabel(templateCounts),
      topBlockReason: getTopLabel(blockReasonCounts),
      topStopCategory: getTopLabel(stopCategoryCounts),
    };

    // 6. Detect confusion signals (simple heuristics)
    const confusionSignals: string[] = [];

    // High block rate
    if (blockRate !== undefined && blockRate > 0.5) {
      confusionSignals.push("CONFUSION_GATE_BLOCK_DOMINATES");
    }

    // High stop rate
    if (stopRate !== undefined && stopRate > 0.3) {
      confusionSignals.push("CONFUSION_STOP_FREQUENT");
    }

    // 7. Detect bottlenecks (optional)
    const bottlenecks: string[] = [];

    if (tops.topBlockReason?.includes("ORACLE")) {
      bottlenecks.push("BOTTLENECK_ORACLE_DOMINANT");
    }

    if (tops.topBlockReason?.includes("SLIPPAGE")) {
      bottlenecks.push("BOTTLENECK_SLIPPAGE_DOMINANT");
    }

    return {
      window,
      status: "AVAILABLE",
      counts: {
        nSnapshots,
        nGatePass,
        nGateBlock,
        nStop,
      },
      rates: {
        passRate,
        blockRate,
        stopRate,
      },
      tops,
      confusionSignals,
      bottlenecks,
      warnings,
    };
  } catch (error) {
    // Defensive: Return ERROR summary
    warnings.push("WARN_WINDOW_SUMMARIZE_ERROR");

    return {
      window,
      status: "ERROR",
      counts: {
        nSnapshots: 0,
        nGatePass: 0,
        nGateBlock: 0,
        nStop: 0,
      },
      rates: {},
      tops: {},
      confusionSignals: [],
      bottlenecks: [],
      warnings,
    };
  }
}
