#!/usr/bin/env node
/**
 * PR169: v1.4 Policy Attribution Graph v1 - CLI
 *
 * Purpose:
 *   Analyze snapshot logs to identify causal chains (attribution paths)
 *   that lead to outcomes like BLOCK, STOP, etc.
 *
 * Constitutional Constraints:
 *   - READ-ONLY: Analysis only (no proposals, no execution, no changes)
 *   - Label-only: Normal mode uses labels (no counts)
 *   - Debug mode: MERIDIAN_DEBUG=true allows numeric counts
 *   - Defensive: Never throws, handles errors gracefully
 *
 * Usage:
 *   npx ts-node src/cli/attribution.ts
 *   npx ts-node src/cli/attribution.ts --tail 500
 *   npx ts-node src/cli/attribution.ts --focus top_paths
 *   npx ts-node src/cli/attribution.ts --json
 *   MERIDIAN_DEBUG=true npx ts-node src/cli/attribution.ts --tail 500
 *   node dist/cli/attribution.js
 */

import { readRecentSnapshotsV1 } from "../snapshot/exporter";
import { attributeSnapshotsV1 } from "../attribution/attributor";
import {
  formatLabelOnlyLines,
  sanitizeAttributionResultForDisplay,
  isDebugMode,
} from "../attribution/guards";
import { AttrFocus } from "../attribution/types";

/**
 * Parse CLI arguments
 */
function parseArgs(): {
  tail?: number;
  focus?: AttrFocus;
  json?: boolean;
} {
  const args = process.argv.slice(2);
  const result: { tail?: number; focus?: AttrFocus; json?: boolean } = {};

  for (let i = 0; i < args.length; i++) {
    const arg = args[i];

    if (arg === "--tail" && i + 1 < args.length) {
      result.tail = parseInt(args[i + 1], 10);
      i++;
    } else if (arg === "--focus" && i + 1 < args.length) {
      const focus = args[i + 1].toUpperCase();
      if (
        ["TOP_PATHS", "TOP_EDGES", "BOTTLENECKS", "WEAK_LINKS"].includes(focus)
      ) {
        result.focus = focus as AttrFocus;
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
 * Main attribution CLI function
 */
async function main(): Promise<void> {
  try {
    const args = parseArgs();
    const debugMode = isDebugMode();
    const tailN = args.tail || 200;

    if (debugMode) {
      console.log("=== Debug Mode: MERIDIAN_DEBUG=true ===\n");
    }

    // Read snapshots
    const snapshotResult = await readRecentSnapshotsV1(
      {},
      { maxLines: tailN }
    );

    if (snapshotResult.warnings.length > 0) {
      console.log(`WARNINGS: ${snapshotResult.warnings.join(", ")}\n`);
    }

    if (snapshotResult.snapshots.length === 0) {
      console.log("NO_SNAPSHOTS_FOUND");
      return;
    }

    // Attribute snapshots
    const attributionResult = attributeSnapshotsV1(snapshotResult.snapshots, {
      tail: tailN,
      focus: args.focus,
    });

    // Display based on mode
    if (args.json) {
      // JSON mode (sanitized, or raw in debug mode)
      if (debugMode) {
        console.log(JSON.stringify(attributionResult, null, 2));
      } else {
        const sanitized = sanitizeAttributionResultForDisplay(
          attributionResult,
          false
        );
        console.log(JSON.stringify(sanitized, null, 2));
      }
    } else if (args.focus) {
      // Focus mode: show only requested section
      console.log(`=== Attribution Focus: ${args.focus} ===\n`);

      switch (args.focus) {
        case "TOP_PATHS":
          if (attributionResult.topPaths.length === 0) {
            console.log("NO_PATHS");
          } else {
            for (const path of attributionResult.topPaths) {
              const pathStr = path.nodes
                .map((n) => `${n.t}:${n.v}`)
                .join(" → ");
              if (debugMode) {
                console.log(`${pathStr} (count: ${path.count})`);
              } else {
                console.log(pathStr);
              }
            }
          }
          break;

        case "TOP_EDGES":
          if (attributionResult.topEdges.length === 0) {
            console.log("NO_EDGES");
          } else {
            for (const edge of attributionResult.topEdges) {
              const edgeStr = `${edge.from.t}:${edge.from.v} → ${edge.to.t}:${edge.to.v}`;
              if (debugMode) {
                console.log(`${edgeStr} (count: ${edge.count})`);
              } else {
                console.log(edgeStr);
              }
            }
          }
          break;

        case "BOTTLENECKS":
          if (attributionResult.bottlenecks.length === 0) {
            console.log("NO_BOTTLENECKS");
          } else {
            for (const bottleneck of attributionResult.bottlenecks) {
              console.log(`  - ${bottleneck}`);
            }
          }
          break;

        case "WEAK_LINKS":
          if (attributionResult.weakLinks.length === 0) {
            console.log("NO_WEAK_LINKS");
          } else {
            for (const weakLink of attributionResult.weakLinks) {
              console.log(`  - ${weakLink}`);
            }
          }
          break;
      }

      console.log("\n=== End Focus ===");
    } else {
      // Normal mode: full attribution (label-only)
      const lines = formatLabelOnlyLines(attributionResult, debugMode);

      for (const line of lines) {
        console.log(line);
      }
    }
  } catch (error) {
    console.error("ERROR: Attribution CLI failed");
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
