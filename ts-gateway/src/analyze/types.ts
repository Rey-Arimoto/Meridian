/**
 * PR166: v1.4 Snapshot Analysis Helper v1 - Types
 *
 * Purpose:
 *   Define analysis result types for strategy improvement through
 *   deterministic analysis of snapshot logs (A/B/C pattern analysis).
 *
 * Constitutional Constraints:
 *   - READ-ONLY: Analysis reads snapshot logs only, no execution
 *   - Label-only: Normal output uses labels (numeric counts only in debug mode)
 *   - Defensive: Never throws, always returns result (even on error)
 *   - Fixed rules: No prediction, no optimization, no recommendations
 *
 * Analysis Categories:
 *   A) Frequency Analysis: Phase/stress/template/gate distribution
 *   B) Confusion Signals: Regime misidentification indicators
 *   C) Timing Analysis: Phase transition timing and stop reasons
 */

/**
 * Analysis status
 */
export type AnalysisStatus = "COMPLETE" | "PARTIAL" | "ERROR";

/**
 * Lag label (phase transition delay)
 */
export type LagLabel =
  | "LAG_NONE" // Immediate transition
  | "LAG_SHORT" // 1-3 ticks
  | "LAG_MEDIUM" // 4-10 ticks
  | "LAG_LONG" // 11+ ticks
  | "LAG_UNKNOWN"; // Cannot determine

/**
 * Stop reason category (label-only)
 */
export type StopReasonCategory =
  | "STOP_BY_PHASE_POLICY" // Stopped by phase escalation
  | "STOP_BY_GATE" // Stopped by gate block
  | "STOP_BY_POLICY_HARDSTOP" // Stopped by HardStop
  | "STOP_BY_DURATION" // Stopped by duration limit
  | "STOP_BY_BLOCK_STREAK" // Stopped by consecutive blocks
  | "STOP_UNKNOWN"; // Unknown stop reason

/**
 * Confusion signal type (label-only)
 */
export type ConfusionSignalType =
  | "CONFUSION_SHOCK_BUT_RISK_HIGH_FREQUENT" // UP_REVERSAL/DOWN_SHOCK with TPL_RISK_90 frequent
  | "CONFUSION_PRE_SHOCK_NO_TEMPLATE_SHIFT" // PRE_SHOCK but no template change
  | "CONFUSION_GATE_BLOCK_DOMINATES" // BLOCK dominates PASS
  | "NO_CONFUSION"; // No confusion detected

/**
 * Frequency item (label + count)
 *
 * NOTE: count is internal only, displayed only in debug mode
 */
export interface FrequencyItem {
  label: string; // Label value (e.g., "PHASE_NORMAL")
  count: number; // Count (internal, debug-only display)
  rank?: number; // Rank (optional)
}

/**
 * Frequency analysis result
 */
export interface FrequencyAnalysis {
  // Phase label distribution
  phaseLabels: FrequencyItem[];

  // Stress label distribution
  stressLabels: FrequencyItem[];

  // Template ID distribution
  templateIds: FrequencyItem[];

  // Gate decision distribution
  gateDecisions: FrequencyItem[];

  // Block reason ranking (top N)
  blockReasons: FrequencyItem[];
}

/**
 * Confusion signal result
 */
export interface ConfusionSignal {
  // Signal type
  type: ConfusionSignalType;

  // Active flag (true if signal fired)
  active: boolean;

  // Reasons (label-only)
  reasons: string[];

  // Details (label-only, optional)
  details?: {
    category?: string; // e.g., "ORACLE" / "IMPACT" / "SLIPPAGE"
    dominantLabel?: string;
  };
}

/**
 * Phase transition event
 */
export interface PhaseTransition {
  // From phase (label)
  from: string;

  // To phase (label)
  to: string;

  // Lag label (how long it took)
  lag: LagLabel;

  // Tick count (internal, debug-only display)
  tickCount: number;
}

/**
 * Stop reason breakdown
 */
export interface StopReasonBreakdown {
  // Category
  category: StopReasonCategory;

  // Count (internal, debug-only display)
  count: number;

  // Percentage label (debug-only)
  percentageLabel?: string;
}

/**
 * Timing analysis result
 */
export interface TimingAnalysis {
  // Phase transitions
  transitions: PhaseTransition[];

  // Stop reason breakdown
  stopReasons: StopReasonBreakdown[];
}

/**
 * Analysis result v1
 *
 * Purpose:
 *   Aggregate snapshot analysis for strategy improvement.
 *   Provides frequency, confusion signals, and timing analysis.
 *
 * Display:
 *   - Normal mode: label-only (no counts)
 *   - Debug mode (MERIDIAN_DEBUG=true): includes counts
 */
export interface AnalysisResultV1 {
  // Schema version
  version: "v1.0";

  // Analysis status
  status: AnalysisStatus;

  // Warnings (label-only)
  warnings: string[];

  // Snapshot count analyzed (internal, debug-only display)
  snapshotCount: number;

  // Frequency analysis
  frequency: FrequencyAnalysis;

  // Confusion signals
  confusionSignals: ConfusionSignal[];

  // Timing analysis
  timing: TimingAnalysis;
}

/**
 * Sanitized analysis result (for normal CLI display)
 *
 * Purpose:
 *   Analysis result with counts removed for label-only display.
 */
export interface SanitizedAnalysisResult {
  version: "v1.0";
  status: AnalysisStatus;
  warnings: string[];
  snapshotCountLabel: string; // "HAS_SNAPSHOTS" / "NO_SNAPSHOTS"

  // Frequency (labels only, no counts)
  frequency: {
    phaseLabels: string[];
    stressLabels: string[];
    templateIds: string[];
    gateDecisions: string[];
    blockReasons: string[];
  };

  // Confusion signals (label-only)
  confusionSignals: {
    type: ConfusionSignalType;
    active: boolean;
    reasons: string[];
  }[];

  // Timing (labels only, no tick counts)
  timing: {
    transitions: {
      from: string;
      to: string;
      lag: LagLabel;
    }[];
    stopReasons: StopReasonCategory[];
  };
}
