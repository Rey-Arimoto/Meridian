/**
 * PR168: v1.4 Policy-First Adoption Loop - Adopter
 *
 * Purpose:
 *   Main adoption engine that decides ADOPT/HOLD/REJECT based on patch plan
 *   and replay compare results.
 *
 * Constitutional Constraints:
 *   - Policy-First: PATCH_NOT_ALLOWED → REJECT
 *   - Defensive: Never throws, always returns result
 *   - Fixed rules: Deterministic decision logic
 */

import { MarketRegimeSnapshotV1 } from "../snapshot/types";
import { analyzeSnapshotsV1, AnalysisResultV1 } from "../analyze";
import { generateProposalsV1 } from "../propose/proposer";
import {
  AdoptResultV1,
  AdoptDecision,
  AdoptPriority,
  AdoptStatus,
  PatchPlan,
  ReplayCompare,
} from "./types";
import { selectTopProposalV1, buildPatchPlanFromSelectedV1 } from "./patcher";
import { simulateReplayCompareV1 } from "./replay";
import { hasNotAllowedOps } from "./rules";

/**
 * Adopt improvement from snapshots
 *
 * Main adoption flow:
 * 1. Analyze snapshots (PR166)
 * 2. Generate proposals (PR167)
 * 3. Select top proposal
 * 4. Build patch plan
 * 5. Simulate replay compare
 * 6. Decide ADOPT/HOLD/REJECT
 *
 * @param snapshots - Snapshots from PR165
 * @param priority - Optional priority filter (P0, P1, or P2)
 * @param tailN - Number of snapshots to use
 * @returns Adopt result
 */
export async function adoptImprovementV1(
  snapshots: MarketRegimeSnapshotV1[],
  priority?: AdoptPriority,
  tailN: number = 200
): Promise<AdoptResultV1> {
  const warnings: string[] = [];

  try {
    // Step 1: Analyze snapshots (PR166)
    const analysis = await analyzeSnapshotsV1(snapshots);

    if (analysis.status === "ERROR") {
      warnings.push("WARN_ANALYSIS_ERROR");
    }

    // Step 2: Generate proposals (PR167)
    const proposeResult = await generateProposalsV1(analysis);

    if (proposeResult.status === "ERROR") {
      warnings.push("WARN_PROPOSE_ERROR");
    }

    if (proposeResult.proposals.length === 0) {
      warnings.push("WARN_NO_PROPOSALS");

      return {
        version: "v1.0",
        status: "PARTIAL",
        decision: "HOLD",
        patchPlan: {
          status: "PARTIAL",
          ops: [],
          warnings: ["NO_PROPOSALS"],
        },
        compare: {
          status: "PARTIAL",
          window: `TAIL_${tailN}`,
          before: [],
          after: [],
          signals: ["COMPARE_UNAVAILABLE"],
          warnings: [],
        },
        reasons: ["NO_PROPOSALS_TO_ADOPT"],
        warnings,
        ts: Date.now(),
      };
    }

    // Step 3: Select top proposal
    const selectedProposal = selectTopProposalV1(
      proposeResult.proposals,
      priority
    );

    if (!selectedProposal) {
      warnings.push("WARN_NO_PROPOSAL_SELECTED");

      return {
        version: "v1.0",
        status: "PARTIAL",
        decision: "HOLD",
        priority,
        patchPlan: {
          status: "PARTIAL",
          ops: [],
          warnings: ["NO_PROPOSAL_SELECTED"],
        },
        compare: {
          status: "PARTIAL",
          window: `TAIL_${tailN}`,
          before: [],
          after: [],
          signals: ["COMPARE_UNAVAILABLE"],
          warnings: [],
        },
        reasons: ["NO_PROPOSAL_FOR_PRIORITY"],
        warnings,
        ts: Date.now(),
      };
    }

    // Step 4: Build patch plan
    const patchPlan = buildPatchPlanFromSelectedV1(selectedProposal, analysis);

    // Step 5: Simulate replay compare
    const compare = await simulateReplayCompareV1(
      snapshots,
      patchPlan,
      tailN
    );

    // Step 6: Decide ADOPT/HOLD/REJECT
    const { decision, reasons } = decideAdoptionV1(
      patchPlan,
      compare,
      selectedProposal.priority as AdoptPriority
    );

    // Merge warnings
    warnings.push(...patchPlan.warnings, ...compare.warnings);

    // Determine overall status
    const status: AdoptStatus =
      warnings.length > 0 ? "PARTIAL" : "COMPLETE";

    return {
      version: "v1.0",
      status,
      decision,
      priority: selectedProposal.priority as AdoptPriority,
      proposalId: selectedProposal.id,
      patchPlan,
      compare,
      reasons,
      warnings,
      ts: Date.now(),
    };
  } catch (error) {
    // Defensive: Return minimal result on error
    warnings.push("WARN_ADOPTER_ERROR");

    return {
      version: "v1.0",
      status: "ERROR",
      decision: "HOLD",
      priority,
      patchPlan: {
        status: "ERROR",
        ops: [],
        warnings: ["ADOPTER_ERROR"],
      },
      compare: {
        status: "ERROR",
        window: `TAIL_${tailN}`,
        before: [],
        after: [],
        signals: ["COMPARE_UNAVAILABLE"],
        warnings: [],
      },
      reasons: ["ADOPTER_ERROR_OCCURRED"],
      warnings,
      ts: Date.now(),
    };
  }
}

