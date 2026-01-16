#!/usr/bin/env node
/**
 * PR171: v1.4 Patch Preview Report v1 - CLI
 *
 * Purpose:
 *   View and filter patch preview reports from previews.log.
 *   READ-ONLY tool for reviewing change previews before adoption.
 *
 * Constitutional Constraints:
 *   - READ-ONLY: View only (no generation, no adoption)
 *   - Label-only: Normal mode uses labels (no counts)
 *   - Debug mode: MERIDIAN_DEBUG=true allows numeric timestamps
 *   - Defensive: Never throws, handles errors gracefully
 *
 * Usage:
 *   npx ts-node src/cli/preview.ts
 *   npx ts-node src/cli/preview.ts --tail 10
 *   npx ts-node src/cli/preview.ts --proposal P0_REDUCE_ORACLE_STALE_BLOCKS_DEGRADE
 *   npx ts-node src/cli/preview.ts --priority P0
 *   npx ts-node src/cli/preview.ts --decision ADOPT
 *   npx ts-node src/cli/preview.ts --json
 *   MERIDIAN_DEBUG=true npx ts-node src/cli/preview.ts --tail 10
 *   node dist/cli/preview.js
 */

import { readRecentPreviewsV1 } from "../preview/store";
import {
  formatPreviewLines,
  sanitizePreviewForDisplay,
  isDebugMode,
} from "../preview/guards";
import { PreviewFilter } from "../preview/types";

/**
 * Parse CLI arguments
 */
function parseArgs(): PreviewFilter & { json?: boolean } {
  const args = process.argv.slice(2);
  const result: PreviewFilter & { json?: boolean } = {};

  for (let i = 0; i < args.length; i++) {
    const arg = args[i];

    if (arg === "--tail" && i + 1 < args.length) {
      result.tail = parseInt(args[i + 1], 10);
      i++;
    } else if (arg === "--proposal" && i + 1 < args.length) {
      result.proposalId = args[i + 1];
      i++;
    } else if (arg === "--priority" && i + 1 < args.length) {
      const priority = args[i + 1] as "P0" | "P1" | "P2" | "UNKNOWN";
      if (["P0", "P1", "P2", "UNKNOWN"].includes(priority)) {
        result.priority = priority;
      }
      i++;
    } else if (arg === "--decision" && i + 1 < args.length) {
      const decision = args[i + 1] as "ADOPT" | "HOLD" | "REJECT" | "UNKNOWN";
      if (["ADOPT", "HOLD", "REJECT", "UNKNOWN"].includes(decision)) {
        result.decisionCandidate = decision;
      }
      i++;
    } else if (arg === "--json") {
      result.json = true;
    }
  }

  return result;
}

/**
 * Main preview CLI function
 */
async function main(): Promise<void> {
  try {
    const args = parseArgs();
    const debugMode = isDebugMode();

    if (debugMode) {
      console.log("=== Debug Mode: MERIDIAN_DEBUG=true ===\n");
    }

    // Read previews
    const { previews, warnings } = readRecentPreviewsV1({
      tail: args.tail,
      proposalId: args.proposalId,
      priority: args.priority,
      decisionCandidate: args.decisionCandidate,
    });

    if (warnings.length > 0) {
      console.log(`WARNINGS: ${warnings.join(", ")}\n`);
    }

    if (previews.length === 0) {
      console.log("NO_PREVIEWS_FOUND");
      return;
    }

    // Display based on mode
    if (args.json) {
      // JSON mode (sanitized, or raw in debug mode)
      if (debugMode) {
        console.log(JSON.stringify({ previews, warnings }, null, 2));
      } else {
        const sanitized = previews.map((p) =>
          sanitizePreviewForDisplay(p, false)
        );
        console.log(JSON.stringify({ previews: sanitized, warnings }, null, 2));
      }
    } else {
      // Normal mode: formatted lines (label-only)
      console.log(`=== Preview Reports (${previews.length} found) ===\n`);

      for (let i = 0; i < previews.length; i++) {
        const preview = previews[i];
        const lines = formatPreviewLines(preview, debugMode);

        for (const line of lines) {
          console.log(line);
        }

        // Separator between previews (except last one)
        if (i < previews.length - 1) {
          console.log("---");
          console.log("");
        }
      }
    }
  } catch (error) {
    console.error("ERROR: Preview CLI failed");
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
