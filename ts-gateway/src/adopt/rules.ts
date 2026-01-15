/**
 * PR168: v1.4 Policy-First Adoption Loop - Fixed Rules
 *
 * Purpose:
 *   Fixed rules to convert improvement proposals into patch plans.
 *   All mappings are predetermined (no learning, no optimization).
 *
 * Constitutional Constraints:
 *   - Policy-First: Changes that reduce safety are PATCH_NOT_ALLOWED
 *   - Fixed rules: All mappings are predetermined
 *   - Deterministic: Same proposal → same patch plan
 *   - Small patches: 1-3 ops per plan (keep it simple)
 */

import { AnalysisResultV1 } from "../analyze/types";
import { ImprovementProposalV1 } from "../propose/types";
import {
  PatchPlan,
  PatchOp,
  PatchKind,
  PatchTarget,
  AdoptStatus,
  AdoptPriority,
} from "./types";

/**
 * Build patch plan from proposal
 *
 * Maps a proposal to a concrete patch plan with operations.
 * Enforces Policy-First: changes that reduce safety are NOT_ALLOWED.
 *
 * @param proposal - Improvement proposal from PR167
 * @param analysis - Analysis result from PR166
 * @returns Patch plan
 */
export function buildPatchPlanFromProposalV1(
  proposal: ImprovementProposalV1,
  analysis: AnalysisResultV1
): PatchPlan {
  const warnings: string[] = [];

  try {
    // Map proposal ID to patch operations
    const ops = mapProposalToPatchOps(proposal, analysis, warnings);

    // Limit to 1-3 ops (keep patches small)
    const limitedOps = ops.slice(0, 3);
    if (ops.length > 3) {
      warnings.push("WARN_OPS_TRUNCATED_TO_3");
    }

    // Determine status
    const status: AdoptStatus =
      warnings.length > 0 ? "PARTIAL" : "COMPLETE";

    return {
      status,
      proposalId: proposal.id,
      priority: proposal.priority as AdoptPriority,
      ops: limitedOps,
      warnings,
    };
  } catch (error) {
    // Defensive: Return minimal plan on error
    warnings.push("WARN_PATCH_PLAN_ERROR");

    return {
      status: "ERROR",
      proposalId: proposal.id,
      priority: proposal.priority as AdoptPriority,
      ops: [],
      warnings,
    };
  }
}

/**
 * Map proposal to patch operations
 *
 * Fixed mapping from proposal IDs to patch ops.
 *
 * @param proposal - Proposal
 * @param analysis - Analysis result
 * @param warnings - Warnings array (mutated)
 * @returns Patch operations
 */
