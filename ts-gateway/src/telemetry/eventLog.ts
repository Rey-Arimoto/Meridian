/**
 * PR164: v1.4 Event Log (READ-ONLY)
 *
 * Purpose:
 *   Append-only JSONL audit log for telemetry events.
 *
 * Constitutional Constraints:
 *   - READ-ONLY: Record facts only, no learning, no optimization
 *   - Defensive: Never throws, returns warnings on failure
 *   - Append-only: JSONL format (1 event = 1 line)
 *   - Safe defaults: Missing file → empty array, corrupted lines → skip with warning
 */

import * as fs from "fs";
import * as path from "path";
import * as os from "os";
import { MeridianEventV1 } from "./types";
import { validateEventV1 } from "./guards";

/**
 * Event log configuration
 */
export interface EventLogConfig {
  // Log file path
  path?: string;

  // Maximum file size in bytes (optional, for future use)
  maxBytes?: number;
}

/**
 * Resolve event log path (from env or default)
 *
 * @returns Event log file path
 */
export function resolveEventLogPath(): string {
  return (
    process.env.MERIDIAN_EVENTS_PATH ||
    path.join(os.homedir(), ".meridian", "events.log")
  );
}

/**
 * Append event to log (defensive)
 *
 * @param event - Event to append
 * @param cfg - Configuration (optional)
 * @returns Result with ok flag and warnings
 */
export async function appendEventV1(
  event: MeridianEventV1,
  cfg?: EventLogConfig
): Promise<{ ok: boolean; warnings: string[] }> {
  const warnings: string[] = [];

  try {
    const logPath = cfg?.path || resolveEventLogPath();

    // Validate and sanitize event
    const sanitizedEvent = validateEventV1(event);

    // Ensure directory exists
    const dir = path.dirname(logPath);
    if (!fs.existsSync(dir)) {
      await fs.promises.mkdir(dir, { recursive: true });
    }

    // Serialize event as JSONL (single line)
    const line = JSON.stringify(sanitizedEvent) + "\n";

    // Append to file
    await fs.promises.appendFile(logPath, line, "utf-8");

    return {
      ok: true,
      warnings,
    };
  } catch (error) {
    warnings.push("WARN_EVENT_APPEND_FAILED");

    return {
      ok: false,
      warnings,
    };
  }
}

/**
 * Read recent events from log (defensive)
 *
 * @param cfg - Configuration (optional)
 * @param opts - Read options (optional)
 * @returns Events array and warnings
 */
export async function readRecentEventsV1(
  cfg?: EventLogConfig,
  opts?: { maxLines?: number }
): Promise<{ events: MeridianEventV1[]; warnings: string[] }> {
  const warnings: string[] = [];
  const events: MeridianEventV1[] = [];
  const maxLines = opts?.maxLines || 200;

  try {
    const logPath = cfg?.path || resolveEventLogPath();

    // Check if file exists
    if (!fs.existsSync(logPath)) {
      warnings.push("WARN_EVENT_LOG_NOT_FOUND");
      return { events, warnings };
    }

    // Read file
    const content = await fs.promises.readFile(logPath, "utf-8");

    // Split into lines
    const lines = content.split("\n").filter((line) => line.trim() !== "");

    // Take last N lines
    const recentLines = lines.slice(-maxLines);

    // Parse each line
    for (const line of recentLines) {
      try {
        const parsed = JSON.parse(line);

        // Basic validation (defensive)
        if (parsed.v === "v1" && parsed.ts && parsed.type) {
          events.push(parsed as MeridianEventV1);
        } else {
          warnings.push("WARN_EVENT_PARSE_INVALID_SCHEMA");
        }
      } catch (parseError) {
        warnings.push("WARN_EVENT_PARSE_FAILED_LINE");
        // Continue parsing other lines
      }
    }

    return { events, warnings };
  } catch (error) {
    warnings.push("WARN_EVENT_READ_FAILED");

    return { events, warnings };
  }
}

/**
 * Read events with filter (defensive)
 *
 * @param filter - Filter options
 * @param cfg - Configuration (optional)
 * @returns Filtered events and warnings
 */
export async function readFilteredEventsV1(
  filter: {
    type?: string;
    level?: string;
    maxLines?: number;
  },
  cfg?: EventLogConfig
): Promise<{ events: MeridianEventV1[]; warnings: string[] }> {
  const result = await readRecentEventsV1(cfg, { maxLines: filter.maxLines });

  // Apply filters
  let filteredEvents = result.events;

  if (filter.type) {
    filteredEvents = filteredEvents.filter((e) => e.type === filter.type);
  }

  if (filter.level) {
    filteredEvents = filteredEvents.filter((e) => e.level === filter.level);
  }

  return {
    events: filteredEvents,
    warnings: result.warnings,
  };
}
