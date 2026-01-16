/**
 * PR167: v1.4 Improvement Proposal Generator v1 - Fixed Rules
 *
 * Purpose:
 *   Fixed trigger rules and proposal templates.
 *   All triggers and proposals are predetermined (no learning, no optimization).
 *
 * Constitutional Constraints:
 *   - Fixed rules: All thresholds and logic are predetermined
 *   - Deterministic: Same analysis → same proposals
 *   - Policy-first: P0 = degrade, P1 = policy restrict, P2 = observable
 *   - No predictions: Proposals based only on observed patterns
 */

import { AnalysisResultV1 } from "../analyze/types";
import {
  ImprovementProposalV1,
  ProposalId,
  ProposalPriority,
  ProposalCategory,
  TriggerId,
} from "./types";

/**
 * Trigger Rule
 *
 * Defines how to evaluate if a trigger is active.
 */
export interface TriggerRule {
  /**
   * Trigger ID
   */
  id: TriggerId;

  /**
   * Description (for debugging)
   */
  description: string;

  /**
   * Evaluate function
   *
   * @param analysis - Analysis result
   * @returns True if trigger is active
   */
  evaluate: (analysis: AnalysisResultV1) => boolean;
}

/**
 * Proposal Template
 *
 * Defines a fixed proposal with all details.
 */
export interface ProposalTemplate {
  /**
   * Proposal ID
   */
  id: ProposalId;

  /**
   * Priority
   */
  priority: ProposalPriority;

  /**
   * Category
   */
  category: ProposalCategory;

  /**
   * Title
   */
  title: string;

  /**
   * Rationale (why this proposal exists)
   */
  rationale: string[];

  /**
   * Expected effects
   */
  expected_effects: string[];

  /**
   * Side effects
   */
  side_effects: string[];

  /**
   * Safe guards
   */
  safe_guards: string[];

  /**
   * Applies when
   */
  applies_when: string;

  /**
   * Triggered by (which triggers activate this proposal)
   */
  triggered_by: TriggerId[];
}

/**
 * Fixed Trigger Rules
 *
 * All trigger rules are predetermined.
 */
