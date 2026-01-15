/**
 * PR168: v1.4 Policy-First Adoption Loop - Replay Compare
 *
 * Purpose:
 *   Simulate before/after comparison via snapshot replay.
 *   Virtually apply patch operations without code changes.
 *
 * Constitutional Constraints:
 *   - READ-ONLY: No execution, no code changes (virtual remapping only)
 *   - Defensive: Never throws, always returns result
 *   - Label-only: Normal output uses labels (no numeric counts)
 *   - Fixed rules: Deterministic remapping based on patch ops
 */

import { MarketRegimeSnapshotV1 } from "../snapshot/types";
import { analyzeSnapshotsV1 } from "../analyze/analyzer";
import {
  PatchPlan,
  PatchOp,
  ReplayCompare,
  CompareSignal,
  AdoptStatus,
} from "./types";

/**
 * Simulate replay compare
 *
 * Virtually applies patch operations to snapshots and compares before/after metrics.
 * Does NOT modify code or execute anything - just remaps snapshot labels.
 *
 * @param snapshots - Snapshots to analyze
 * @param patchPlan - Patch plan to apply virtually
 * @param tailN - Number of snapshots to use (for window label)
 * @returns Replay compare result
 */
export async function simulateReplayCompareV1(
  snapshots: MarketRegimeSnapshotV1[],
  patchPlan: PatchPlan,
  tailN: number = 200
): Promise<ReplayCompare> {
  const warnings: string[] = [];

  try {
    // Check if snapshots are available
    if (snapshots.length === 0) {
      warnings.push("WARN_NO_SNAPSHOTS_FOR_REPLAY");

      return {
        status: "PARTIAL",
        window: `TAIL_${tailN}`,
        before: ["NO_SNAPSHOTS"],
        after: ["NO_SNAPSHOTS"],
        signals: ["COMPARE_UNAVAILABLE"],
        warnings,
      };
    }

    // Analyze before (original snapshots)
    const beforeAnalysis = await analyzeSnapshotsV1(snapshots);

    // Apply virtual remapping based on patch ops
    const remappedSnapshots = applyVirtualRemapping(snapshots, patchPlan.ops);

    // Analyze after (remapped snapshots)
    const afterAnalysis = await analyzeSnapshotsV1(remappedSnapshots);

    // Build before summary
    const beforeSummary = buildBeforeSummary(beforeAnalysis);

    // Build after summary
    const afterSummary = buildAfterSummary(afterAnalysis);

    // Detect comparison signals
    const signals = detectCompareSignals(beforeAnalysis, afterAnalysis);

    // Determine status
    const status: AdoptStatus =
      warnings.length > 0 ? "PARTIAL" : "COMPLETE";

    return {
      status,
      window: `TAIL_${tailN}`,
      before: beforeSummary,
      after: afterSummary,
      signals,
      warnings,
    };
  } catch (error) {
    // Defensive: Return minimal result on error
    warnings.push("WARN_REPLAY_ERROR");

    return {
      status: "ERROR",
      window: `TAIL_${tailN}`,
      before: ["ERROR"],
      after: ["ERROR"],
      signals: ["COMPARE_UNAVAILABLE"],
      warnings,
    };
  }
}

/**
 * Apply virtual remapping
 *
 * Remaps snapshot labels based on patch operations without modifying code.
 * This simulates "what would happen if patch was applied".
 *
 * @param snapshots - Original snapshots
 * @param ops - Patch operations
 * @returns Remapped snapshots
 */
