import datetime as dt

def today_str() -> str:
    return dt.date.today().isoformat()

def emoji_bar(count: int, total: int, width: int = 20) -> str:
    if total <= 0:
        return "—"
    filled = int(round((count / total) * width))
    filled = max(1, filled)
    return "■" * filled + "□" * max(0, width - filled)

def big_emoji_bar(count: int, total: int, width: int = 28) -> str:
    if total <= 0:
        return "—"
    if count <= 0:
        return "░" * width
    filled = max(1, int(round((count / total) * width)))
    return "█" * filled + "░" * (width - filled)

def pct(n: int, d: int) -> str:
    return f"{(100*n/d):.1f}%" if d else "0.0%"
