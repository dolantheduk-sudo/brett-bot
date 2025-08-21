# utils/storage.py
import os
import json
from typing import Dict, Any, List

# Where to write stats. On Render, set env var:
# STATS_FILE=/data/stats.json   (or /opt/render/project/src/data/stats.json)
STATS_FILE = os.getenv("STATS_FILE", "stats.json")

# Ensure parent folder exists
_parent = os.path.dirname(STATS_FILE)
if _parent:
    os.makedirs(_parent, exist_ok=True)


# ---- helpers ----
def _blank_user(outcomes: List[str]) -> Dict[str, Any]:
    return {
        "total": 0,
        "outcomes": {k: 0 for k in outcomes},
        "last_roll_date": None,
        "streak_days": 0,
    }


def _blank_stats(outcomes: List[str]) -> Dict[str, Any]:
    return {
        "global": {"total": 0, "outcomes": {k: 0 for k in outcomes}},
        "users": {}
    }


def load_stats(outcomes: List[str]) -> Dict[str, Any]:
    """Read stats JSON; create a fresh structure if missing/corrupt."""
    try:
        if os.path.exists(STATS_FILE):
            with open(STATS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)

            # Ensure shape and keys exist
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
        pass  # fall through to fresh struct

    return _blank_stats(outcomes)


def _atomic_save(obj: Dict[str, Any]) -> None:
    tmp = STATS_FILE + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(obj, f, indent=2)
    os.replace(tmp, STATS_FILE)


def ensure_user(stats: Dict[str, Any], user_id: int, outcomes: List[str]) -> Dict[str, Any]:
    uid = str(user_id)
    if uid not in stats["users"]:
        stats["users"][uid] = _blank_user(outcomes)
    return stats["users"][uid]


# ---- writers (NO recursion) ----
def _record_roll_impl(guild_id: int, user_id: int, outcome: str, ts: float | None = None) -> None:
    """Internal implementation used by both new and legacy entrypoints."""
    # Prefer the same list stats.py iterates over
    try:
        from constants import BRETT_RESPONSES as OUTCOME_KEYS
    except Exception:
        OUTCOME_KEYS = [outcome]

    stats = load_stats(OUTCOME_KEYS)

    # Global
    stats["global"]["total"] = int(stats["global"].get("total", 0)) + 1
    stats["global"]["outcomes"].setdefault(outcome, 0)
    stats["global"]["outcomes"][outcome] += 1

    # User
    u = ensure_user(stats, user_id, OUTCOME_KEYS)
    u["total"] = int(u.get("total", 0)) + 1
    u["outcomes"].setdefault(outcome, 0)
    u["outcomes"][outcome] += 1

    _atomic_save(stats)


def record_roll(guild_id: int, user_id: int, outcome: str, ts: float | None = None) -> None:
    """Primary entrypoint: (gid, uid, outcome, [ts])."""
    _record_roll_impl(guild_id, user_id, outcome, ts)


def record_roll_legacy(user_id: int, outcome: str) -> None:
    """Legacy entrypoint: (uid, outcome)."""
    _record_roll_impl(0, user_id, outcome, None)
    
def save_stats(stats: Dict[str, Any]) -> None:
    """Write the stats dictionary back to disk safely."""
    _atomic_save(stats)
