/**
 * PR179: v1.4 Spec Version Lock + Human ACK Gate v1 - Types
 *
 * Purpose:
 *   Define spec version records, ACK records, and lock status.
 *
 * Constitutional Constraints:
 *   - Label-only: No numeric literals, addresses, or trading vocab in warnings/reasons
 *   - Defensive: Types support defensive parsing
 */

export type SpecVersion = string;

export type SpecSource = "PATCH_ADOPTION" | "MANUAL";

export interface SpecRecordV1 {
  kind: "SPEC_RECORD_V1";
  specVersion: SpecVersion; // opaque string (hash or id)
  createdAt: number; // epoch ms (internal only)
  source: SpecSource;
  warnings: string[]; // label-only
}

export type ReviewerKind =
  | "HUMAN_PRIMARY"
  | "HUMAN_SECONDARY"
  | "AUTO_ASSISTED"
  | "UNKNOWN";

export interface SpecAckRecordV1 {
  kind: "SPEC_ACK_V1";
  specVersion: SpecVersion;
  ackAt: number; // epoch ms (internal only)
  reviewer: ReviewerKind;
  reason: string; // label-only
  warnings: string[]; // label-only
}

export type SpecLockStatus =
  | "ACTIVE_OK"
  | "LOCKED_PENDING_ACK"
  | "LOCKED_EXPIRED"
  | "ERROR";

export interface SpecLockResultV1 {
  kind: "SPEC_LOCK_RESULT_V1";
  status: SpecLockStatus;
  activeSpec?: SpecVersion; // acked spec used for execution
  latestSpec?: SpecVersion; // newest spec produced
  ttlLabel?: "TTL_OK" | "TTL_EXPIRED" | "TTL_UNKNOWN";
  warnings: string[]; // label-only
}

export interface SpecLockConfig {
  ttlMs: number; // default 6h
}
