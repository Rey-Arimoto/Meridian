/**
 * PR170: v1.4 Evidence-Linked Proposals v1 - Evidence Extraction
 *
 * Purpose:
 *   Extract evidence from PR169 attribution results and map to PR167 proposals.
 *   Uses fixed rules to link bottlenecks, paths, and edges to proposals.
 *
 * Constitutional Constraints:
 *   - READ-ONLY: Analysis only (no execution, no changes)
 *   - Fixed rules: Deterministic mapping from attribution to evidence
 *   - Label-only: All evidence labels are sanitized
 *   - Defensive: Never throws, always returns evidence array
 */

import { AttributionResultV1 } from "../attribution/types";
import {
  ProposalId,
  ProposalEvidence,
  EvidenceKind,
  EvidenceStrength,
} from "./types";
import { sanitizeProposalLabel } from "./guards";

/**
 * Extract evidence from attribution result
 *
 * Maps attribution bottlenecks, paths, and edges to proposal evidence.
 * Uses fixed rules for mapping.
 *
 * @param proposalId - Proposal ID to extract evidence for
 * @param attribution - Attribution result from PR169
 * @returns Evidence array (empty if no evidence found)
 */
export function extractEvidenceForProposal(
  proposalId: ProposalId,
  attribution: AttributionResultV1 | null
): ProposalEvidence[] {
  if (!attribution) {
    return [];
  }

  const evidence: ProposalEvidence[] = [];

  try {
    // Extract bottleneck evidence (STRONG)
    const bottleneckEvidence = extractBottleneckEvidence(
      proposalId,
      attribution
    );
    evidence.push(...bottleneckEvidence);

    // Extract top path evidence (MEDIUM)
    const pathEvidence = extractPathEvidence(proposalId, attribution);
    evidence.push(...pathEvidence);

    // Extract top edge evidence (WEAK)
    const edgeEvidence = extractEdgeEvidence(proposalId, attribution);
    evidence.push(...edgeEvidence);

    return evidence;
  } catch (error) {
    // Defensive: Return empty array on error
    return [];
  }
}

/**
 * Extract bottleneck evidence (STRONG)
 *
 * Maps bottlenecks to proposals using fixed rules.
 *
 * @param proposalId - Proposal ID
 * @param attribution - Attribution result
 * @returns Bottleneck evidence array
 */
function extractBottleneckEvidence(
  proposalId: ProposalId,
  attribution: AttributionResultV1
): ProposalEvidence[] {
  const evidence: ProposalEvidence[] = [];

  // Fixed mapping: Bottleneck → Proposal
  const bottleneckMap: Record<string, ProposalId[]> = {
    BOTTLENECK_ORACLE_DOMINANT: ["P0_REDUCE_ORACLE_STALE_BLOCKS_DEGRADE"],
    BOTTLENECK_MARKET_IMPACT_DOMINANT: [
      "P0_REDUCE_IMPACT_BLOCKS_DEGRADE",
      "P0_REDUCE_SLIPPAGE_BLOCKS_DEGRADE",
    ],
    BOTTLENECK_GATE_BLOCK_FREQUENT: ["P1_GATE_BLOCK_DOMINATES_GATE_POLICY_REVIEW"],
    BOTTLENECK_STOP_FREQUENT: ["P1_PHASE_ESCALATION_DOMINATES_PHASE_POLICY_REVIEW"],
    BOTTLENECK_PHASE_POLICY_DOMINANT: [
      "P1_PHASE_ESCALATION_DOMINATES_PHASE_POLICY_REVIEW",
    ],
  };

  for (const bottleneck of attribution.bottlenecks) {
    const matchingProposals = bottleneckMap[bottleneck] || [];

    if (matchingProposals.includes(proposalId)) {
      evidence.push({
        kind: "EVID_BOTTLENECK",
        label: sanitizeProposalLabel(bottleneck),
        strength: "EVIDENCE_STRONG",
        context: "FROM_ATTRIBUTION_BOTTLENECK_ANALYSIS",
      });
    }
  }

  return evidence;
}

/**
 * Extract top path evidence (MEDIUM)
 *
 * Maps top paths to proposals using pattern matching.
 *
 * @param proposalId - Proposal ID
 * @param attribution - Attribution result
 * @returns Path evidence array
 */