function applyVirtualRemapping(
  snapshots: MarketRegimeSnapshotV1[],
  ops: PatchOp[]
): MarketRegimeSnapshotV1[] {
  // Create deep copies to avoid mutation
  const remapped = snapshots.map((s) => JSON.parse(JSON.stringify(s)));

  for (const op of ops) {
    switch (op.kind) {
      case "PATCH_PHASE_POLICY":
        // Remap phase policy stops to WAIT_RESUME (not EXECUTE)
        for (const snap of remapped) {
          if (
            snap.labels.blockReason?.includes("PHASE") &&
            snap.labels.resume === "WAIT"
          ) {
            // Virtual remap: STOP → WAIT_RESUME (keep blocked, but change category)
            snap.labels.resume = "WAIT";
            // Add a marker for analysis
            (snap as any).virtualRemap = "PHASE_POLICY_TO_WAIT";
          }
        }
        break;

      case "PATCH_GATE_ORDER":
        // Remap some BLOCK to SKIP (not EXECUTE)
        for (const snap of remapped) {
          // Only remap minor blocks (drift, delta small)
          if (
            snap.labels.blockReason?.includes("DRIFT") ||
            snap.labels.blockReason?.includes("DELTA")
          ) {
            // Virtual remap: BLOCK → SKIP (in runner logic)
            snap.labels.gateDecision = "SKIP" as any;
            (snap as any).virtualRemap = "BLOCK_TO_SKIP";
          }
        }
        break;

      case "PATCH_ORACLE_FRESHNESS":
        // Remap ORACLE_STALE to WAIT_RESUME (not EXECUTE)
        for (const snap of remapped) {
          if (snap.labels.blockReason?.includes("ORACLE_STALE")) {
            snap.labels.resume = "WAIT";
            (snap as any).virtualRemap = "ORACLE_STALE_TO_WAIT";
          }
        }
        break;

      case "PATCH_SLIPPAGE_RULES":
        // No remapping (just logging)
        break;

      case "PATCH_COOLDOWN_RULES":
        // No remapping (just logging)
        break;

      case "PATCH_DRIFT_RULES":
        // No remapping (just logging)
        break;

      case "PATCH_ROUTER_TIEBREAK":
        // No remapping (just logging)
        break;

      case "PATCH_NOT_ALLOWED":
        // No remapping (rejected patches)
        break;

      default:
        // Unknown patch kind - no remapping
        break;
    }
  }

  return remapped;
}

/**
 * Build before summary
 *
 * @param analysis - Before analysis
 * @returns Before summary (label-only)
 */
function buildBeforeSummary(analysis: any): string[] {
  const summary: string[] = [];

  // Gate decision distribution
  const gatePass =
    analysis.frequency.gateDecisions.find((g: any) => g.label === "PASS")
      ?.count || 0;
  const gateBlock =
    analysis.frequency.gateDecisions.find((g: any) => g.label === "BLOCK")
      ?.count || 0;
  const totalGate = gatePass + gateBlock;

  if (totalGate > 0) {
    const blockRatio = gateBlock / totalGate;
    if (blockRatio > 0.5) {
      summary.push("GATE_BLOCK_DOMINATES");
    } else if (blockRatio > 0.3) {
      summary.push("GATE_BLOCK_FREQUENT");
    } else {
      summary.push("GATE_PASS_MAJORITY");
    }
  }

  // Top block reasons
  if (analysis.frequency.blockReasons.length > 0) {
    const topReason = analysis.frequency.blockReasons[0].label;
    summary.push(`TOP_BLOCK_${topReason}`);
  }

  // Stop reasons
  const phaseStops = analysis.timing.stopReasons.find(
    (s: any) => s.category === "STOP_BY_PHASE_POLICY"
  );
  if (phaseStops) {
    summary.push("PHASE_POLICY_STOPS_PRESENT");
  }

  const unknownStops = analysis.timing.stopReasons.find(
    (s: any) => s.category === "STOP_UNKNOWN"
  );
  if (unknownStops) {
    summary.push("STOP_UNKNOWN_PRESENT");
  }

  return summary.length > 0 ? summary : ["NO_PATTERNS"];
}

/**
 * Build after summary
 *
 * @param analysis - After analysis
 * @returns After summary (label-only)
 */
function buildAfterSummary(analysis: any): string[] {
  const summary: string[] = [];

  // Gate decision distribution
  const gatePass =
    analysis.frequency.gateDecisions.find((g: any) => g.label === "PASS")
      ?.count || 0;
  const gateBlock =
    analysis.frequency.gateDecisions.find((g: any) => g.label === "BLOCK")
      ?.count || 0;
  const gateSkip =
    analysis.frequency.gateDecisions.find((g: any) => g.label === "SKIP")
      ?.count || 0;
  const totalGate = gatePass + gateBlock + gateSkip;

  if (totalGate > 0) {
    const blockRatio = gateBlock / totalGate;
    if (blockRatio > 0.5) {
      summary.push("GATE_BLOCK_STILL_DOMINATES");
    } else if (blockRatio > 0.3) {
      summary.push("GATE_BLOCK_REDUCED");
    } else {
      summary.push("GATE_PASS_INCREASED");
    }
  }

  // Top block reasons
  if (analysis.frequency.blockReasons.length > 0) {
    const topReason = analysis.frequency.blockReasons[0].label;
    summary.push(`TOP_BLOCK_${topReason}`);
  }

  // Stop reasons
  const phaseStops = analysis.timing.stopReasons.find(
    (s: any) => s.category === "STOP_BY_PHASE_POLICY"
  );
  if (phaseStops) {
    summary.push("PHASE_POLICY_STOPS_PRESENT");
  } else {
    summary.push("PHASE_POLICY_STOPS_REDUCED");
  }

  const unknownStops = analysis.timing.stopReasons.find(
    (s: any) => s.category === "STOP_UNKNOWN"
  );
  if (unknownStops) {
    summary.push("STOP_UNKNOWN_STILL_PRESENT");
  } else {
    summary.push("STOP_UNKNOWN_ELIMINATED");
  }

  return summary.length > 0 ? summary : ["NO_PATTERNS"];
}

