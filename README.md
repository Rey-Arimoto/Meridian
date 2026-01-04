Meridian

Meridian is an entropy-native intelligence for on-chain markets.
It earns alpha from entropy, protects capital from entropy, and refuses to act when entropy dominates.

Meridian is not a “trading bot.”
It is a stateful intelligence system designed to survive and profit in markets that become increasingly chaotic, reflexive, and automated.

⸻

Core Idea

Markets do not fail because of lack of strategies.
They fail because the underlying assumptions silently break.

Meridian treats entropy as a first-class state variable:

Entropy = how much the current market state becomes unexplained by existing rules, models, and strategies.

When entropy is low, structure exists → action is allowed.
When entropy rises, structure collapses → restraint becomes intelligence.

Meridian’s core belief:

The most valuable action in high-entropy markets is often non-action.

⸻

What Meridian Is (and Is Not)

Meridian IS
	•	An entropy-native market intelligence
	•	A system that earns alpha when structure emerges
	•	A system that automatically freezes when structure collapses
	•	A foundation for intelligence-native on-chain markets

Meridian IS NOT
	•	A high-frequency trading bot
	•	A prediction engine
	•	A “black box AI that always trades”
	•	A strategy optimized only for returns

⸻

Why Entropy?

Traditional indicators assume stability.
Entropy measures when that assumption itself breaks.

Meridian’s entropy is:
	•	Not volatility
	•	Not randomness
	•	Not noise

It is a measure of explanation failure.

When entropy crosses a constitutional threshold, Meridian must stop.

📄 Detailed definition:
👉 docs/entropy_spec.md

⸻

Constitution Summary (5 Lines)
	1.	Entropy is the primary state variable.
	2.	Action is permitted only when entropy allows explanation.
	3.	Non-action (NoOp) is a first-class decision.
	4.	Freeze is mandatory at critical entropy.
	5.	Survival precedes profit.

⸻

Current Status

Phase A — v0.1 ✅

Paper Trading Loop (Completed)
	•	Composite entropy calculation
	•	Entropy-based freeze (bp threshold)
	•	Deterministic decision loop
	•	CSV logging for every state and action
	•	Capital-preserving paper broker

Key property:

Meridian can prove why it did nothing.

⸻

Phase B — v0.2 (Starting)

Sui Objectization
	•	Meridian state becomes an on-chain object
	•	Deterministic state transitions
	•	Off-chain execution with on-chain verification
	•	No learning, no randomness, full reproducibility

⸻

Repository Structure

Meridian/
├── README.md
├── docs/
│   ├── vision.md          # Philosophy & long-term vision
│   ├── entropy_spec.md    # Formal entropy definition
│   └── decisions.md       # ADR (design decisions)
├── python/
│   ├── entropy.py         # Canonical entropy implementation
│   ├── core/              # Policy, guards, logging
│   ├── market/            # Price feeds
│   ├── brokers/           # Paper / real brokers
│   └── realtime/          # v0.1 execution loop
├── move/                  # (v0.2) On-chain contracts
├── ts-gateway/            # (future) execution gateway
└── logs/                  # Runtime logs (gitignored)

Running v0.1 (Paper)

cd Meridian
python3 -m venv .venv
source .venv/bin/activate
pip install requests pandas

python python/realtime/run_realtime.py

Logs are written to:

logs/meridian_realtime_log.csv

Design Decisions (ADR)

All irreversible design choices are documented.

👉 docs/decisions.md

This includes:
	•	Why entropy is primary
	•	Why freeze is mandatory
	•	Why learning is deferred
	•	Why non-action is explicit

⸻

Why This Matters

As markets move on-chain:
	•	Automation increases
	•	Reflexivity accelerates
	•	Failure cascades become faster

In such markets:

Survival itself becomes alpha.

Meridian is designed not for the next trade,
but for the next decade of intelligence-native markets.

⸻

Roadmap Snapshot
	•	v0.1: Entropy-aware paper intelligence ✅
	•	v0.2: On-chain state (Sui Objects)
	•	v0.5: Weak agent loop (Plan / Act / Reflect)
	•	v1.0: Integrated Intelligence-Native Market Agent

⸻

License

MIT License
See LICENSE

⸻

Final Note

Meridian is built under one assumption:

Markets will continue to become more complex faster than humans can react.

In that world,
the intelligence that knows when not to act will outlive the intelligence that always does.
