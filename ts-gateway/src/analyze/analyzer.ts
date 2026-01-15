/**
 * PR166: v1.4 Snapshot Analysis Helper v1 - Analyzer
 *
 * Purpose:
 *   Deterministic analysis of snapshot logs for strategy improvement.
 *   Provides frequency, confusion signals, and timing analysis.
 *
 * Constitutional Constraints:
 *   - READ-ONLY: Analysis reads snapshot logs only
 *   - Defensive: Never throws, always returns result
 *   - Fixed rules: No prediction, no optimization, no recommendations
 *   - Deterministic: Same input → same output (no randomness)
 */

import { MarketRegimeSnapshotV1 } from "../snapshot/types";
import {
  AnalysisResultV1,
  AnalysisStatus,
  FrequencyAnalysis,
  FrequencyItem,
  ConfusionSignal,
  ConfusionSignalType,
  TimingAnalysis,
  PhaseTransition,
  StopReasonBreakdown,
  StopReasonCategory,
  LagLabel,
} from "./types";

/**
 * Analyze snapshots v1
 *
 * Purpose:
 *   Perform deterministic analysis on snapshot logs.
 *
 * @param snapshots - Snapshots to analyze
 * @returns Analysis result (never throws)
 */
export async function analyzeSnapshotsV1(
  snapshots: MarketRegimeSnapshotV1[]
): Promise<AnalysisResultV1> {
  const warnings: string[] = [];

  try {
    // Check if empty
    if (snapshots.length === 0) {
      warnings.push("WARN_NO_SNAPSHOTS_TO_ANALYZE");

      return {
        version: "v1.0",
        status: "PARTIAL",
        warnings,
        snapshotCount: 0,
        frequency: {
          phaseLabels: [],
          stressLabels: [],
          templateIds: [],
          gateDecisions: [],
          blockReasons: [],
        },
        confusionSignals: [],
        timing: {
          transitions: [],
          stopReasons: [],
        },
      };
    }

    // Build frequency analysis
    const frequency = buildFrequencyAnalysis(snapshots);

    // Detect confusion signals
    const confusionSignals = detectConfusionSignals(snapshots, frequency);

    // Analyze timing patterns
    const timing = analyzeTimingPatterns(snapshots);

    // Determine overall status
    const status: AnalysisStatus =
      warnings.length > 0 ? "PARTIAL" : "COMPLETE";

    return {
      version: "v1.0",
      status,
      warnings,
      snapshotCount: snapshots.length,
      frequency,
      confusionSignals,
      timing,
    };
  } catch (error) {
    // Defensive: Even on error, return minimal result
    warnings.push("WARN_ANALYSIS_ERROR");

    return {
      version: "v1.0",
      status: "ERROR",
      warnings,
      snapshotCount: snapshots.length,
      frequency: {
        phaseLabels: [],
        stressLabels: [],
        templateIds: [],
        gateDecisions: [],
        blockReasons: [],
      },
      confusionSignals: [],
      timing: {
        transitions: [],
        stopReasons: [],
      },
    };
  }
}

/**
 * Build frequency analysis
 *
 * @param snapshots - Snapshots to analyze
 * @returns Frequency analysis
 */
function buildFrequencyAnalysis(
  snapshots: MarketRegimeSnapshotV1[]
): FrequencyAnalysis {
  // Phase labels
  const phaseCounts = new Map<string, number>();
  for (const snap of snapshots) {
    const phase = snap.labels.shockPhase || "UNKNOWN";
    phaseCounts.set(phase, (phaseCounts.get(phase) || 0) + 1);
  }

  const phaseLabels: FrequencyItem[] = Array.from(phaseCounts.entries())
    .map(([label, count]) => ({ label, count }))
    .sort((a, b) => b.count - a.count);

  // Stress labels
  const stressCounts = new Map<string, number>();
  for (const snap of snapshots) {
    const stress = snap.labels.stress || "UNKNOWN";
    stressCounts.set(stress, (stressCounts.get(stress) || 0) + 1);
  }

  const stressLabels: FrequencyItem[] = Array.from(stressCounts.entries())
    .map(([label, count]) => ({ label, count }))
    .sort((a, b) => b.count - a.count);

  // Template IDs
  const templateCounts = new Map<string, number>();
  for (const snap of snapshots) {
    const template = snap.labels.templateId || "UNKNOWN";
    templateCounts.set(template, (templateCounts.get(template) || 0) + 1);
  }

  const templateIds: FrequencyItem[] = Array.from(templateCounts.entries())
    .map(([label, count]) => ({ label, count }))
    .sort((a, b) => b.count - a.count);

  // Gate decisions
  const gateCounts = new Map<string, number>();
  for (const snap of snapshots) {
    const gate = snap.labels.gateDecision || "UNKNOWN";
    gateCounts.set(gate, (gateCounts.get(gate) || 0) + 1);
  }

  const gateDecisions: FrequencyItem[] = Array.from(gateCounts.entries())
    .map(([label, count]) => ({ label, count }))
    .sort((a, b) => b.count - a.count);

  // Block reasons (top N)
  const blockCounts = new Map<string, number>();
  for (const snap of snapshots) {
    const blockReason = snap.labels.blockReason;
    if (blockReason) {
      blockCounts.set(blockReason, (blockCounts.get(blockReason) || 0) + 1);
    }
  }

  const blockReasons: FrequencyItem[] = Array.from(blockCounts.entries())
    .map(([label, count], index) => ({ label, count, rank: index + 1 }))
    .sort((a, b) => b.count - a.count)
    .slice(0, 10); // Top 10

  return {
    phaseLabels,
    stressLabels,
    templateIds,
    gateDecisions,
    blockReasons,
  };
}

