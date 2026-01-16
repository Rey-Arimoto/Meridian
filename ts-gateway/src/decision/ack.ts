/**
 * PR173: v1.4 Decision Acknowledgement + Reviewer Trace v1 - Ack Builder
 *
 * Purpose:
 *   Build decision acknowledgement records from PR168/171/172 outputs.
 *   Captures "who decided what, when, and why" for audit trail.
 *
 * Constitutional Constraints:
 *   - READ-ONLY: Records decision facts only (no automatic adoption)
 *   - Fixed rules: Deterministic record building
 *   - Label-only: All fields sanitized
 *   - Defensive: Never throws, always returns valid record
 */

import {
  DecisionAckRecordV1,
  DecisionAckStatus,
  ReviewerKind,
  AckSource,
  AckDecision,
} from "./types";
import { formatTimeLabel, sanitizeDecisionLabel, sanitizeLines } from "./guards";

/**
 * Build Ack Input
 *
 * Optional fields allow building from partial data.
 */
export interface BuildAckInput {
  /**
   * Who made the decision (optional, defaults to UNKNOWN)
   */
  reviewer?: ReviewerKind;

  /**
   * Where the ack was created (optional, defaults to UNKNOWN)
   */
  source?: AckSource;

  /**
   * Proposal ID (e.g., "P0_REDUCE_ORACLE_STALE_BLOCKS_DEGRADE")
   */
  proposalId?: string;

  /**
   * Preview report (from PR171)
   */
  previewReport?: any;

  /**
   * Review report (from PR172)
   */
  reviewReport?: any;

  /**
   * Decision result (from PR168)
   */
  decisionResult?: any;
}

/**
 * Build decision acknowledgement record v1
 *
 * Main ack building function that creates audit record from inputs.
 *
 * Decision priority:
 * 1. decisionResult.decision (PR168)
 * 2. reviewReport.rationale.decisionCandidate (PR172)
 * 3. fallback to UNKNOWN
 *
 * Status:
 * - AVAILABLE: proposalId + decision present
 * - PARTIAL: decision is UNKNOWN
 * - ERROR: input shape is corrupt
 *
 * @param input - Build ack input
 * @returns Decision ack record (never throws)
 */
export function buildDecisionAckV1(input: BuildAckInput): DecisionAckRecordV1 {
  const warnings: string[] = [];
  const ts = Date.now();

  try {
    // 1. Determine reviewer and source
    const reviewer = input.reviewer || "UNKNOWN";
    const source = input.source || "UNKNOWN";

    // 2. Determine decision (priority: decisionResult > reviewReport > UNKNOWN)
    let decision: AckDecision = "UNKNOWN";

    if (input.decisionResult && input.decisionResult.decision) {
      const d = input.decisionResult.decision;
      if (d === "ADOPT" || d === "HOLD" || d === "REJECT") {
        decision = d;
      }
    } else if (
      input.reviewReport &&
      input.reviewReport.rationale &&
      input.reviewReport.rationale.decisionCandidate
    ) {
      const candidate = input.reviewReport.rationale.decisionCandidate;
      // Map CANDIDATE_ADOPT -> ADOPT, etc.
      if (candidate === "CANDIDATE_ADOPT") {
        decision = "ADOPT";
      } else if (candidate === "CANDIDATE_HOLD") {
        decision = "HOLD";
      } else if (candidate === "CANDIDATE_REJECT") {
        decision = "REJECT";
      }
    }

    if (decision === "UNKNOWN") {
      warnings.push("WARN_DECISION_UNKNOWN");
    }

    // 3. Build refs
    const refs = {
      proposalId: input.proposalId
        ? sanitizeDecisionLabel(input.proposalId)
        : undefined,
      previewId: input.previewReport ? "PREVIEW_PRESENT" : undefined,
      reviewId: input.reviewReport ? "REVIEW_PRESENT" : undefined,
      patchPlanId:
        input.decisionResult && input.decisionResult.patchPlan
          ? "PATCHPLAN_PRESENT"
          : undefined,
    };

    // 4. Build rationale labels
    const rationaleLabels: string[] = [];
    if (input.reviewReport && input.reviewReport.rationale) {
      const reasons = input.reviewReport.rationale.reasons || [];
      rationaleLabels.push(...sanitizeLines(reasons));
    }

    if (rationaleLabels.length === 0) {
      rationaleLabels.push("RAT_UNAVAILABLE");
    }

    // 5. Build checklist summary
    const checklistSummary: string[] = [];
    if (input.reviewReport && input.reviewReport.checklist) {
      for (const item of input.reviewReport.checklist) {
        if (item.id && item.status) {
          const summary = `${sanitizeDecisionLabel(item.id)}:${item.status}`;
          checklistSummary.push(summary);
        }
      }
    }

    if (checklistSummary.length === 0) {
      checklistSummary.push("CHECKLIST_UNAVAILABLE");
    }

    // 6. Build evidence summary
    const evidenceSummary: string[] = [];
    if (input.previewReport && input.previewReport.evidence) {
      const evidence = input.previewReport.evidence.slice(0, 3); // Max 3
      for (const evid of evidence) {
        if (evid.strength) {
          evidenceSummary.push(sanitizeDecisionLabel(evid.strength));
        }
      }
    }

    if (evidenceSummary.length === 0) {
      evidenceSummary.push("EVIDENCE_UNAVAILABLE");
    }

    // 7. Build compare summary
    const compareSummary: string[] = [];
    if (input.previewReport && input.previewReport.compareSignals) {
      const signals = input.previewReport.compareSignals.slice(0, 3); // Max 3
      compareSummary.push(...sanitizeLines(signals));
    }

    if (compareSummary.length === 0) {
      compareSummary.push("COMPARE_UNAVAILABLE");
    }

    // 8. Determine status
    let status: DecisionAckStatus = "AVAILABLE";
    if (decision === "UNKNOWN") {
      status = "PARTIAL";
    }
    if (!refs.proposalId) {
      status = "PARTIAL";
      warnings.push("WARN_NO_PROPOSAL_ID");
    }

    // 9. Build record
    return {
      kind: "DECISION_ACK_V1",
      status,
      ts,
      timeLabel: formatTimeLabel(ts),
      reviewer,
      source,
      refs,
      rationale: {
        decision,
        rationaleLabels,
        checklistSummary,
        evidenceSummary,
        compareSummary,
      },
      warnings: sanitizeLines(warnings),
    };
  } catch (error) {
    // Defensive: Return ERROR record
    warnings.push("WARN_ACK_BUILD_ERROR");

    return {
      kind: "DECISION_ACK_V1",
      status: "ERROR",
      ts,
      timeLabel: formatTimeLabel(ts),
      reviewer: input.reviewer || "UNKNOWN",
      source: input.source || "UNKNOWN",
      refs: {
        proposalId: input.proposalId
          ? sanitizeDecisionLabel(input.proposalId)
          : undefined,
      },
      rationale: {
        decision: "UNKNOWN",
        rationaleLabels: ["RAT_UNAVAILABLE"],
        checklistSummary: ["CHECKLIST_UNAVAILABLE"],
        evidenceSummary: ["EVIDENCE_UNAVAILABLE"],
        compareSummary: ["COMPARE_UNAVAILABLE"],
      },
      warnings: sanitizeLines(warnings),
    };
  }
}
