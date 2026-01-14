/**
 * PR156: v1.4 Auto Execution Policy (Aggressive + HardStop) - Exports
 *
 * Purpose:
 *   Central export point for policy package.
 */

// Main policy API
export {
  evaluateExecutionPolicy,
  isExecutionAllowed,
  checkEnvKey,
  getPolicySummary,
} from "./policy";

// HardStop management
export {
  createInitialHardStopState,
  updateHardStopState,
  isHardStopExpired,
  deactivateHardStop,
  activateHardStop,
  getHardStopSummary,
} from "./hardStop";

// Heartbeat monitoring
export {
  runHeartbeat,
  getHeartbeatSummary,
  isHeartbeatHealthy,
} from "./heartbeat";

// Types
export type {
  PolicyStatus,
  HardStopReason,
  HardStopState,
  PolicyResult,
  PolicyInput,
  HeartbeatStatus,
  HeartbeatResult,
} from "./types";

// Guards (for testing/validation)
export {
  containsForbiddenVocab,
  containsTokenLiteral,
  containsNumericLike,
  containsPrescriptive,
  validateLabelOnlyStrings,
  sanitizeWarnings,
  validatePolicyOutput,
} from "./guards";