/**
 * Detect confusion signals
 *
 * @param snapshots - Snapshots to analyze
 * @param frequency - Frequency analysis
 * @returns Confusion signals
 */
function detectConfusionSignals(
  snapshots: MarketRegimeSnapshotV1[],
  frequency: FrequencyAnalysis
): ConfusionSignal[] {
  const signals: ConfusionSignal[] = [];

  // Signal 1: CONFUSION_SHOCK_BUT_RISK_HIGH_FREQUENT
  // UP_REVERSAL/DOWN_SHOCK with TPL_RISK_90 frequent
  const shockPhases = ["PHASE_UP_REVERSAL", "PHASE_DOWN_REVERSAL", "PHASE_UP_SHOCK", "PHASE_DOWN_SHOCK"];
  const shockSnapshots = snapshots.filter((s) =>
    shockPhases.includes(s.labels.shockPhase || "")
  );

  if (shockSnapshots.length > 0) {
    const riskHighCount = shockSnapshots.filter(
      (s) => s.labels.templateId === "TPL_RISK_90"
    ).length;

    const riskHighRatio = riskHighCount / shockSnapshots.length;

    if (riskHighRatio > 0.3) {
      // 30% threshold (deterministic)
      signals.push({
        type: "CONFUSION_SHOCK_BUT_RISK_HIGH_FREQUENT",
        active: true,
        reasons: [
          `REASON_SHOCK_PHASE_WITH_HIGH_RISK_TEMPLATE`,
          `RATIO_ABOVE_THRESHOLD`,
        ],
        details: {
          dominantLabel: "TPL_RISK_90",
        },
      });
    } else {
      signals.push({
        type: "CONFUSION_SHOCK_BUT_RISK_HIGH_FREQUENT",
        active: false,
        reasons: [],
      });
    }
  } else {
    signals.push({
      type: "CONFUSION_SHOCK_BUT_RISK_HIGH_FREQUENT",
      active: false,
      reasons: ["NO_SHOCK_PHASES"],
    });
  }

  // Signal 2: CONFUSION_PRE_SHOCK_NO_TEMPLATE_SHIFT
  // PRE_SHOCK but no template change
  const preShockSnapshots = snapshots.filter(
    (s) => s.labels.shockPhase === "PHASE_PRE_SHOCK"
  );

  if (preShockSnapshots.length > 0) {
    const templateIds = new Set(
      preShockSnapshots.map((s) => s.labels.templateId || "UNKNOWN")
    );

    // If PRE_SHOCK exists but only 1 template ID (no shift)
    if (templateIds.size === 1 && preShockSnapshots.length > 3) {
      signals.push({
        type: "CONFUSION_PRE_SHOCK_NO_TEMPLATE_SHIFT",
        active: true,
        reasons: [
          "REASON_PRE_SHOCK_WITHOUT_TEMPLATE_CHANGE",
          "SINGLE_TEMPLATE_DOMINANT",
        ],
        details: {
          dominantLabel: Array.from(templateIds)[0],
        },
      });
    } else {
      signals.push({
        type: "CONFUSION_PRE_SHOCK_NO_TEMPLATE_SHIFT",
        active: false,
        reasons: [],
      });
    }
  } else {
    signals.push({
      type: "CONFUSION_PRE_SHOCK_NO_TEMPLATE_SHIFT",
      active: false,
      reasons: ["NO_PRE_SHOCK_PHASES"],
    });
  }

  // Signal 3: CONFUSION_GATE_BLOCK_DOMINATES
  // BLOCK dominates PASS
  const gatePassCount =
    frequency.gateDecisions.find((g) => g.label === "PASS")?.count || 0;
  const gateBlockCount =
    frequency.gateDecisions.find((g) => g.label === "BLOCK")?.count || 0;

  const totalGate = gatePassCount + gateBlockCount;

  if (totalGate > 0) {
    const blockRatio = gateBlockCount / totalGate;

    if (blockRatio > 0.5) {
      // 50% threshold (deterministic)
      // Categorize block reasons
      const blockCategories = categorizeBlockReasons(frequency.blockReasons);

      signals.push({
        type: "CONFUSION_GATE_BLOCK_DOMINATES",
        active: true,
        reasons: ["REASON_GATE_BLOCK_MAJORITY", "RATIO_ABOVE_THRESHOLD"],
        details: {
          category: blockCategories[0] || "UNKNOWN",
        },
      });
    } else {
      signals.push({
        type: "CONFUSION_GATE_BLOCK_DOMINATES",
        active: false,
        reasons: [],
      });
    }
  } else {
    signals.push({
      type: "CONFUSION_GATE_BLOCK_DOMINATES",
      active: false,
      reasons: ["NO_GATE_DECISIONS"],
    });
  }

  return signals;
}

