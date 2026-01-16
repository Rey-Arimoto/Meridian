/**
 * PR177: v1.4 Pre-Adoption Risk Overlay v1 - Reader
 *
 * Purpose:
 *   Read PR175 regressions and PR176 interactions for risk overlay.
 *
 * Constitutional Constraints:
 *   - READ-ONLY: No file modification
 *   - Defensive: Handles missing/corrupt files gracefully
 */

import { readRecentRegressionReportsV1 } from "../regress/store";
import { readRecentInteractionReportsV1 } from "../interaction/store";
import { OVERLAY_PARAMS } from "./types";

/**
 * Regression evidence summary
 */
export interface RegressionEvidenceSummary {
  status: "AVAILABLE" | "PARTIAL";
  labels: string[];
  strength: "STRONG" | "MEDIUM" | "WEAK" | "UNKNOWN";
  warnings: string[];
}

/**
 * Interaction evidence summary
 */
export interface InteractionEvidenceSummary {
  status: "AVAILABLE" | "PARTIAL";
  labels: string[];
  strength: "STRONG" | "MEDIUM" | "WEAK" | "UNKNOWN";
  warnings: string[];
}

/**
 * Read recent regressions for proposal
 *
 * @param proposalId - Proposal ID
 * @param tail - Number of recent records to read
 * @returns Regression evidence summary
 */
export async function readRecentRegressionsForProposalV1(
  proposalId: string,
  tail: number = OVERLAY_PARAMS.RECENT_TAIL
): Promise<RegressionEvidenceSummary> {
  try {
    const { reports, warnings } = readRecentRegressionReportsV1({
      tail,
      proposalId,
    });

    if (reports.length === 0) {
      return {
        status: "PARTIAL",
        labels: [],
        strength: "UNKNOWN",
        warnings: [...warnings, "WARN_NO_REGRESSIONS_FOR_PROPOSAL"],
      };
    }

    // Collect labels and determine strength
    const labels: string[] = [];
    let maxStrength: "STRONG" | "MEDIUM" | "WEAK" | "UNKNOWN" = "UNKNOWN";

    for (const report of reports) {
      // Add regression decision as label
      if (report.analysis.decision === "REGRESSION_DETECTED") {
        labels.push(`REGRESSION_${report.analysis.kind}`);

        // Update max strength
        const strength = report.analysis.strength;
        if (strength === "STRONG" && maxStrength !== "STRONG") {
          maxStrength = "STRONG";
        } else if (
          strength === "MEDIUM" &&
          maxStrength !== "STRONG" &&
          maxStrength !== "MEDIUM"
        ) {
          maxStrength = "MEDIUM";
        } else if (
          strength === "WEAK" &&
          maxStrength === "UNKNOWN"
        ) {
          maxStrength = "WEAK";
        }
      }
    }

    return {
      status: "AVAILABLE",
      labels,
      strength: maxStrength,
      warnings,
    };
  } catch (error) {
    return {
      status: "PARTIAL",
      labels: [],
      strength: "UNKNOWN",
      warnings: ["ERROR_READING_REGRESSIONS"],
    };
  }
}

/**
 * Read recent interactions for proposal
 *
 * @param proposalId - Proposal ID
 * @param tail - Number of recent records to read
 * @returns Interaction evidence summary
 */
export async function readRecentInteractionsForProposalV1(
  proposalId: string,
  tail: number = OVERLAY_PARAMS.RECENT_TAIL
): Promise<InteractionEvidenceSummary> {
  try {
    const { reports, warnings } = readRecentInteractionReportsV1({
      tail,
      proposalId, // Matches either primary or secondary
    });

    if (reports.length === 0) {
      return {
        status: "PARTIAL",
        labels: [],
        strength: "UNKNOWN",
        warnings: [...warnings, "WARN_NO_INTERACTIONS_FOR_PROPOSAL"],
      };
    }

    // Collect labels and determine strength
    const labels: string[] = [];
    let maxStrength: "STRONG" | "MEDIUM" | "WEAK" | "UNKNOWN" = "UNKNOWN";

    for (const report of reports) {
      // Add interaction kind as label
      if (report.interaction === "INTERACTION_DETECTED") {
        labels.push(`INTERACTION_${report.interactionKind}`);

        // Update max strength
        const strength = report.strength;
        if (strength === "STRONG" && maxStrength !== "STRONG") {
          maxStrength = "STRONG";
        } else if (
          strength === "MEDIUM" &&
          maxStrength !== "STRONG" &&
          maxStrength !== "MEDIUM"
        ) {
          maxStrength = "MEDIUM";
        } else if (
          strength === "WEAK" &&
          maxStrength === "UNKNOWN"
        ) {
          maxStrength = "WEAK";
        }
      }
    }

    return {
      status: "AVAILABLE",
      labels,
      strength: maxStrength,
      warnings,
    };
  } catch (error) {
    return {
      status: "PARTIAL",
      labels: [],
      strength: "UNKNOWN",
      warnings: ["ERROR_READING_INTERACTIONS"],
    };
  }
}
