/**
 * PR171: v1.4 Patch Preview Report v1 - Previewer Engine
 *
 * Purpose:
 *   Generate human-readable preview reports from PatchPlan and related data.
 *   Shows "what will change" before adoption (READ-ONLY).
 *
 * Constitutional Constraints:
 *   - READ-ONLY: Report generation only (no adoption, no code changes)
 *   - Fixed rules: Deterministic mapping from inputs to preview
 *   - Label-only: All output is sanitized
 *   - Defensive: Never throws, always returns result
 */

import { PatchPreviewReportV1, PreviewStatus } from "./types";
import { getSectionsForPatchOps } from "./templates";
import { sanitizeLabel, sanitizeLines, formatTimeLabel } from "./guards";

/**
 * Preview Input
 *
 * Minimal interface for preview generation.
 * Uses structural typing to accept PR168/167/170 outputs.
 */
export interface PreviewInput {
  /**
   * Patch operations (from PR168 PatchPlan)
   */
  patchOps?: Array<{ kind: string }>;

  /**
   * Proposal ID (from PR167)
   */
  proposalId?: string;

  /**
   * Priority (from PR167)
   */
  priority?: "P0" | "P1" | "P2" | "UNKNOWN";

  /**
   * Decision candidate (from PR168)
   */
  decisionCandidate?: "ADOPT" | "HOLD" | "REJECT" | "UNKNOWN";

  /**
   * Evidence (from PR170, optional)
   */
  evidence?: Array<{
    kind: string;
    label: string;
    strength: string;
    context?: string;
  }>;

  /**
   * Compare signals (from PR168, optional)
   */
  compareSignals?: string[];
}

/**
 * Generate patch preview report v1
 *
 * Main preview generation function.
 *
 * @param input - Preview input (from PR168/167/170)
 * @returns Preview report (never throws)
 */
export function generatePreviewV1(input: PreviewInput): PatchPreviewReportV1 {
  const warnings: string[] = [];

  try {
    // Extract patch ops
    const patchOps = input.patchOps?.map((op) => op.kind) || [];

    if (patchOps.length === 0) {
      warnings.push("WARN_NO_PATCH_OPS");
    }

    // Generate sections from patch ops
    const sections = getSectionsForPatchOps(patchOps);

    // Extract evidence (max 3, strength-sorted)
    const evidence = extractEvidence(input.evidence || []);

    // Extract compare signals
    const compareSignals = sanitizeLines(input.compareSignals || []);

    // Determine risk labels and readiness
    const riskLabels: string[] = [];
    const readiness: string[] = [];

    // Check for PATCH_NOT_ALLOWED
    if (patchOps.some((op) => op === "PATCH_NOT_ALLOWED")) {
      riskLabels.push("RISK_PATCH_NOT_ALLOWED_PRESENT");
      readiness.push("NOT_REVIEWABLE_REJECT_EXPECTED");
    } else {
      readiness.push("REVIEWABLE");
    }

    // Check for missing information
    if (!input.proposalId) {
      warnings.push("WARN_NO_PROPOSAL_ID");
    }

    if (!input.priority) {
      warnings.push("WARN_NO_PRIORITY");
    }

    if (patchOps.length === 0) {
      readiness.push("NOT_REVIEWABLE_NO_CHANGES");
    }

    // Determine status
    const status: PreviewStatus = warnings.length > 0 ? "PARTIAL" : "AVAILABLE";

    return {
      kind: "PATCH_PREVIEW_V1",
      status,
      proposalId: input.proposalId
        ? sanitizeLabel(input.proposalId)
        : undefined,
      priority: input.priority,
      decisionCandidate: input.decisionCandidate,
      patchOps: patchOps.map(sanitizeLabel),
      sections,
      riskLabels: sanitizeLines(riskLabels),
      readiness: sanitizeLines(readiness),
      evidence,
      compareSignals,
      warnings: sanitizeLines(warnings),
      timeLabel: formatTimeLabel(Date.now()),
      ts: Date.now(),
    };
  } catch (error) {
    // Defensive: Return minimal result on error
    warnings.push("WARN_PREVIEW_ERROR");

    return {
      kind: "PATCH_PREVIEW_V1",
      status: "ERROR",
      patchOps: [],
      sections: [],
      riskLabels: [],
      readiness: ["NOT_REVIEWABLE_ERROR"],
      evidence: [],
      compareSignals: [],
      warnings: sanitizeLines(warnings),
      timeLabel: "T_UNKNOWN",
      ts: Date.now(),
    };
  }
}

/**
 * Extract evidence for preview
 *
 * - Max 3 evidence records
 * - Sorted by strength (STRONG > MEDIUM > WEAK > UNKNOWN)
 * - Sanitized
 *
 * @param evidence - Evidence array (from PR170)
 * @returns Sanitized evidence array (max 3)
 */
function extractEvidence(
  evidence: Array<{
    kind: string;
    label: string;
    strength: string;
    context?: string;
  }>
): Array<{
  kind: string;
  label: string;
  strength: string;
  context?: string[];
}> {
  // Strength order
  const strengthOrder: Record<string, number> = {
    EVIDENCE_STRONG: 0,
    EVIDENCE_MEDIUM: 1,
    EVIDENCE_WEAK: 2,
    EVIDENCE_UNKNOWN: 3,
  };

  // Sort by strength
  const sorted = [...evidence].sort((a, b) => {
    const orderA = strengthOrder[a.strength] ?? 99;
    const orderB = strengthOrder[b.strength] ?? 99;
    return orderA - orderB;
  });

  // Take max 3
  const top3 = sorted.slice(0, 3);

  // Sanitize
  return top3.map((evid) => ({
    kind: sanitizeLabel(evid.kind),
    label: sanitizeLabel(evid.label),
    strength: sanitizeLabel(evid.strength),
    context: evid.context ? [sanitizeLabel(evid.context)] : undefined,
  }));
}
