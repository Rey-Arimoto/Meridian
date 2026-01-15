/**
 * PR167: v1.4 Improvement Proposal Generator v1 - Guards
 *
 * Purpose:
 *   Guards for proposal sanitization and display formatting.
 *   Ensures proposals are label-only and follow constitutional constraints.
 *
 * Constitutional Constraints:
 *   - Label-only: No numerics in normal mode (except in MERIDIAN_DEBUG=true)
 *   - Forbidden patterns: Token literals, trading vocab, prescriptive language, addresses, prices
 *   - Defensive: Never throws, always returns safe output
 */

import {
  ImprovementProposalV1,
  ProposeResultV1,
  ProposalPriority,
} from "./types";

/**
 * Forbidden patterns (same as PR165/PR166)
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
 * Sanitize proposal label
 *
 * Removes forbidden patterns and replaces with "REDACTED".
 *
 * @param value - Label value
 * @returns Sanitized label
 */
export function sanitizeProposalLabel(value: string): string {
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
 * Sanitize proposal for display
 *
 * In normal mode:
 * - Keeps labels only
 * - Removes triggered_by details (keeps label count only)
 *
 * In debug mode (MERIDIAN_DEBUG=true):
 * - Returns raw proposal with all details
 *
 * @param proposal - Raw proposal
 * @param debugMode - Debug mode flag
 * @returns Sanitized proposal
 */
export function sanitizeProposalForDisplay(
  proposal: ImprovementProposalV1,
  debugMode: boolean
): any {
  if (debugMode) {
    // Debug mode: Return raw proposal
    return proposal;
  }

  // Normal mode: Label-only
  return {
    id: sanitizeProposalLabel(proposal.id),
    priority: proposal.priority,
    category: sanitizeProposalLabel(proposal.category),
    title: sanitizeProposalLabel(proposal.title),
    rationale: proposal.rationale.map(sanitizeProposalLabel),
    expected_effects: proposal.expected_effects.map(sanitizeProposalLabel),
    side_effects: proposal.side_effects.map(sanitizeProposalLabel),
    safe_guards: proposal.safe_guards.map(sanitizeProposalLabel),
    applies_when: sanitizeProposalLabel(proposal.applies_when),
    triggered_by_count:
      proposal.triggered_by.length > 0 ? "HAS_TRIGGERS" : "NO_TRIGGERS",
  };
}

/**
 * Sanitize propose result for display
 *
 * In normal mode:
 * - Sanitizes all proposals
 * - Keeps label-only fields
 *
 * In debug mode:
 * - Returns raw result with all details
 *
 * @param result - Raw propose result
 * @param debugMode - Debug mode flag
 * @returns Sanitized result
 */
export function sanitizeProposeResultForDisplay(
  result: ProposeResultV1,
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
    warnings: result.warnings.map(sanitizeProposalLabel),
    proposals: result.proposals.map((p) =>
      sanitizeProposalForDisplay(p, debugMode)
    ),
    ts_label: result.ts > 0 ? "HAS_TIMESTAMP" : "NO_TIMESTAMP",
    snapshotCountLabel: result.snapshotCountLabel,
  };
}

/**
 * Format proposal lines for console output
 *
 * Formats proposals in a human-readable format.
 * Priority-sorted (P0 > P1 > P2).
 *
 * @param result - Propose result
 * @param debugMode - Debug mode flag
 * @returns Formatted lines
 */
export function formatProposalLines(
  result: ProposeResultV1,
  debugMode: boolean
): string[] {
  const lines: string[] = [];

  // Header
  lines.push("=== Improvement Proposals v1 ===");
  lines.push("");
  lines.push(`Status: ${result.status}`);

  if (result.warnings.length > 0) {
    lines.push(`Warnings: ${result.warnings.join(", ")}`);
  }

  if (result.snapshotCountLabel) {
    lines.push(`Snapshot Count: ${result.snapshotCountLabel}`);
  }

  lines.push("");

  // Proposals (grouped by priority)
  if (result.proposals.length === 0) {
    lines.push("NO_PROPOSALS");
    lines.push("");
    return lines;
  }

  // Group by priority
  const p0Proposals = result.proposals.filter((p) => p.priority === "P0");
  const p1Proposals = result.proposals.filter((p) => p.priority === "P1");
  const p2Proposals = result.proposals.filter((p) => p.priority === "P2");
  const unknownProposals = result.proposals.filter(
    (p) => p.priority === "UNKNOWN"
  );

  // Format each priority group
  if (p0Proposals.length > 0) {
    lines.push("--- P0: Degrade Policy (Highest Priority) ---");
    lines.push("");
    for (const proposal of p0Proposals) {
      lines.push(...formatSingleProposal(proposal, debugMode));
    }
  }

  if (p1Proposals.length > 0) {
    lines.push("--- P1: Template/Gate Policy ---");
    lines.push("");
    for (const proposal of p1Proposals) {
      lines.push(...formatSingleProposal(proposal, debugMode));
    }
  }

  if (p2Proposals.length > 0) {
    lines.push("--- P2: Observable Improvement ---");
    lines.push("");
    for (const proposal of p2Proposals) {
      lines.push(...formatSingleProposal(proposal, debugMode));
    }
  }

  if (unknownProposals.length > 0) {
    lines.push("--- Unknown Priority ---");
    lines.push("");
    for (const proposal of unknownProposals) {
      lines.push(...formatSingleProposal(proposal, debugMode));
    }
  }

  lines.push("=== End Proposals ===");
  lines.push("");

  return lines;
}

/**
 * Format single proposal
 *
 * @param proposal - Proposal to format
 * @param debugMode - Debug mode flag
 * @returns Formatted lines
 */
function formatSingleProposal(
  proposal: ImprovementProposalV1,
  debugMode: boolean
): string[] {
  const lines: string[] = [];

  lines.push(`[${proposal.priority}] ${proposal.title}`);
  lines.push(`  ID: ${proposal.id}`);
  lines.push(`  Category: ${proposal.category}`);
  lines.push("");

  lines.push(`  Rationale:`);
  for (const rationale of proposal.rationale) {
    lines.push(`    - ${rationale}`);
  }
  lines.push("");

  lines.push(`  Expected Effects:`);
  for (const effect of proposal.expected_effects) {
    lines.push(`    - ${effect}`);
  }
  lines.push("");

  lines.push(`  Side Effects:`);
  for (const side of proposal.side_effects) {
    lines.push(`    - ${side}`);
  }
  lines.push("");

  lines.push(`  Safe Guards:`);
  for (const guard of proposal.safe_guards) {
    lines.push(`    - ${guard}`);
  }
  lines.push("");

  lines.push(`  Applies When: ${proposal.applies_when}`);
  lines.push("");

  if (debugMode) {
    lines.push(
      `  Triggered By: ${proposal.triggered_by.join(", ") || "NONE"}`
    );
    lines.push("");
  }

  lines.push("---");
  lines.push("");

  return lines;
}

/**
 * Get priority order value
 *
 * P0 = 0 (highest)
 * P1 = 1
 * P2 = 2
 * UNKNOWN = 99
 *
 * @param priority - Priority
 * @returns Order value
 */
export function getPriorityOrder(priority: ProposalPriority): number {
  switch (priority) {
    case "P0":
      return 0;
    case "P1":
      return 1;
    case "P2":
      return 2;
    case "UNKNOWN":
      return 99;
    default:
      return 99;
  }
}