export const TRIGGER_RULES: TriggerRule[] = [
  // Confusion signals (from PR166)
  {
    id: "TRG_GATE_BLOCK_DOMINATES",
    description: "Gate BLOCK dominates PASS (confusion signal active)",
    evaluate: (analysis) => {
      const signal = analysis.confusionSignals.find(
        (s) => s.type === "CONFUSION_GATE_BLOCK_DOMINATES"
      );
      return signal?.active === true;
    },
  },
  {
    id: "TRG_SHOCK_RISK90_OVERUSE",
    description: "SHOCK phases with TPL_RISK_90 frequent (confusion signal active)",
    evaluate: (analysis) => {
      const signal = analysis.confusionSignals.find(
        (s) => s.type === "CONFUSION_SHOCK_BUT_RISK_HIGH_FREQUENT"
      );
      return signal?.active === true;
    },
  },
  {
    id: "TRG_PRE_SHOCK_NO_SHIFT",
    description: "PRE_SHOCK without template shift (confusion signal active)",
    evaluate: (analysis) => {
      const signal = analysis.confusionSignals.find(
        (s) => s.type === "CONFUSION_PRE_SHOCK_NO_TEMPLATE_SHIFT"
      );
      return signal?.active === true;
    },
  },

  // Frequency patterns
  {
    id: "TRG_ORACLE_STALE_TOP",
    description: "ORACLE_STALE is top block reason",
    evaluate: (analysis) => {
      const topBlockReason = analysis.frequency.blockReasons[0];
      return (
        topBlockReason?.label?.includes("ORACLE") &&
        topBlockReason?.label?.includes("STALE")
      );
    },
  },
  {
    id: "TRG_IMPACT_HIGH_TOP",
    description: "IMPACT_HIGH is top block reason",
    evaluate: (analysis) => {
      const topBlockReason = analysis.frequency.blockReasons[0];
      return (
        topBlockReason?.label?.includes("IMPACT") &&
        topBlockReason?.label?.includes("HIGH")
      );
    },
  },
  {
    id: "TRG_SLIPPAGE_HIGH_TOP",
    description: "SLIPPAGE_HIGH is top block reason",
    evaluate: (analysis) => {
      const topBlockReason = analysis.frequency.blockReasons[0];
      return (
        topBlockReason?.label?.includes("SLIPPAGE") &&
        topBlockReason?.label?.includes("HIGH")
      );
    },
  },
  {
    id: "TRG_DRIFT_HIGH_TOP",
    description: "DRIFT_HIGH is top block reason",
    evaluate: (analysis) => {
      const topBlockReason = analysis.frequency.blockReasons[0];
      return (
        topBlockReason?.label?.includes("DRIFT") &&
        topBlockReason?.label?.includes("HIGH")
      );
    },
  },
  {
    id: "TRG_COOLDOWN_TOP",
    description: "COOLDOWN is top block reason",
    evaluate: (analysis) => {
      const topBlockReason = analysis.frequency.blockReasons[0];
      return topBlockReason?.label?.includes("COOLDOWN");
    },
  },

  // Timing patterns
  {
    id: "TRG_PHASE_ESCALATION_FREQUENT",
    description: "Phase escalation blocks are frequent (in top 3)",
    evaluate: (analysis) => {
      const top3 = analysis.frequency.blockReasons.slice(0, 3);
      return top3.some((b) => b.label?.includes("PHASE_ESCALATION"));
    },
  },
  {
    id: "TRG_TRANSITIONS_FREQUENT",
    description: "Phase transitions are frequent (LAG_SHORT majority)",
    evaluate: (analysis) => {
      const shortLags = analysis.timing.transitions.filter(
        (t) => t.lag === "LAG_SHORT"
      );
      return (
        shortLags.length > 0 &&
        shortLags.length > analysis.timing.transitions.length * 0.5
      );
    },
  },
  {
    id: "TRG_LAG_LONG_FREQUENT",
    description: "LAG_LONG transitions are frequent",
    evaluate: (analysis) => {
      const longLags = analysis.timing.transitions.filter(
        (t) => t.lag === "LAG_LONG"
      );
      return (
        longLags.length > 0 &&
        longLags.length > analysis.timing.transitions.length * 0.2
      );
    },
  },
  {
    id: "TRG_HARDSTOP_FREQUENT",
    description: "HardStop is frequent (in top 3 stop reasons)",
    evaluate: (analysis) => {
      const hardStopReason = analysis.timing.stopReasons.find(
        (s) => s.category === "STOP_BY_POLICY_HARDSTOP"
      );
      return (
        hardStopReason !== undefined &&
        analysis.timing.stopReasons.indexOf(hardStopReason) < 3
      );
    },
  },
];

/**
 * Fixed Proposal Templates
 *
 * All proposal templates are predetermined.
 */
