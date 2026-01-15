/**
 * PR166: v1.4 Snapshot Analysis Helper v1 - Guards
 *
 * Purpose:
 *   Sanitize analysis results for label-only display (normal mode).
 *   Allow numeric counts only in debug mode (MERIDIAN_DEBUG=true).
 *
 * Constitutional Constraints:
 *   - Normal mode: label-only (no counts, no numerics)
 *   - Debug mode: allows counts (but not addresses/secrets)
 *   - Always sanitize: token literals, trading vocab, prescriptive language
 */

import {
  AnalysisResultV1,
  SanitizedAnalysisResult,
  ConfusionSignalType,
  StopReasonCategory,
} from "./types";

/**
 * Forbidden patterns (same as PR164/165)
 */
const FORBIDDEN_PATTERNS = [
  // Token literals
  /\bwBTC\b/gi,
  /\bUSDC\b/gi,
  /\bSUI\b/gi,
  /\btoken\b/gi,

  // Trading vocabulary
  /\bbuy\b/gi,
  /\bsell\b/gi,
  /\bswap\b/gi,
  /\btrade\b/gi,
  /\bexecute\b/gi,
  /\bsign\b/gi,
  /\btransfer\b/gi,

  // Prescriptive language
  /\bshould\b/gi,
  /\bmust\b/gi,
  /\brecommend\b/gi,
  /\badvise\b/gi,

  // Address patterns (always forbidden, even in debug mode)
  /0x[a-fA-F0-9]{40}/g,
  /0x[a-fA-F0-9]{64}/g,
];

/**
 * Check if debug mode is enabled
 *
 * @returns True if MERIDIAN_DEBUG=true
 */
export function isDebugMode(): boolean {
  return process.env.MERIDIAN_DEBUG === "true";
}

/**
 * Sanitize a single label value
 *
 * @param value - Label value to sanitize
 * @returns Sanitized value (REDACTED if forbidden pattern found)
 */
export function sanitizeAnalysisLabel(value: string): string {
  if (!value) return value;

  for (const pattern of FORBIDDEN_PATTERNS) {
    if (pattern.test(value)) {
      return "REDACTED";
    }
  }

  return value;
}

/**
 * Sanitize analysis result for display
 *
 * Purpose:
 *   Remove counts and numerics for label-only display (normal mode).
 *   In debug mode, counts are preserved.
 *
 * @param analysis - Raw analysis result
 * @param debugMode - Debug mode flag (default: false)
 * @returns Sanitized analysis result
 */
export function sanitizeAnalysisForDisplay(
  analysis: AnalysisResultV1,
  debugMode: boolean = false
): SanitizedAnalysisResult {
  // Sanitize warnings
  const sanitizedWarnings = analysis.warnings.map(sanitizeAnalysisLabel);

  // Snapshot count label
  const snapshotCountLabel =
    analysis.snapshotCount > 0 ? "HAS_SNAPSHOTS" : "NO_SNAPSHOTS";

  // Frequency (extract labels only, no counts)
  const frequency = {
    phaseLabels: analysis.frequency.phaseLabels.map((item) =>
      sanitizeAnalysisLabel(item.label)
    ),
    stressLabels: analysis.frequency.stressLabels.map((item) =>
      sanitizeAnalysisLabel(item.label)
    ),
    templateIds: analysis.frequency.templateIds.map((item) =>
      sanitizeAnalysisLabel(item.label)
    ),
    gateDecisions: analysis.frequency.gateDecisions.map((item) =>
      sanitizeAnalysisLabel(item.label)
    ),
    blockReasons: analysis.frequency.blockReasons.map((item) =>
      sanitizeAnalysisLabel(item.label)
    ),
  };

  // Confusion signals (label-only)
  const confusionSignals = analysis.confusionSignals.map((signal) => ({
    type: signal.type,
    active: signal.active,
    reasons: signal.reasons.map(sanitizeAnalysisLabel),
  }));

  // Timing (remove tick counts)
  const timing = {
    transitions: analysis.timing.transitions.map((t) => ({
      from: sanitizeAnalysisLabel(t.from),
      to: sanitizeAnalysisLabel(t.to),
      lag: t.lag,
      // tickCount removed (not displayed in normal mode)
    })),
    stopReasons: analysis.timing.stopReasons.map((sr) => sr.category),
  };

  return {
    version: analysis.version,
    status: analysis.status,
    warnings: sanitizedWarnings,
    snapshotCountLabel,
    frequency,
    confusionSignals,
    timing,
  };
}

