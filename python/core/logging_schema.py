# python/core/logging_schema.py
import csv
import os
from typing import Dict, Any

from config import LOG_CSV_PATH


LOG_COLUMNS = [
    "timestamp_utc",
    "symbol",
    "env",
    "agent_version",

    "price",
    "ma",
    "deviation_pct",

    "entropy_pct",
    "entropy_bp",
    "ea_norm",
    "es_norm",

    "volatility_band",
    "entropy_state",

    "action_label",
    "target_weight",
    "equity",

    "guard_type",
    "guard_reason",
]


def ensure_log_file():
    # Ensure logs/ exists
    dirpath = os.path.dirname(LOG_CSV_PATH)
    if dirpath:
        os.makedirs(dirpath, exist_ok=True)

    if not os.path.exists(LOG_CSV_PATH):
        with open(LOG_CSV_PATH, "w", newline="") as f:
            csv.DictWriter(f, fieldnames=LOG_COLUMNS).writeheader()


def append_log_row(row: Dict[str, Any]):
    ensure_log_file()
    out = {k: row.get(k) for k in LOG_COLUMNS}
    with open(LOG_CSV_PATH, "a", newline="") as f:
        csv.DictWriter(f, fieldnames=LOG_COLUMNS).writerow(out)
