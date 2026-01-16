#!/usr/bin/env node
/**
 * PR180: v1.4 Spec Change Digest v1 - CLI
 *
 * Purpose:
 *   Display spec change digest (label-only compressed view).
 *
 * Constitutional Constraints:
 *   - READ-ONLY: Display digest, no execution/adoption changes
 *   - Label-only: No numerics, addresses, tokens in normal mode
 *   - Defensive: Never throws
 *
 * Usage:
 *   npx ts-node src/cli/digest.ts
 *   npx ts-node src/cli/digest.ts --tail 20
 *   npx ts-node src/cli/digest.ts --json
 *   MERIDIAN_DEBUG=true npx ts-node src/cli/digest.ts --json
 */

import { readRecentDigestsV1 } from "../digest/store";
import { SpecChangeDigestV1 } from "../digest/types";

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
  json?: boolean;
  status?: string;
} {
  const args = process.argv.slice(2);
  const result: {
    tail?: number;
    json?: boolean;
    status?: string;
  } = {};

  for (let i = 0; i < args.length; i++) {
    const arg = args[i];

    if (arg === "--tail" && i + 1 < args.length) {
      result.tail = parseInt(args[i + 1], 10);
      i++;
    } else if (arg === "--json") {
      result.json = true;
    } else if (arg === "--status" && i + 1 < args.length) {
      result.status = args[i + 1].toUpperCase();
      i++;
    }
  }

  return result;
}

/**
 * Format digest for display
 *
 * @param digest - Digest report
 */
function formatDigest(digest: SpecChangeDigestV1): void {
  console.log("=== Spec Change Digest ===\n");

  console.log(`STATUS: ${digest.status}`);
  console.log(`TIME: ${digest.time}`);
  console.log("");

  console.log("HEADLINE:");
  if (digest.headline.length > 0) {
    digest.headline.forEach((h) => console.log(`  - ${h}`));
  } else {
    console.log("  (none)");
  }
  console.log("");

  console.log("WHY:");
  if (digest.why.length > 0) {
    digest.why.forEach((w) => console.log(`  - ${w}`));
  } else {
    console.log("  (none)");
  }
  console.log("");

  console.log("WHAT:");
  if (digest.what.length > 0) {
    digest.what.forEach((w) => console.log(`  - ${w}`));
  } else {
    console.log("  (none)");
  }
  console.log("");

  console.log("RISKS:");
  if (digest.risks.length > 0) {
    digest.risks.forEach((r) => console.log(`  - ${r}`));
  } else {
    console.log("  (none)");
  }
  console.log("");

  console.log("CHECKLIST:");
  if (digest.checklist.length > 0) {
    digest.checklist.forEach((c) => console.log(`  - ${c}`));
  } else {
    console.log("  (none)");
  }
  console.log("");

  console.log("RATIONALE:");
  if (digest.rationale.length > 0) {
    digest.rationale.forEach((r) => console.log(`  - ${r}`));
  } else {
    console.log("  (none)");
  }
  console.log("");

  console.log(`SUGGESTED_NEXT: ${digest.suggestedNext}`);
  console.log("");

  console.log("REFS:");
  console.log(`  - hasSpecLock: ${digest.refs.hasSpecLock}`);
  console.log(`  - hasPatchPlan: ${digest.refs.hasPatchPlan}`);
  console.log(`  - hasPreview: ${digest.refs.hasPreview}`);
  console.log(`  - hasReview: ${digest.refs.hasReview}`);
  console.log(`  - hasDecisionAck: ${digest.refs.hasDecisionAck}`);
  console.log(`  - hasEffect: ${digest.refs.hasEffect}`);
  console.log(`  - hasAttribution: ${digest.refs.hasAttribution}`);
  console.log(`  - hasEvidenceLinked: ${digest.refs.hasEvidenceLinked}`);
  console.log("");

  if (digest.warnings.length > 0) {
    console.log("WARNINGS:");
    digest.warnings.forEach((w) => console.log(`  - ${w}`));
    console.log("");
  }
}

/**
 * Main CLI function
 */
async function main(): Promise<void> {
  try {
    const args = parseArgs();
    const debugMode = isDebugMode();

    if (debugMode) {
      console.log("=== Debug Mode: MERIDIAN_DEBUG=true ===\n");
    }

    // Read recent digests
    const result = await readRecentDigestsV1({
      tail: args.tail || 1, // Default to most recent
      status: args.status,
    });

    if (result.items.length === 0) {
      console.log("No digests found");
      return;
    }

    // Display results
    if (args.json) {
      // JSON output
      console.log(JSON.stringify(result.items, null, 2));
    } else {
      // Normal output (latest digest)
      const latest = result.items[result.items.length - 1];
      formatDigest(latest);

      if (result.items.length > 1) {
        console.log(`(Showing latest of ${result.items.length} digests)`);
        console.log("Use --json to see all digests");
      }
    }

    if (result.warnings.length > 0 && !args.json) {
      console.log("\nStore warnings:");
      result.warnings.forEach((w) => console.log(`  - ${w}`));
    }
  } catch (error) {
    console.error("ERROR: Digest CLI failed");
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
