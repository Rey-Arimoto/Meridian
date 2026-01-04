import "dotenv/config";
import express from "express";
import bodyParser from "body-parser";
import { execDeepSwap } from "./deepbookExecutor";
import { DeepSwapRequest, DeepSwapResponse } from "./types";
import { address, suiEnv } from "./suiClient";

const app = express();
app.use(bodyParser.json());

app.get("/api/health", (_req, res) => {
  res.json({
    ok: true,
    service: "meridian-ts-gateway",
    env: suiEnv,
    address,
  });
});

app.post("/api/swap_deepbook", async (req, res) => {
  const payload = req.body as DeepSwapRequest;

  // Minimal validation (v0.1)
  if (!payload?.side || !payload?.poolKey) {
    res.status(400).json({
      ok: false,
      side: payload?.side ?? "base_to_quote",
      poolKey: payload?.poolKey ?? "UNKNOWN",
      amount: payload?.amount ?? 0,
      amountOut: 0,
      errorMessage: "Invalid payload: side/poolKey required",
    } satisfies DeepSwapResponse);
    return;
  }

  try {
    const result = await execDeepSwap(payload);

    if (!result.ok) {
      res.status(500).json(result);
      return;
    }

    res.json(result);
  } catch (e: any) {
    res.status(500).json({
      ok: false,
      side: payload.side,
      poolKey: payload.poolKey,
      amount: payload.amount,
      amountOut: 0,
      clientOrderId: payload.clientOrderId,
      errorMessage: String(e?.message ?? e),
    } satisfies DeepSwapResponse);
  }
});

const PORT = Number(process.env.PORT || "3000");
app.listen(PORT, () => {
  console.log(`meridian-ts-gateway listening on :${PORT}`);
  console.log(`env=${suiEnv} address=${address}`);
});
