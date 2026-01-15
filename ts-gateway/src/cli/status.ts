#!/usr/bin/env node
/**
 * PR163: v1.4 Status CLI (READ-ONLY)
 *
 * Purpose:
 *   Display current Meridian state in label-only format.
 *   "What's happening now?" at a glance.
 *
 * Constitutional Constraints:
 *   - Label-only: No numerics, no prices, no addresses
 *   - READ-ONLY: Monitoring only, no execution control
 *   - Defensive: Never throws, handles errors gracefully
 *
 * Usage:
 *   npx ts-node src/cli/status.ts
 *   node dist/cli/status.js
 */

import { createFileStateStore, sanitizeStateForDisplay } from "../state";

/**
 * Main status CLI function
 */
async function main(): Promise<void> {
  try {
    console.log("=== Meridian Status ===\n");

    // Read state
    const store = createFileStateStore();
    const result = await store.readState();

    if (result.status === "ERROR") {
      console.log("STATE: ERROR");
      console.log("WARNINGS:", result.warnings.join(", "));
      return;
    }

    const state = result.state;

    // Display status
    console.log(`STATE: ${result.status}`);
    console.log(`VERSION: ${state.version}`);

    // Last run
    if (state.lastRun) {
      console.log(`\nLAST_RUN: ${state.lastRun.status}`);
      if (state.lastRun.stopReason) {
        console.log(`STOP_REASON: ${state.lastRun.stopReason}`);
      }
      if (state.lastRun.phaseLabel) {
        console.log(`PHASE: ${state.lastRun.phaseLabel}`);
      }
      if (state.lastRun.routeSelected) {
        console.log(`ROUTE: ${state.lastRun.routeSelected}`);
      }
      if (state.lastRun.templateId) {
        console.log(`TEMPLATE: ${state.lastRun.templateId}`);
      }
      if (state.lastRun.warnings && state.lastRun.warnings.length > 0) {
        console.log(`RUN_WARNINGS: ${state.lastRun.warnings.join(", ")}`);
      }
    } else {
      console.log("\nLAST_RUN: NONE");
    }

    // Resume state
    if (state.resumeState) {
      console.log(`\nRESUME_STATUS: STOPPED`);
      console.log(`RESUME_REASON: ${state.resumeState.stopReason}`);
      if (state.resumeState.lastPhaseLabel) {
        console.log(`RESUME_LAST_PHASE: ${state.resumeState.lastPhaseLabel}`);
      }
      if (state.resumeState.lastRoute) {
        console.log(`RESUME_LAST_ROUTE: ${state.resumeState.lastRoute}`);
      }
      if (state.resumeState.warnings && state.resumeState.warnings.length > 0) {
        console.log(`RESUME_WARNINGS: ${state.resumeState.warnings.join(", ")}`);
      }
    } else {
      console.log(`\nRESUME_STATUS: NONE`);
    }

    // HardStop
    if (state.hardStop) {
      console.log(`\nHARDSTOP: ${state.hardStop.active ? "ACTIVE" : "INACTIVE"}`);
      if (state.hardStop.reason) {
        console.log(`HARDSTOP_REASON: ${state.hardStop.reason}`);
      }
    } else {
      console.log(`\nHARDSTOP: INACTIVE`);
    }

    // Cooldown
    if (state.cooldown && state.cooldown.lastActionTs) {
      console.log(`\nCOOLDOWN: ACTIVE`);
    } else {
      console.log(`\nCOOLDOWN: INACTIVE`);
    }

    // Health
    if (state.health) {
      console.log(`\nHEALTH:`);
      console.log(`  ORACLE: ${state.health.oracle}`);
      console.log(`  ROUTE: ${state.health.route}`);
      console.log(`  POLICY: ${state.health.policy}`);
      if (state.health.notes && state.health.notes.length > 0) {
        console.log(`  NOTES: ${state.health.notes.join(", ")}`);
      }
    } else {
      console.log(`\nHEALTH: UNKNOWN`);
    }

    // Warnings
    if (state.warnings && state.warnings.length > 0) {
      console.log(`\nWARNINGS: ${state.warnings.join(", ")}`);
    }

    // Sanitized state (for debugging)
    if (process.env.MERIDIAN_DEBUG === "true") {
      console.log(`\n=== Sanitized State (DEBUG) ===`);
      const sanitized = sanitizeStateForDisplay(state);
      console.log(JSON.stringify(sanitized, null, 2));
    }

    console.log("\n=== End Status ===");
  } catch (error) {
    console.error("ERROR: Status CLI failed");
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