/**
 * Decide adoption (ADOPT / HOLD / REJECT)
 *
 * Fixed decision rules:
 * - PATCH_NOT_ALLOWED → REJECT
 * - WORSENED_* signal → HOLD
 * - IMPROVED_* signal (no worsening) → ADOPT
 * - COMPARE_UNAVAILABLE → HOLD
 * - P0 → ADOPT-leaning
 * - P1/P2 → HOLD-leaning
 *
 * @param patchPlan - Patch plan
 * @param compare - Replay compare
 * @param priority - Proposal priority
 * @returns Decision and reasons
 */
export function decideAdoptionV1(
  patchPlan: PatchPlan,
  compare: ReplayCompare,
  priority: AdoptPriority
): { decision: AdoptDecision; reasons: string[] } {
  const reasons: string[] = [];

  // Rule 1: PATCH_NOT_ALLOWED → REJECT
  if (hasNotAllowedOps(patchPlan)) {
    reasons.push("REJECT_PATCH_NOT_ALLOWED");
    reasons.push("WOULD_REDUCE_SAFETY");
    return { decision: "REJECT", reasons };
  }

  // Rule 2: COMPARE_UNAVAILABLE → HOLD
  if (compare.signals.includes("COMPARE_UNAVAILABLE")) {
    reasons.push("HOLD_COMPARE_UNAVAILABLE");
    reasons.push("CANNOT_VERIFY_IMPROVEMENT");
    return { decision: "HOLD", reasons };
  }

  // Rule 3: WORSENED_* signal → HOLD
  const hasWorsened = compare.signals.some((s) => s.startsWith("WORSENED_"));
  if (hasWorsened) {
    reasons.push("HOLD_WORSENED_DETECTED");
    reasons.push("NEEDS_REVIEW_BEFORE_ADOPTION");
    return { decision: "HOLD", reasons };
  }

  // Rule 4: IMPROVED_* signal (no worsening) → ADOPT
  const hasImproved = compare.signals.some((s) => s.startsWith("IMPROVED_"));
  if (hasImproved) {
    reasons.push("ADOPT_IMPROVED_WITHOUT_WORSENING");

    // P0 → stronger ADOPT
    if (priority === "P0") {
      reasons.push("P0_PRIORITY_HIGH_CONFIDENCE");
    }

    return { decision: "ADOPT", reasons };
  }

  // Rule 5: NO_CHANGE → HOLD (P0 → ADOPT, P1/P2 → HOLD)
  if (compare.signals.includes("NO_CHANGE")) {
    if (priority === "P0") {
      reasons.push("ADOPT_P0_NO_WORSENING");
      reasons.push("P0_PRIORITY_ACCEPT_NO_CHANGE");
      return { decision: "ADOPT", reasons };
    } else {
      reasons.push("HOLD_NO_CHANGE_DETECTED");
      reasons.push("P1_P2_REQUIRE_CLEAR_IMPROVEMENT");
      return { decision: "HOLD", reasons };
    }
  }

  // Default: HOLD
  reasons.push("HOLD_DEFAULT");
  reasons.push("UNCLEAR_BENEFIT");
  return { decision: "HOLD", reasons };
}
