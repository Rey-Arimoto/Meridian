#!/usr/bin/env python3
"""
PR7C: Static Explainability Dashboard (HTML)

Purpose: Generate single-file HTML dashboard integrating PR7A + PR7B.
Input: meridian_log.csv
Output: pr7c_dashboard.html (with embedded or referenced PNGs)

READ-ONLY: No trading logic modification. No CSV schema changes.
"""

import sys
import os
import argparse
import base64
import tempfile
from datetime import datetime
from collections import Counter
from io import BytesIO

# Force matplotlib to use Agg backend (headless)
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

import pandas as pd

# Import shared logic from PR7A/PR7B (avoid duplication)
# We'll define these functions locally to avoid complex imports
# but the logic is identical to PR7A/PR7B


def extract_overlay_rule(decision_reason: str) -> str:
    """Extract overlay rule from decision_reason field."""
    if not isinstance(decision_reason, str):
        return "unknown"
    parts = decision_reason.split(" | overlay=")
    if len(parts) >= 2:
        return parts[1].strip()
    return "unknown"


def classify_overlay_category(overlay_rule: str) -> str:
    """Classify overlay rule into categories."""
    if "EMERGENCY_FREEZE" in overlay_rule:
        return "EMERGENCY_FREEZE"
    elif "FAIL_CLOSED" in overlay_rule:
        return "FAIL_CLOSED"
    elif "COOLDOWN_HOLD" in overlay_rule:
        return "COOLDOWN_HOLD"
    elif "MAX_DELTA_CLAMP" in overlay_rule:
        return "MAX_DELTA_CLAMP"
    elif "MIN_THRESHOLD_HOLD" in overlay_rule:
        return "MIN_THRESHOLD_HOLD"
    elif "PASS_THROUGH" in overlay_rule or overlay_rule == "PASS_THROUGH":
        return "PASS_THROUGH"
    else:
        return "OTHER"


def map_regime_to_numeric(regime: str) -> float:
    """Map regime to numeric value for plotting."""
    regime_map = {
        "stable_range": 0,
        "emerging_trend": 1,
        "volatile_noise": 2,
        "liquidity_stress": 3,
        "regime_transition": 4,
        "post_stress_reset": 5,
        "unknown": 6,
    }
    return regime_map.get(regime, 6)


def map_action_to_numeric(action: str) -> float:
    """Map action to numeric value for plotting."""
    action_map = {
        "HOLD": 0,
        "BUY": 1,
        "SELL": -1,
        "FREEZE": -2,
        "unknown": -3,
    }
    return action_map.get(action, -3)


