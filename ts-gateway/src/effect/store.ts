/**
 * PR174: v1.4 Patch Effectiveness Tracker v1 - Store
 *
 * Purpose:
 *   JSONL append-only storage for patch effect reports.
 *   Follows the same pattern as PR165/171/172/173 stores.
 *
 * Constitutional Constraints:
 *   - Append-only: No deletion, no modification
 *   - Defensive: Corrupt lines skipped with warnings (never throws)
 *   - File-based: ~/.meridian/effects.log
 */

import * as fs from "fs";
import * as path from "path";
import * as os from "os";
import { PatchEffectReportV1 } from "./types";

/**
 * Effect Store Config
 */
export interface EffectStoreConfig {
  /**
   * Custom log path (overrides default)
   */
  path?: string;

  /**
   * Maximum lines to read (for tail)
   */
  maxLines?: number;
}

/**
 * Effect Filter
 */
export interface EffectFilter {
  /**
   * Tail N most recent records
   */
  tail?: number;

  /**
   * Filter by proposal ID
   */
  proposalId?: string;

  /**
   * Filter by effect decision
   */
  effectDecision?: string;

  /**
   * Filter by original ack decision
   */
  ackDecision?: string;
}

/**
 * Get effect log path
 *
 * @returns Effect log path (~/.meridian/effects.log)
 */
export function getEffectLogPath(): string {
  const meridianDir = process.env.MERIDIAN_EFFECT_PATH
    ? path.dirname(process.env.MERIDIAN_EFFECT_PATH)
    : path.join(os.homedir(), ".meridian");

  const fileName = process.env.MERIDIAN_EFFECT_PATH
    ? path.basename(process.env.MERIDIAN_EFFECT_PATH)
    : "effects.log";

  return path.join(meridianDir, fileName);
}

/**
 * Ensure effect log directory exists
 */
function ensureEffectLogDir(): void {
  const logPath = getEffectLogPath();
  const dir = path.dirname(logPath);

  if (!fs.existsSync(dir)) {
    fs.mkdirSync(dir, { recursive: true });
  }
}

/**
 * Append effect report to log
 *
 * Defensive: Never throws, returns status.
 *
 * @param report - Effect report
 * @param cfg - Store config
 * @returns Append result
 */
export function appendEffectReportV1(
  report: PatchEffectReportV1,
  cfg?: EffectStoreConfig
): { status: "OK" | "ERROR"; warnings: string[] } {
  const warnings: string[] = [];

  try {
    ensureEffectLogDir();

    const logPath = cfg?.path || getEffectLogPath();
    const line = JSON.stringify(report) + "\n";

    fs.appendFileSync(logPath, line, "utf-8");

    return { status: "OK", warnings };
  } catch (error) {
    // Defensive: Return error status but don't throw
    warnings.push("WARN_EFFECT_APPEND_FAILED");
    console.error("ERROR: Failed to append effect report:", error);

    return { status: "ERROR", warnings };
  }
}

/**
 * Read recent effect reports
 *
 * Defensive: Corrupt lines skipped with warnings.
 *
 * @param cfg - Store config with optional filter
 * @returns Effect reports and warnings
 */
export function readRecentEffectReportsV1(
  cfg: EffectStoreConfig & EffectFilter = {}
): { status: "OK" | "ERROR"; reports: PatchEffectReportV1[]; warnings: string[] } {
  const warnings: string[] = [];
  const reports: PatchEffectReportV1[] = [];

  try {
    const logPath = cfg?.path || getEffectLogPath();

    if (!fs.existsSync(logPath)) {
      warnings.push("WARN_EFFECT_LOG_NOT_FOUND");
      return { status: "OK", reports: [], warnings };
    }

    const content = fs.readFileSync(logPath, "utf-8");
    const lines = content.split("\n").filter((line) => line.trim().length > 0);

    // Parse all lines
    for (const line of lines) {
      try {
        const report = JSON.parse(line) as PatchEffectReportV1;

        // Validate kind
        if (report.kind !== "PATCH_EFFECT_V1") {
          warnings.push("WARN_INVALID_EFFECT_KIND");
          continue;
        }

        // Apply filters
        if (cfg.proposalId && report.decisionAckRef.proposalId !== cfg.proposalId) {
          continue;
        }

        if (cfg.effectDecision && report.effectDecision !== cfg.effectDecision) {
          continue;
        }

        if (cfg.ackDecision && report.decisionAckRef.decision !== cfg.ackDecision) {
          continue;
        }

        reports.push(report);
      } catch (error) {
        // Corrupt line: Skip and warn
        warnings.push("WARN_CORRUPT_EFFECT_LINE");
      }
    }

    // Sort by timestamp (newest first)
    reports.sort((a, b) => b.ts - a.ts);

    // Apply tail limit
    const tail = cfg.tail || 20;
    const result = reports.slice(0, tail);

    return { status: "OK", reports: result, warnings };
  } catch (error) {
    warnings.push("WARN_EFFECT_READ_FAILED");
    return { status: "ERROR", reports: [], warnings };
  }
}
