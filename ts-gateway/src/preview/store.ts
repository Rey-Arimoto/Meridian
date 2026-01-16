/**
 * PR171: v1.4 Patch Preview Report v1 - Store
 *
 * Purpose:
 *   JSONL append-only storage for preview reports.
 *   Follows the same pattern as PR165 snapshot store.
 *
 * Constitutional Constraints:
 *   - Append-only: No deletion, no modification
 *   - Defensive: Corrupt lines skipped with warnings (never throws)
 *   - File-based: ~/.meridian/previews.log
 */

import * as fs from "fs";
import * as path from "path";
import * as os from "os";
import { PatchPreviewReportV1, PreviewFilter } from "./types";

/**
 * Get preview log path
 *
 * @returns Preview log path (~/.meridian/previews.log)
 */
export function getPreviewLogPath(): string {
  const meridianDir = process.env.MERIDIAN_PREVIEW_PATH
    ? path.dirname(process.env.MERIDIAN_PREVIEW_PATH)
    : path.join(os.homedir(), ".meridian");

  const fileName = process.env.MERIDIAN_PREVIEW_PATH
    ? path.basename(process.env.MERIDIAN_PREVIEW_PATH)
    : "previews.log";

  return path.join(meridianDir, fileName);
}

/**
 * Ensure preview log directory exists
 */
function ensurePreviewLogDir(): void {
  const logPath = getPreviewLogPath();
  const dir = path.dirname(logPath);

  if (!fs.existsSync(dir)) {
    fs.mkdirSync(dir, { recursive: true });
  }
}

/**
 * Append preview report to log
 *
 * Defensive: Never throws, logs errors to console.
 *
 * @param report - Preview report
 */
export function appendPreviewV1(report: PatchPreviewReportV1): void {
  try {
    ensurePreviewLogDir();

    const logPath = getPreviewLogPath();
    const line = JSON.stringify(report) + "\n";

    fs.appendFileSync(logPath, line, "utf-8");
  } catch (error) {
    // Defensive: Log error but don't throw
    console.error("ERROR: Failed to append preview:", error);
  }
}

/**
 * Read recent preview reports
 *
 * Defensive: Corrupt lines skipped with warnings.
 *
 * @param filter - Preview filter
 * @returns Preview reports and warnings
 */
export function readRecentPreviewsV1(
  filter: PreviewFilter = {}
): { previews: PatchPreviewReportV1[]; warnings: string[] } {
  const warnings: string[] = [];
  const previews: PatchPreviewReportV1[] = [];

  try {
    const logPath = getPreviewLogPath();

    if (!fs.existsSync(logPath)) {
      warnings.push("WARN_PREVIEW_LOG_NOT_FOUND");
      return { previews: [], warnings };
    }

    const content = fs.readFileSync(logPath, "utf-8");
    const lines = content.split("\n").filter((line) => line.trim().length > 0);

    // Parse all lines
    for (const line of lines) {
      try {
        const preview = JSON.parse(line) as PatchPreviewReportV1;

        // Validate kind
        if (preview.kind !== "PATCH_PREVIEW_V1") {
          warnings.push("WARN_INVALID_PREVIEW_KIND");
          continue;
        }

        previews.push(preview);
      } catch (error) {
        // Defensive: Skip corrupt line
        warnings.push("WARN_CORRUPT_PREVIEW_LINE");
      }
    }

    // Apply filters
    let filtered = previews;

    if (filter.proposalId) {
      filtered = filtered.filter((p) => p.proposalId === filter.proposalId);
    }

    if (filter.priority) {
      filtered = filtered.filter((p) => p.priority === filter.priority);
    }

    if (filter.decisionCandidate) {
      filtered = filtered.filter(
        (p) => p.decisionCandidate === filter.decisionCandidate
      );
    }

    // Sort by timestamp (newest first)
    filtered.sort((a, b) => b.ts - a.ts);

    // Apply tail limit
    if (filter.tail && filter.tail > 0) {
      filtered = filtered.slice(0, filter.tail);
    }

    return { previews: filtered, warnings };
  } catch (error) {
    // Defensive: Return empty on error
    warnings.push("WARN_PREVIEW_READ_ERROR");
    return { previews: [], warnings };
  }
}

/**
 * Get preview count
 *
 * @returns Total preview count in log
 */
export function getPreviewCount(): number {
  try {
    const logPath = getPreviewLogPath();

    if (!fs.existsSync(logPath)) {
      return 0;
    }

    const content = fs.readFileSync(logPath, "utf-8");
    const lines = content.split("\n").filter((line) => line.trim().length > 0);

    return lines.length;
  } catch (error) {
    return 0;
  }
}
