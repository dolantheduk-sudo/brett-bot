# utils/storage.py
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
                data = json.load(f)
            # ensure keys exist for any newly added outcomes
            data.setdefault("global", {}).setdefault("outcomes", {})
            data["global"].setdefault("total", 0)
            data.setdefault("users", {})
            for name in outcomes:
                data["global"]["outcomes"].setdefault(name, 0)
            for u in data["users"].values():
                u.setdefault("outcomes", {})
                u.setdefault("total", 0)
                u.setdefault("streak_days", 0)
                for name in outcomes:
                    u["outcomes"].setdefault(name, 0)
            return data
    except Exception:
        pass
    return _blank_stats(outcomes)

def save_stats(stats: Dict[str, Any]) -> None:
    tmp = STATS_FILE + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(stats, f, indent=2)
    os.replace(tmp, STATS_FILE)

def ensure_user(stats: Dict[str, Any], user_id: int, outcomes: list[str]) -> Dict[str, Any]:
    uid = str(user_id)
    if uid not in stats["users"]:
        stats["users"][uid] = _blank_user(outcomes)
    return stats["users"][uid]

# ---------- NEW: writers ----------
def record_roll(guild_id: int, user_id: int, outcome: str, ts: float | None = None) -> None:
    """
    Primary writer used by cogs. Records 'outcome' for the user and global totals.
    Works even if 'outcome' wasn't in the initial outcomes list (sets default keys).
    """
    # Use the same list stats.py expects. If constants import fails, fall back to the single outcome.
    try:
        from constants import BRETT_RESPONSES as DEFAULT_OUTCOMES
    except Exception:
        DEFAULT_OUTCOMES = [outcome]

    stats = load_stats(DEFAULT_OUTCOMES)

    # Global
    stats["global"]["total"] = int(stats["global"].get("total", 0)) + 1
    stats["global"]["outcomes"].setdefault(outcome, 0)
    stats["global"]["outcomes"][outcome] += 1

    # User
    u = ensure_user(stats, user_id, DEFAULT_OUTCOMES)
    u["total"] = int(u.get("total", 0)) + 1
    u["outcomes"].setdefault(outcome, 0)
    u["outcomes"][outcome] += 1

    save_stats(stats)

# Legacy compatibility: record_roll(user_id, outcome)
def record_roll_compat(*args):
    if len(args) == 2:
        return record_roll(0, args[0], args[1], None)
    # (gid, uid, outcome, [ts])
    gid, uid, outcome = args[0], args[1], args[2]
    ts = args[3] if len(args) > 3 else None
    return record_roll(gid, uid, outcome, ts)

# Expose the compatibility name
record_roll = record_roll_compat
