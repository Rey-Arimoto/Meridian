#!/usr/bin/env python3
"""
PR9A: Performance & Risk Summary Report

Purpose: Calculate performance and risk metrics from meridian_log.csv.
Input: meridian_log.csv
Output: stdout + optional Markdown file

READ-ONLY: No trading logic modification. No CSV schema changes.
Deterministic: No network, no randomness.
"""

import sys
import os
import argparse
from datetime import datetime
import pandas as pd
import numpy as np


def extract_overlay_rule(decision_reason: str) -> str:
    """Extract overlay rule from decision_reason field."""
    if not isinstance(decision_reason, str):
        return "unknown"
    parts = decision_reason.split(" | overlay=")
    if len(parts) >= 2:
        return parts[1].strip()
    return "unknown"


def calculate_max_drawdown(equity_series: pd.Series) -> float:
    """
    Calculate maximum drawdown from equity time series.

    Max Drawdown = max((peak - valley) / peak) over all time windows
    Returns percentage (e.g., 15.0 for 15% drawdown)
    """
    if equity_series.empty or equity_series.isna().all():
        return np.nan

    # Calculate running maximum (peak)
    running_max = equity_series.expanding().max()

    # Calculate drawdown at each point
    drawdown = (running_max - equity_series) / running_max

    # Maximum drawdown as percentage
    max_dd = drawdown.max() * 100.0

    return max_dd if not np.isnan(max_dd) else 0.0


def calculate_time_under_water(equity_series: pd.Series) -> int:
    """
    Calculate maximum time under water (TUW) in ticks.

    TUW = number of ticks from peak to recovery (back to peak or higher).
    Returns the maximum TUW across all drawdown periods.

    Returns -1 if equity is N/A or empty.
    """
    if equity_series.empty or equity_series.isna().all():
        return -1

    equity = equity_series.reset_index(drop=True)
    running_max = equity.expanding().max()

    max_tuw = 0
    current_tuw = 0

    for i in range(len(equity)):
        if equity.iloc[i] < running_max.iloc[i]:
            # Under water
            current_tuw += 1
            max_tuw = max(max_tuw, current_tuw)
        else:
            # At or above peak - reset
            current_tuw = 0

    return max_tuw


def calculate_max_drawdown_duration(equity_series: pd.Series) -> int:
    """
    Calculate maximum drawdown duration in ticks.

    Duration = length of the longest continuous drawdown period.

    Returns -1 if equity is N/A or empty.
    """
    if equity_series.empty or equity_series.isna().all():
        return -1

    equity = equity_series.reset_index(drop=True)
    running_max = equity.expanding().max()
    drawdown = (running_max - equity) / running_max

    # Find the maximum drawdown value
    max_dd_value = drawdown.max()

    if np.isnan(max_dd_value) or max_dd_value == 0:
        return 0

    # Find all periods where drawdown equals max drawdown
    # Allow small tolerance for floating point comparison
    tolerance = 1e-9
    max_duration = 0
    current_duration = 0
    in_max_dd = False

    for i in range(len(drawdown)):
        if abs(drawdown.iloc[i] - max_dd_value) < tolerance:
            if not in_max_dd:
                in_max_dd = True
                current_duration = 1
            else:
                current_duration += 1
            max_duration = max(max_duration, current_duration)
        else:
            in_max_dd = False
            current_duration = 0

    return max_duration


def calculate_exposure_ratio(weights: pd.Series) -> float:
    """
    Calculate exposure ratio: fraction of ticks with non-zero weight.

    Returns -1.0 if weights are N/A or empty.
    """
    if weights.empty or weights.isna().all():
        return -1.0

    weights_clean = weights.dropna()
    if len(weights_clean) == 0:
        return -1.0

    exposed_count = (weights_clean.abs() > 0).sum()
    return exposed_count / len(weights_clean)


def calculate_turnover_proxy(weights: pd.Series) -> float:
    """
    Calculate turnover proxy: mean absolute weight change per tick.

    Returns -1.0 if weights are N/A or empty.
    """
    if weights.empty or weights.isna().all():
        return -1.0

    weights_clean = weights.dropna()
    if len(weights_clean) < 2:
        return -1.0

    weight_changes = weights_clean.diff().abs()
    return weight_changes.mean()


