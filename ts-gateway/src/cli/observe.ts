#!/usr/bin/env node
/**
 * PR181: v1.4 Observe 1s Loop + Chunk 10s + Immediate STOP v1 - CLI
 * PR181a: v1.4 Spec Lock ≠ STOP (Run-on-Old-Spec) v1
 *
 * Purpose:
 *   Display observe state and stop token status.
 *   Show spec ACK status (visible but not a STOP reason).
 *
 * Constitutional Constraints:
 *   - READ-ONLY: Display only, no execution changes
 *   - Label-only: No numerics in normal mode
 *   - Defensive: Never throws
 *
 * Usage:
 *   npx ts-node src/cli/observe.ts status
 *   npx ts-node src/cli/observe.ts stop-token
 *   npx ts-node src/cli/observe.ts --json
 *   MERIDIAN_DEBUG=true npx ts-node src/cli/observe.ts --json
 */

import { getStopToken } from "../observeLoop/loop";

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
  command: string;
  json?: boolean;
} {
  const args = process.argv.slice(2);
  const result: {
    command: string;
    json?: boolean;
  } = {
    command: args[0] || "status",
  };

  for (let i = 0; i < args.length; i++) {
    const arg = args[i];

    if (arg === "--json") {
      result.json = true;
    }
  }

  return result;
}

/**
 * Status command
 */
async function statusCommand(json: boolean = false): Promise<void> {
  console.log("=== Observe State Status ===\n");

  // For v1, we need to read from state store
  // Since we don't have direct access here, show a placeholder message
  console.log("Observe state: (stored in state.json via supervisor)");
  console.log("Use supervisor status or state CLI to view current observe state");
  console.log("");

  if (!json) {
    console.log("Expected fields:");
    console.log("  - status: AVAILABLE | PARTIAL | ERROR");
    console.log("  - phaseLabel: PHASE_*");
    console.log("  - trendLabel: UP_TREND | DOWN_TREND | RANGE | UNKNOWN");
    console.log("  - labelsPresence: HAS_LABELS | NO_LABELS");
    console.log("  - oracleStatus: AVAILABLE | STALE | ERROR | UNKNOWN");
    console.log("  - stopSignal: STOP | NO_STOP | UNKNOWN");
    console.log("  - specAckStatus: SPEC_ACK_OK | SPEC_ACK_PENDING | etc (PR181a)");
    console.log("  - warnings: [...]");
    console.log("");
    console.log("Note: specAckStatus is visible but NOT a STOP reason.");
    console.log("Execution continues with activeSpec even if latest spec is not ACKed.");
  }

  console.log("");
}

/**
 * Stop token command
 */
async function stopTokenCommand(json: boolean = false): Promise<void> {
  console.log("=== Stop Token Status ===\n");

  const stopToken = getStopToken();

  if (json) {
    console.log(JSON.stringify(stopToken, null, 2));
  } else {
    console.log(`STATUS: ${stopToken.status}`);
    console.log(`REASON: ${stopToken.reason}`);
    console.log(`TIME: ${stopToken.tsLabel}`);
  }

  console.log("");
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

    switch (args.command) {
      case "status":
        await statusCommand(args.json);
        break;

      case "stop-token":
        await stopTokenCommand(args.json);
        break;

      default:
        console.log("Usage:");
        console.log("  npx ts-node src/cli/observe.ts status");
        console.log("  npx ts-node src/cli/observe.ts stop-token");
        console.log("  npx ts-node src/cli/observe.ts --json");
        process.exit(1);
    }
  } catch (error) {
    console.error("ERROR: Observe CLI failed");
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
