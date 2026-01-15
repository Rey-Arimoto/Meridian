/**
 * PR167: v1.4 Improvement Proposal Generator v1 - Types
 *
 * Purpose:
 *   Generate fixed-rule improvement proposals from analysis results.
 *   These proposals are READ-ONLY suggestions based on deterministic triggers.
 *
 * Constitutional Constraints:
 *   - READ-ONLY: Proposals are suggestions, not actions
 *   - Fixed rules: All triggers and proposals are predetermined
 *   - Policy-first: P0 = degradation policy, P1 = template/gate policy, P2 = observable improvements
 *   - No predictions: Proposals based only on observed patterns
 *   - Label-only: Normal mode uses labels (no counts in proposals)
 */

/**
 * Proposal Priority
 *
 * P0 = Degrade policy (highest priority)
 * P1 = Template/Gate policy
 * P2 = Observable improvement
 * UNKNOWN = Fallback
 */
export type ProposalPriority = "P0" | "P1" | "P2" | "UNKNOWN";

/**
 * Proposal Category
 *
 * Categories align with Meridian's constitutional structure:
 * - GATE_POLICY: Gate thresholds and degradation
 * - TEMPLATE_POLICY: Risk template selection logic
 * - PHASE_POLICY: Shock phase escalation rules
 * - COOLDOWN_POLICY: Cooldown duration/behavior
 * - HARDSTOP_POLICY: HardStop triggers
 * - OBSERVABLE: Non-policy improvements (monitoring, logging)
 * - UNKNOWN: Fallback
 */
export type ProposalCategory =
  | "GATE_POLICY"
  | "TEMPLATE_POLICY"
  | "PHASE_POLICY"
  | "COOLDOWN_POLICY"
  | "HARDSTOP_POLICY"
  | "OBSERVABLE"
  | "UNKNOWN";

/**
 * Proposal ID
 *
 * Fixed proposal IDs (predetermined list).
 * Format: {Priority}_{Action}_{Reason}_{Target}
 *
 * P0 proposals: Degrade gate thresholds to reduce blocks
 * P1 proposals: Template/gate policy restrictions
 * P2 proposals: Observable improvements
 */
export type ProposalId =
  // P0: Gate degradation (reduce blocks)
  | "P0_REDUCE_ORACLE_STALE_BLOCKS_DEGRADE"
  | "P0_REDUCE_IMPACT_BLOCKS_DEGRADE"
  | "P0_REDUCE_SLIPPAGE_BLOCKS_DEGRADE"
  | "P0_REDUCE_DRIFT_BLOCKS_DEGRADE"
  | "P0_REDUCE_COOLDOWN_BLOCKS_DEGRADE"
  // P1: Template policy (reduce confusion)
  | "P1_SHOCK_RISK90_OVERUSE_TEMPLATE_POLICY_RESTRICT"
  | "P1_PRE_SHOCK_NO_SHIFT_TEMPLATE_POLICY_TRIGGER"
  // P1: Phase policy
  | "P1_PHASE_ESCALATION_DOMINATES_PHASE_POLICY_REVIEW"
  // P1: Gate policy
  | "P1_GATE_BLOCK_DOMINATES_GATE_POLICY_REVIEW"
  // P2: Observable improvements
  | "P2_FREQUENT_TRANSITIONS_OBSERVABLE_LOG"
  | "P2_LAG_LONG_OBSERVABLE_LOG"
  | "P2_HARDSTOP_FREQUENT_OBSERVABLE_LOG"
  // Unknown
  | "PROPOSAL_UNKNOWN";

/**
 * Trigger ID
 *
 * Fixed triggers that activate proposals.
 * Each trigger maps to one or more proposals.
 */
