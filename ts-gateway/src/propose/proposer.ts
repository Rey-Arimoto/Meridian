/**
 * PR167: v1.4 Improvement Proposal Generator v1 - Proposer Engine
 *
 * Purpose:
 *   Generate fixed-rule improvement proposals from analysis results.
 *   Core engine that evaluates triggers and activates proposals.
 *
 * Constitutional Constraints:
 *   - READ-ONLY: Proposals are suggestions, not actions
 *   - Fixed rules: All triggers and proposals are predetermined
 *   - Defensive: Never throws, always returns result
 *   - Deterministic: Same analysis → same proposals
 */

import { AnalysisResultV1 } from "../analyze/types";
import { ProposeResultV1, TriggerId } from "./types";
import { TRIGGER_RULES, getProposalsForTriggers } from "./rules";
import { getPriorityOrder } from "./guards";

/**
 * Generate improvement proposals from analysis results
 *
 * Purpose:
 *   Evaluate all fixed trigger rules and generate matching proposals.
 *
 * @param analysis - Analysis result from PR166
 * @returns Propose result (never throws)
 */
export async function generateProposalsV1(
  analysis: AnalysisResultV1
): Promise<ProposeResultV1> {
  const warnings: string[] = [];

  try {
    // Check if analysis is valid
    if (!analysis || analysis.status === "ERROR") {
      warnings.push("WARN_ANALYSIS_ERROR");

      return {
        version: "v1.0",
        status: "ERROR",
        warnings,
        proposals: [],
        ts: Date.now(),
        snapshotCountLabel: "UNKNOWN",
      };
    }

    // Check if analysis has snapshots
    if (analysis.snapshotCount === 0) {
      warnings.push("WARN_NO_SNAPSHOTS_IN_ANALYSIS");

      return {
        version: "v1.0",
        status: "NO_PROPOSALS",
        warnings,
        proposals: [],
        ts: Date.now(),
        snapshotCountLabel: "NO_SNAPSHOTS",
      };
    }

    // Evaluate all trigger rules
    const activeTriggers: TriggerId[] = [];

    for (const rule of TRIGGER_RULES) {
      try {
        if (rule.evaluate(analysis)) {
          activeTriggers.push(rule.id);
        }
      } catch (error) {
        // Defensive: Skip failed trigger evaluation
        warnings.push(`WARN_TRIGGER_EVAL_FAILED_${rule.id}`);
      }
    }

    // Check if any triggers are active
    if (activeTriggers.length === 0) {
      return {
        version: "v1.0",
        status: "NO_PROPOSALS",
        warnings,
        proposals: [],
        ts: Date.now(),
        snapshotCountLabel: "HAS_SNAPSHOTS",
      };
    }

    // Get proposals for active triggers
    const proposals = getProposalsForTriggers(activeTriggers);

    // Sort by priority (P0 > P1 > P2)
    proposals.sort((a, b) => {
      const priorityOrder = getPriorityOrder(a.priority) - getPriorityOrder(b.priority);
      if (priorityOrder !== 0) {
        return priorityOrder;
      }

      // Secondary sort: by ID (deterministic)
      return a.id.localeCompare(b.id);
    });

    // Determine status
    const status = warnings.length > 0 ? "PARTIAL" : "AVAILABLE";

    return {
      version: "v1.0",
      status,
      warnings,
      proposals,
      ts: Date.now(),
      snapshotCountLabel: "HAS_SNAPSHOTS",
    };
  } catch (error) {
    // Defensive: Even on fatal error, return minimal result
    warnings.push("WARN_PROPOSER_ERROR");

    return {
      version: "v1.0",
      status: "ERROR",
      warnings,
      proposals: [],
      ts: Date.now(),
      snapshotCountLabel: "UNKNOWN",
    };
  }
}

/**
 * Get active triggers from analysis
 *
 * Helper function to get all active triggers without generating proposals.
 * Useful for debugging and testing.
 *
 * @param analysis - Analysis result
 * @returns Active trigger IDs
 */
export function getActiveTriggersV1(analysis: AnalysisResultV1): TriggerId[] {
  const activeTriggers: TriggerId[] = [];

  for (const rule of TRIGGER_RULES) {
    try {
      if (rule.evaluate(analysis)) {
        activeTriggers.push(rule.id);
      }
    } catch (error) {
      // Defensive: Skip failed trigger evaluation
    }
  }

  return activeTriggers;
}