def calculate_action_switch_rate(actions: pd.Series) -> float:
    """
    Calculate action switch rate: fraction of ticks where action changed.

    Returns -1.0 if actions are N/A or empty.
    """
    if actions.empty or actions.isna().all():
        return -1.0

    actions_clean = actions.dropna()
    if len(actions_clean) < 2:
        return -1.0

    switches = (actions_clean != actions_clean.shift()).sum() - 1  # -1 to exclude first row
    return switches / (len(actions_clean) - 1)


def calculate_longest_streak(actions: pd.Series, target_action: str) -> int:
    """
    Calculate longest consecutive streak of a specific action.

    Returns -1 if actions are N/A or empty.
    """
    if actions.empty or actions.isna().all():
        return -1

    actions_clean = actions.fillna("unknown")

    max_streak = 0
    current_streak = 0

    for action in actions_clean:
        if action == target_action:
            current_streak += 1
            max_streak = max(max_streak, current_streak)
        else:
            current_streak = 0

    return max_streak


def calculate_longest_non_hold_streak(actions: pd.Series) -> int:
    """
    Calculate longest consecutive streak of non-HOLD actions.

    Returns -1 if actions are N/A or empty.
    """
    if actions.empty or actions.isna().all():
        return -1

    actions_clean = actions.fillna("unknown")

    max_streak = 0
    current_streak = 0

    for action in actions_clean:
        if action != "HOLD":
            current_streak += 1
            max_streak = max(max_streak, current_streak)
        else:
            current_streak = 0

    return max_streak