/**
 * Detect compare signals
 *
 * Detects improvement or worsening signals by comparing before/after analyses.
 *
 * @param beforeAnalysis - Before analysis
 * @param afterAnalysis - After analysis
 * @returns Comparison signals
 */
function detectCompareSignals(
  beforeAnalysis: any,
  afterAnalysis: any
): CompareSignal[] {
  const signals: CompareSignal[] = [];

  // Gate BLOCK dominance
  const beforeGatePass =
    beforeAnalysis.frequency.gateDecisions.find((g: any) => g.label === "PASS")
      ?.count || 0;
  const beforeGateBlock =
    beforeAnalysis.frequency.gateDecisions.find(
      (g: any) => g.label === "BLOCK"
    )?.count || 0;
  const beforeTotalGate = beforeGatePass + beforeGateBlock;

  const afterGatePass =
    afterAnalysis.frequency.gateDecisions.find((g: any) => g.label === "PASS")
      ?.count || 0;
  const afterGateBlock =
    afterAnalysis.frequency.gateDecisions.find((g: any) => g.label === "BLOCK")
      ?.count || 0;
  const afterGateSkip =
    afterAnalysis.frequency.gateDecisions.find((g: any) => g.label === "SKIP")
      ?.count || 0;
  const afterTotalGate = afterGatePass + afterGateBlock + afterGateSkip;

  if (beforeTotalGate > 0 && afterTotalGate > 0) {
    const beforeBlockRatio = beforeGateBlock / beforeTotalGate;
    const afterBlockRatio = afterGateBlock / afterTotalGate;

    if (afterBlockRatio < beforeBlockRatio - 0.05) {
      // Improved: block ratio decreased by >5%
      signals.push("IMPROVED_BLOCK_DOMINANCE");
    } else if (afterBlockRatio > beforeBlockRatio + 0.05) {
      // Worsened: block ratio increased by >5%
      signals.push("WORSENED_BLOCK_DOMINANCE");
    }
  }

  // Phase policy stops
  const beforePhaseStops = beforeAnalysis.timing.stopReasons.find(
    (s: any) => s.category === "STOP_BY_PHASE_POLICY"
  );
  const afterPhaseStops = afterAnalysis.timing.stopReasons.find(
    (s: any) => s.category === "STOP_BY_PHASE_POLICY"
  );

  const beforePhaseCount = beforePhaseStops?.count || 0;
  const afterPhaseCount = afterPhaseStops?.count || 0;

  if (beforePhaseCount > 0 && afterPhaseCount < beforePhaseCount) {
    signals.push("IMPROVED_STOP_BY_PHASE_POLICY");
  }

  // Stop unknown
  const beforeUnknownStops = beforeAnalysis.timing.stopReasons.find(
    (s: any) => s.category === "STOP_UNKNOWN"
  );
  const afterUnknownStops = afterAnalysis.timing.stopReasons.find(
    (s: any) => s.category === "STOP_UNKNOWN"
  );

  const beforeUnknownCount = beforeUnknownStops?.count || 0;
  const afterUnknownCount = afterUnknownStops?.count || 0;

  if (afterUnknownCount > beforeUnknownCount) {
    signals.push("WORSENED_STOP_UNKNOWN");
  }

  // Oracle stale rate
  const beforeOracleStale = beforeAnalysis.frequency.blockReasons.find(
    (b: any) => b.label?.includes("ORACLE_STALE")
  );
  const afterOracleStale = afterAnalysis.frequency.blockReasons.find(
    (b: any) => b.label?.includes("ORACLE_STALE")
  );

  if (beforeOracleStale && afterOracleStale) {
    if (afterOracleStale.count < beforeOracleStale.count) {
      signals.push("IMPROVED_ORACLE_STALE_RATE");
    }
  }

  // If no signals detected
  if (signals.length === 0) {
    signals.push("NO_CHANGE");
  }

  return signals;
}
