# Meridian v0.1 — Python Reference Implementation (Frozen)

This directory contains the **frozen Python reference implementation**
corresponding exactly to Meridian v0.1.

## Guarantees
- Deterministic behavior
- Composite Entropy with basis-point scaling
- Constitutional entropy freeze (NoOp / Freeze)
- Full CSV audit log per tick

## Scope (v0.1)
- Paper execution only
- Single-asset loop
- No learning, no agent autonomy

## Entry point
python realtime/run_realtime.py

## Immutability
This directory MUST NOT be modified.
All future development happens outside code/v0.1.

