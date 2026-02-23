"""
analysis/performance_tracker.py
================================
Records sorting runs for the Performance Analytics tab.
Persists to data/sort_history.json (last 200 entries).
"""

import json
import os
import time
from collections import defaultdict

try:
    from config.constants import get_project_root
    _HIST_PATH = os.path.join(get_project_root(), "data", "sort_history.json")
except ImportError:
    _HIST_PATH = os.path.join(os.getcwd(), "data", "sort_history.json")

_history: list[dict] = []


def _load():
    global _history
    if os.path.exists(_HIST_PATH):
        try:
            with open(_HIST_PATH, "r", encoding="utf-8") as f:
                _history = json.load(f)
        except (json.JSONDecodeError, OSError):
            _history = []


def _save():
    os.makedirs(os.path.dirname(_HIST_PATH), exist_ok=True)
    with open(_HIST_PATH, "w", encoding="utf-8") as f:
        json.dump(_history[-200:], f, indent=2)


_load()


def record(algorithm: str, column: str, time_ms: float, job_count: int = 0):
    """Store one sort result."""
    _history.append({
        "algorithm": algorithm,
        "column":    column,
        "time_ms":   round(time_ms, 4),
        "timestamp": time.strftime("%H:%M:%S"),
        "job_count": job_count,
    })
    _save()


def get_history() -> list[dict]:
    return list(_history)


def clear_history():
    global _history
    _history = []
    _save()


def get_per_algorithm_avg() -> dict[str, float]:
    """Return {algorithm: average_time_ms} across all recorded sorts."""
    grouped: dict[str, list] = defaultdict(list)
    for entry in _history:
        grouped[entry["algorithm"]].append(entry["time_ms"])
    return {alg: sum(times) / len(times) for alg, times in grouped.items()}