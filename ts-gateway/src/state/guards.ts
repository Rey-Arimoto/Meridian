/**
 * PR163: v1.4 State Guards (READ-ONLY)
 *
 * Purpose:
 *   Ensure state output is label-only (no numerics, no sensitive data).
 *
 * Constitutional Constraints:
 *   - Label-only: All output must be labels, not numbers/prices/addresses
 *   - Defensive: Never throws, returns sanitized copy
 */

import { MeridianStateV1 } from "./types";

/**
 * Sanitize state for external display (remove numeric timestamps)
 *
 * @param state - Raw state
 * @returns Sanitized copy (timestamps removed from display)
 */
export function sanitizeStateForDisplay(
  state: MeridianStateV1
): Record<string, unknown> {
  const sanitized: Record<string, unknown> = {
    version: state.version,
    // updatedAtTs: removed (internal only)
  };

  if (state.lastRun) {
    sanitized.lastRun = {
      status: state.lastRun.status,
      stopReason: state.lastRun.stopReason,
      phaseLabel: state.lastRun.phaseLabel,
      routeSelected: state.lastRun.routeSelected,
      templateId: state.lastRun.templateId,
      action: state.lastRun.action,
      warnings: state.lastRun.warnings,
    };
  }

  if (state.resumeState) {
    sanitized.resumeState = {
      status: state.resumeState.status,
      stopReason: state.resumeState.stopReason,
      // stopAtTs: removed (internal only)
      // resumeAfterTs: removed (internal only)
      lastPhaseLabel: state.resumeState.lastPhaseLabel,
      lastRoute: state.resumeState.lastRoute,
      lastTemplateId: state.resumeState.lastTemplateId,
      lastIntent: state.resumeState.lastIntent,
      warnings: state.resumeState.warnings,
    };
  }

  if (state.hardStop) {
    sanitized.hardStop = {
      active: state.hardStop.active,
      reason: state.hardStop.reason,
      // untilTs: removed (internal only)
    };
  }

  if (state.cooldown) {
    sanitized.cooldown = {
      // lastActionTs: removed (internal only)
      active: state.cooldown.lastActionTs ? true : false,
    };
  }

  if (state.health) {
    sanitized.health = {
      oracle: state.health.oracle,
      route: state.health.route,
      policy: state.health.policy,
      notes: state.health.notes,
    };
  }

  sanitized.warnings = state.warnings;

  return sanitized;
}

/**
 * Check if string contains numeric patterns (for validation)
 *
 * @param text - Text to check
 * @returns True if contains numeric patterns
 */
export function containsNumericPatterns(text: string): boolean {
  // Check for common numeric patterns
  const patterns = [
    /\d+\.\d+/, // Decimal numbers (1.23)
    /\d{4,}/, // Large numbers (1000+)
    /\$\d+/, // Dollar amounts ($100)
    /\d+%/, // Percentages (50%)
    /0x[0-9a-fA-F]+/, // Hex addresses
  ];

  return patterns.some((pattern) => pattern.test(text));
}

/**
 * Validate warnings/notes are label-only
 *
 * @param items - Array of warnings/notes
 * @returns Validation result
 */
export function validateLabelOnly(items: string[]): {
  ok: boolean;
  violations: string[];
} {
  const violations: string[] = [];

  for (const item of items) {
    if (containsNumericPatterns(item)) {
      violations.push(item);
    }
  }

  return {
    ok: violations.length === 0,
    violations,
  };
}
