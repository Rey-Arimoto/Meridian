import { Transaction } from "@mysten/sui/transactions";
import { suiClient, keypair, address, suiEnv } from "./suiClient";
import { DeepSwapRequest, DeepSwapResponse } from "./types";

/**
 * v0.1 DeepBook executor (SKELETON)
 *
 * Why skeleton?
 * - DeepBook v3 SDK APIs and package names can differ by version.
 * - We freeze the boundary:
 *     Request -> build tx -> signAndExecute -> response
 *
 * v0.2 will:
 * - pin DeepBook v3 SDK package/version
 * - implement real swap calls
 * - parse amountOut from events/effects deterministically
 */
export async function execDeepSwap(req: DeepSwapRequest): Promise<DeepSwapResponse> {
  const tx = new Transaction();

  try {
    // ---- TODO(v0.2): integrate DeepBook v3 swap builder ----
    // Example pseudocode:
    //   if (req.side === "base_to_quote") { deepbook.swapExactBaseForQuote(...)(tx) }
    //   else { deepbook.swapExactQuoteForBase(...)(tx) }
    //
    // v0.1: we do NOT perform real swap here unless DeepBook SDK is wired.

    throw new Error(
      `DeepBook swap is not wired in v0.1 skeleton. (env=${suiEnv})`
    );

    // const res = await suiClient.signAndExecuteTransaction({
    //   transaction: tx,
    //   signer: keypair,
    //   options: { showEffects: true, showEvents: true },
    // });
    //
    // const amountOut = 0; // TODO(v0.2): parse events/effects
    //
    // return { ok: true, side: req.side, poolKey: req.poolKey, amount: req.amount, amountOut, txDigest: res.digest, clientOrderId: req.clientOrderId };

  } catch (e: any) {
    return {
      ok: false,
      side: req.side,
      poolKey: req.poolKey,
      amount: req.amount,
      amountOut: 0,
      txDigest: undefined,
      clientOrderId: req.clientOrderId,
      errorMessage: String(e?.message ?? e),
    };
  }
}