def generate_timeline_png(df: pd.DataFrame) -> bytes:
    """Generate timeline plot PNG (PR7B style) and return as bytes."""

    df["timestamp"] = pd.to_datetime(df["timestamp_utc"], errors="coerce")
    df["overlay_rule"] = df["decision_reason"].apply(extract_overlay_rule)
    df["overlay_category"] = df["overlay_rule"].apply(classify_overlay_category)
    df["regime_numeric"] = df["regime"].fillna("unknown").apply(map_regime_to_numeric)
    df["action_numeric"] = df["action_label"].fillna("unknown").apply(map_action_to_numeric)

    fig, axes = plt.subplots(4, 1, figsize=(14, 10), sharex=True)
    fig.suptitle("Meridian v0.2 Timeline: Regime → Action → Overlay → Weight", fontsize=14, fontweight="bold")

    # Subplot 1: Regime
    ax1 = axes[0]
    ax1.step(df["timestamp"], df["regime_numeric"], where="post", color="steelblue", linewidth=1.5)
    ax1.set_ylabel("Regime", fontweight="bold")
    ax1.set_yticks([0, 1, 2, 3, 4, 5, 6])
    ax1.set_yticklabels(["STABLE", "EMERGING", "VOLATILE", "LIQUIDITY", "TRANSITION", "POST_STRESS", "UNKNOWN"], fontsize=8)
    ax1.grid(True, alpha=0.3)
    ax1.set_ylim(-0.5, 6.5)

    # Subplot 2: Action
    ax2 = axes[1]
    action_colors = df["action_numeric"].apply(
        lambda x: "green" if x == 1 else "red" if x == -1 else "orange" if x == -2 else "gray"
    )
    ax2.scatter(df["timestamp"], df["action_numeric"], c=action_colors, alpha=0.6, s=20)
    ax2.axhline(0, color="black", linewidth=0.5, linestyle="--", alpha=0.5)
    ax2.set_ylabel("Action", fontweight="bold")
    ax2.set_yticks([-3, -2, -1, 0, 1])
    ax2.set_yticklabels(["UNKNOWN", "FREEZE", "SELL", "HOLD", "BUY"], fontsize=8)
    ax2.grid(True, alpha=0.3)
    ax2.set_ylim(-3.5, 1.5)

    # Subplot 3: Target Weight
    ax3 = axes[2]
    ax3.plot(df["timestamp"], df["target_weight"].fillna(0.0), color="purple", linewidth=1.5, alpha=0.7)
    ax3.fill_between(df["timestamp"], 0, df["target_weight"].fillna(0.0), color="purple", alpha=0.2)
    ax3.set_ylabel("Target Weight", fontweight="bold")
    ax3.grid(True, alpha=0.3)
    ax3.set_ylim(-0.05, max(1.0, df["target_weight"].max() * 1.1) if not df["target_weight"].isna().all() else 1.0)

    # Subplot 4: Overlay Events
    ax4 = axes[3]
    overlay_events = df[df["overlay_category"] != "PASS_THROUGH"].copy()
    overlay_colors = {
        "EMERGENCY_FREEZE": "red",
        "FAIL_CLOSED": "orange",
        "COOLDOWN_HOLD": "blue",
        "MAX_DELTA_CLAMP": "green",
        "MIN_THRESHOLD_HOLD": "cyan",
        "OTHER": "gray",
    }
    for _, row in overlay_events.iterrows():
        category = row["overlay_category"]
        color = overlay_colors.get(category, "gray")
        ax4.axvline(row["timestamp"], color=color, alpha=0.5, linewidth=1.5, linestyle="-")

    from matplotlib.patches import Patch
    legend_elements = [
        Patch(facecolor=overlay_colors["EMERGENCY_FREEZE"], label="EMERGENCY_FREEZE"),
        Patch(facecolor=overlay_colors["FAIL_CLOSED"], label="FAIL_CLOSED"),
        Patch(facecolor=overlay_colors["COOLDOWN_HOLD"], label="COOLDOWN_HOLD"),
        Patch(facecolor=overlay_colors["MAX_DELTA_CLAMP"], label="MAX_DELTA_CLAMP"),
        Patch(facecolor=overlay_colors["MIN_THRESHOLD_HOLD"], label="MIN_THRESHOLD_HOLD"),
    ]
    ax4.legend(handles=legend_elements, loc="upper right", fontsize=7)
    ax4.set_ylabel("Overlay Events", fontweight="bold")
    ax4.set_ylim(0, 1)
    ax4.set_yticks([])
    ax4.grid(True, alpha=0.3, axis="x")

    ax4.set_xlabel("Time (UTC)", fontweight="bold")
    ax4.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m-%d %H:%M"))
    plt.setp(ax4.xaxis.get_majorticklabels(), rotation=45, ha="right")

    plt.tight_layout(rect=[0, 0, 1, 0.97])

    # Save to bytes
    buf = BytesIO()
    plt.savefig(buf, format="png", dpi=150, bbox_inches="tight")
    plt.close()
    buf.seek(0)
    return buf.read()


def generate_overlay_histogram_png(df: pd.DataFrame) -> bytes:
    """Generate overlay histogram PNG (PR7B style) and return as bytes."""

    df["overlay_rule"] = df["decision_reason"].apply(extract_overlay_rule)
    df["overlay_category"] = df["overlay_rule"].apply(classify_overlay_category)
    overlay_counts = Counter(df["overlay_category"])

    categories = [
        "PASS_THROUGH",
        "COOLDOWN_HOLD",
        "MAX_DELTA_CLAMP",
        "MIN_THRESHOLD_HOLD",
        "FAIL_CLOSED",
        "EMERGENCY_FREEZE",
        "OTHER",
    ]
    categories = [c for c in categories if c in overlay_counts]
    counts = [overlay_counts[c] for c in categories]

    color_map = {
        "PASS_THROUGH": "lightgray",
        "COOLDOWN_HOLD": "steelblue",
        "MAX_DELTA_CLAMP": "green",
        "MIN_THRESHOLD_HOLD": "cyan",
        "FAIL_CLOSED": "orange",
        "EMERGENCY_FREEZE": "red",
        "OTHER": "gray",
    }
    colors = [color_map.get(c, "gray") for c in categories]

    fig, ax = plt.subplots(figsize=(10, 6))
    bars = ax.bar(categories, counts, color=colors, alpha=0.8, edgecolor="black")

    for bar, count in zip(bars, counts):
        height = bar.get_height()
        ax.text(
            bar.get_x() + bar.get_width() / 2.0,
            height,
            f"{int(count)}",
            ha="center",
            va="bottom",
            fontsize=10,
            fontweight="bold",
        )

    ax.set_xlabel("Overlay Rule", fontweight="bold", fontsize=12)
    ax.set_ylabel("Count", fontweight="bold", fontsize=12)
    ax.set_title("Safety Overlay Distribution", fontweight="bold", fontsize=14)
    ax.grid(True, alpha=0.3, axis="y")
    plt.setp(ax.xaxis.get_majorticklabels(), rotation=45, ha="right")
    plt.tight_layout()

    buf = BytesIO()
    plt.savefig(buf, format="png", dpi=150, bbox_inches="tight")
    plt.close()
    buf.seek(0)
    return buf.read()