/**
 * Categorize block reasons
 *
 * @param blockReasons - Block reason frequency items
 * @returns Category labels (sorted by frequency)
 */
function categorizeBlockReasons(blockReasons: FrequencyItem[]): string[] {
  const categories = new Map<string, number>();

  for (const item of blockReasons) {
    let category = "UNKNOWN";

    if (item.label.includes("ORACLE")) {
      category = "ORACLE";
    } else if (item.label.includes("IMPACT")) {
      category = "IMPACT";
    } else if (item.label.includes("SLIPPAGE")) {
      category = "SLIPPAGE";
    } else if (item.label.includes("COOLDOWN")) {
      category = "COOLDOWN";
    } else if (item.label.includes("DRIFT")) {
      category = "DRIFT";
    } else if (item.label.includes("PHASE")) {
      category = "PHASE_POLICY";
    } else if (item.label.includes("POLICY")) {
      category = "POLICY";
    }

    categories.set(category, (categories.get(category) || 0) + item.count);
  }

  return Array.from(categories.entries())
    .sort((a, b) => b[1] - a[1])
    .map(([cat]) => cat);
}

/**
 * Analyze timing patterns
 *
 * @param snapshots - Snapshots to analyze (assumed to be in time order)
 * @returns Timing analysis
 */
function analyzeTimingPatterns(
  snapshots: MarketRegimeSnapshotV1[]
): TimingAnalysis {
  const transitions: PhaseTransition[] = [];
  const stopReasonCounts = new Map<StopReasonCategory, number>();

  // Track phase transitions
  let prevPhase: string | undefined = undefined;
  let prevPhaseIndex = 0;

  for (let i = 0; i < snapshots.length; i++) {
    const snap = snapshots[i];
    const currentPhase = snap.labels.shockPhase;

    if (currentPhase && prevPhase && currentPhase !== prevPhase) {
      // Transition detected
      const tickCount = i - prevPhaseIndex;
      const lag = determineLag(tickCount);

      transitions.push({
        from: prevPhase,
        to: currentPhase,
        lag,
        tickCount,
      });
    }

    if (currentPhase) {
      if (currentPhase !== prevPhase) {
        prevPhase = currentPhase;
        prevPhaseIndex = i;
      }
    }

    // Categorize stop reasons (if resume state exists)
    if (snap.labels.resume && snap.labels.resume !== "NONE") {
      const category = categorizeStopReason(snap);
      stopReasonCounts.set(category, (stopReasonCounts.get(category) || 0) + 1);
    }
  }

  // Build stop reason breakdown
  const stopReasons: StopReasonBreakdown[] = Array.from(
    stopReasonCounts.entries()
  ).map(([category, count]) => ({
    category,
    count,
  }));

  return {
    transitions,
    stopReasons,
  };
}

/**
 * Determine lag label from tick count
 *
 * @param tickCount - Number of ticks
 * @returns Lag label
 */
function determineLag(tickCount: number): LagLabel {
  if (tickCount <= 0) {
    return "LAG_NONE";
  } else if (tickCount <= 3) {
    return "LAG_SHORT";
  } else if (tickCount <= 10) {
    return "LAG_MEDIUM";
  } else {
    return "LAG_LONG";
  }
}

/**
 * Categorize stop reason from snapshot
 *
 * @param snapshot - Snapshot with resume state
 * @returns Stop reason category
 */
function categorizeStopReason(
  snapshot: MarketRegimeSnapshotV1
): StopReasonCategory {
  const blockReason = snapshot.labels.blockReason || "";
  const policyReason = snapshot.labels.policyReason || "";
  const hardStop = snapshot.labels.hardStop;

  // Phase policy
  if (
    blockReason.includes("PHASE") ||
    policyReason.includes("PHASE") ||
    snapshot.labels.shockPhase?.includes("ESCALAT")
  ) {
    return "STOP_BY_PHASE_POLICY";
  }

  // Gate block
  if (
    blockReason.includes("ORACLE") ||
    blockReason.includes("IMPACT") ||
    blockReason.includes("SLIPPAGE") ||
    blockReason.includes("QUOTE") ||
    blockReason.includes("DRIFT") ||
    blockReason.includes("COOLDOWN")
  ) {
    return "STOP_BY_GATE";
  }

  // HardStop
  if (hardStop === "ACTIVE" || policyReason.includes("HARDSTOP")) {
    return "STOP_BY_POLICY_HARDSTOP";
  }

  // Duration
  if (blockReason.includes("DURATION") || policyReason.includes("DURATION")) {
    return "STOP_BY_DURATION";
  }

  // Block streak
  if (blockReason.includes("STREAK") || blockReason.includes("CONSECUTIVE")) {
    return "STOP_BY_BLOCK_STREAK";
  }

  return "STOP_UNKNOWN";
}
