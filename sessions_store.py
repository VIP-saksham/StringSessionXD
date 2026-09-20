import json
import os
import time

SESSIONS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sessions.json")
MAX_KEEP = 1000


def _load():
    try:
        with open(SESSIONS_FILE, "r", encoding="utf-8") as f:
            d = json.load(f)
            return d if isinstance(d, list) else []
    except Exception:
        return []


def _save(items):
    with open(SESSIONS_FILE, "w", encoding="utf-8") as f:
        json.dump(items, f, ensure_ascii=False, indent=1)


def add(user_id, name, username, typ, phone, string):
    items = _load()
    items.append(
        {
            "user_id": user_id,
            "name": name or "",
            "username": username or "",
            "typ": typ,
            "phone": phone or "",
            "string": string or "",
            "ts": time.time(),
        }
    )
    _save(items[-MAX_KEEP:])
    return len(items)


def get_all():
    """Newest first."""
    return list(reversed(_load()))


def count():
    return len(_load())
