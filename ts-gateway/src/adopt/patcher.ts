/**
 * PR168: v1.4 Policy-First Adoption Loop - Patcher
 *
 * Purpose:
 *   Select proposals and build patch plans.
 *   Handles proposal selection by priority and defensive error handling.
 *
 * Constitutional Constraints:
 *   - Defensive: Never throws, always returns result
 *   - Priority-based: P0 > P1 > P2
 *   - Small patches: 1-3 ops per plan
 */

import { AnalysisResultV1 } from "../analyze/types";
import { ImprovementProposalV1 } from "../propose/types";
import { PatchPlan, AdoptPriority, AdoptStatus } from "./types";
import { buildPatchPlanFromProposalV1 } from "./rules";

/**
 * Select top proposal by priority
 *
 * Selects the highest priority proposal from the list.
 * Priority order: P0 > P1 > P2
 *
 * @param proposals - List of proposals
 * @param priority - Optional priority filter (P0, P1, or P2)
 * @returns Top proposal or undefined
 */
export function selectTopProposalV1(
  proposals: ImprovementProposalV1[],
  priority?: AdoptPriority
): ImprovementProposalV1 | undefined {
  if (proposals.length === 0) {
    return undefined;
  }

  // Filter by priority if specified
  let filtered = proposals;
  if (priority) {
    filtered = proposals.filter((p) => p.priority === priority);
  }

  if (filtered.length === 0) {
    return undefined;
  }

  // Sort by priority (P0 > P1 > P2)
  const sorted = filtered.sort((a, b) => {
    const priorityOrder: Record<string, number> = {
      P0: 0,
      P1: 1,
      P2: 2,
      UNKNOWN: 99,
    };

    const orderA = priorityOrder[a.priority] ?? 99;
    const orderB = priorityOrder[b.priority] ?? 99;

    if (orderA !== orderB) {
      return orderA - orderB;
    }

    // Secondary sort: by ID (deterministic)
    return a.id.localeCompare(b.id);
  });

  return sorted[0];
}

/**
 * Build patch plan from selected proposal
 *
 * Builds a patch plan from the selected proposal and analysis.
 * Defensive: handles errors gracefully.
 *
 * @param proposal - Selected proposal
 * @param analysis - Analysis result
 * @returns Patch plan
 */
export function buildPatchPlanFromSelectedV1(
  proposal: ImprovementProposalV1 | undefined,
  analysis: AnalysisResultV1
): PatchPlan {
  const warnings: string[] = [];

  try {
    // Check if proposal is available
    if (!proposal) {
      warnings.push("WARN_NO_PROPOSAL_SELECTED");

      return {
        status: "PARTIAL",
        ops: [],
        warnings,
      };
    }

    // Check if analysis is valid
    if (!analysis || analysis.status === "ERROR") {
      warnings.push("WARN_ANALYSIS_ERROR");

      return {
        status: "ERROR",
        proposalId: proposal.id,
        priority: proposal.priority as AdoptPriority,
        ops: [],
        warnings,
      };
    }

    // Build patch plan
    const patchPlan = buildPatchPlanFromProposalV1(proposal, analysis);

    // Merge warnings
    patchPlan.warnings = [...warnings, ...patchPlan.warnings];

    return patchPlan;
  } catch (error) {
    // Defensive: Return minimal plan on error
    warnings.push("WARN_PATCHER_ERROR");

    return {
      status: "ERROR",
      proposalId: proposal?.id,
      priority: proposal?.priority as AdoptPriority,
      ops: [],
      warnings,
    };
  }
}
