/**
 * PR180: v1.4 Spec Change Digest v1 - Templates
 *
 * Purpose:
 *   Fixed extraction rules for digest generation.
 *
 * Constitutional Constraints:
 *   - Fixed rules: No learning, optimization, or prediction
 *   - Defensive: Never throws
 */

import { DigestInputV1 } from "./types";

/**
 * Extract headline labels
 *
 * @param input - Digest input
 * @returns Headline labels
 */
export function extractHeadline(input: DigestInputV1): string[] {
  const headline: string[] = [];

  // Spec lock status
  if (input.specLock?.hasPendingSpec) {
    headline.push("PENDING_ACK");
  }
  if (input.specLock?.hasActiveSpec) {
    headline.push("HAS_ACTIVE_SPEC");
  }

  // Preview status
  if (input.preview?.status === "AVAILABLE") {
    headline.push("HAS_PREVIEW");
  }

  // Review status
  if (input.review?.status === "AVAILABLE") {
    headline.push("HAS_REVIEW");
  }

  // Decision ACK
  if (input.decisionAck) {
    headline.push("HAS_DECISION_ACK");
  }

  // Patch plan
  if (input.patchPlan) {
    headline.push("HAS_PATCHPLAN");
  }

  return headline;
}

/**
 * Extract "what" changes
 *
 * @param input - Digest input
 * @returns What labels (max 3)
 */
export function extractWhat(input: DigestInputV1): string[] {
  const what: string[] = [];

  // Extract patch ops (max 3, preserve order)
  if (input.patchPlan?.patchOps) {
    const ops = input.patchPlan.patchOps.slice(0, 3);
    for (const op of ops) {
      if (op.kind) {
        what.push(op.kind);
      }
    }
  }

  return what;
}

/**
 * Extract "why" reasons
 *
 * @param input - Digest input
 * @returns Why labels (max 3)
 */
export function extractWhy(input: DigestInputV1): string[] {
  const why: string[] = [];

  // Extract strong/medium evidence (max 3)
  if (input.preview?.evidence) {
    const strongEvidence = input.preview.evidence.filter(
      (e) => e.strength === "STRONG" || e.strength === "MEDIUM"
    );

    for (const ev of strongEvidence.slice(0, 3)) {
      if (ev.label) {
        why.push(ev.label);
      } else if (ev.kind) {
        why.push(`EVIDENCE_${ev.kind}`);
      }
    }
  }

  // Extract bottlenecks (max 2)
  if (input.attribution?.bottlenecks) {
    for (const bottleneck of input.attribution.bottlenecks.slice(0, 2)) {
      why.push(`BOTTLENECK_${bottleneck}`);
    }
  }

  return why;
}

/**
 * Extract risks
 *
 * @param input - Digest input
 * @returns Risk labels (max 5)
 */
export function extractRisks(input: DigestInputV1): string[] {
  const risks: string[] = [];

  // Preview risks (max 3)
  if (input.preview?.risks) {
    for (const risk of input.preview.risks.slice(0, 3)) {
      risks.push(risk);
    }
  }

  // Review checklist failures
  if (input.review?.checklist) {
    const hasFail = input.review.checklist.some((c) => c.status === "FAIL");
    if (hasFail) {
      risks.push("RISK_CHECKLIST_FAIL_PRESENT");
    }
  }

  // Patch NOT_ALLOWED
  if (input.patchPlan?.patchOps) {
    const hasNotAllowed = input.patchPlan.patchOps.some(
      (op) => op.kind === "NOT_ALLOWED"
    );
    if (hasNotAllowed) {
      risks.push("RISK_PATCH_NOT_ALLOWED_PRESENT");
    }
  }

  return risks;
}

/**
 * Extract checklist summary
 *
 * @param input - Digest input
 * @returns Checklist labels
 */
export function extractChecklist(input: DigestInputV1): string[] {
  const checklist: string[] = [];

  if (input.review?.checklist) {
    for (const item of input.review.checklist) {
      checklist.push(`${item.id}_${item.status}`);
    }
  }

  return checklist;
}

/**
 * Extract rationale summary
 *
 * @param input - Digest input
 * @returns Rationale labels
 */
export function extractRationale(input: DigestInputV1): string[] {
  if (input.review?.rationale) {
    return input.review.rationale.slice(0, 5); // Max 5
  }

  return [];
}

/**
 * Determine suggested next action
 *
 * @param input - Digest input
 * @returns Suggested next action label
 */
export function determineSuggestedNext(
  input: DigestInputV1
): "ACK_OK" | "ACK_HOLD" | "ACK_REJECT" | "ACK_UNKNOWN" {
  // Based on review decision (not a command, just a reading label)
  if (input.review?.decision === "CANDIDATE_ADOPT") {
    return "ACK_OK";
  } else if (input.review?.decision === "CANDIDATE_HOLD") {
    return "ACK_HOLD";
  } else if (input.review?.decision === "CANDIDATE_REJECT") {
    return "ACK_REJECT";
  }

  // Unknown
  return "ACK_UNKNOWN";
}
