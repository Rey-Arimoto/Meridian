/**
 * PR175: v1.4 Regression Guard v1 - Store
 *
 * Purpose:
 *   JSONL storage for regression reports.
 *   Append-only audit trail at ~/.meridian/regressions.log
 *
 * Constitutional Constraints:
 *   - Append-only: Never modify/delete existing records
 *   - Defensive: Handles missing/corrupt files gracefully
 */

import * as fs from "fs";
import * as path from "path";
import * as os from "os";
import { RegressionReportV1 } from "./types";

/**
 * Get regression log path
 *
 * @returns Path to regressions.log
 */
export function getRegressionLogPath(): string {
  const meridianDir = path.join(os.homedir(), ".meridian");

  // Ensure directory exists
  if (!fs.existsSync(meridianDir)) {
    fs.mkdirSync(meridianDir, { recursive: true });
  }

  return path.join(meridianDir, "regressions.log");
}

/**
 * Append regression report to log
 *
 * @param report - Regression report
 * @returns Status and warnings
 */
export function appendRegressionReportV1(report: RegressionReportV1): {
  status: "OK" | "ERROR";
  warnings: string[];
} {
  try {
    const logPath = getRegressionLogPath();
    const line = JSON.stringify(report) + "\n";

    fs.appendFileSync(logPath, line, "utf-8");

    return {
      status: "OK",
      warnings: [],
    };
  } catch (error) {
    return {
      status: "ERROR",
      warnings: ["ERROR_APPENDING_REGRESSION_REPORT"],
    };
  }
}

/**
 * Read recent regression reports
 *
 * @param options - Read options
 * @returns Reports and warnings
 */
export function readRecentRegressionReportsV1(options: {
  tail?: number;
  proposalId?: string;
  decision?: string;
}): {
  reports: RegressionReportV1[];
  warnings: string[];
} {
  const warnings: string[] = [];

  try {
    const logPath = getRegressionLogPath();

    // Check if file exists
    if (!fs.existsSync(logPath)) {
      return {
        reports: [],
        warnings: ["WARN_REGRESSION_LOG_NOT_FOUND"],
      };
    }

    // Read file
    const content = fs.readFileSync(logPath, "utf-8");
    const lines = content.trim().split("\n").filter(Boolean);

    // Parse JSONL
    const reports: RegressionReportV1[] = [];

    for (let i = 0; i < lines.length; i++) {
      try {
        const report = JSON.parse(lines[i]) as RegressionReportV1;

        // Validate kind
        if (report.kind !== "REGRESSION_REPORT_V1") {
          warnings.push(`WARN_LINE_${i}_INVALID_KIND`);
          continue;
        }

        reports.push(report);
      } catch (error) {
        warnings.push(`WARN_LINE_${i}_PARSE_ERROR`);
      }
    }

    // Filter by proposalId
    let filtered = reports;
    if (options.proposalId) {
      filtered = reports.filter(
        (r) => r.analysis.proposalId === options.proposalId
      );
    }

    // Filter by decision
    if (options.decision) {
      filtered = filtered.filter(
        (r) => r.analysis.decision === options.decision
      );
    }

    // Sort by timestamp (newest first)
    filtered.sort((a, b) => b.ts - a.ts);

    // Apply tail limit
    const tail = options.tail || 100;
    const result = filtered.slice(0, tail);

    return {
      reports: result,
      warnings,
    };
  } catch (error) {
    return {
      reports: [],
      warnings: ["ERROR_READING_REGRESSION_LOG"],
    };
  }
}
