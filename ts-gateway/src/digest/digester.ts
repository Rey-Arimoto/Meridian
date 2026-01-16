/**
 * PR180: v1.4 Spec Change Digest v1 - Digester
 *
 * Purpose:
 *   Build spec change digest from inputs.
 *
 * Constitutional Constraints:
 *   - READ-ONLY: Digest generation is observation/summary only
 *   - Fixed rules: No learning, optimization, or prediction
 *   - Defensive: Never throws
 *   - Label-only: Output is label-only (debug JSON is store/CLI responsibility)
 */

import { DigestInputV1, SpecChangeDigestV1, DigestRefsV1 } from "./types";
import {
  sanitizeStringArray,
  validateDigestLabelOnly,
  formatTimeLabel,
} from "./guards";
import {
  extractHeadline,
  extractWhat,
  extractWhy,
  extractRisks,
  extractChecklist,
  extractRationale,
  determineSuggestedNext,
} from "./templates";

/**
 * Build spec change digest
 *
 * @param input - Digest input
 * @returns Spec change digest
 */
export function buildSpecChangeDigestV1(
  input: DigestInputV1
): SpecChangeDigestV1 {
  const warnings: string[] = [];

  try {
    // Extract refs
    const refs: DigestRefsV1 = {
      hasSpecLock: !!input.specLock,
      hasPatchPlan: !!input.patchPlan,
      hasPreview: !!input.preview,
      hasReview: !!input.review,
      hasDecisionAck: !!input.decisionAck,
      hasEffect: !!input.effect,
      hasAttribution: !!input.attribution,
      hasEvidenceLinked: !!(input.preview?.evidence && input.preview.evidence.length > 0),
    };

    // Extract components using fixed templates
    const headline = extractHeadline(input);
    const what = extractWhat(input);
    const why = extractWhy(input);
    const risks = extractRisks(input);
    const checklist = extractChecklist(input);
    const rationale = extractRationale(input);
    const suggestedNext = determineSuggestedNext(input);

    // Merge input warnings
    if (input.warnings) {
      warnings.push(...input.warnings);
    }

    // Determine status
    let status: "AVAILABLE" | "PARTIAL" | "ERROR" = "AVAILABLE";

    // Check if partial (missing key components)
    if (!refs.hasPreview && !refs.hasReview && !refs.hasPatchPlan) {
      status = "PARTIAL";
      warnings.push("WARN_MISSING_KEY_COMPONENTS");
    }

    // Sanitize all output arrays
    const sanitizedHeadline = sanitizeStringArray(headline);
    const sanitizedWhat = sanitizeStringArray(what);
    const sanitizedWhy = sanitizeStringArray(why);
    const sanitizedRisks = sanitizeStringArray(risks);
    const sanitizedChecklist = sanitizeStringArray(checklist);
    const sanitizedRationale = sanitizeStringArray(rationale);
    const sanitizedWarnings = sanitizeStringArray(warnings);

    // Build report
    const report: SpecChangeDigestV1 = {
      status,
      time: formatTimeLabel(Date.now()),
      headline: sanitizedHeadline,
      why: sanitizedWhy,
      what: sanitizedWhat,
      risks: sanitizedRisks,
      checklist: sanitizedChecklist,
      rationale: sanitizedRationale,
      suggestedNext,
      refs,
      warnings: sanitizedWarnings,
    };

    // Validate label-only
    const validation = validateDigestLabelOnly(report);
    if (!validation.ok) {
      report.warnings.push(...validation.warnings);
      report.status = "PARTIAL";
    }

    return report;
  } catch (error) {
    // Defensive: Return ERROR report instead of throwing
    warnings.push("ERROR_DIGEST_BUILD_FAILED");

    return {
      status: "ERROR",
      time: "T_UNKNOWN",
      headline: [],
      why: [],
      what: [],
      risks: [],
      checklist: [],
      rationale: [],
      suggestedNext: "ACK_UNKNOWN",
      refs: {
        hasSpecLock: false,
        hasPatchPlan: false,
        hasPreview: false,
        hasReview: false,
        hasDecisionAck: false,
        hasEffect: false,
        hasAttribution: false,
        hasEvidenceLinked: false,
      },
      warnings: sanitizeStringArray(warnings),
    };
  }
}