export const PROPOSAL_TEMPLATES: ProposalTemplate[] = [
  // P0: Gate degradation proposals
  {
    id: "P0_REDUCE_ORACLE_STALE_BLOCKS_DEGRADE",
    priority: "P0",
    category: "GATE_POLICY",
    title: "DEGRADE_ORACLE_STALE_THRESHOLD",
    rationale: [
      "GATE_BLOCK_DOMINATES_WITH_ORACLE_CATEGORY",
      "ORACLE_STALE_IS_TOP_BLOCK_REASON",
      "REDUCING_STALE_THRESHOLD_MAY_INCREASE_PASS_RATIO",
    ],
    expected_effects: [
      "REDUCE_ORACLE_STALE_BLOCKS",
      "INCREASE_GATE_PASS_RATIO",
      "ALLOW_MORE_RECENT_ORACLE_DATA",
    ],
    side_effects: [
      "MAY_INCREASE_STALE_DATA_RISK",
      "MAY_DEGRADE_EXECUTION_QUALITY",
    ],
    safe_guards: [
      "MONITOR_ORACLE_AGE_DISTRIBUTION",
      "TEST_IN_DRY_RUN_MODE",
      "SET_MINIMUM_THRESHOLD",
    ],
    applies_when:
      "WHEN_GATE_BLOCK_RATIO_HIGH_AND_ORACLE_STALE_TOP_AND_ORACLE_CATEGORY",
    triggered_by: ["TRG_GATE_BLOCK_DOMINATES", "TRG_ORACLE_STALE_TOP"],
  },
  {
    id: "P0_REDUCE_IMPACT_BLOCKS_DEGRADE",
    priority: "P0",
    category: "GATE_POLICY",
    title: "DEGRADE_IMPACT_HIGH_THRESHOLD",
    rationale: [
      "GATE_BLOCK_DOMINATES_WITH_IMPACT_CATEGORY",
      "IMPACT_HIGH_IS_TOP_BLOCK_REASON",
      "REDUCING_IMPACT_THRESHOLD_MAY_INCREASE_PASS_RATIO",
    ],
    expected_effects: [
      "REDUCE_IMPACT_HIGH_BLOCKS",
      "INCREASE_GATE_PASS_RATIO",
      "ALLOW_HIGHER_IMPACT_TRADES",
    ],
    side_effects: [
      "MAY_INCREASE_MARKET_IMPACT",
      "MAY_DEGRADE_EXECUTION_QUALITY",
    ],
    safe_guards: [
      "MONITOR_ACTUAL_IMPACT_POST_EXECUTION",
      "TEST_IN_DRY_RUN_MODE",
      "SET_MAXIMUM_THRESHOLD",
    ],
    applies_when:
      "WHEN_GATE_BLOCK_RATIO_HIGH_AND_IMPACT_HIGH_TOP_AND_IMPACT_CATEGORY",
    triggered_by: ["TRG_GATE_BLOCK_DOMINATES", "TRG_IMPACT_HIGH_TOP"],
  },
  {
    id: "P0_REDUCE_SLIPPAGE_BLOCKS_DEGRADE",
    priority: "P0",
    category: "GATE_POLICY",
    title: "DEGRADE_SLIPPAGE_HIGH_THRESHOLD",
    rationale: [
      "GATE_BLOCK_DOMINATES_WITH_SLIPPAGE_CATEGORY",
      "SLIPPAGE_HIGH_IS_TOP_BLOCK_REASON",
      "REDUCING_SLIPPAGE_THRESHOLD_MAY_INCREASE_PASS_RATIO",
    ],
    expected_effects: [
      "REDUCE_SLIPPAGE_HIGH_BLOCKS",
      "INCREASE_GATE_PASS_RATIO",
      "ALLOW_HIGHER_SLIPPAGE_TRADES",
    ],
    side_effects: [
      "MAY_INCREASE_SLIPPAGE_LOSS",
      "MAY_DEGRADE_EXECUTION_QUALITY",
    ],
    safe_guards: [
      "MONITOR_ACTUAL_SLIPPAGE_POST_EXECUTION",
      "TEST_IN_DRY_RUN_MODE",
      "SET_MAXIMUM_THRESHOLD",
    ],
    applies_when:
      "WHEN_GATE_BLOCK_RATIO_HIGH_AND_SLIPPAGE_HIGH_TOP_AND_SLIPPAGE_CATEGORY",
    triggered_by: ["TRG_GATE_BLOCK_DOMINATES", "TRG_SLIPPAGE_HIGH_TOP"],
  },
  {
    id: "P0_REDUCE_DRIFT_BLOCKS_DEGRADE",
    priority: "P0",
    category: "GATE_POLICY",
    title: "DEGRADE_DRIFT_HIGH_THRESHOLD",
    rationale: [
      "GATE_BLOCK_DOMINATES_WITH_DRIFT_CATEGORY",
      "DRIFT_HIGH_IS_TOP_BLOCK_REASON",
      "REDUCING_DRIFT_THRESHOLD_MAY_INCREASE_PASS_RATIO",
    ],
    expected_effects: [
      "REDUCE_DRIFT_HIGH_BLOCKS",
      "INCREASE_GATE_PASS_RATIO",
      "ALLOW_HIGHER_DRIFT_TOLERANCE",
    ],
    side_effects: ["MAY_INCREASE_DRIFT_RISK", "MAY_DEGRADE_EXECUTION_QUALITY"],
    safe_guards: [
      "MONITOR_DRIFT_DISTRIBUTION",
      "TEST_IN_DRY_RUN_MODE",
      "SET_MAXIMUM_THRESHOLD",
    ],
    applies_when:
      "WHEN_GATE_BLOCK_RATIO_HIGH_AND_DRIFT_HIGH_TOP_AND_DRIFT_CATEGORY",
    triggered_by: ["TRG_GATE_BLOCK_DOMINATES", "TRG_DRIFT_HIGH_TOP"],
  },
  {
    id: "P0_REDUCE_COOLDOWN_BLOCKS_DEGRADE",
    priority: "P0",
    category: "COOLDOWN_POLICY",
    title: "DEGRADE_COOLDOWN_DURATION",
    rationale: [
      "GATE_BLOCK_DOMINATES_WITH_COOLDOWN_CATEGORY",
      "COOLDOWN_IS_TOP_BLOCK_REASON",
      "REDUCING_COOLDOWN_DURATION_MAY_INCREASE_PASS_RATIO",
    ],
    expected_effects: [
      "REDUCE_COOLDOWN_BLOCKS",
      "INCREASE_GATE_PASS_RATIO",
      "ALLOW_FASTER_RESUME",
    ],
    side_effects: [
      "MAY_INCREASE_CONSECUTIVE_EXECUTION_RISK",
      "MAY_REDUCE_OBSERVATION_TIME",
    ],
    safe_guards: [
      "MONITOR_BLOCK_STREAK_FREQUENCY",
      "TEST_IN_DRY_RUN_MODE",
      "SET_MINIMUM_COOLDOWN",
    ],
    applies_when:
      "WHEN_GATE_BLOCK_RATIO_HIGH_AND_COOLDOWN_TOP_AND_COOLDOWN_CATEGORY",
    triggered_by: ["TRG_GATE_BLOCK_DOMINATES", "TRG_COOLDOWN_TOP"],
  },

  // P1: Template policy proposals
  {
    id: "P1_SHOCK_RISK90_OVERUSE_TEMPLATE_POLICY_RESTRICT",
    priority: "P1",
    category: "TEMPLATE_POLICY",
    title: "RESTRICT_TPL_RISK_90_IN_SHOCK_PHASES",
    rationale: [
      "SHOCK_PHASES_WITH_TPL_RISK_90_FREQUENT",
      "HIGH_RISK_TEMPLATE_IN_SHOCK_IS_CONFUSION",
      "RESTRICTING_TPL_RISK_90_MAY_REDUCE_CONFUSION",
    ],
    expected_effects: [
      "REDUCE_TPL_RISK_90_IN_SHOCK",
      "INCREASE_TEMPLATE_CONSISTENCY",
      "REDUCE_CONFUSION_SIGNAL",
    ],
    side_effects: [
      "MAY_REDUCE_AVAILABLE_TEMPLATE_OPTIONS",
      "MAY_REQUIRE_NEW_TEMPLATE_LOGIC",
    ],
    safe_guards: [
      "MONITOR_TEMPLATE_DISTRIBUTION",
      "TEST_IN_DRY_RUN_MODE",
      "ENSURE_ALTERNATIVE_TEMPLATES_EXIST",
    ],
    applies_when:
      "WHEN_SHOCK_PHASES_WITH_TPL_RISK_90_RATIO_ABOVE_THRESHOLD",
    triggered_by: ["TRG_SHOCK_RISK90_OVERUSE"],
  },
  {
    id: "P1_PRE_SHOCK_NO_SHIFT_TEMPLATE_POLICY_TRIGGER",
    priority: "P1",
    category: "TEMPLATE_POLICY",
    title: "TRIGGER_TEMPLATE_SHIFT_IN_PRE_SHOCK",
    rationale: [
      "PRE_SHOCK_WITHOUT_TEMPLATE_CHANGE",
      "SINGLE_TEMPLATE_DOMINANT_IN_PRE_SHOCK",
      "TRIGGERING_TEMPLATE_SHIFT_MAY_REDUCE_CONFUSION",
    ],
    expected_effects: [
      "INCREASE_TEMPLATE_SHIFT_IN_PRE_SHOCK",
      "REDUCE_SINGLE_TEMPLATE_DOMINANCE",
      "REDUCE_CONFUSION_SIGNAL",
    ],
    side_effects: [
      "MAY_INCREASE_TEMPLATE_TRANSITION_FREQUENCY",
      "MAY_REQUIRE_NEW_TRIGGER_LOGIC",
    ],
    safe_guards: [
      "MONITOR_TEMPLATE_SHIFT_FREQUENCY",
      "TEST_IN_DRY_RUN_MODE",
      "ENSURE_SHIFT_LOGIC_IS_DETERMINISTIC",
    ],
    applies_when:
      "WHEN_PRE_SHOCK_EXISTS_BUT_SINGLE_TEMPLATE_DOMINATES",
    triggered_by: ["TRG_PRE_SHOCK_NO_SHIFT"],
  },

  // P1: Phase policy proposals
  {
    id: "P1_PHASE_ESCALATION_DOMINATES_PHASE_POLICY_REVIEW",
    priority: "P1",
    category: "PHASE_POLICY",
    title: "REVIEW_PHASE_ESCALATION_POLICY",
    rationale: [
      "PHASE_ESCALATION_BLOCKS_FREQUENT",
      "PHASE_POLICY_MAY_BE_TOO_STRICT",
      "REVIEWING_ESCALATION_POLICY_MAY_REDUCE_BLOCKS",
    ],
    expected_effects: [
      "REDUCE_PHASE_ESCALATION_BLOCKS",
      "INCREASE_PHASE_POLICY_FLEXIBILITY",
      "ALLOW_MORE_ESCALATION_SCENARIOS",
    ],
    side_effects: [
      "MAY_INCREASE_ESCALATION_RISK",
      "MAY_REQUIRE_POLICY_REDESIGN",
    ],
    safe_guards: [
      "MONITOR_ESCALATION_FREQUENCY",
      "TEST_IN_DRY_RUN_MODE",
      "ENSURE_ESCALATION_LOGIC_IS_SOUND",
    ],
    applies_when:
      "WHEN_PHASE_ESCALATION_BLOCKS_IN_TOP_3_BLOCK_REASONS",
    triggered_by: ["TRG_PHASE_ESCALATION_FREQUENT"],
  },

  // P1: Gate policy proposals
  {
    id: "P1_GATE_BLOCK_DOMINATES_GATE_POLICY_REVIEW",
    priority: "P1",
    category: "GATE_POLICY",
    title: "REVIEW_GATE_THRESHOLDS",
    rationale: [
      "GATE_BLOCK_DOMINATES_PASS",
      "GATE_POLICY_MAY_BE_TOO_STRICT",
      "REVIEWING_GATE_THRESHOLDS_MAY_INCREASE_PASS_RATIO",
    ],
    expected_effects: [
      "INCREASE_GATE_PASS_RATIO",
      "REDUCE_BLOCK_DOMINANCE",
      "IMPROVE_GATE_BALANCE",
    ],
    side_effects: [
      "MAY_INCREASE_EXECUTION_RISK",
      "MAY_REQUIRE_THRESHOLD_RECALIBRATION",
    ],
    safe_guards: [
      "MONITOR_GATE_DECISION_DISTRIBUTION",
      "TEST_IN_DRY_RUN_MODE",
      "ENSURE_MINIMUM_THRESHOLDS",
    ],
    applies_when:
      "WHEN_GATE_BLOCK_RATIO_ABOVE_50_PERCENT",
    triggered_by: ["TRG_GATE_BLOCK_DOMINATES"],
  },

  // P2: Observable improvements
  {
    id: "P2_FREQUENT_TRANSITIONS_OBSERVABLE_LOG",
    priority: "P2",
    category: "OBSERVABLE",
    title: "LOG_FREQUENT_PHASE_TRANSITIONS",
    rationale: [
      "PHASE_TRANSITIONS_FREQUENT_WITH_SHORT_LAG",
      "FREQUENT_TRANSITIONS_MAY_INDICATE_INSTABILITY",
      "LOGGING_TRANSITIONS_MAY_IMPROVE_OBSERVABILITY",
    ],
    expected_effects: [
      "INCREASE_TRANSITION_OBSERVABILITY",
      "ENABLE_TRANSITION_PATTERN_ANALYSIS",
      "IMPROVE_DEBUGGING",
    ],
    side_effects: ["MAY_INCREASE_LOG_VOLUME", "MAY_REQUIRE_LOG_ROTATION"],
    safe_guards: [
      "MONITOR_LOG_SIZE",
      "SET_LOG_ROTATION_POLICY",
      "USE_STRUCTURED_LOGGING",
    ],
    applies_when:
      "WHEN_SHORT_LAG_TRANSITIONS_ABOVE_50_PERCENT",
    triggered_by: ["TRG_TRANSITIONS_FREQUENT"],
  },
  {
    id: "P2_LAG_LONG_OBSERVABLE_LOG",
    priority: "P2",
    category: "OBSERVABLE",
    title: "LOG_LAG_LONG_TRANSITIONS",
    rationale: [
      "LAG_LONG_TRANSITIONS_FREQUENT",
      "LONG_LAG_MAY_INDICATE_SLOW_RESPONSE",
      "LOGGING_LONG_LAG_MAY_IMPROVE_OBSERVABILITY",
    ],
    expected_effects: [
      "INCREASE_LAG_OBSERVABILITY",
      "ENABLE_LATENCY_ANALYSIS",
      "IMPROVE_DEBUGGING",
    ],
    side_effects: ["MAY_INCREASE_LOG_VOLUME", "MAY_REQUIRE_LOG_ROTATION"],
    safe_guards: [
      "MONITOR_LOG_SIZE",
      "SET_LOG_ROTATION_POLICY",
      "USE_STRUCTURED_LOGGING",
    ],
    applies_when:
      "WHEN_LONG_LAG_TRANSITIONS_ABOVE_20_PERCENT",
    triggered_by: ["TRG_LAG_LONG_FREQUENT"],
  },
  {
    id: "P2_HARDSTOP_FREQUENT_OBSERVABLE_LOG",
    priority: "P2",
    category: "OBSERVABLE",
    title: "LOG_HARDSTOP_ACTIVATIONS",
    rationale: [
      "HARDSTOP_ACTIVATIONS_FREQUENT",
      "FREQUENT_HARDSTOP_MAY_INDICATE_POLICY_ISSUE",
      "LOGGING_HARDSTOP_MAY_IMPROVE_OBSERVABILITY",
    ],
    expected_effects: [
      "INCREASE_HARDSTOP_OBSERVABILITY",
      "ENABLE_POLICY_ANALYSIS",
      "IMPROVE_DEBUGGING",
    ],
    side_effects: ["MAY_INCREASE_LOG_VOLUME", "MAY_REQUIRE_LOG_ROTATION"],
    safe_guards: [
      "MONITOR_LOG_SIZE",
      "SET_LOG_ROTATION_POLICY",
      "USE_STRUCTURED_LOGGING",
    ],
    applies_when:
      "WHEN_HARDSTOP_IN_TOP_3_STOP_REASONS",
    triggered_by: ["TRG_HARDSTOP_FREQUENT"],
  },
];

/**
 * Get proposals for active triggers
 *
 * @param activeTriggers - Active trigger IDs
 * @returns Proposals that match active triggers
 */
export function getProposalsForTriggers(
  activeTriggers: TriggerId[]
): ImprovementProposalV1[] {
  const proposals: ImprovementProposalV1[] = [];

  for (const template of PROPOSAL_TEMPLATES) {
    // Check if any of the proposal's triggers are active
    const hasActiveTrigger = template.triggered_by.some((triggerId) =>
      activeTriggers.includes(triggerId)
    );

    if (hasActiveTrigger) {
      proposals.push({
        id: template.id,
        priority: template.priority,
        category: template.category,
        title: template.title,
        rationale: template.rationale,
        expected_effects: template.expected_effects,
        side_effects: template.side_effects,
        safe_guards: template.safe_guards,
        applies_when: template.applies_when,
        triggered_by: template.triggered_by.filter((t) =>
          activeTriggers.includes(t)
        ),
        evidence: [], // PR170: Evidence will be attached by proposer.ts
      });
    }
  }

  return proposals;
}
