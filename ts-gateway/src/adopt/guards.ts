/**
 * PR168: v1.4 Policy-First Adoption Loop - Guards
 *
 * Purpose:
 *   Guards for adoption sanitization and display formatting.
 *   Ensures patch plans and comparisons are label-only and follow constitutional constraints.
 *
 * Constitutional Constraints:
 *   - Label-only: No numerics in normal mode (except in MERIDIAN_DEBUG=true)
 *   - Forbidden patterns: Token literals, trading vocab, prescriptive language, addresses, prices
 *   - Defensive: Never throws, always returns safe output
 */

import { AdoptResultV1, PatchPlan, ReplayCompare } from "./types";

/**
 * Forbidden patterns (same as PR165/166/167)
 *
 * - Token literals: wBTC, USDC, SUI, etc.
 * - Trading vocab: buy, sell, long, short, trade, execute, etc.
 * - Prescriptive: should, must, will, shall, etc.
 * - Address: 0x...
 * - Price: $, USD, price patterns
 * - Numerics in normal mode (except debug)
 */
const FORBIDDEN_PATTERNS = [
  // Token literals
  /\bwBTC\b/i,
  /\bUSDC\b/i,
  /\bUSDT\b/i,
  /\bSUI\b/i,
  /\bETH\b/i,
  /\bBTC\b/i,
  // Trading vocab
  /\bbuy\b/i,
  /\bsell\b/i,
  /\blong\b/i,
  /\bshort\b/i,
  /\btrade\b/i,
  /\bexecute\b/i,
  /\border\b/i,
  /\bposition\b/i,
  // Prescriptive
  /\bshould\b/i,
  /\bmust\b/i,
  /\bwill\b/i,
  /\bshall\b/i,
  /\brecommend\b/i,
  /\badvise\b/i,
  // Address
  /0x[a-fA-F0-9]{8,}/,
  // Price
  /\$\d+/,
  /\d+\s*USD/i,
  /\bprice\b/i,
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
 * Sanitize label
 *
 * Removes forbidden patterns and replaces with "REDACTED".
 *
 * @param value - Label value
 * @returns Sanitized label
 */
export function sanitizeLabel(value: string): string {
  if (typeof value !== "string") {
    return "REDACTED";
  }

  for (const pattern of FORBIDDEN_PATTERNS) {
    if (pattern.test(value)) {
      return "REDACTED";
    }
  }

  return value;
}

/**
 * Sanitize lines
 *
 * @param lines - Lines to sanitize
 * @returns Sanitized lines
 */
export function sanitizeLines(lines: string[]): string[] {
  return lines.map(sanitizeLabel);
}

/**
 * Validate label-only
 *
 * Check if lines contain only labels (no numeric patterns).
 *
 * @param lines - Lines to validate
 * @returns True if label-only
 */
export function validateLabelOnly(lines: string[]): boolean {
  // Allow labels like "LAG_SHORT", "TPL_RISK_50", "P0"
  // Reject numeric counts like "142", "30%", "3.5"
  const numericPattern = /^\d+$|^\d+\.\d+$|^\d+%$/;

  for (const line of lines) {
    // Check each word in the line
    const words = line.split(/\s+/);
    for (const word of words) {
      if (numericPattern.test(word)) {
        return false;
      }
    }
  }

  return true;
}

/**
 * Sanitize patch plan for display
 *
 * In normal mode:
 * - Keeps labels only
 * - Removes op details (keeps count label)
 *
 * In debug mode:
 * - Returns raw patch plan with all details
 *
 * @param patchPlan - Raw patch plan
 * @param debugMode - Debug mode flag
 * @returns Sanitized patch plan
 */
export function sanitizePatchPlanForDisplay(
  patchPlan: PatchPlan,
  debugMode: boolean
): any {
  if (debugMode) {
    // Debug mode: Return raw patch plan
    return patchPlan;
  }

  // Normal mode: Label-only
  return {
    status: patchPlan.status,
    proposalId: patchPlan.proposalId
      ? sanitizeLabel(patchPlan.proposalId)
      : undefined,
    priority: patchPlan.priority,
    opsCount: patchPlan.ops.length > 0 ? "HAS_OPS" : "NO_OPS",
    warnings: patchPlan.warnings.map(sanitizeLabel),
  };
}

/**
 * Sanitize replay compare for display
 *
 * In normal mode:
 * - Keeps labels only
 * - Removes signal details (keeps count label)
 *
 * In debug mode:
 * - Returns raw compare with all details
 *
 * @param compare - Raw compare
 * @param debugMode - Debug mode flag
 * @returns Sanitized compare
 */
export function sanitizeReplayCompareForDisplay(
  compare: ReplayCompare,
  debugMode: boolean
): any {
  if (debugMode) {
    // Debug mode: Return raw compare
    return compare;
  }

  // Normal mode: Label-only
  return {
    status: compare.status,
    window: sanitizeLabel(compare.window),
    before: sanitizeLines(compare.before),
    after: sanitizeLines(compare.after),
    signalsCount: compare.signals.length > 0 ? "HAS_SIGNALS" : "NO_SIGNALS",
    warnings: sanitizeLines(compare.warnings),
  };
}

/**
 * Sanitize adopt result for display
 *
 * In normal mode:
 * - Sanitizes all fields
 * - Keeps label-only fields
 *
 * In debug mode:
 * - Returns raw result with all details
 *
 * @param result - Raw adopt result
 * @param debugMode - Debug mode flag
 * @returns Sanitized result
 */
export function sanitizeAdoptResultForDisplay(
  result: AdoptResultV1,
  debugMode: boolean
): any {
  if (debugMode) {
    // Debug mode: Return raw result
    return result;
  }

  // Normal mode: Label-only
  return {
    version: result.version,
    status: result.status,
    decision: result.decision,
    priority: result.priority,
    proposalId: result.proposalId
      ? sanitizeLabel(result.proposalId)
      : undefined,
    patchPlan: sanitizePatchPlanForDisplay(result.patchPlan, debugMode),
    compare: sanitizeReplayCompareForDisplay(result.compare, debugMode),
    reasons: sanitizeLines(result.reasons),
    warnings: sanitizeLines(result.warnings),
    ts_label: result.ts > 0 ? "HAS_TIMESTAMP" : "NO_TIMESTAMP",
  };
}

/**
 * Format adopt result lines for console output
 *
 * Formats adoption result in a human-readable format.
 *
 * @param result - Adopt result
 * @param debugMode - Debug mode flag
 * @returns Formatted lines
 */
export function formatAdoptResultLabelOnlyLines(
  result: AdoptResultV1,
  debugMode: boolean
): string[] {
  const lines: string[] = [];

  // Header
  lines.push("=== Policy-First Adoption Loop v1 ===");
  lines.push("");
  lines.push(`Status: ${result.status}`);
  lines.push(`Decision: ${result.decision}`);

  if (result.priority) {
    lines.push(`Priority: ${result.priority}`);
  }

  if (result.proposalId) {
    lines.push(`Proposal ID: ${result.proposalId}`);
  }

  lines.push("");

  // Warnings
  if (result.warnings.length > 0) {
    lines.push(`Warnings: ${result.warnings.join(", ")}`);
    lines.push("");
  }

  // Patch Plan
  lines.push("--- Patch Plan ---");
  lines.push("");
  lines.push(`Status: ${result.patchPlan.status}`);
  lines.push(`Operations: ${result.patchPlan.ops.length}`);
  lines.push("");

  for (const op of result.patchPlan.ops) {
    lines.push(`[${op.kind}]`);
    lines.push(`  Target: ${op.target}`);
    lines.push(`  Op ID: ${op.opId}`);
    lines.push(`  Change: ${op.change}`);

    if (op.safety.length > 0) {
      lines.push(`  Safety: ${op.safety.join(", ")}`);
    }

    if (op.notAllowedReason) {
      lines.push(`  NOT ALLOWED: ${op.notAllowedReason}`);
    }

    lines.push("");
  }

  // Replay Compare
  lines.push("--- Replay Compare ---");
  lines.push("");
  lines.push(`Status: ${result.compare.status}`);
  lines.push(`Window: ${result.compare.window}`);
  lines.push("");

  lines.push("Before:");
  for (const b of result.compare.before) {
    lines.push(`  - ${b}`);
  }
  lines.push("");

  lines.push("After:");
  for (const a of result.compare.after) {
    lines.push(`  - ${a}`);
  }
  lines.push("");

  lines.push("Signals:");
  if (result.compare.signals.length === 0) {
    lines.push("  NO_SIGNALS");
  } else {
    for (const signal of result.compare.signals) {
      lines.push(`  - ${signal}`);
    }
  }
  lines.push("");

  // Decision Reasons
  lines.push("--- Decision Reasons ---");
  lines.push("");
  for (const reason of result.reasons) {
    lines.push(`  - ${reason}`);
  }
  lines.push("");

  lines.push("=== End Adoption ===");
  lines.push("");

  return lines;
}
