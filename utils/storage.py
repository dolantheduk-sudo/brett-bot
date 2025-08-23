# utils/storage.py
import os
import json
import time
from typing import Dict, Any, List

# Where to write stats. On Render, set env var:
# STATS_FILE=/data/stats.json   (or /opt/render/project/src/data/stats.json)
STATS_FILE = os.getenv("STATS_FILE", "stats.json")

# Brettventures stamina regen: default 1 point every 6 hours
BV_STAMINA_REGEN_SECS = int(os.getenv("BV_STAMINA_REGEN_SECS", str(3 * 3600)))

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



# =====================================================================
# Brettventures section
# =====================================================================

def _load_all() -> Dict[str, Any]:
    if os.path.exists(STATS_FILE):
        try:
            with open(STATS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {}

def _save_all(root: Dict[str, Any]) -> None:
    _atomic_save(root)

def _blank_player(user_id: int, name: str) -> Dict[str, Any]:
    return {
        "user_id": user_id,
        "name": name,
        "level": 1,
        "xp": 0,
        "hp": 20, "hp_max": 20,
        "stamina": 5, "stamina_max": 5,
        "pow": 1, "smt": 1, "luck": 0,
        "gold": 0,
        "inventory": [],
        "flags": {},
        "stamina_ts": int(time.time()),  # <--- add this
    }


def bv_get_player(user_id: int) -> Dict[str, Any] | None:
    root = _load_all()
    p = root.get("brettventures", {}).get("players", {}).get(str(user_id))
    if not p:
        return None
    # Apply regen every read
    changed = _tick_stamina_inplace(p)
    if changed:
        ns = root.setdefault("brettventures", {})
        ns.setdefault("players", {})[str(user_id)] = p
        _save_all(root)
    return p

def bv_get_or_create_player(user_id: int, name: str) -> Dict[str, Any]:
    root = _load_all()
    ns = root.setdefault("brettventures", {})
    players = ns.setdefault("players", {})
    if str(user_id) in players:
        p = players[str(user_id)]
        changed = _tick_stamina_inplace(p)
        if changed:
            _save_all(root)
        return p
    p = _blank_player(user_id, name)
    players[str(user_id)] = p
    _save_all(root)
    return p

def bv_upsert_player(p: Dict[str, Any]) -> None:
    root = _load_all()
    ns = root.setdefault("brettventures", {})
    players = ns.setdefault("players", {})
    players[str(p["user_id"])] = p
    _save_all(root)

def bv_add_xp(user_id: int, amount: int) -> Dict[str, Any]:
    root = _load_all()
    ns = root.setdefault("brettventures", {})
    players = ns.setdefault("players", {})
    p = players.get(str(user_id))
    if not p:
        raise ValueError("No such player")
    p["xp"] += amount
    while p["xp"] >= 10 * p["level"]:
        p["xp"] -= 10 * p["level"]
        p["level"] += 1
        p["hp_max"] += 2
        p["stamina_max"] += 1
    _save_all(root)
    return p

def _tick_stamina_inplace(p: Dict[str, Any], now: int | None = None) -> int:
    """
    Apply time-based stamina regen in-place.
    Returns how many stamina points were regenerated.
    """
    if not p or BV_STAMINA_REGEN_SECS <= 0:
        return 0
    now = int(now or time.time())
    p.setdefault("stamina_ts", now)
    if p["stamina"] >= p["stamina_max"]:
        # Keep ts “caught up” so next ETA is sane
        p["stamina_ts"] = now
        return 0

    elapsed = max(0, now - int(p["stamina_ts"]))
    if elapsed < BV_STAMINA_REGEN_SECS:
        return 0

    ticks = elapsed // BV_STAMINA_REGEN_SECS
    if ticks <= 0:
        return 0

    before = p["stamina"]
    p["stamina"] = min(p["stamina_max"], p["stamina"] + int(ticks))
    # Advance ts by the number of full-interval ticks actually applied.
    applied = p["stamina"] - before
    if applied > 0:
        p["stamina_ts"] = int(p["stamina_ts"]) + applied * BV_STAMINA_REGEN_SECS
    else:
        # If we were already full by the time we checked, catch up ts to now.
        p["stamina_ts"] = now
    return applied


def bv_next_stamina_eta(user_id: int) -> int | None:
    """
    Seconds until next stamina point for this user.
    Returns 0 if a point is ready now, None if already full.
    """
    root = _load_all()
    p = root.get("brettventures", {}).get("players", {}).get(str(user_id))
    if not p:
        return None
    now = int(time.time())
    _ = _tick_stamina_inplace(p, now)
    # Save after tick
    ns = root.setdefault("brettventures", {})
    ns.setdefault("players", {})[str(user_id)] = p
    _save_all(root)

    if p["stamina"] >= p["stamina_max"]:
        return None
    due = int(p.get("stamina_ts", now)) + BV_STAMINA_REGEN_SECS
    return max(0, due - now)
