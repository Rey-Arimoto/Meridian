/**
 * PR163: v1.4 State Store (READ-ONLY)
 *
 * Purpose:
 *   Persistent state storage with atomic writes and defensive reads.
 *
 * Constitutional Constraints:
 *   - READ-ONLY: No learning, no optimization
 *   - Defensive: Never throws, returns status + warnings
 *   - Atomic writes: tmp→rename to prevent corruption
 *   - Safe defaults: Missing file → empty state
 */

import * as fs from "fs";
import * as path from "path";
import * as os from "os";
import { MeridianStateV1, StateStatus, createEmptyStateV1 } from "./types";

/**
 * State store interface
 */
export interface StateStore {
  readState(): Promise<{
    status: StateStatus;
    state: MeridianStateV1;
    warnings: string[];
  }>;

  writeState(next: MeridianStateV1): Promise<{
    status: StateStatus;
    warnings: string[];
  }>;

  patchState(patch: Partial<MeridianStateV1>): Promise<{
    status: StateStatus;
    state: MeridianStateV1;
    warnings: string[];
  }>;
}

/**
 * File-based state store
 */
export class FileStateStore implements StateStore {
  private readonly filePath: string;

  constructor(filePath?: string) {
    this.filePath =
      filePath ||
      process.env.MERIDIAN_STATE_PATH ||
      path.join(os.homedir(), ".meridian", "state.json");
  }

  /**
   * Read state from file (defensive)
   */
  async readState(): Promise<{
    status: StateStatus;
    state: MeridianStateV1;
    warnings: string[];
  }> {
    const warnings: string[] = [];

    try {
      // Check if file exists
      if (!fs.existsSync(this.filePath)) {
        warnings.push("WARN_STATE_FILE_NOT_FOUND");
        return {
          status: "OK",
          state: createEmptyStateV1(),
          warnings,
        };
      }

      // Read file
      const content = await fs.promises.readFile(this.filePath, "utf-8");

      // Parse JSON
      const parsed = JSON.parse(content);

      // Validate version
      if (parsed.version !== "v1") {
        warnings.push("WARN_STATE_VERSION_MISMATCH");
        return {
          status: "ERROR",
          state: createEmptyStateV1(),
          warnings,
        };
      }

      return {
        status: "OK",
        state: parsed as MeridianStateV1,
        warnings,
      };
    } catch (error) {
      warnings.push("WARN_STATE_READ_ERROR");

      if (error instanceof SyntaxError) {
        warnings.push("WARN_STATE_JSON_CORRUPT");
      }

      return {
        status: "ERROR",
        state: createEmptyStateV1(),
        warnings,
      };
    }
  }

  /**
   * Write state to file (atomic)
   */
  async writeState(next: MeridianStateV1): Promise<{
    status: StateStatus;
    warnings: string[];
  }> {
    const warnings: string[] = [];

    try {
      // Ensure directory exists
      const dir = path.dirname(this.filePath);
      if (!fs.existsSync(dir)) {
        await fs.promises.mkdir(dir, { recursive: true });
      }

      // Update timestamp
      next.updatedAtTs = Date.now();

      // Serialize
      const content = JSON.stringify(next, null, 2);

      // Atomic write: tmp→rename
      const tmpPath = `${this.filePath}.tmp`;
      await fs.promises.writeFile(tmpPath, content, "utf-8");
      await fs.promises.rename(tmpPath, this.filePath);

      return {
        status: "OK",
        warnings,
      };
    } catch (error) {
      warnings.push("WARN_STATE_WRITE_ERROR");

      return {
        status: "ERROR",
        warnings,
      };
    }
  }

  /**
   * Patch state (read-modify-write)
   */
  async patchState(patch: Partial<MeridianStateV1>): Promise<{
    status: StateStatus;
    state: MeridianStateV1;
    warnings: string[];
  }> {
    const warnings: string[] = [];

    try {
      // Read current state
      const readResult = await this.readState();
      warnings.push(...readResult.warnings);

      if (readResult.status === "ERROR") {
        return {
          status: "ERROR",
          state: readResult.state,
          warnings,
        };
      }

      // Merge patch
      const next: MeridianStateV1 = {
        ...readResult.state,
        ...patch,
        updatedAtTs: Date.now(),
      };

      // Write merged state
      const writeResult = await this.writeState(next);
      warnings.push(...writeResult.warnings);

      if (writeResult.status === "ERROR") {
        return {
          status: "ERROR",
          state: next,
          warnings,
        };
      }

      return {
        status: "OK",
        state: next,
        warnings,
      };
    } catch (error) {
      warnings.push("WARN_STATE_PATCH_ERROR");

      return {
        status: "ERROR",
        state: createEmptyStateV1(),
        warnings,
      };
    }
  }
}

/**
 * Create file state store
 *
 * @param filePath - Optional file path (defaults to ~/.meridian/state.json)
 * @returns State store instance
 */
export function createFileStateStore(filePath?: string): StateStore {
  return new FileStateStore(filePath);
}
