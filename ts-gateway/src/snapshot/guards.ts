/**
 * PR165: v1.4 Market Regime Snapshot Export v1 - Guards
 *
 * Purpose:
 *   Sanitize and validate snapshot labels/warnings to prevent:
 *   - Token literals (wBTC, USDC, SUI, etc.)
 *   - Trading vocabulary (buy, sell, swap, execute, sign, transfer)
 *   - Prescriptive language (should, must, recommend)
 *   - Numeric/address patterns (0x..., prices, amounts)
 *
 * Constitutional Constraints:
 *   - Numerics allowed in saved files (for analysis)
 *   - Numerics FORBIDDEN in CLI/telemetry display
 *   - Always sanitize warnings/labels before display
 */

import {
  MarketRegimeSnapshotV1,
  SanitizedSnapshot,
  SnapshotLabels,
} from "./types";

/**
 * Forbidden patterns (same as PR164 telemetry guards)
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

  // Address patterns
  /0x[a-fA-F0-9]{40}/g,
  /0x[a-fA-F0-9]{64}/g,

  // Price-like patterns (decimal numbers)
  /\b\d+\.\d+\b/g,
];

/**
 * Sanitize a single label value
 *
 * @param value - Label value to sanitize
 * @returns Sanitized value (REDACTED if forbidden pattern found)
 */
export function sanitizeSnapshotLabel(value: string): string {
  if (!value) return value;

  for (const pattern of FORBIDDEN_PATTERNS) {
    if (pattern.test(value)) {
      return "REDACTED";
    }
  }

  return value;
}

/**
 * Validate snapshot labels (check for forbidden patterns)
 *
 * @param snapshot - Snapshot to validate
 * @returns Validation result with warnings
 */
export function validateSnapshotLabelsOnly(snapshot: MarketRegimeSnapshotV1): {
  ok: boolean;
  warnings: string[];
} {
  const warnings: string[] = [];
  let ok = true;

  // Check warnings array
  for (const warning of snapshot.warnings) {
    for (const pattern of FORBIDDEN_PATTERNS) {
      if (pattern.test(warning)) {
        warnings.push("WARN_SNAPSHOT_WARNING_SANITIZED");
        ok = false;
        break;
      }
    }
  }

  // Check labels
  const labelValues = Object.values(snapshot.labels);
  for (const labelValue of labelValues) {
    if (typeof labelValue === "string") {
      for (const pattern of FORBIDDEN_PATTERNS) {
        if (pattern.test(labelValue)) {
          warnings.push("WARN_SNAPSHOT_LABEL_SANITIZED");
          ok = false;
          break;
        }
      }
    }
  }

  return { ok, warnings };
}

/**
 * Format timestamp as label (for CLI display)
 *
 * @param ts - Timestamp (epoch ms)
 * @returns Time label (T_RECENT / T_MIN / T_HOUR / T_OLD)
 */
export function formatSnapshotTimeLabel(ts: number): string {
  const now = Date.now();
  const ageMs = now - ts;

  if (ageMs < 60_000) {
    // < 1 min
    return "T_RECENT";
  } else if (ageMs < 60 * 60_000) {
    // < 1 hour
    return "T_MIN";
  } else if (ageMs < 24 * 60 * 60_000) {
    // < 24 hours
    return "T_HOUR";
  } else {
    return "T_OLD";
  }
}

/**
 * Sanitize snapshot for display (remove/mask numerics)
 *
 * Purpose:
 *   Remove numerics field and convert ts/id to labels for CLI/telemetry display.
 *
 * @param snapshot - Raw snapshot
 * @returns Sanitized snapshot (label-only)
 */
export function sanitizeSnapshotForDisplay(
  snapshot: MarketRegimeSnapshotV1
): SanitizedSnapshot {
  // Sanitize labels
  const sanitizedLabels: SnapshotLabels = {};

  for (const [key, value] of Object.entries(snapshot.labels)) {
    if (typeof value === "string") {
      (sanitizedLabels as any)[key] = sanitizeSnapshotLabel(value);
    }
  }

  // Sanitize warnings
  const sanitizedWarnings = snapshot.warnings.map(sanitizeSnapshotLabel);

  return {
    version: snapshot.version,
    kind: snapshot.kind,
    status: snapshot.status,
    timeLabel: formatSnapshotTimeLabel(snapshot.ts),
    idLabel: snapshot.id ? "HAS_ID" : "NO_ID",
    warnings: sanitizedWarnings,
    presence: snapshot.presence,
    labels: sanitizedLabels,
    // numerics field is REMOVED (not included in sanitized output)
  };
}

/**
 * Format sanitized snapshot as CLI lines (label-only)
 *
 * @param sanitized - Sanitized snapshot
 * @returns Formatted string lines
 */
export function formatSnapshotLabelOnlyLines(
  sanitized: SanitizedSnapshot
): string[] {
  const lines: string[] = [];

  // Header
  lines.push(`${sanitized.timeLabel} ${sanitized.kind} ${sanitized.status}`);

  // ID
  lines.push(`  ID: ${sanitized.idLabel}`);

  // Presence (show major flags only)
  const presenceFlags = [
    sanitized.presence.hasShockPhase ? "SHOCK_PHASE" : null,
    sanitized.presence.hasStress ? "STRESS" : null,
    sanitized.presence.hasActionShape ? "ACTION" : null,
    sanitized.presence.hasTemplateId ? "TEMPLATE" : null,
    sanitized.presence.hasRoute ? "ROUTE" : null,
    sanitized.presence.hasGate ? "GATE" : null,
    sanitized.presence.hasPolicy ? "POLICY" : null,
    sanitized.presence.hasHardStop ? "HARDSTOP" : null,
  ]
    .filter((f) => f !== null)
    .join(", ");

  lines.push(`  Presence: ${presenceFlags || "NONE"}`);

  // Labels (show non-empty only)
  const labelPairs: string[] = [];
  for (const [key, value] of Object.entries(sanitized.labels)) {
    if (value) {
      labelPairs.push(`${key}=${value}`);
    }
  }

  if (labelPairs.length > 0) {
    lines.push(`  Labels: ${labelPairs.join(", ")}`);
  }

  // Warnings
  if (sanitized.warnings.length > 0) {
    lines.push(`  Warnings: ${sanitized.warnings.join(", ")}`);
  }

  return lines;
}
