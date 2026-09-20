import json
import os

FC_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fc.json")


def _load():
    try:
        with open(FC_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []


def _save(chats):
    with open(FC_FILE, "w", encoding="utf-8") as f:
        json.dump(chats, f, ensure_ascii=False, indent=1)


def get_chats():
    return _load()


def add_chat(chat, url, title):
    chats = _load()
    key = str(chat)
    chats = [c for c in chats if str(c.get("chat")) != key]
    chats.append({"chat": chat, "url": url, "title": title})
    _save(chats)
    return chats


def clear_all():
    _save([])


def set_chats(items):
    _save(items)
