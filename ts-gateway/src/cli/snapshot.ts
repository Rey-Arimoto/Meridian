#!/usr/bin/env node
/**
 * PR165: v1.4 Market Regime Snapshot Export v1 - CLI
 *
 * Purpose:
 *   Display recent market regime snapshots in label-only format.
 *   "What did Meridian see recently?" for troubleshooting and monitoring.
 *
 * Constitutional Constraints:
 *   - Label-only: No numerics, no prices, no addresses
 *   - READ-ONLY: Monitoring only, no execution control
 *   - Defensive: Never throws, handles errors gracefully
 *
 * Usage:
 *   npx ts-node src/cli/snapshot.ts
 *   npx ts-node src/cli/snapshot.ts --tail 50
 *   npx ts-node src/cli/snapshot.ts --level AVAILABLE
 *   npx ts-node src/cli/snapshot.ts --json
 *   node dist/cli/snapshot.js
 */

import {
  readFilteredSnapshotsV1,
  readRecentSnapshotsV1,
} from "../snapshot/exporter";
import {
  sanitizeSnapshotForDisplay,
  formatSnapshotLabelOnlyLines,
} from "../snapshot/guards";
import { SnapshotStatus } from "../snapshot/types";

/**
 * Parse CLI arguments
 */
function parseArgs(): {
  tail?: number;
  level?: SnapshotStatus;
  json?: boolean;
} {
  const args = process.argv.slice(2);
  const result: { tail?: number; level?: SnapshotStatus; json?: boolean } = {};

  for (let i = 0; i < args.length; i++) {
    const arg = args[i];

    if (arg === "--tail" && i + 1 < args.length) {
      result.tail = parseInt(args[i + 1], 10);
      i++;
    } else if (arg === "--level" && i + 1 < args.length) {
      const level = args[i + 1];
      if (level === "AVAILABLE" || level === "PARTIAL" || level === "ERROR") {
        result.level = level;
      }
      i++;
    } else if (arg === "--json") {
      result.json = true;
    }
  }

  // Override from env
  if (process.env.MERIDIAN_SNAPSHOTS_MAXLINES) {
    result.tail = parseInt(process.env.MERIDIAN_SNAPSHOTS_MAXLINES, 10);
  }

  return result;
}

/**
 * Main snapshot CLI function
 */
async function main(): Promise<void> {
  try {
    const args = parseArgs();

    console.log("=== Meridian Snapshot CLI ===\n");

    // Read snapshots with filter
    const result = args.level
      ? await readFilteredSnapshotsV1({
          status: args.level,
          maxLines: args.tail || 200,
        })
      : await readRecentSnapshotsV1({}, { maxLines: args.tail || 200 });

    if (result.warnings.length > 0) {
      console.log(`WARNINGS: ${result.warnings.join(", ")}\n`);
    }

    if (result.snapshots.length === 0) {
      console.log("NO_SNAPSHOTS_FOUND");
      return;
    }

    console.log(`SNAPSHOTS: ${result.snapshots.length}\n`);

    // Display snapshots (label-only)
    if (args.json) {
      // JSON mode (sanitized)
      const sanitized = result.snapshots.map(sanitizeSnapshotForDisplay);
      console.log(JSON.stringify(sanitized, null, 2));
    } else {
      // Label-only mode (formatted lines)
      for (const snapshot of result.snapshots) {
        const sanitized = sanitizeSnapshotForDisplay(snapshot);
        const lines = formatSnapshotLabelOnlyLines(sanitized);

        for (const line of lines) {
          console.log(line);
        }

        console.log(""); // Blank line between snapshots
      }
    }

    console.log("=== End Snapshots ===");
  } catch (error) {
    console.error("ERROR: Snapshot CLI failed");
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
