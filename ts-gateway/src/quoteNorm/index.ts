/**
 * PR187: v1.4 Routing + Quote Normalization v1 - Barrel Export
 *
 * Purpose:
 *   Central export point for quote normalization package.
 */

// Types
export type {
  QuoteSourceVenue,
  QuoteStatus,
  QuoteImpactLabel,
  QuoteDepthLabel,
  TradeSide,
  NormalizedQuoteV1,
  SanitizedQuote,
  DeepBookOrderbookSnapshot,
  CetusPoolSnapshot,
  QuoteSources,
} from "./types";

// Guards
export {
  sanitizeQuoteForLogs,
  isQuoteUsable,
  isQuoteStale,
  getQuoteStatusWithStalenessCheck,
} from "./guards";

// Normalizers
export { normalizeDeepBookQuote } from "./deepbookNormalizer";
export { normalizeCetusQuote } from "./cetusNormalizer";

// Router
export { selectAndNormalizeQuote } from "./router";