export type TriggerId =
  // Confusion signals from PR166
  | "TRG_GATE_BLOCK_DOMINATES"
  | "TRG_SHOCK_RISK90_OVERUSE"
  | "TRG_PRE_SHOCK_NO_SHIFT"
  // Timing patterns
  | "TRG_PHASE_ESCALATION_FREQUENT"
  | "TRG_TRANSITIONS_FREQUENT"
  | "TRG_LAG_LONG_FREQUENT"
  | "TRG_HARDSTOP_FREQUENT"
  // Frequency patterns
  | "TRG_ORACLE_STALE_TOP"
  | "TRG_IMPACT_HIGH_TOP"
  | "TRG_SLIPPAGE_HIGH_TOP"
  | "TRG_DRIFT_HIGH_TOP"
  | "TRG_COOLDOWN_TOP"
  // Fallback
  | "TRG_UNKNOWN";

/**
 * Improvement Proposal v1
 *
 * Fixed-rule proposal generated from analysis results.
 * All fields are label-only (no numerics in normal mode).
 */
export interface ImprovementProposalV1 {
  /**
   * Proposal ID (fixed from ProposalId type)
   */
  id: ProposalId;

  /**
   * Priority (P0 > P1 > P2)
   */
  priority: ProposalPriority;

  /**
   * Category (policy or observable)
   */
  category: ProposalCategory;

  /**
   * Title (label-only, no numerics)
   *
   * Example: "DEGRADE_ORACLE_STALE_THRESHOLD"
   */
  title: string;

  /**
   * Rationale (why this proposal exists)
   *
   * Label-only explanation.
   * Example: "GATE_BLOCK_DOMINATES_WITH_ORACLE_CATEGORY"
   */
  rationale: string[];

  /**
   * Expected effects (what should happen)
   *
   * Label-only effects.
   * Example: "REDUCE_ORACLE_STALE_BLOCKS", "INCREASE_PASS_RATIO"
   */
  expected_effects: string[];

  /**
   * Side effects (potential risks)
   *
   * Label-only side effects.
   * Example: "MAY_INCREASE_SLIPPAGE_RISK", "MAY_DEGRADE_EXECUTION_QUALITY"
   */
  side_effects: string[];

  /**
   * Safe guards (how to mitigate side effects)
   *
   * Label-only safe guards.
   * Example: "MONITOR_SLIPPAGE_IMPACT", "TEST_IN_DRY_RUN_MODE"
   */
  safe_guards: string[];

  /**
   * Applies when (trigger conditions)
   *
   * Label-only trigger summary.
   * Example: "WHEN_GATE_BLOCK_RATIO_HIGH_AND_ORACLE_CATEGORY_TOP"
   */
  applies_when: string;

  /**
   * Triggered by (trigger IDs)
   *
   * Which fixed triggers activated this proposal.
   */
  triggered_by: TriggerId[];
}

/**
 * Propose Result v1
 *
 * Result of proposal generation.
 */
export interface ProposeResultV1 {
  /**
   * Version (always "v1.0")
   */
  version: "v1.0";

  /**
   * Status
   *
   * - AVAILABLE: Proposals generated successfully
   * - PARTIAL: Some proposals could not be generated
   * - NO_PROPOSALS: No proposals (no triggers activated)
   * - ERROR: Fatal error
   */
  status: "AVAILABLE" | "PARTIAL" | "NO_PROPOSALS" | "ERROR";

  /**
   * Warnings (non-fatal issues)
   */
  warnings: string[];

  /**
   * Proposals (sorted by priority: P0 > P1 > P2)
   */
  proposals: ImprovementProposalV1[];

  /**
   * Timestamp (when proposals were generated)
   */
  ts: number;

  /**
   * Analysis snapshot count label (for context)
   *
   * Example: "HAS_SNAPSHOTS", "INSUFFICIENT_SNAPSHOTS"
   */
  snapshotCountLabel?: string;
}

/**
 * Proposal Status
 *
 * Status of proposal generation.
 */
export type ProposeStatus = "AVAILABLE" | "PARTIAL" | "NO_PROPOSALS" | "ERROR";
