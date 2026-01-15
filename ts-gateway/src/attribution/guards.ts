/**
 * PR169: v1.4 Policy Attribution Graph v1 - Guards
 *
 * Purpose:
 *   Guards for attribution sanitization and display formatting.
 *   Ensures attribution results are label-only and follow constitutional constraints.
 *
 * Constitutional Constraints:
 *   - Label-only: No numerics in normal mode (except in MERIDIAN_DEBUG=true)
 *   - Forbidden patterns: Token literals, trading vocab, prescriptive language, addresses, prices
 *   - Defensive: Never throws, always returns safe output
 */

import { AttributionResultV1, AttrNode, AttrPath, AttrEdge } from "./types";

/**
 * Forbidden patterns (same as PR165/166/167/168)
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
 * Validate label-only
 *
 * Check if result contains only labels (no numeric patterns).
 *
 * @param result - Attribution result
 * @returns Validation result
 */
export function validateLabelOnly(
  result: AttributionResultV1
): { ok: boolean; warnings: string[] } {
  const warnings: string[] = [];

  // Check warnings
  for (const warning of result.warnings) {
    if (/\d+/.test(warning)) {
      warnings.push("WARN_NUMERIC_IN_WARNINGS");
      break;
    }
  }

  // Check bottlenecks
  for (const bottleneck of result.bottlenecks) {
    if (/\d+/.test(bottleneck)) {
      warnings.push("WARN_NUMERIC_IN_BOTTLENECKS");
      break;
    }
  }

  // Check weak links
  for (const weakLink of result.weakLinks) {
    if (/\d+/.test(weakLink)) {
      warnings.push("WARN_NUMERIC_IN_WEAK_LINKS");
      break;
    }
  }

  return {
    ok: warnings.length === 0,
    warnings,
  };
}

/**
 * Format node as string
 *
 * @param node - Attribution node
 * @returns Formatted string
 */
function formatNode(node: AttrNode): string {
  return `${node.t}:${sanitizeLabel(node.v)}`;
}

/**
 * Format path as string
 *
 * @param path - Attribution path
 * @param includeCount - Include count (debug mode only)
 * @returns Formatted string
 */
function formatPath(path: AttrPath, includeCount: boolean): string {
  const nodeStr = path.nodes.map(formatNode).join(" → ");
  if (includeCount) {
    return `${nodeStr} (count: ${path.count})`;
  }
  return nodeStr;
}

/**
 * Format edge as string
 *
 * @param edge - Attribution edge
 * @param includeCount - Include count (debug mode only)
 * @returns Formatted string
 */
function formatEdge(edge: AttrEdge, includeCount: boolean): string {
  const edgeStr = `${formatNode(edge.from)} → ${formatNode(edge.to)}`;
  if (includeCount) {
    return `${edgeStr} (count: ${edge.count})`;
  }
  return edgeStr;
}

/**
 * Format attribution result as label-only lines
 *
 * @param result - Attribution result
 * @param debugMode - Debug mode flag
 * @returns Formatted lines
 */
export function formatLabelOnlyLines(
  result: AttributionResultV1,
  debugMode: boolean = false
): string[] {
  const lines: string[] = [];

  // Header
  lines.push("=== Policy Attribution Graph v1 ===");
  lines.push("");
  lines.push(`Status: ${result.status}`);
  lines.push("");

  // Warnings
  if (result.warnings.length > 0) {
    lines.push(`Warnings: ${result.warnings.map(sanitizeLabel).join(", ")}`);
    lines.push("");
  }

  // Presence
  const presenceLabels: string[] = [];
  if (result.presence.hasSnapshots) presenceLabels.push("HAS_SNAPSHOTS");
  if (result.presence.hasPhase) presenceLabels.push("HAS_PHASE");
  if (result.presence.hasStress) presenceLabels.push("HAS_STRESS");
  if (result.presence.hasTemplate) presenceLabels.push("HAS_TEMPLATE");
  if (result.presence.hasGate) presenceLabels.push("HAS_GATE");
  if (result.presence.hasPolicy) presenceLabels.push("HAS_POLICY");
  if (result.presence.hasResume) presenceLabels.push("HAS_RESUME");
  if (result.presence.hasRoute) presenceLabels.push("HAS_ROUTE");
  if (result.presence.hasRunStop) presenceLabels.push("HAS_RUN_STOP");

  lines.push(`Presence: ${presenceLabels.join(" ")}`);
  lines.push("");

  // Top Paths
  lines.push("--- Top Attribution Paths ---");
  lines.push("");
  if (result.topPaths.length === 0) {
    lines.push("NO_PATHS");
  } else {
    for (const path of result.topPaths) {
      lines.push(`  ${formatPath(path, debugMode)}`);
    }
  }
  lines.push("");

  // Top Edges
  lines.push("--- Top Edges ---");
  lines.push("");
  if (result.topEdges.length === 0) {
    lines.push("NO_EDGES");
  } else {
    for (const edge of result.topEdges) {
      lines.push(`  ${formatEdge(edge, debugMode)}`);
    }
  }
  lines.push("");

  // Bottlenecks
  lines.push("--- Bottlenecks ---");
  lines.push("");
  if (result.bottlenecks.length === 0) {
    lines.push("NO_BOTTLENECKS");
  } else {
    for (const bottleneck of result.bottlenecks) {
      lines.push(`  - ${sanitizeLabel(bottleneck)}`);
    }
  }
  lines.push("");

  // Weak Links
  lines.push("--- Weak Links ---");
  lines.push("");
  if (result.weakLinks.length === 0) {
    lines.push("NO_WEAK_LINKS");
  } else {
    for (const weakLink of result.weakLinks) {
      lines.push(`  - ${sanitizeLabel(weakLink)}`);
    }
  }
  lines.push("");

  lines.push("=== End Attribution ===");
  lines.push("");

  return lines;
}

/**
 * Sanitize attribution result for display
 *
 * In normal mode:
 * - Removes counts from paths and edges
 * - Keeps labels only
 *
 * In debug mode:
 * - Returns raw result with counts
 *
 * @param result - Raw attribution result
 * @param debugMode - Debug mode flag
 * @returns Sanitized result
 */
export function sanitizeAttributionResultForDisplay(
  result: AttributionResultV1,
  debugMode: boolean
): any {
  if (debugMode) {
    // Debug mode: Return raw result with counts
    return result;
  }

  // Normal mode: Label-only (remove counts)
  return {
    version: result.version,
    status: result.status,
    presence: result.presence,
    warnings: result.warnings.map(sanitizeLabel),
    topPathsCount: result.topPaths.length > 0 ? "HAS_PATHS" : "NO_PATHS",
    topEdgesCount: result.topEdges.length > 0 ? "HAS_EDGES" : "NO_EDGES",
    bottlenecks: result.bottlenecks.map(sanitizeLabel),
    weakLinks: result.weakLinks.map(sanitizeLabel),
    ts_label: result.ts > 0 ? "HAS_TIMESTAMP" : "NO_TIMESTAMP",
  };
}