function mapProposalToPatchOps(
  proposal: ImprovementProposalV1,
  analysis: AnalysisResultV1,
  warnings: string[]
): PatchOp[] {
  const ops: PatchOp[] = [];

  switch (proposal.id) {
    // P0: Gate degradation proposals (NOT_ALLOWED - reduce safety)
    case "P0_REDUCE_ORACLE_STALE_BLOCKS_DEGRADE":
      ops.push({
        kind: "PATCH_NOT_ALLOWED",
        target: "ORACLE",
        opId: "OP_ORACLE_STALE_DEGRADE_NOT_ALLOWED_V1",
        change: "DEGRADE_ORACLE_STALE_THRESHOLD",
        safety: [],
        notAllowedReason:
          "WOULD_ALLOW_STALE_ORACLE_EXECUTION_REDUCES_SAFETY",
      });
      break;

    case "P0_REDUCE_IMPACT_BLOCKS_DEGRADE":
      ops.push({
        kind: "PATCH_NOT_ALLOWED",
        target: "GATE",
        opId: "OP_IMPACT_HIGH_DEGRADE_NOT_ALLOWED_V1",
        change: "DEGRADE_IMPACT_HIGH_THRESHOLD",
        safety: [],
        notAllowedReason: "WOULD_ALLOW_HIGH_IMPACT_EXECUTION_REDUCES_SAFETY",
      });
      break;

    case "P0_REDUCE_SLIPPAGE_BLOCKS_DEGRADE":
      ops.push({
        kind: "PATCH_NOT_ALLOWED",
        target: "SLIPPAGE",
        opId: "OP_SLIPPAGE_HIGH_DEGRADE_NOT_ALLOWED_V1",
        change: "DEGRADE_SLIPPAGE_HIGH_THRESHOLD",
        safety: [],
        notAllowedReason:
          "WOULD_ALLOW_HIGH_SLIPPAGE_EXECUTION_REDUCES_SAFETY",
      });
      break;

    case "P0_REDUCE_DRIFT_BLOCKS_DEGRADE":
      ops.push({
        kind: "PATCH_NOT_ALLOWED",
        target: "DRIFT",
        opId: "OP_DRIFT_HIGH_DEGRADE_NOT_ALLOWED_V1",
        change: "DEGRADE_DRIFT_HIGH_THRESHOLD",
        safety: [],
        notAllowedReason: "WOULD_ALLOW_HIGH_DRIFT_EXECUTION_REDUCES_SAFETY",
      });
      break;

    case "P0_REDUCE_COOLDOWN_BLOCKS_DEGRADE":
      ops.push({
        kind: "PATCH_NOT_ALLOWED",
        target: "COOLDOWN",
        opId: "OP_COOLDOWN_REDUCE_NOT_ALLOWED_V1",
        change: "REDUCE_COOLDOWN_DURATION",
        safety: [],
        notAllowedReason:
          "WOULD_REDUCE_OBSERVATION_TIME_REDUCES_SAFETY",
      });
      break;

    // P1: Template policy proposals (allowed with safety)
    case "P1_SHOCK_RISK90_OVERUSE_TEMPLATE_POLICY_RESTRICT":
      ops.push({
        kind: "PATCH_PHASE_POLICY",
        target: "PHASE_POLICY",
        opId: "OP_SHOCK_RISK90_RESTRICT_V1",
        change: "RESTRICT_TPL_RISK_90_IN_SHOCK_REVERSAL",
        safety: [
          "KEEP_DOUBLE_KEY",
          "KEEP_LABEL_ONLY",
          "KEEP_BLOCK_ON_UNCERTAIN",
        ],
      });
      break;

    case "P1_PRE_SHOCK_NO_SHIFT_TEMPLATE_POLICY_TRIGGER":
      ops.push({
        kind: "PATCH_PHASE_POLICY",
        target: "PHASE_POLICY",
        opId: "OP_PRE_SHOCK_TEMPLATE_SHIFT_V1",
        change: "TRIGGER_TEMPLATE_SHIFT_IN_PRE_SHOCK",
        safety: [
          "KEEP_DOUBLE_KEY",
          "KEEP_LABEL_ONLY",
          "KEEP_DETERMINISTIC_SHIFT",
        ],
      });
      break;

    case "P1_PHASE_ESCALATION_DOMINATES_PHASE_POLICY_REVIEW":
      ops.push({
        kind: "PATCH_PHASE_POLICY",
        target: "PHASE_POLICY",
        opId: "OP_PHASE_ESCALATION_REVIEW_V1",
        change: "REMAP_PHASE_ESCALATION_TO_WAIT",
        safety: [
          "KEEP_DOUBLE_KEY",
          "KEEP_HARDSTOP_ACTIVE",
          "NO_AUTOMATIC_EXECUTION",
        ],
      });
      break;

    case "P1_GATE_BLOCK_DOMINATES_GATE_POLICY_REVIEW":
      ops.push({
        kind: "PATCH_GATE_ORDER",
        target: "GATE",
        opId: "OP_GATE_BLOCK_REMAP_TO_SKIP_V1",
        change: "REMAP_SOME_BLOCKS_TO_SKIP",
        safety: [
          "KEEP_DOUBLE_KEY",
          "KEEP_ORACLE_STALE_AS_STOP",
          "KEEP_IMPACT_HIGH_AS_STOP",
        ],
      });
      break;

    // P2: Observable improvements (allowed)
    case "P2_FREQUENT_TRANSITIONS_OBSERVABLE_LOG":
      ops.push({
        kind: "PATCH_PHASE_POLICY",
        target: "PHASE_POLICY",
        opId: "OP_LOG_FREQUENT_TRANSITIONS_V1",
        change: "ADD_TRANSITION_LOGGING",
        safety: [
          "KEEP_DOUBLE_KEY",
          "KEEP_LABEL_ONLY",
          "NO_EXECUTION_CHANGE",
        ],
      });
      break;

    case "P2_LAG_LONG_OBSERVABLE_LOG":
      ops.push({
        kind: "PATCH_PHASE_POLICY",
        target: "PHASE_POLICY",
        opId: "OP_LOG_LAG_LONG_V1",
        change: "ADD_LAG_LONG_LOGGING",
        safety: [
          "KEEP_DOUBLE_KEY",
          "KEEP_LABEL_ONLY",
          "NO_EXECUTION_CHANGE",
        ],
      });
      break;

    case "P2_HARDSTOP_FREQUENT_OBSERVABLE_LOG":
      ops.push({
        kind: "PATCH_PHASE_POLICY",
        target: "PHASE_POLICY",
        opId: "OP_LOG_HARDSTOP_ACTIVATIONS_V1",
        change: "ADD_HARDSTOP_LOGGING",
        safety: [
          "KEEP_DOUBLE_KEY",
          "KEEP_LABEL_ONLY",
          "NO_EXECUTION_CHANGE",
        ],
      });
      break;

    default:
      warnings.push(`WARN_UNKNOWN_PROPOSAL_ID_${proposal.id}`);
      ops.push({
        kind: "PATCH_NOT_ALLOWED",
        target: "UNKNOWN",
        opId: "OP_UNKNOWN_V1",
        change: "UNKNOWN_CHANGE",
        safety: [],
        notAllowedReason: "UNKNOWN_PROPOSAL_ID",
      });
  }

  return ops;
}

/**
 * Check if patch plan has NOT_ALLOWED operations
 *
 * @param patchPlan - Patch plan
 * @returns True if any op is NOT_ALLOWED
 */
export function hasNotAllowedOps(patchPlan: PatchPlan): boolean {
  return patchPlan.ops.some((op) => op.kind === "PATCH_NOT_ALLOWED");
}

/**
 * Get patch operation kinds from plan
 *
 * @param patchPlan - Patch plan
 * @returns Array of patch kinds
 */
export function getPatchKinds(patchPlan: PatchPlan): PatchKind[] {
  return patchPlan.ops.map((op) => op.kind);
}
