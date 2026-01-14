/**
 * PR155: v1.4 Price Oracle Integration - Exports
 *
 * Purpose:
 *   Central export point for oracle package.
 */

// Main oracle API
export { fetchOracleV1, createFallbackOracleResult, createErrorOracleResult } from "./oracle";

// Types
export type {
  OracleConfig,
  OracleResult,
  OracleStatus,
  PricePoint,
  PriceOracleSource,
} from "./types";
export { DEFAULT_ORACLE_CONFIG } from "./types";

// Guards (for testing/validation)
export {
  containsForbiddenVocab,
  containsNumericValue,
  validateWarningString,
  sanitizeWarning,
} from "./guards";

// Sources (for testing)
export {
  fetchDeepBookMidPrice,
  fetchUsdcPrice,
  createStalePricePoint,
} from "./sources/deepbookMid";
export {
  fetchCetusPoolPrice,
  createUnavailablePrice,
} from "./sources/cetusPool";