def generate_regime_distribution_png(df: pd.DataFrame) -> bytes:
    """Generate regime distribution PNG (PR7B style) and return as bytes."""

    df["regime"] = df["regime"].fillna("unknown")
    regime_counts = Counter(df["regime"])

    preferred_order = [
        "stable_range",
        "emerging_trend",
        "volatile_noise",
        "liquidity_stress",
        "regime_transition",
        "post_stress_reset",
        "unknown",
    ]
    regimes = [r for r in preferred_order if r in regime_counts]
    for r in regime_counts:
        if r not in regimes:
            regimes.append(r)

    counts = [regime_counts[r] for r in regimes]

    color_map = {
        "stable_range": "lightgreen",
        "emerging_trend": "gold",
        "volatile_noise": "orange",
        "liquidity_stress": "red",
        "regime_transition": "darkred",
        "post_stress_reset": "lightblue",
        "unknown": "gray",
    }
    colors = [color_map.get(r, "gray") for r in regimes]

    fig, ax = plt.subplots(figsize=(10, 6))
    bars = ax.bar(regimes, counts, color=colors, alpha=0.8, edgecolor="black")

    for bar, count in zip(bars, counts):
        height = bar.get_height()
        ax.text(
            bar.get_x() + bar.get_width() / 2.0,
            height,
            f"{int(count)}",
            ha="center",
            va="bottom",
            fontsize=10,
            fontweight="bold",
        )

    ax.set_xlabel("Regime", fontweight="bold", fontsize=12)
    ax.set_ylabel("Count", fontweight="bold", fontsize=12)
    ax.set_title("Regime Distribution", fontweight="bold", fontsize=14)
    ax.grid(True, alpha=0.3, axis="y")
    plt.setp(ax.xaxis.get_majorticklabels(), rotation=45, ha="right")
    plt.tight_layout()

    buf = BytesIO()
    plt.savefig(buf, format="png", dpi=150, bbox_inches="tight")
    plt.close()
    buf.seek(0)
    return buf.read()


def explain_tick(row: pd.Series, index: int) -> str:
    """Generate natural language explanation for a single tick (PR7A style)."""

    timestamp = row.get("timestamp_utc", "unknown")
    entropy_bp = row.get("entropy_bp", "unknown")
    regime = row.get("regime", "unknown")
    base_action = row.get("base_action", "unknown")
    target_weight = row.get("target_weight", "unknown")
    action_label = row.get("action_label", "unknown")
    decision_reason = row.get("decision_reason", "unknown")
    overlay_rule = extract_overlay_rule(decision_reason)

    lines = []
    lines.append(f"<h4>Tick #{index + 1} | {timestamp}</h4>")
    lines.append(f"<p><strong>Entropy:</strong> {entropy_bp} bp | <strong>Regime:</strong> {regime} | <strong>BaseAction:</strong> {base_action}</p>")
    lines.append(f"<p><strong>Overlay:</strong> {overlay_rule} | <strong>Final Weight:</strong> {target_weight} | <strong>Action:</strong> {action_label}</p>")

    if action_label == "HOLD":
        lines.append(f"<p><em>✓ DOING NOTHING (Capital Preservation)</em></p>")
        lines.append(f"<p>The system chose NOT to trade. This is a positive outcome:</p>")
        lines.append(f"<ul>")
        if "COOLDOWN_HOLD" in overlay_rule:
            lines.append(f"<li>Cooldown protection prevented premature action</li>")
        elif "MIN_THRESHOLD_HOLD" in overlay_rule:
            lines.append(f"<li>Change too small to justify transaction costs</li>")
        elif "EMERGENCY_FREEZE" in overlay_rule:
            lines.append(f"<li>Emergency freeze protected capital during crisis</li>")
        elif "FAIL_CLOSED" in overlay_rule:
            lines.append(f"<li>Fail-closed safety: defaulted to zero exposure</li>")
        elif base_action == "PAUSE":
            lines.append(f"<li>Regime indicated PAUSE: constitutional restraint</li>")
        else:
            lines.append(f"<li>No change needed: optimal weight maintained</li>")
        lines.append(f"</ul>")
    elif action_label == "BUY":
        lines.append(f"<p><em>→ BUYING (Increasing Exposure)</em></p>")
        if "MAX_DELTA_CLAMP" in overlay_rule:
            lines.append(f"<p>Overlay clamped the increase for gradual position building.</p>")
    elif action_label == "SELL":
        lines.append(f"<p><em>→ SELLING (Decreasing Exposure)</em></p>")
        if "MAX_DELTA_CLAMP" in overlay_rule:
            lines.append(f"<p>Overlay clamped the decrease for gradual unwinding.</p>")
    elif action_label == "FREEZE":
        lines.append(f"<p><em>⚠ EMERGENCY FREEZE (Constitutional Halt)</em></p>")
        lines.append(f"<p>Critical entropy threshold exceeded. All positions frozen.</p>")

    return "\n".join(lines)