/**
 * Format analysis result as CLI lines
 *
 * Purpose:
 *   Format analysis for CLI display (label-only in normal mode).
 *
 * @param sanitized - Sanitized analysis result
 * @param debugMode - Debug mode flag (for including counts)
 * @param rawAnalysis - Raw analysis (for counts in debug mode)
 * @returns Formatted string lines
 */
export function formatAnalysisLabelOnlyLines(
  sanitized: SanitizedAnalysisResult,
  debugMode: boolean = false,
  rawAnalysis?: AnalysisResultV1
): string[] {
  const lines: string[] = [];

  // Header
  lines.push(`=== Meridian Snapshot Analysis ===\n`);
  lines.push(`Status: ${sanitized.status}`);

  // Snapshot count (label-only in normal mode, numeric in debug mode)
  if (debugMode && rawAnalysis) {
    lines.push(`Snapshots: ${rawAnalysis.snapshotCount}`);
  } else {
    lines.push(`Snapshots: ${sanitized.snapshotCountLabel}`);
  }

  if (sanitized.warnings.length > 0) {
    lines.push(`Warnings: ${sanitized.warnings.join(", ")}`);
  }

  lines.push("");

  // Frequency Analysis
  lines.push("=== Frequency Analysis ===");

  if (sanitized.frequency.phaseLabels.length > 0) {
    lines.push(`Phase Labels: ${sanitized.frequency.phaseLabels.join(", ")}`);
  }

  if (sanitized.frequency.stressLabels.length > 0) {
    lines.push(`Stress Labels: ${sanitized.frequency.stressLabels.join(", ")}`);
  }

  if (sanitized.frequency.templateIds.length > 0) {
    lines.push(`Template IDs: ${sanitized.frequency.templateIds.join(", ")}`);
  }

  if (sanitized.frequency.gateDecisions.length > 0) {
    lines.push(`Gate Decisions: ${sanitized.frequency.gateDecisions.join(", ")}`);
  }

  if (sanitized.frequency.blockReasons.length > 0) {
    lines.push(`Block Reasons (Top): ${sanitized.frequency.blockReasons.slice(0, 5).join(", ")}`);
  }

  lines.push("");

  // Confusion Signals
  lines.push("=== Confusion Signals ===");

  const activeSignals = sanitized.confusionSignals.filter((s) => s.active);

  if (activeSignals.length === 0) {
    lines.push("NO_CONFUSION");
  } else {
    for (const signal of activeSignals) {
      lines.push(`${signal.type}: ACTIVE`);
      if (signal.reasons.length > 0) {
        lines.push(`  Reasons: ${signal.reasons.join(", ")}`);
      }
    }
  }

  lines.push("");

  // Timing Analysis
  lines.push("=== Timing Analysis ===");

  if (sanitized.timing.transitions.length > 0) {
    lines.push("Phase Transitions:");
    for (const t of sanitized.timing.transitions) {
      lines.push(`  ${t.from} → ${t.to}: ${t.lag}`);
    }
  } else {
    lines.push("Phase Transitions: NONE");
  }

  if (sanitized.timing.stopReasons.length > 0) {
    lines.push(`Stop Reasons: ${sanitized.timing.stopReasons.join(", ")}`);
  } else {
    lines.push("Stop Reasons: NONE");
  }

  lines.push("");
  lines.push("=== End Analysis ===");

  return lines;
}