function extractPathEvidence(
  proposalId: ProposalId,
  attribution: AttributionResultV1
): ProposalEvidence[] {
  const evidence: ProposalEvidence[] = [];

  // Fixed mapping: Path patterns → Proposals
  const pathPatterns: Record<string, { pattern: RegExp; proposals: ProposalId[] }> = {
    ORACLE_PATH: {
      pattern: /ORACLE/i,
      proposals: ["P0_REDUCE_ORACLE_STALE_BLOCKS_DEGRADE"],
    },
    IMPACT_PATH: {
      pattern: /IMPACT/i,
      proposals: ["P0_REDUCE_IMPACT_BLOCKS_DEGRADE"],
    },
    SLIPPAGE_PATH: {
      pattern: /SLIPPAGE/i,
      proposals: ["P0_REDUCE_SLIPPAGE_BLOCKS_DEGRADE"],
    },
    DRIFT_PATH: {
      pattern: /DRIFT/i,
      proposals: ["P0_REDUCE_DRIFT_BLOCKS_DEGRADE"],
    },
    COOLDOWN_PATH: {
      pattern: /COOLDOWN/i,
      proposals: ["P0_REDUCE_COOLDOWN_BLOCKS_DEGRADE"],
    },
    PHASE_ESCALATION_PATH: {
      pattern: /PHASE.*ESCALATION|ESCALATION.*PHASE/i,
      proposals: ["P1_PHASE_ESCALATION_DOMINATES_PHASE_POLICY_REVIEW"],
    },
    SHOCK_RISK90_PATH: {
      pattern: /RISK_?90|RISK.*90/i,
      proposals: ["P1_SHOCK_RISK90_OVERUSE_TEMPLATE_POLICY_RESTRICT"],
    },
  };

  for (const path of attribution.topPaths) {
    const pathStr = path.nodes.map((n) => `${n.t}:${n.v}`).join("_");

    for (const [patternName, { pattern, proposals }] of Object.entries(pathPatterns)) {
      if (pattern.test(pathStr) && proposals.includes(proposalId)) {
        evidence.push({
          kind: "EVID_TOP_PATH",
          label: sanitizeProposalLabel(`PATH_${patternName}`),
          strength: "EVIDENCE_MEDIUM",
          context: "FROM_ATTRIBUTION_TOP_PATHS",
        });
        break; // Only add one path evidence per pattern match
      }
    }
  }

  return evidence;
}

/**
 * Extract top edge evidence (WEAK)
 *
 * Maps top edges to proposals using pattern matching.
 *
 * @param proposalId - Proposal ID
 * @param attribution - Attribution result
 * @returns Edge evidence array
 */
function extractEdgeEvidence(
  proposalId: ProposalId,
  attribution: AttributionResultV1
): ProposalEvidence[] {
  const evidence: ProposalEvidence[] = [];

  // Fixed mapping: Edge patterns → Proposals
  const edgePatterns: Record<string, { pattern: RegExp; proposals: ProposalId[] }> = {
    ORACLE_BLOCK_EDGE: {
      pattern: /ORACLE.*BLOCK|BLOCK.*ORACLE/i,
      proposals: ["P0_REDUCE_ORACLE_STALE_BLOCKS_DEGRADE"],
    },
    IMPACT_BLOCK_EDGE: {
      pattern: /IMPACT.*BLOCK|BLOCK.*IMPACT/i,
      proposals: ["P0_REDUCE_IMPACT_BLOCKS_DEGRADE"],
    },
    SLIPPAGE_BLOCK_EDGE: {
      pattern: /SLIPPAGE.*BLOCK|BLOCK.*SLIPPAGE/i,
      proposals: ["P0_REDUCE_SLIPPAGE_BLOCKS_DEGRADE"],
    },
    GATE_BLOCK_EDGE: {
      pattern: /GATE.*BLOCK/i,
      proposals: ["P1_GATE_BLOCK_DOMINATES_GATE_POLICY_REVIEW"],
    },
  };

  for (const edge of attribution.topEdges) {
    const edgeStr = `${edge.from.t}:${edge.from.v}_TO_${edge.to.t}:${edge.to.v}`;

    for (const [patternName, { pattern, proposals }] of Object.entries(edgePatterns)) {
      if (pattern.test(edgeStr) && proposals.includes(proposalId)) {
        evidence.push({
          kind: "EVID_TOP_EDGE",
          label: sanitizeProposalLabel(`EDGE_${patternName}`),
          strength: "EVIDENCE_WEAK",
          context: "FROM_ATTRIBUTION_TOP_EDGES",
        });
        break; // Only add one edge evidence per pattern match
      }
    }
  }

  return evidence;
}

/**
 * Check if attribution has any evidence
 *
 * @param attribution - Attribution result
 * @returns True if attribution has bottlenecks, paths, or edges
 */
export function hasAnyEvidence(attribution: AttributionResultV1 | null): boolean {
  if (!attribution) {
    return false;
  }

  return (
    attribution.bottlenecks.length > 0 ||
    attribution.topPaths.length > 0 ||
    attribution.topEdges.length > 0
  );
}
