import os
import json
from typing import Dict, Any

# Read stats file path from env; default to a local file if not set.
# On Render with a persistent disk, set STATS_FILE=/data/stats.json
STATS_FILE = os.getenv("STATS_FILE", "stats.json")

def _blank_user(outcomes: list[str]) -> Dict[str, Any]:
    return {
        "total": 0,
        "outcomes": {k: 0 for k in outcomes},
        "last_roll_date": None,
        "streak_days": 0,
    }

def _blank_stats(outcomes: list[str]) -> Dict[str, Any]:
    return {
        "global": {"total": 0, "outcomes": {k: 0 for k in outcomes}},
        "users": {}
    }

def load_stats(outcomes: list[str]) -> Dict[str, Any]:
    try:
        if os.path.exists(STATS_FILE):
            with open(STATS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception:
        # If file is corrupt or unreadable, fall back to blank stats
        pass
    return _blank_stats(outcomes)

def save_stats(stats: Dict[str, Any]) -> None:
    # Atomic write via temp file then replace
    tmp = STATS_FILE + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(stats, f, indent=2)
    os.replace(tmp, STATS_FILE)

def ensure_user(stats: Dict[str, Any], user_id: int, outcomes: list[str]) -> Dict[str, Any]:
    uid = str(user_id)
    if uid not in stats["users"]:
        stats["users"][uid] = _blank_user(outcomes)
    return stats["users"][uid]
