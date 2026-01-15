/**
 * PR164: v1.4 Telemetry Guards (READ-ONLY)
 *
 * Purpose:
 *   Ensure telemetry events are label-only (no numerics, no sensitive data).
 *
 * Constitutional Constraints:
 *   - Label-only: No numerics, no token literals, no trading vocab, no prescriptive
 *   - Defensive: Never throws, returns sanitized copy
 *   - Safe defaults: Forbidden values → "REDACTED"
 */

import { MeridianEventV1 } from "./types";

/**
 * Forbidden patterns (extended from PR154/155/156)
 */
const FORBIDDEN_PATTERNS = {
  // Token literals
  tokens: /\b(wBTC|WBTC|BTC|USDC|SUI|ETH|SOL)\b/gi,

  // Trading vocabulary
  trading: /\b(swap|buy|sell|execute|sign|transfer|approve|allowance|spend)\b/gi,

  // Prescriptive vocabulary
  prescriptive: /\b(should|must|need|recommend|advise|suggest|ought)\b/gi,

  // Numeric patterns
  numeric: /(\d+\.\d+|\d{4,}|\$\d+|\d+%|0x[0-9a-fA-F]+)/g,
};

/**
 * Check if value contains forbidden patterns
 *
 * @param value - Value to check
 * @returns True if contains forbidden patterns
 */
export function containsForbiddenPatterns(value: string): boolean {
  return Object.values(FORBIDDEN_PATTERNS).some((pattern) => pattern.test(value));
}

/**
 * Sanitize label value (replace forbidden with "REDACTED")
 *
 * @param value - Label value to sanitize
 * @returns Sanitized value
 */
export function sanitizeLabelValue(value: string): string {
  let sanitized = value;

  // Replace each forbidden pattern
  for (const pattern of Object.values(FORBIDDEN_PATTERNS)) {
    sanitized = sanitized.replace(pattern, "REDACTED");
  }

  // If still contains issues, redact entirely
  if (containsForbiddenPatterns(sanitized)) {
    return "REDACTED";
  }

  return sanitized;
}

/**
 * Validate and sanitize event (defensive)
 *
 * @param event - Event to validate
 * @returns Sanitized event
 */
export function validateEventV1(event: MeridianEventV1): MeridianEventV1 {
  try {
    const sanitizedLabels: Record<string, string | undefined> = {};

    // Sanitize labels
    for (const [key, value] of Object.entries(event.labels)) {
      if (value === undefined) {
        sanitizedLabels[key] = undefined;
        continue;
      }

      sanitizedLabels[key] = sanitizeLabelValue(value);
    }

    // Sanitize warnings
    const sanitizedWarnings = event.warnings.map(sanitizeLabelValue);

    return {
      ...event,
      labels: sanitizedLabels,
      warnings: sanitizedWarnings,
    };
  } catch (error) {
    // Defensive: Return minimal safe event
    return {
      v: "v1",
      ts: event.ts || Date.now(),
      level: "ERROR",
      type: "ERROR",
      labels: {},
      warnings: ["WARN_EVENT_VALIDATION_ERROR"],
    };
  }
}

/**
 * Format timestamp as label (no numeric output)
 *
 * @param ts - Timestamp (epoch ms)
 * @param nowTs - Current timestamp (optional)
 * @returns Time label (T_RECENT / T_OLD / T_UNKNOWN)
 */
export function formatTimestampLabel(ts: number, nowTs?: number): string {
  try {
    const now = nowTs || Date.now();
    const ageMs = now - ts;

    if (ageMs < 0) {
      return "T_FUTURE"; // Clock skew
    }

    if (ageMs < 60_000) {
      return "T_RECENT"; // < 1 minute
    }

    if (ageMs < 3600_000) {
      return "T_HOUR"; // < 1 hour
    }

    if (ageMs < 86400_000) {
      return "T_DAY"; // < 1 day
    }

    return "T_OLD"; // > 1 day
  } catch (error) {
    return "T_UNKNOWN";
  }
}

/**
 * Format event as label-only line (for CLI display)
 *
 * @param event - Event to format
 * @returns Label-only string (no numerics)
 */
export function formatLabelOnlyLine(event: MeridianEventV1): string {
  try {
    const timeLabel = formatTimestampLabel(event.ts);
    const level = event.level.padEnd(5);
    const type = event.type.padEnd(20);

    // Format labels (key=value pairs)
    const labelPairs: string[] = [];
    for (const [key, value] of Object.entries(event.labels)) {
      if (value !== undefined) {
        labelPairs.push(`${key}=${value}`);
      }
    }

    const labelsStr = labelPairs.length > 0 ? labelPairs.join(" ") : "";
    const warningsStr =
      event.warnings.length > 0 ? `[${event.warnings.join(", ")}]` : "";

    // Combine parts
    const parts = [
      `[${timeLabel}]`,
      `[${level}]`,
      `[${type}]`,
      labelsStr,
      warningsStr,
    ].filter((p) => p !== "" && p !== "[]");

    return parts.join(" ");
  } catch (error) {
    return "[ERROR] WARN_FORMAT_ERROR";
  }
}

/**
 * Check if line contains any numeric patterns (for validation)
 *
 * @param line - Line to check
 * @returns True if contains numeric patterns
 */
export function containsNumericPatterns(line: string): boolean {
  const numericPattern = /(\d+\.\d+|\d{4,}|\$\d+|\d+%|0x[0-9a-fA-F]+)/;
  return numericPattern.test(line);
}