def generate_report(df: pd.DataFrame, csv_path: str) -> str:
    """Generate performance and risk summary report."""

    lines = []
    lines.append("=" * 70)
    lines.append("PR9A: Performance & Risk Summary Report")
    lines.append("=" * 70)
    lines.append(f"CSV: {csv_path}")
    lines.append(f"Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}")
    lines.append("")

    total_rows = len(df)
    lines.append(f"Total Rows: {total_rows:,}")
    lines.append("")

    # (1) Period
    lines.append("-" * 70)
    lines.append("Period")
    lines.append("-" * 70)

    if "timestamp_utc" in df.columns and total_rows > 0:
        start_ts = df["timestamp_utc"].iloc[0]
        end_ts = df["timestamp_utc"].iloc[-1]
        lines.append(f"Start: {start_ts}")
        lines.append(f"End:   {end_ts}")
    else:
        lines.append(f"Start: N/A")
        lines.append(f"End:   N/A")

    lines.append("")

    # (2) Equity-based Performance
    lines.append("-" * 70)
    lines.append("Equity-Based Performance")
    lines.append("-" * 70)

    has_equity = "equity" in df.columns and not df["equity"].isna().all()

    if has_equity:
        equity = df["equity"].dropna()
        if len(equity) > 0:
            start_equity = equity.iloc[0]
            end_equity = equity.iloc[-1]
            total_return_pct = ((end_equity / start_equity) - 1.0) * 100.0 if start_equity != 0 else 0.0
            max_dd_pct = calculate_max_drawdown(equity)
            tuw_ticks = calculate_time_under_water(equity)
            max_dd_duration = calculate_max_drawdown_duration(equity)

            lines.append(f"Start Equity:      {start_equity:.6f}")
            lines.append(f"End Equity:        {end_equity:.6f}")
            lines.append(f"Total Return:      {total_return_pct:+.2f}%")
            lines.append(f"Max Drawdown:      {max_dd_pct:.2f}%")

            # PR11A: Drawdown supplementary metrics
            if tuw_ticks >= 0:
                lines.append(f"Time Under Water:  {tuw_ticks} ticks")
            else:
                lines.append(f"Time Under Water:  N/A")

            if max_dd_duration >= 0:
                lines.append(f"Max DD Duration:   {max_dd_duration} ticks")
            else:
                lines.append(f"Max DD Duration:   N/A")
        else:
            lines.append("Performance Section: N/A (equity column has no valid values)")
    else:
        lines.append("Performance Section: N/A (equity column missing or all NaN)")

    lines.append("")
    lines.append("Note: Annualized returns not provided (tick frequency unknown).")
    lines.append("")

    # (3) Exposure / Activity
    lines.append("-" * 70)
    lines.append("Exposure / Activity")
    lines.append("-" * 70)

    if "target_weight" in df.columns:
        weights = df["target_weight"].dropna()
        if len(weights) > 0:
            avg_abs_weight = weights.abs().mean()
            max_abs_weight = weights.abs().max()
            exposure_ratio = calculate_exposure_ratio(df["target_weight"])
            turnover_proxy = calculate_turnover_proxy(df["target_weight"])

            lines.append(f"Avg |Weight|:       {avg_abs_weight:.4f}")
            lines.append(f"Max |Weight|:       {max_abs_weight:.4f}")

            # PR11A: Exposure metrics
            if exposure_ratio >= 0:
                lines.append(f"Exposure Ratio:     {exposure_ratio:.4f}")
            else:
                lines.append(f"Exposure Ratio:     N/A")

            if turnover_proxy >= 0:
                lines.append(f"Turnover Proxy:     {turnover_proxy:.6f}")
            else:
                lines.append(f"Turnover Proxy:     N/A")
        else:
            lines.append(f"Avg |Weight|:       N/A")
            lines.append(f"Max |Weight|:       N/A")
            lines.append(f"Exposure Ratio:     N/A")
            lines.append(f"Turnover Proxy:     N/A")
    else:
        lines.append(f"Avg |Weight|:       N/A (column missing)")
        lines.append(f"Max |Weight|:       N/A (column missing)")
        lines.append(f"Exposure Ratio:     N/A (column missing)")
        lines.append(f"Turnover Proxy:     N/A (column missing)")

    lines.append("")

    # Action counts
    if "action_label" in df.columns:
        action_counts = df["action_label"].fillna("unknown").value_counts()
        lines.append("Action Counts:")
        for action in ["BUY", "SELL", "HOLD", "FREEZE", "unknown"]:
            count = action_counts.get(action, 0)
            pct = (count / total_rows * 100.0) if total_rows > 0 else 0.0
            lines.append(f"  {action:10s}: {count:6d} ({pct:5.1f}%)")

        hold_count = action_counts.get("HOLD", 0)
        hold_ratio = (hold_count / total_rows * 100.0) if total_rows > 0 else 0.0
        lines.append("")
        lines.append(f"HOLD Ratio:         {hold_ratio:.1f}%")
    else:
        lines.append("Action Counts:      N/A (column missing)")

    lines.append("")

    # PR11A: Decision Stability
    lines.append("-" * 70)
    lines.append("Decision Stability")
    lines.append("-" * 70)

    if "action_label" in df.columns:
        actions = df["action_label"]
        switch_rate = calculate_action_switch_rate(actions)
        hold_streak = calculate_longest_streak(actions, "HOLD")
        non_hold_streak = calculate_longest_non_hold_streak(actions)

        if switch_rate >= 0:
            lines.append(f"Action Switch Rate: {switch_rate:.4f}")
        else:
            lines.append(f"Action Switch Rate: N/A")

        if hold_streak >= 0:
            lines.append(f"Longest HOLD:       {hold_streak} ticks")
        else:
            lines.append(f"Longest HOLD:       N/A")

        if non_hold_streak >= 0:
            lines.append(f"Longest non-HOLD:   {non_hold_streak} ticks")
        else:
            lines.append(f"Longest non-HOLD:   N/A")
    else:
        lines.append("Decision Stability: N/A (action_label column missing)")

    lines.append("")

    # (4) Regime / Overlay Summary
    lines.append("-" * 70)
    lines.append("Regime Distribution")
    lines.append("-" * 70)

    if "regime" in df.columns:
        regime_counts = df["regime"].fillna("unknown").value_counts()
        for regime, count in regime_counts.items():
            pct = (count / total_rows * 100.0) if total_rows > 0 else 0.0
            lines.append(f"  {regime:25s}: {count:6d} ({pct:5.1f}%)")
    else:
        lines.append("  Regime data: N/A (column missing)")

    lines.append("")
    lines.append("-" * 70)
    lines.append("Safety Overlay Distribution (Top 5)")
    lines.append("-" * 70)

    if "decision_reason" in df.columns:
        df_temp = df.copy()
        df_temp["overlay_rule"] = df_temp["decision_reason"].apply(extract_overlay_rule)
        overlay_counts = df_temp["overlay_rule"].value_counts()

        for overlay, count in overlay_counts.head(5).items():
            pct = (count / total_rows * 100.0) if total_rows > 0 else 0.0
            lines.append(f"  {overlay:30s}: {count:6d} ({pct:5.1f}%)")

        if len(overlay_counts) > 5:
            lines.append(f"  ... and {len(overlay_counts) - 5} more")
    else:
        lines.append("  Overlay data: N/A (column missing)")

    lines.append("")

    # PR11A: Regime-Based Exposure
    lines.append("-" * 70)
    lines.append("Regime-Based Exposure")
    lines.append("-" * 70)

    if "regime" in df.columns:
        regimes = df["regime"].fillna("unknown").unique()
        for regime in sorted(regimes):
            regime_df = df[df["regime"].fillna("unknown") == regime]

            lines.append(f"\n{regime}:")

            # Exposure Ratio
            if "target_weight" in regime_df.columns:
                regime_exposure = calculate_exposure_ratio(regime_df["target_weight"])
                if regime_exposure >= 0:
                    lines.append(f"  Exposure Ratio: {regime_exposure:.4f}")
                else:
                    lines.append(f"  Exposure Ratio: N/A")
            else:
                lines.append(f"  Exposure Ratio: N/A")

            # Avg |Weight|
            if "target_weight" in regime_df.columns:
                regime_weights = regime_df["target_weight"].dropna()
                if len(regime_weights) > 0:
                    regime_avg_weight = regime_weights.abs().mean()
                    lines.append(f"  Avg |Weight|:   {regime_avg_weight:.4f}")
                else:
                    lines.append(f"  Avg |Weight|:   N/A")
            else:
                lines.append(f"  Avg |Weight|:   N/A")

            # HOLD Ratio
            if "action_label" in regime_df.columns:
                regime_actions = regime_df["action_label"].fillna("unknown")
                regime_hold_count = (regime_actions == "HOLD").sum()
                regime_total = len(regime_df)
                regime_hold_ratio = (regime_hold_count / regime_total * 100.0) if regime_total > 0 else 0.0
                lines.append(f"  HOLD Ratio:     {regime_hold_ratio:.1f}%")
            else:
                lines.append(f"  HOLD Ratio:     N/A")
    else:
        lines.append("Regime-Based Exposure: N/A (regime column missing)")

    lines.append("")

    # (5) Health Gate Reference
    lines.append("-" * 70)
    lines.append("Data Quality Gate Reference")
    lines.append("-" * 70)
    lines.append("")
    lines.append("IMPORTANT: Run PR8A/PR8B integrity validation before using this report.")
    lines.append("")
    lines.append("Recommended workflow:")
    lines.append("  1. python3 python/validation/pr8a_log_integrity_invariants.py <csv>")
    lines.append("  2. python3 python/tools/pr8b_integrity_gate_runner.py <csv>")
    lines.append("  3. Review this PR9A performance report")
    lines.append("")
    lines.append("PR8A/PR8B ensure data integrity before performance calculation.")
    lines.append("")
    lines.append("Note: Tick-based durations are reported in ticks, not time.")
    lines.append("")

    lines.append("=" * 70)
    lines.append("END OF REPORT")
    lines.append("=" * 70)

    return "\n".join(lines)


