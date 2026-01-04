import "dotenv/config";
import { getFullnodeUrl, SuiClient } from "@mysten/sui/client";
import { decodeSuiPrivateKey } from "@mysten/sui/cryptography";
import { Ed25519Keypair } from "@mysten/sui/keypairs/ed25519";

type SuiEnv = "mainnet" | "testnet" | "devnet";

const ENV = (process.env.SUI_ENV as SuiEnv) || "devnet";
const PRIVATE_KEY = process.env.SUI_PRIVATE_KEY;

if (!PRIVATE_KEY) {
  throw new Error("SUI_PRIVATE_KEY is not set (.env)");
}

const { schema, secretKey } = decodeSuiPrivateKey(PRIVATE_KEY);

// v0.1: only ED25519
if (schema !== "ED25519") {
  throw new Error(`Unsupported key schema: ${schema}`);
}

export const keypair = Ed25519Keypair.fromSecretKey(secretKey);
export const address = keypair.toSuiAddress();

export const suiClient = new SuiClient({
  url: getFullnodeUrl(ENV),
});

export const suiEnv = ENV;
