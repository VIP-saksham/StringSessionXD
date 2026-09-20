import json
import os

SUDO_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sudos.json")


def _load():
    try:
        with open(SUDO_FILE, "r", encoding="utf-8") as f:
            d = json.load(f)
            return d if isinstance(d, list) else []
    except Exception:
        return []


def _save(ids):
    with open(SUDO_FILE, "w", encoding="utf-8") as f:
        json.dump([int(i) for i in ids], f)


def get_ids():
    return _load()


def is_sudo(user_id):
    return int(user_id) in _load()


def add_sudo(user_id):
    ids = _load()
    if int(user_id) not in ids:
        ids.append(int(user_id))
        _save(ids)
    return ids


def remove_sudo(user_id):
    ids = [i for i in _load() if int(i) != int(user_id)]
    _save(ids)
    return ids
