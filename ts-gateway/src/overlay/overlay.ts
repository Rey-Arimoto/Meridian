/**
 * PR177: v1.4 Pre-Adoption Risk Overlay v1 - Overlay Engine
 *
 * Purpose:
 *   Generate risk overlay by combining regression and interaction evidence.
 *   Uses fixed rules to assess risk level.
 *
 * Constitutional Constraints:
 *   - Fixed rules: Hardcoded risk assessment logic (no learning)
 *   - READ-ONLY: Observation only
 *   - Defensive: Never throws
 */

import {
  readRecentRegressionsForProposalV1,
  readRecentInteractionsForProposalV1,
} from "./reader";
import {
  RiskOverlayV1,
  OverlayRiskLevel,
  OverlayRiskKind,
  OverlayEvidence,
  OVERLAY_PARAMS,
} from "./types";
import { sanitizeRiskOverlayV1 } from "./guards";

/**
 * Generate risk overlay for proposal
 *
 * @param proposalId - Proposal ID
 * @param priority - Optional priority (P0/P1/P2)
 * @returns Risk overlay
 */
export async function generateRiskOverlayV1(
  proposalId: string,
  priority?: "P0" | "P1" | "P2" | "UNKNOWN"
): Promise<RiskOverlayV1> {
  const warnings: string[] = [];

  try {
    // Step A: Extract evidence
    const regressionEvidence = await readRecentRegressionsForProposalV1(
      proposalId
    );
    const interactionEvidence = await readRecentInteractionsForProposalV1(
      proposalId
    );

    warnings.push(...regressionEvidence.warnings);
    warnings.push(...interactionEvidence.warnings);

    // Step B: Assess risk level (priority-based)
    let riskLevel: OverlayRiskLevel;
    const risks: { kind: OverlayRiskKind; label: string }[] = [];
    const evidence: OverlayEvidence[] = [];

    // Rule 1: Regression evidence STRONG → RISK_HIGH
    if (regressionEvidence.strength === "STRONG") {
      riskLevel = "RISK_HIGH";
      risks.push({
        kind: "RISK_REGRESSION_HISTORY",
        label: "REGRESSION_STRONG_DETECTED_RECENTLY",
      });

      for (const label of regressionEvidence.labels.slice(
        0,
        OVERLAY_PARAMS.MAX_RISKS
      )) {
        evidence.push({
          kind: "EVID_REGRESSION",
          label,
          strength: "STRONG",
        });
      }
    }
    // Rule 2: Interaction evidence STRONG → RISK_HIGH
    else if (interactionEvidence.strength === "STRONG") {
      riskLevel = "RISK_HIGH";
      risks.push({
        kind: "RISK_INTERACTION_COUPLING",
        label: "INTERACTION_STRONG_DETECTED_RECENTLY",
      });

      for (const label of interactionEvidence.labels.slice(
        0,
        OVERLAY_PARAMS.MAX_RISKS
      )) {
        evidence.push({
          kind: "EVID_INTERACTION",
          label,
          strength: "STRONG",
        });
      }
    }
    // Rule 3: Interaction evidence MEDIUM → RISK_MEDIUM
    else if (interactionEvidence.strength === "MEDIUM") {
      riskLevel = "RISK_MEDIUM";
      risks.push({
        kind: "RISK_INTERACTION_COUPLING",
        label: "INTERACTION_MEDIUM_DETECTED_RECENTLY",
      });

      for (const label of interactionEvidence.labels.slice(
        0,
        OVERLAY_PARAMS.MAX_RISKS
      )) {
        evidence.push({
          kind: "EVID_INTERACTION",
          label,
          strength: "MEDIUM",
        });
      }
    }
    // Rule 4: Regression evidence MEDIUM → RISK_MEDIUM
    else if (regressionEvidence.strength === "MEDIUM") {
      riskLevel = "RISK_MEDIUM";
      risks.push({
        kind: "RISK_REGRESSION_HISTORY",
        label: "REGRESSION_MEDIUM_DETECTED_RECENTLY",
      });

      for (const label of regressionEvidence.labels.slice(
        0,
        OVERLAY_PARAMS.MAX_RISKS
      )) {
        evidence.push({
          kind: "EVID_REGRESSION",
          label,
          strength: "MEDIUM",
        });
      }
    }
    // Rule 5: No evidence or UNKNOWN → RISK_UNKNOWN
    else if (
      regressionEvidence.strength === "UNKNOWN" &&
      interactionEvidence.strength === "UNKNOWN"
    ) {
      riskLevel = "RISK_UNKNOWN";
      risks.push({
        kind: "RISK_EVIDENCE_WEAK",
        label: "NO_RECENT_EVIDENCE_FOUND",
      });
    }
    // Rule 6: Otherwise → RISK_LOW
    else {
      riskLevel = "RISK_LOW";

      // Add any weak evidence
      if (regressionEvidence.labels.length > 0) {
        for (const label of regressionEvidence.labels.slice(
          0,
          OVERLAY_PARAMS.MAX_RISKS
        )) {
          evidence.push({
            kind: "EVID_REGRESSION",
            label,
            strength: regressionEvidence.strength,
          });
        }
      }

      if (interactionEvidence.labels.length > 0) {
        for (const label of interactionEvidence.labels.slice(
          0,
          OVERLAY_PARAMS.MAX_RISKS
        )) {
          evidence.push({
            kind: "EVID_INTERACTION",
            label,
            strength: interactionEvidence.strength,
          });
        }
      }
    }

    // Step C: Limit evidence to max
    const limitedEvidence = evidence
      .sort((a, b) => {
        // Sort by kind priority: REGRESSION > INTERACTION > NONE
        const kindOrder: Record<string, number> = {
          EVID_REGRESSION: 3,
          EVID_INTERACTION: 2,
          EVID_NONE: 1,
        };
        const kindDiff = kindOrder[b.kind] - kindOrder[a.kind];
        if (kindDiff !== 0) return kindDiff;

        // Then by strength: STRONG > MEDIUM > WEAK > UNKNOWN
        const strengthOrder: Record<string, number> = {
          STRONG: 4,
          MEDIUM: 3,
          WEAK: 2,
          UNKNOWN: 1,
        };
        return strengthOrder[b.strength] - strengthOrder[a.strength];
      })
      .slice(0, OVERLAY_PARAMS.MAX_EVIDENCE);

    // Build overlay
    const overlay: RiskOverlayV1 = {
      status:
        regressionEvidence.status === "PARTIAL" ||
        interactionEvidence.status === "PARTIAL"
          ? "PARTIAL"
          : "AVAILABLE",
      proposalId,
      priority,
      riskLevel,
      risks: risks.slice(0, OVERLAY_PARAMS.MAX_RISKS),
      evidence: limitedEvidence,
      warnings,
    };

    // Sanitize and return
    return sanitizeRiskOverlayV1(overlay);
  } catch (error) {
    // Defensive: Return ERROR overlay
    return {
      status: "ERROR",
      proposalId,
      priority,
      riskLevel: "RISK_UNKNOWN",
      risks: [
        {
          kind: "RISK_UNKNOWN",
          label: "ERROR_GENERATING_OVERLAY",
        },
      ],
      evidence: [],
      warnings: [...warnings, "ERROR_OVERLAY_GENERATION"],
    };
  }
}
