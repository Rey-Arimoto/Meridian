#!/usr/bin/env node
/**
 * PR172: v1.4 Patch Review Checklist + Decision Rationale v1 - CLI
 *
 * Purpose:
 *   Review patch preview reports and generate structured checklists + decision rationale.
 *   READ-ONLY tool for supporting human judgment (no automatic adoption).
 *
 * Constitutional Constraints:
 *   - READ-ONLY: Suggests decision, does not auto-adopt
 *   - Fixed rules: All checklist items and rationale rules predetermined
 *   - Label-only: Normal mode uses labels (no counts)
 *   - Debug mode: MERIDIAN_DEBUG=true allows additional details
 *   - Defensive: Never throws, handles errors gracefully
 *
 * Usage:
 *   npx ts-node src/cli/review.ts
 *   npx ts-node src/cli/review.ts --proposal P0_REDUCE_ORACLE_STALE_BLOCKS_DEGRADE
 *   npx ts-node src/cli/review.ts --json
 *   MERIDIAN_DEBUG=true npx ts-node src/cli/review.ts
 *   node dist/cli/review.js
 */

import { readRecentPreviewsV1 } from "../preview/store";
import { reviewPatchPreviewV1 } from "../review/reviewer";
import {
  formatReviewLines,
  sanitizeReviewForDisplay,
  isDebugMode,
} from "../review/guards";

/**
 * Parse CLI arguments
 */
function parseArgs(): {
  proposal?: string;
  json?: boolean;
} {
  const args = process.argv.slice(2);
  const result: { proposal?: string; json?: boolean } = {};

  for (let i = 0; i < args.length; i++) {
    const arg = args[i];

    if (arg === "--proposal" && i + 1 < args.length) {
      result.proposal = args[i + 1];
      i++;
    } else if (arg === "--json") {
      result.json = true;
    }
  }

  return result;
}

/**
 * Main review CLI function
 */
async function main(): Promise<void> {
  try {
    const args = parseArgs();
    const debugMode = isDebugMode();

    if (debugMode) {
      console.log("=== Debug Mode: MERIDIAN_DEBUG=true ===\n");
    }

    // Read most recent preview
    const { previews, warnings } = readRecentPreviewsV1({
      tail: 1,
      proposalId: args.proposal,
    });

    if (warnings.length > 0 && debugMode) {
      console.log(`PREVIEW_WARNINGS: ${warnings.join(", ")}\n`);
    }

    if (previews.length === 0) {
      console.log("NO_PREVIEWS_FOUND");
      return;
    }

    // Get most recent preview
    const preview = previews[0];

    // Review the preview
    const reviewReport = reviewPatchPreviewV1(preview);

    // Display based on mode
    if (args.json) {
      // JSON mode (sanitized, or raw in debug mode)
      if (debugMode) {
        console.log(JSON.stringify(reviewReport, null, 2));
      } else {
        const sanitized = sanitizeReviewForDisplay(reviewReport, false);
        console.log(JSON.stringify(sanitized, null, 2));
      }
    } else {
      // Normal mode: formatted lines (label-only)
      const lines = formatReviewLines(reviewReport, debugMode);

      for (const line of lines) {
        console.log(line);
      }
    }
  } catch (error) {
    console.error("ERROR: Review CLI failed");
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
