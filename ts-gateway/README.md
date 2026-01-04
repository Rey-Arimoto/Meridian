# Meridian TS Gateway (v0.1)

This gateway is the "hands" for Meridian.
It holds the Sui private key **only here** and exposes minimal HTTP APIs for swaps.

## Guarantees (v0.1)
- Private key never leaves TS gateway
- Python calls gateway over HTTP only
- Minimal health + swap endpoint

## Setup
```bash
cd ts-gateway
cp .env.example .env
# edit .env and set SUI_PRIVATE_KEY
npm install
npm run dev