def generate_markdown(df: pd.DataFrame, csv_path: str) -> str:
    """Generate Markdown version of performance report."""

    lines = []
    lines.append("# PR9A: Performance & Risk Summary Report")
    lines.append("")
    lines.append("> **Important Notes on Interpretation**")
    lines.append(">")
    lines.append("> - All performance metrics in this report are computed **only from the `equity` column when present**.")
    lines.append(">   If `equity` is missing or invalid, performance metrics are reported as **N/A**.")
    lines.append("> - No annualization or time-normalization is applied.")
    lines.append(">   Tick frequency, sampling interval, and capital deployment assumptions are intentionally **not inferred**.")
    lines.append("> - This report evaluates **observed system behavior**, not theoretical strategy performance.")
    lines.append(">   Metrics reflect what actually occurred in the log, not what could have occurred under different assumptions.")
    lines.append("> - The purpose of this report is **diagnostic and structural validation**, not return maximization or benchmarking.")
    lines.append("")
    lines.append(f"**CSV:** `{csv_path}`")
    lines.append("")
    lines.append(f"**Generated:** {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}")
    lines.append("")

    total_rows = len(df)
    lines.append(f"**Total Rows:** {total_rows:,}")
    lines.append("")

    # Period
    lines.append("## Period")
    lines.append("")

    if "timestamp_utc" in df.columns and total_rows > 0:
        start_ts = df["timestamp_utc"].iloc[0]
        end_ts = df["timestamp_utc"].iloc[-1]
        lines.append(f"- **Start:** {start_ts}")
        lines.append(f"- **End:** {end_ts}")
    else:
        lines.append(f"- **Start:** N/A")
        lines.append(f"- **End:** N/A")

    lines.append("")

    # Equity-based Performance
    lines.append("## Equity-Based Performance")
    lines.append("")
    lines.append("_The following metrics are derived solely from the recorded equity time series, without interpolation or normalization._")
    lines.append("")

    has_equity = "equity" in df.columns and not df["equity"].isna().all()

    if has_equity:
        equity = df["equity"].dropna()
        if len(equity) > 0:
            start_equity = equity.iloc[0]
            end_equity = equity.iloc[-1]
            total_return_pct = ((end_equity / start_equity) - 1.0) * 100.0 if start_equity != 0 else 0.0
            max_dd_pct = calculate_max_drawdown(equity)
            tuw_ticks = calculate_time_under_water(equity)
            max_dd_duration = calculate_max_drawdown_duration(equity)

            lines.append("| Metric | Value |")
            lines.append("|--------|-------|")
            lines.append(f"| Start Equity | {start_equity:.6f} |")
            lines.append(f"| End Equity | {end_equity:.6f} |")
            lines.append(f"| Total Return | {total_return_pct:+.2f}% |")
            lines.append(f"| Max Drawdown | {max_dd_pct:.2f}% |")

            # PR11A: Drawdown supplementary metrics
            if tuw_ticks >= 0:
                lines.append(f"| Time Under Water | {tuw_ticks} ticks |")
            else:
                lines.append(f"| Time Under Water | N/A |")

            if max_dd_duration >= 0:
                lines.append(f"| Max DD Duration | {max_dd_duration} ticks |")
            else:
                lines.append(f"| Max DD Duration | N/A |")
        else:
            lines.append("**Performance Section:** N/A (equity column has no valid values)")
    else:
        lines.append("**Performance Section:** N/A (equity column missing or all NaN)")

    lines.append("")
    lines.append("*Note: Annualized returns not provided (tick frequency unknown).*")
    lines.append("")

    # Exposure / Activity
    lines.append("## Exposure / Activity")
    lines.append("")

    if "target_weight" in df.columns:
        weights = df["target_weight"].dropna()
        if len(weights) > 0:
            avg_abs_weight = weights.abs().mean()
            max_abs_weight = weights.abs().max()
            exposure_ratio = calculate_exposure_ratio(df["target_weight"])
            turnover_proxy = calculate_turnover_proxy(df["target_weight"])

            lines.append("| Metric | Value |")
            lines.append("|--------|-------|")
            lines.append(f"| Avg \\|Weight\\| | {avg_abs_weight:.4f} |")
            lines.append(f"| Max \\|Weight\\| | {max_abs_weight:.4f} |")

            # PR11A: Exposure metrics
            if exposure_ratio >= 0:
                lines.append(f"| Exposure Ratio | {exposure_ratio:.4f} |")
            else:
                lines.append(f"| Exposure Ratio | N/A |")

            if turnover_proxy >= 0:
                lines.append(f"| Turnover Proxy | {turnover_proxy:.6f} |")
            else:
                lines.append(f"| Turnover Proxy | N/A |")
        else:
            lines.append("**Weight Metrics:** N/A")
    else:
        lines.append("**Weight Metrics:** N/A (column missing)")

    lines.append("")

    # Action counts
    if "action_label" in df.columns:
        action_counts = df["action_label"].fillna("unknown").value_counts()

        lines.append("### Action Counts")
        lines.append("")
        lines.append("| Action | Count | Percentage |")
        lines.append("|--------|-------|------------|")

        for action in ["BUY", "SELL", "HOLD", "FREEZE", "unknown"]:
            count = action_counts.get(action, 0)
            pct = (count / total_rows * 100.0) if total_rows > 0 else 0.0
            lines.append(f"| {action} | {count:,} | {pct:.1f}% |")

        lines.append("")

        hold_count = action_counts.get("HOLD", 0)
        hold_ratio = (hold_count / total_rows * 100.0) if total_rows > 0 else 0.0
        lines.append(f"**HOLD Ratio:** {hold_ratio:.1f}%")
    else:
        lines.append("**Action Counts:** N/A (column missing)")

    lines.append("")

    # PR11A: Decision Stability
    lines.append("## Decision Stability")
    lines.append("")

    if "action_label" in df.columns:
        actions = df["action_label"]
        switch_rate = calculate_action_switch_rate(actions)
        hold_streak = calculate_longest_streak(actions, "HOLD")
        non_hold_streak = calculate_longest_non_hold_streak(actions)

        lines.append("| Metric | Value |")
        lines.append("|--------|-------|")

        if switch_rate >= 0:
            lines.append(f"| Action Switch Rate | {switch_rate:.4f} |")
        else:
            lines.append(f"| Action Switch Rate | N/A |")

        if hold_streak >= 0:
            lines.append(f"| Longest HOLD Streak | {hold_streak} ticks |")
        else:
            lines.append(f"| Longest HOLD Streak | N/A |")

        if non_hold_streak >= 0:
            lines.append(f"| Longest non-HOLD Streak | {non_hold_streak} ticks |")
        else:
            lines.append(f"| Longest non-HOLD Streak | N/A |")
    else:
        lines.append("**Decision Stability:** N/A (action_label column missing)")

    lines.append("")

    # Regime Distribution
    lines.append("## Regime Distribution")
    lines.append("")

    if "regime" in df.columns:
        regime_counts = df["regime"].fillna("unknown").value_counts()

        lines.append("| Regime | Count | Percentage |")
        lines.append("|--------|-------|------------|")

        for regime, count in regime_counts.items():
            pct = (count / total_rows * 100.0) if total_rows > 0 else 0.0
            lines.append(f"| {regime} | {count:,} | {pct:.1f}% |")
    else:
        lines.append("**Regime Data:** N/A (column missing)")

    lines.append("")

    # Safety Overlay Distribution
    lines.append("## Safety Overlay Distribution (Top 5)")
    lines.append("")

    if "decision_reason" in df.columns:
        df_temp = df.copy()
        df_temp["overlay_rule"] = df_temp["decision_reason"].apply(extract_overlay_rule)
        overlay_counts = df_temp["overlay_rule"].value_counts()

        lines.append("| Overlay Rule | Count | Percentage |")
        lines.append("|--------------|-------|------------|")

        for overlay, count in overlay_counts.head(5).items():
            pct = (count / total_rows * 100.0) if total_rows > 0 else 0.0
            lines.append(f"| {overlay} | {count:,} | {pct:.1f}% |")

        if len(overlay_counts) > 5:
            lines.append("")
            lines.append(f"*... and {len(overlay_counts) - 5} more overlay rules*")
    else:
        lines.append("**Overlay Data:** N/A (column missing)")

    lines.append("")

    # PR11A: Regime-Based Exposure
    lines.append("## Regime-Based Exposure")
    lines.append("")

    if "regime" in df.columns:
        regimes = df["regime"].fillna("unknown").unique()
        for regime in sorted(regimes):
            regime_df = df[df["regime"].fillna("unknown") == regime]

            lines.append(f"### {regime}")
            lines.append("")
            lines.append("| Metric | Value |")
            lines.append("|--------|-------|")

            # Exposure Ratio
            if "target_weight" in regime_df.columns:
                regime_exposure = calculate_exposure_ratio(regime_df["target_weight"])
                if regime_exposure >= 0:
                    lines.append(f"| Exposure Ratio | {regime_exposure:.4f} |")
                else:
                    lines.append(f"| Exposure Ratio | N/A |")
            else:
                lines.append(f"| Exposure Ratio | N/A |")

            # Avg |Weight|
            if "target_weight" in regime_df.columns:
                regime_weights = regime_df["target_weight"].dropna()
                if len(regime_weights) > 0:
                    regime_avg_weight = regime_weights.abs().mean()
                    lines.append(f"| Avg \\|Weight\\| | {regime_avg_weight:.4f} |")
                else:
                    lines.append(f"| Avg \\|Weight\\| | N/A |")
            else:
                lines.append(f"| Avg \\|Weight\\| | N/A |")

            # HOLD Ratio
            if "action_label" in regime_df.columns:
                regime_actions = regime_df["action_label"].fillna("unknown")
                regime_hold_count = (regime_actions == "HOLD").sum()
                regime_total = len(regime_df)
                regime_hold_ratio = (regime_hold_count / regime_total * 100.0) if regime_total > 0 else 0.0
                lines.append(f"| HOLD Ratio | {regime_hold_ratio:.1f}% |")
            else:
                lines.append(f"| HOLD Ratio | N/A |")

            lines.append("")
    else:
        lines.append("**Regime-Based Exposure:** N/A (regime column missing)")
        lines.append("")

    # Health Gate Reference
    lines.append("## Data Quality Gate Reference")
    lines.append("")
    lines.append("**IMPORTANT:** Run PR8A/PR8B integrity validation before using this report.")
    lines.append("")
    lines.append("**Recommended workflow:**")
    lines.append("")
    lines.append("1. `python3 python/validation/pr8a_log_integrity_invariants.py <csv>`")
    lines.append("2. `python3 python/tools/pr8b_integrity_gate_runner.py <csv>`")
    lines.append("3. Review this PR9A performance report")
    lines.append("")
    lines.append("PR8A/PR8B ensure data integrity before performance calculation.")
    lines.append("")
    lines.append("**Note:** Tick-based durations are reported in ticks, not time.")
    lines.append("")

    lines.append("---")
    lines.append("")
    lines.append("*Generated by PR9A: Performance & Risk Summary Report*")
    lines.append("")
    lines.append("> This report does not prescribe actions.")
    lines.append("> It exists to make system behavior observable, auditable, and comparable over time.")
    lines.append("")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description="PR9A: Generate performance and risk summary from meridian_log.csv"
    )
    parser.add_argument("csv_path", help="Path to meridian_log.csv")
    parser.add_argument("--out", help="Output Markdown file (optional)")
    parser.add_argument("--from", dest="from_ts", help="Filter from timestamp (ISO format)")
    parser.add_argument("--to", dest="to_ts", help="Filter to timestamp (ISO format)")

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

    # Apply timestamp filter if provided
    if args.from_ts or args.to_ts:
        if "timestamp_utc" in df.columns:
            try:
                timestamps = pd.to_datetime(df["timestamp_utc"], errors="coerce")
                df = df[~timestamps.isna()].copy()
                df["_ts_parsed"] = pd.to_datetime(df["timestamp_utc"])

                if args.from_ts:
                    from_dt = pd.to_datetime(args.from_ts)
                    df = df[df["_ts_parsed"] >= from_dt]

                if args.to_ts:
                    to_dt = pd.to_datetime(args.to_ts)
                    df = df[df["_ts_parsed"] <= to_dt]

                df = df.drop(columns=["_ts_parsed"])

                if df.empty:
                    print("Warning: No rows match timestamp filter", file=sys.stderr)
            except Exception as e:
                print(f"Warning: Timestamp filter failed: {e}", file=sys.stderr)

    # Generate text report (stdout)
    text_report = generate_report(df, args.csv_path)
    print(text_report)

    # Generate Markdown if requested
    if args.out:
        md_report = generate_markdown(df, args.csv_path)
        with open(args.out, "w") as f:
            f.write(md_report)
        print(f"\n✓ Markdown report written to: {args.out}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
