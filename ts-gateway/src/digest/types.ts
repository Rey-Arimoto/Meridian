/**
 * PR180: v1.4 Spec Change Digest v1 - Types
 *
 * Purpose:
 *   Define digest types for compressing spec change information.
 *
 * Constitutional Constraints:
 *   - READ-ONLY: Digest generation is observation/summary only
 *   - Fixed rules: Template/extraction/formatting are fixed rules
 *   - Label-only: No numerics, prices, addresses, tokens, specific times in normal mode
 *   - Defensive: Types support defensive parsing
 */

export type DigestStatus = "AVAILABLE" | "PARTIAL" | "ERROR";

export type DigestReadiness = "REVIEWABLE" | "NOT_REVIEWABLE" | "UNKNOWN";

export type DigestTimeLabel =
  | "T_RECENT"
  | "T_MIN"
  | "T_HOUR"
  | "T_OLD"
  | "T_UNKNOWN";

/**
 * Digest references (READ-ONLY links)
 * Lists what was referenced (contents are label-only summarized)
 */
export interface DigestRefsV1 {
  hasSpecLock: boolean;
  hasPatchPlan: boolean;
  hasPreview: boolean;
  hasReview: boolean;
  hasDecisionAck: boolean;
  hasEffect: boolean; // PR174 (optional)
  hasAttribution: boolean; // PR169 (optional)
  hasEvidenceLinked: boolean; // PR170 (optional)
}

/**
 * Spec change digest report (label-only)
 */
export interface SpecChangeDigestV1 {
  status: DigestStatus;
  time: DigestTimeLabel;

  // Most important: What is happening (label-only)
  headline: string[]; // e.g., ["PENDING_ACK", "HAS_PREVIEW", "HAS_REVIEW", "HAS_PATCHPLAN"]

  // "Why" and "What changes"
  why: string[]; // e.g., ["EVIDENCE_PRESENT", "BOTTLENECK_ORACLE_DOMINANT"]
  what: string[]; // e.g., ["PATCH_GATE_ORDER", "PATCH_PHASE_POLICY"]

  // Risks/concerns (label-only)
  risks: string[]; // e.g., ["RISK_PATCH_NOT_ALLOWED_PRESENT", "RISK_WORSENING_SIGNAL_PRESENT"]

  // Review/check summary (label-only)
  checklist: string[]; // From PR172
  rationale: string[]; // From PR172

  // Adoption decision material (not decision itself)
  suggestedNext: "ACK_OK" | "ACK_HOLD" | "ACK_REJECT" | "ACK_UNKNOWN";

  // Reference presence
  refs: DigestRefsV1;

  warnings: string[]; // label-only
}

/**
 * Digester input (loosely coupled)
 * Receives "sanitized label-only output" from each module
 */
export interface DigestInputV1 {
  // PR179 Spec Lock
  specLock?: {
    status?: string;
    hasActiveSpec?: boolean;
    hasPendingSpec?: boolean;
  };

  // PR168 patch plan (label-only assumed)
  patchPlan?: {
    proposalId?: string;
    priority?: string; // P0/P1/P2
    patchOps?: { kind: string; label?: string }[];
    decision?: string; // ADOPT/HOLD/REJECT/UNKNOWN
    compareSignals?: string[];
  };

  // PR171 preview
  preview?: {
    status?: string; // AVAILABLE/PARTIAL/ERROR
    readiness?: string; // REVIEWABLE/NOT_REVIEWABLE
    sections?: {
      title: string;
      before: string[];
      after: string[];
      notes: string[];
    }[];
    risks?: string[];
    evidence?: { kind?: string; strength?: string; label?: string }[];
    signals?: string[];
  };

  // PR172 review
  review?: {
    status?: string;
    checklist?: { id: string; status: string }[];
    decision?: string; // CANDIDATE_ADOPT/HOLD/REJECT
    rationale?: string[];
  };

  // PR173 decision ack (optional)
  decisionAck?: {
    decision?: string;
    reviewerKind?: string;
    reason?: string;
  };

  // PR174 effect (optional)
  effect?: {
    status?: string;
    headline?: string[];
  };

  // PR169 attribution / PR170 evidence (optional)
  attribution?: {
    bottlenecks?: string[];
    topPaths?: string[];
    topEdges?: string[];
  };

  warnings?: string[];
}
