#!/usr/bin/env node
/**
 * PR164: v1.4 Replay CLI (READ-ONLY)
 *
 * Purpose:
 *   Display recent audit events in label-only format.
 *   "What happened recently?" for troubleshooting and monitoring.
 *
 * Constitutional Constraints:
 *   - Label-only: No numerics, no prices, no addresses
 *   - READ-ONLY: Monitoring only, no execution control
 *   - Defensive: Never throws, handles errors gracefully
 *
 * Usage:
 *   npx ts-node src/cli/replay.ts
 *   npx ts-node src/cli/replay.ts --lines 500
 *   npx ts-node src/cli/replay.ts --type GATE_BLOCK
 *   npx ts-node src/cli/replay.ts --level ERROR
 *   node dist/cli/replay.js
 */

import {
  readFilteredEventsV1,
  formatLabelOnlyLine,
} from "../telemetry";

/**
 * Parse CLI arguments
 */
function parseArgs(): {
  lines?: number;
  type?: string;
  level?: string;
} {
  const args = process.argv.slice(2);
  const result: { lines?: number; type?: string; level?: string } = {};

  for (let i = 0; i < args.length; i++) {
    const arg = args[i];

    if (arg === "--lines" && i + 1 < args.length) {
      result.lines = parseInt(args[i + 1], 10);
      i++;
    } else if (arg === "--type" && i + 1 < args.length) {
      result.type = args[i + 1];
      i++;
    } else if (arg === "--level" && i + 1 < args.length) {
      result.level = args[i + 1];
      i++;
    }
  }

  // Override from env
  if (process.env.MERIDIAN_EVENTS_MAXLINES) {
    result.lines = parseInt(process.env.MERIDIAN_EVENTS_MAXLINES, 10);
  }

  return result;
}

/**
 * Main replay CLI function
 */
async function main(): Promise<void> {
  try {
    const args = parseArgs();

    console.log("=== Meridian Event Replay ===\n");

    // Read events with filter
    const result = await readFilteredEventsV1({
      type: args.type,
      level: args.level,
      maxLines: args.lines || 200,
    });

    if (result.warnings.length > 0) {
      console.log(`WARNINGS: ${result.warnings.join(", ")}\n`);
    }

    if (result.events.length === 0) {
      console.log("NO_EVENTS_FOUND");
      return;
    }

    console.log(`EVENTS: ${result.events.length}\n`);

    // Display events (label-only)
    for (const event of result.events) {
      const line = formatLabelOnlyLine(event);
      console.log(line);
    }

    console.log("\n=== End Replay ===");
  } catch (error) {
    console.error("ERROR: Replay CLI failed");
    console.error(error);
    process.exit(1);
  }
}

// Run if called directly
if (require.main === module) {
  main().catch((error) => {
    console.error("FATAL:", error);
    process.exit(1);
  });
}

export { main };
