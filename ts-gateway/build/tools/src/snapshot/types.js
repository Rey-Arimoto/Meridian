"use strict";
/**
 * PR165: v1.4 Market Regime Snapshot Export v1 - Types
 *
 * Purpose:
 *   Define snapshot schema for exporting "what Meridian saw at that moment"
 *   for strategy verification and post-analysis.
 *
 * Constitutional Constraints:
 *   - READ-ONLY: Snapshots are observations, not recommendations
 *   - Label-only: CLI/telemetry display uses labels (no numerics)
 *   - Defensive: Never throws, always returns snapshot (even on error)
 *   - No prediction/optimization: Fixed snapshot logic only
 *
 * NOTE:
 *   - Numerics are allowed in saved files (for analysis)
 *   - Numerics are FORBIDDEN in CLI/telemetry display (use guards)
 */
Object.defineProperty(exports, "__esModule", { value: true });
