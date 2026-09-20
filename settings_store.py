import json
import os

SETTINGS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "settings.json")

DEFAULTS = {"fc_enabled": True, "log_enabled": True}


def _load():
    try:
        with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
            d = json.load(f)
            if isinstance(d, dict):
                return d
    except Exception:
        pass
    return dict(DEFAULTS)


def _save(d):
    with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False, indent=1)


def get(key):
    return _load().get(key, DEFAULTS.get(key, True))


def set(key, val):
    d = _load()
    d[key] = bool(val)
    _save(d)
    return d


def all_settings():
    d = dict(DEFAULTS)
    d.update(_load())
    return d
