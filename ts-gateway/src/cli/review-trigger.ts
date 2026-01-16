#!/usr/bin/env node
/**
 * PR178: v1.4 Manual Review Trigger Hook v1 - CLI
 *
 * Purpose:
 *   Human-initiated review pipeline:
 *   snapshot → analyze → propose → preview → review
 *
 * Constitutional Constraints:
 *   - READ-ONLY: No execution/policy changes, no trade stops
 *   - Analysis only: Separate market response from strategy improvement
 *   - Defensive: Never throws
 *
 * Usage:
 *   npx ts-node src/cli/review-trigger.ts
 *   npx ts-node src/cli/review-trigger.ts --tail 300
 *   npx ts-node src/cli/review-trigger.ts --priority P0
 *   npx ts-node src/cli/review-trigger.ts --json
 *   MERIDIAN_DEBUG=true npx ts-node src/cli/review-trigger.ts --json
 *   node dist/cli/review-trigger.js
 */

import { runManualReviewTriggerV1 } from "../reviewTrigger/pipeline";

/**
 * Check if debug mode is enabled
 *
 * @returns True if MERIDIAN_DEBUG=true
 */
function isDebugMode(): boolean {
  return process.env.MERIDIAN_DEBUG === "true";
}

/**
 * Parse CLI arguments
 */
function parseArgs(): {
  tail?: number;
  priority?: "P0" | "P1" | "P2" | "ALL";
  json?: boolean;
} {
  const args = process.argv.slice(2);
  const result: {
    tail?: number;
    priority?: "P0" | "P1" | "P2" | "ALL";
    json?: boolean;
  } = {};

  for (let i = 0; i < args.length; i++) {
    const arg = args[i];

    if (arg === "--tail" && i + 1 < args.length) {
      result.tail = parseInt(args[i + 1], 10);
      i++;
    } else if (arg === "--priority" && i + 1 < args.length) {
      const priority = args[i + 1].toUpperCase();
      if (["P0", "P1", "P2", "ALL"].includes(priority)) {
        result.priority = priority as "P0" | "P1" | "P2" | "ALL";
      }
      i++;
    } else if (arg === "--json") {
      result.json = true;
    }
  }

  return result;
}

/**
 * Main review trigger CLI function
 */
async function main(): Promise<void> {
  try {
    const args = parseArgs();
    const debugMode = isDebugMode();

    if (debugMode) {
      console.log("=== Debug Mode: MERIDIAN_DEBUG=true ===\n");
    }

    // Run review trigger pipeline
    const result = await runManualReviewTriggerV1({
      tailSnapshots: args.tail,
      priority: args.priority,
    });

    // Display result
    if (args.json) {
      // JSON output
      console.log(JSON.stringify(result, null, 2));
    } else {
      // Normal output
      console.log("=== Manual Review Trigger ===\n");
      console.log(`REVIEW_TRIGGER: ${result.status}`);
      console.log(`SNAPSHOT: ${result.ranSnapshot ? "OK" : "FAILED"}`);
      console.log(`ANALYZE: ${result.ranAnalyze ? "OK" : "FAILED"}`);
      console.log(`PROPOSE: ${result.ranPropose ? "OK" : "FAILED"}`);
      console.log(`PREVIEW: ${result.ranPreview ? "OK" : "FAILED"}`);
      console.log(`REVIEW: ${result.ranReview ? "OK" : "FAILED"}`);

      if (result.warnings.length > 0) {
        console.log(`\nWarnings: ${result.warnings.join(", ")}`);
      }

      console.log("");
    }

    // Exit with appropriate code
    if (result.status === "ERROR") {
      process.exit(1);
    }
  } catch (error) {
    console.error("ERROR: Review trigger CLI failed");
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