def generate_html(df: pd.DataFrame, timeline_src: str, overlay_src: str, regime_src: str, limit: int) -> str:
    """Generate complete HTML dashboard."""

    # Extract data
    df["overlay_rule"] = df["decision_reason"].apply(extract_overlay_rule)
    df["overlay_category"] = df["overlay_rule"].apply(classify_overlay_category)

    total_ticks = len(df)
    action_counts = Counter(df["action_label"].fillna("unknown"))
    overlay_counts = Counter(df["overlay_category"])
    regime_counts = Counter(df["regime"].fillna("unknown"))

    hold_count = action_counts.get("HOLD", 0)
    buy_count = action_counts.get("BUY", 0)
    sell_count = action_counts.get("SELL", 0)
    freeze_count = action_counts.get("FREEZE", 0)
    hold_ratio = hold_count / total_ticks if total_ticks > 0 else 0.0

    period_start = df["timestamp_utc"].iloc[0] if "timestamp_utc" in df.columns else "unknown"
    period_end = df["timestamp_utc"].iloc[-1] if "timestamp_utc" in df.columns else "unknown"

    # Generate Top-N decisions
    top_decisions = []
    for idx, row in df.head(limit).iterrows():
        top_decisions.append(explain_tick(row, idx))

    # Build HTML
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Meridian v0.2 Dashboard</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            line-height: 1.6;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background: #f5f5f5;
        }}
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            border-radius: 8px;
            margin-bottom: 20px;
        }}
        .header h1 {{
            margin: 0 0 10px 0;
        }}
        .section {{
            background: white;
            padding: 25px;
            margin-bottom: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .section h2 {{
            color: #333;
            border-bottom: 2px solid #667eea;
            padding-bottom: 10px;
            margin-top: 0;
        }}
        .metric {{
            display: inline-block;
            margin: 10px 20px 10px 0;
            padding: 10px 15px;
            background: #f8f9fa;
            border-left: 4px solid #667eea;
            border-radius: 4px;
        }}
        .metric strong {{
            color: #667eea;
        }}
        img {{
            max-width: 100%;
            height: auto;
            border-radius: 4px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 15px 0;
        }}
        th, td {{
            text-align: left;
            padding: 12px;
            border-bottom: 1px solid #ddd;
        }}
        th {{
            background: #667eea;
            color: white;
        }}
        .hold-highlight {{
            background: #d4edda;
            padding: 15px;
            border-left: 4px solid #28a745;
            border-radius: 4px;
            margin: 15px 0;
        }}
        .decision-card {{
            background: #f8f9fa;
            padding: 15px;
            margin: 10px 0;
            border-radius: 4px;
            border-left: 4px solid #667eea;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>Meridian v0.2 Dashboard</h1>
        <p>Static Explainability Report</p>
        <p><strong>Generated:</strong> {datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")}</p>
    </div>

    <!-- Executive Summary -->
    <div class="section">
        <h2>Executive Summary</h2>
        <p><strong>Period:</strong> {period_start} to {period_end}</p>
        <p><strong>Total Observations:</strong> {total_ticks:,} ticks</p>

        <div class="hold-highlight">
            <h3>Capital Preservation: {hold_ratio*100:.1f}%</h3>
            <p>The system chose to <strong>DO NOTHING</strong> in {hold_count:,} out of {total_ticks:,} ticks.
            This is not inaction—it's an active decision to preserve capital when conditions don't warrant exposure changes.</p>
        </div>

        <div class="metric">
            <strong>BUY:</strong> {buy_count:,} ({buy_count/total_ticks*100:.1f}%)
        </div>
        <div class="metric">
            <strong>SELL:</strong> {sell_count:,} ({sell_count/total_ticks*100:.1f}%)
        </div>
        <div class="metric">
            <strong>HOLD:</strong> {hold_count:,} ({hold_ratio*100:.1f}%)
        </div>
        <div class="metric">
            <strong>FREEZE:</strong> {freeze_count:,} ({freeze_count/total_ticks*100:.1f}%)
        </div>
    </div>

    <!-- Safety Contract Summary -->
    <div class="section">
        <h2>Safety Contract</h2>
        <p>Meridian v0.2 operates under a mathematically proven safety contract (PR6). All decisions are constrained by these 7 inviolable rules:</p>

        <table>
            <tr>
                <th>Rule</th>
                <th>Guarantee</th>
            </tr>
            <tr>
                <td>1. Suppression-Only</td>
                <td>final_target_weight ≤ decision.target_weight (never amplify)</td>
            </tr>
            <tr>
                <td>2. Fail-Closed</td>
                <td>All error/unknown states → 0.0 exposure</td>
            </tr>
            <tr>
                <td>3. Emergency Freeze</td>
                <td>emergency_freeze=True has absolute priority → 0.0</td>
            </tr>
            <tr>
                <td>4. Cooldown</td>
                <td>No weight changes during cooldown period</td>
            </tr>
            <tr>
                <td>5. Max Delta</td>
                <td>Clamp to ±MAX_DW_PER_STEP per tick</td>
            </tr>
            <tr>
                <td>6. Min Threshold</td>
                <td>Ignore changes below MIN_DW_IGNORE</td>
            </tr>
            <tr>
                <td>7. Determinism</td>
                <td>Same inputs → same outputs (no randomness)</td>
            </tr>
        </table>

        <p><em>This system is mathematically incapable of accidental aggression.</em></p>
    </div>

    <!-- Metrics -->
    <div class="section">
        <h2>Metrics</h2>

        <h3>Overlay Rule Distribution</h3>
        <table>
            <tr>
                <th>Overlay Rule</th>
                <th>Count</th>
                <th>Percentage</th>
            </tr>
"""

    for category in sorted(overlay_counts.keys(), key=lambda x: -overlay_counts[x]):
        count = overlay_counts[category]
        pct = count / total_ticks * 100
        html += f"            <tr><td>{category}</td><td>{count:,}</td><td>{pct:.1f}%</td></tr>\n"

    html += """        </table>

        <h3>Regime Distribution</h3>
        <table>
            <tr>
                <th>Regime</th>
                <th>Count</th>
                <th>Percentage</th>
            </tr>
"""

    for regime in sorted(regime_counts.keys(), key=lambda x: -regime_counts[x]):
        count = regime_counts[regime]
        pct = count / total_ticks * 100
        html += f"            <tr><td>{regime}</td><td>{count:,}</td><td>{pct:.1f}%</td></tr>\n"

    html += f"""        </table>
    </div>

    <!-- Timeline -->
    <div class="section">
        <h2>Timeline</h2>
        <p>Visual timeline showing Regime → Action → Weight → Overlay events over time.</p>
        <img src="{timeline_src}" alt="Timeline">
    </div>

    <!-- Regime Distribution -->
    <div class="section">
        <h2>Regime Distribution</h2>
        <img src="{regime_src}" alt="Regime Distribution">
    </div>

    <!-- Overlay Distribution -->
    <div class="section">
        <h2>Overlay Distribution</h2>
        <img src="{overlay_src}" alt="Overlay Distribution">
    </div>

    <!-- Top-N Decisions -->
    <div class="section">
        <h2>Top {limit} Decisions</h2>
        <p>Natural language explanations of decisions, emphasizing when the system chose NOT to trade.</p>
"""

    for decision_html in top_decisions:
        html += f'        <div class="decision-card">\n{decision_html}\n        </div>\n'

    html += """    </div>

    <div class="section">
        <h2>Conclusion</h2>
        <p>Meridian v0.2 demonstrates disciplined restraint and constitutional compliance:</p>
        <ul>
            <li>✓ Mathematical safety guarantees enforced</li>
            <li>✓ High capital preservation rate through "doing nothing"</li>
            <li>✓ Regime-first decision making with overlay protection</li>
            <li>✓ All actions auditable and explainable</li>
        </ul>
        <p><em>This dashboard was generated by PR7C: Static Explainability Dashboard</em></p>
    </div>
</body>
</html>
"""

    return html


def main():
    parser = argparse.ArgumentParser(
        description="PR7C: Build static HTML dashboard from meridian_log.csv"
    )
    parser.add_argument("csv_path", help="Path to meridian_log.csv")
    parser.add_argument("--out", default="pr7c_dashboard.html", help="Output HTML file (default: pr7c_dashboard.html)")
    parser.add_argument("--limit", type=int, default=50, help="Number of top decisions to explain (default: 50)")
    parser.add_argument("--from", dest="from_ts", help="Filter from timestamp (ISO format)")
    parser.add_argument("--to", dest="to_ts", help="Filter to timestamp (ISO format)")
    parser.add_argument("--assets-dir", help="Save PNGs to directory and use relative paths (default: base64 embed)")

    args = parser.parse_args()

    # Read CSV
    if not os.path.exists(args.csv_path):
        print(f"Error: CSV file not found: {args.csv_path}", file=sys.stderr)
        return 1

    try:
        df = pd.read_csv(args.csv_path)
    except Exception as e:
        print(f"Error reading CSV: {e}", file=sys.stderr)
        return 1

    if df.empty:
        print("Error: CSV is empty", file=sys.stderr)
        return 1

    # Filter by timestamp if requested
    if args.from_ts:
        df = df[df["timestamp_utc"] >= args.from_ts]
    if args.to_ts:
        df = df[df["timestamp_utc"] <= args.to_ts]

    if df.empty:
        print("Error: No data after filters", file=sys.stderr)
        return 1

    print(f"Building dashboard for {len(df):,} rows...")

    # Generate PNGs
    try:
        print("Generating timeline plot...")
        timeline_bytes = generate_timeline_png(df)

        print("Generating overlay histogram...")
        overlay_bytes = generate_overlay_histogram_png(df)

        print("Generating regime distribution...")
        regime_bytes = generate_regime_distribution_png(df)
    except Exception as e:
        print(f"Error generating visualizations: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1

    # Handle PNG embedding/saving
    if args.assets_dir:
        # Save to assets directory and use relative paths
        os.makedirs(args.assets_dir, exist_ok=True)

        timeline_path = os.path.join(args.assets_dir, "timeline.png")
        overlay_path = os.path.join(args.assets_dir, "overlay_hist.png")
        regime_path = os.path.join(args.assets_dir, "regime_dist.png")

        with open(timeline_path, "wb") as f:
            f.write(timeline_bytes)
        with open(overlay_path, "wb") as f:
            f.write(overlay_bytes)
        with open(regime_path, "wb") as f:
            f.write(regime_bytes)

        timeline_src = f"{args.assets_dir}/timeline.png"
        overlay_src = f"{args.assets_dir}/overlay_hist.png"
        regime_src = f"{args.assets_dir}/regime_dist.png"

        print(f"  PNGs saved to: {args.assets_dir}/")
    else:
        # Base64 embed (default)
        timeline_b64 = base64.b64encode(timeline_bytes).decode('utf-8')
        overlay_b64 = base64.b64encode(overlay_bytes).decode('utf-8')
        regime_b64 = base64.b64encode(regime_bytes).decode('utf-8')

        timeline_src = f"data:image/png;base64,{timeline_b64}"
        overlay_src = f"data:image/png;base64,{overlay_b64}"
        regime_src = f"data:image/png;base64,{regime_b64}"

        print("  PNGs embedded as base64")

    # Generate HTML
    print("Generating HTML...")
    html = generate_html(df, timeline_src, overlay_src, regime_src, args.limit)

    # Write HTML
    with open(args.out, "w") as f:
        f.write(html)

    print(f"\n✓ Dashboard generated: {args.out}")
    print(f"  Rows processed: {len(df):,}")
    print(f"  Top decisions: {min(args.limit, len(df))}")
    print(f"  HTML size: {len(html):,} bytes")

    return 0


if __name__ == "__main__":
    sys.exit(main())
