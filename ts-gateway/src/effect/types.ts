/**
 * PR174: v1.4 Patch Effectiveness Tracker v1 - Types
 *
 * Purpose:
 *   Type definitions for patch effectiveness tracking.
 *   Measures "did the adoption actually improve things" post-adoption.
 *
 * Constitutional Constraints:
 *   - READ-ONLY: Observation only (no automatic adoption/execution)
 *   - Fixed rules: Fixed thresholds (no learning/optimization)
 *   - Label-only: Display mode sanitizes numerics
 *   - Defensive: All types designed to handle missing/corrupt data
 */

/**
 * Effect Status
 *
 * - AVAILABLE: Complete effect report with all windows
 * - PARTIAL: Some windows missing but report valid
 * - ERROR: Report creation failed but returned safe fallback
 */
export type EffectStatus = "AVAILABLE" | "PARTIAL" | "ERROR";

/**
 * Effect Decision
 *
 * Overall effectiveness verdict based on fixed thresholds.
 *
 * - EFFECT_IMPROVED: Metrics improved post-adoption
 * - EFFECT_WORSENED: Metrics worsened post-adoption
 * - EFFECT_NO_CHANGE: No significant change detected
 * - EFFECT_MIXED: Some improved, some worsened
 * - EFFECT_UNKNOWN: Insufficient data to determine
 */
export type EffectDecision =
  | "EFFECT_IMPROVED"
  | "EFFECT_WORSENED"
  | "EFFECT_NO_CHANGE"
  | "EFFECT_MIXED"
  | "EFFECT_UNKNOWN";

/**
 * Window Label
 *
 * Time window identifier for Before/After snapshots.
 *
 * - WIN_BEFORE: Snapshots before adoption
 * - WIN_AFTER_SHORT: Short-term after adoption
 * - WIN_AFTER_MEDIUM: Medium-term after adoption
 * - WIN_AFTER_LONG: Long-term after adoption
 */
export type WindowLabel =
  | "WIN_BEFORE"
  | "WIN_AFTER_SHORT"
  | "WIN_AFTER_MEDIUM"
  | "WIN_AFTER_LONG";

/**
 * Effect Window Config
 *
 * Fixed configuration for snapshot window sizes.
 */
export interface EffectWindowConfig {
  /**
   * Snapshots to take before ack timestamp (default: 120)
   */
  beforeTail: number;

  /**
   * Snapshots in short-term after window (default: 60)
   */
  afterShort: number;

  /**
   * Snapshots in medium-term after window (default: 180)
   */
  afterMedium: number;

  /**
   * Snapshots in long-term after window (default: 600)
   */
  afterLong: number;
}

/**
 * Effect Counts
 *
 * Raw counts (numerics allowed internally, sanitized for display).
 */
export interface EffectCounts {
  /**
   * Total snapshots in window
   */
  nSnapshots: number;

  /**
   * Gate PASS count
   */
  nGatePass: number;

  /**
   * Gate BLOCK count
   */
  nGateBlock: number;

  /**
   * STOP count
   */
  nStop: number;
}

/**
 * Effect Rates
 *
 * Calculated rates (numerics allowed internally, sanitized for display).
 */
export interface EffectRates {
  /**
   * Pass rate (nGatePass / nSnapshots)
   */
  passRate?: number;

  /**
   * Block rate (nGateBlock / nSnapshots)
   */
  blockRate?: number;

  /**
   * Stop rate (nStop / nSnapshots)
   */
  stopRate?: number;
}

/**
 * Effect Top Labels
 *
 * Most common labels in window (label-only).
 */
export interface EffectTopLabels {
  /**
   * Most common phase
   */
  topPhase?: string;

  /**
   * Most common template
   */
  topTemplate?: string;

  /**
   * Most common block reason
   */
  topBlockReason?: string;

  /**
   * Most common stop category
   */
  topStopCategory?: string;
}

/**
 * Effect Window Summary
 *
 * Summary of one time window (Before/After).
 */
export interface EffectWindowSummary {
  /**
   * Window label
   */
  window: WindowLabel;

  /**
   * Window status
   */
  status: EffectStatus;

  /**
   * Raw counts
   */
  counts: EffectCounts;

  /**
   * Calculated rates
   */
  rates: EffectRates;

  /**
   * Top labels
   */
  tops: EffectTopLabels;

  /**
   * Confusion signals (from PR166, label-only)
   */
  confusionSignals: string[];

  /**
   * Bottlenecks (optional, label-only)
   */
  bottlenecks: string[];

  /**
   * Warnings (label-only)
   */
  warnings: string[];
}

/**
 * Effect Compare Signals
 *
 * Label-only comparison signals derived from fixed thresholds.
 */
export interface EffectCompareSignals {
  /**
   * Improved metrics (label-only)
   */
  improved: string[];

  /**
   * Worsened metrics (label-only)
   */
  worsened: string[];

  /**
   * Unchanged metrics (label-only)
   */
  unchanged: string[];

  /**
   * Unavailable metrics (label-only)
   */
  unavailable: string[];
}

/**
 * Patch Effect Report v1
 *
 * Complete effectiveness report for one adoption decision.
 *
 * Constitutional Constraints:
 * - READ-ONLY: Observation only (no automatic adoption)
 * - Fixed rules: Fixed thresholds (10% point change)
 * - Label-only: Display mode sanitizes numerics
 * - Defensive: Always valid, even on error
 */
export interface PatchEffectReportV1 {
  /**
   * Report kind identifier
   */
  kind: "PATCH_EFFECT_V1";

  /**
   * Report status
   */
  status: EffectStatus;

  /**
   * Decision ack reference
   */
  decisionAckRef: {
    proposalId?: string;
    decision?: string;
    reviewerKind?: string;
    timeLabel?: string;
  };

  /**
   * Time windows (includes BEFORE + AFTER windows)
   */
  windows: EffectWindowSummary[];

  /**
   * Compare signals
   */
  compare: EffectCompareSignals;

  /**
   * Overall effect decision
   */
  effectDecision: EffectDecision;

  /**
   * Rationale (label-only)
   */
  rationale: string[];

  /**
   * Warnings (label-only)
   */
  warnings: string[];

  /**
   * Timestamp (internal storage only)
   */
  ts: number;
}
