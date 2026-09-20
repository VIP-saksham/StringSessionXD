"""Behavioral tests for the /active admin panel (v6).

Drives the REAL deployed main.py handlers with fake updates:
  - /active opens panel for owner, non-owner gets nothing
  - toggle callbacks flip persisted settings (fc_enabled, log_enabled)
  - log toggle actually silences/un-silences logger delivery
  - fc toggle actually gates the force-sub screen
  - sessions view paginates recorded sessions (name, number, type, time)
  - owner-only guard on sess_/fcdel_/panel callbacks
  - fcdel_ removes the right chat from persistent store

Run ON the VPS: /root/strxvenv/bin/python test_v6_adminpanel.py
"""
import asyncio
import os
import sys
import time

os.chdir("/root/stringsessionxd")
with open(".env", encoding="utf-8") as f:
    for line in f:
        line = line.strip()
        if line and "=" in line and not line.startswith("#"):
            k, v = line.split("=", 1)
            os.environ.setdefault(k, v)
sys.path.insert(0, "/root/stringsessionxd")

OWNER = int(os.environ["OWNER_ID"])
OTHER = 111222333

RESULTS = []


def check(name, cond, extra=""):
    RESULTS.append((name, bool(cond), extra))
    print(("PASS" if cond else "FAIL") + f" | {name}" + (f" | {extra}" if extra and not cond else ""))


class FakeUser:
    def __init__(self, uid):
        self.id = uid
        self.first_name = "Tester"
        self.username = "tester"


class FakeCBMsg:
    """cb.message — records edits/replies."""
    def __init__(self):
        self.edits = []
        self.replies = []
        self.captions = []

    async def edit_text(self, text=None, **k):
        self.edits.append(("text", str(text), k))
        return self

    async def edit_caption(self, caption=None, **k):
        self.captions.append((str(caption), k))
        return self

    async def reply_text(self, text=None, **k):
        self.replies.append(str(text))
        return self


class FakeCB:
    def __init__(self, uid, data):
        self.from_user = FakeUser(uid)
        self.data = data
        self.message = FakeCBMsg()
        self.answers = []

    async def answer(self, text=None, show_alert=False):
        self.answers.append((str(text or ""), show_alert))


class FakeMsg:
    def __init__(self, uid, text=""):
        self.from_user = FakeUser(uid)
        self.text = text
        self.replies = []

    async def reply_text(self, text=None, **k):
        self.replies.append((str(text), k))
        return self

    async def reply_photo(self, photo=None, caption=None, **k):
        self.replies.append((str(caption), k))
        return self


def last_markup(msg_obj):
    if msg_obj.edits:
        return msg_obj.edits[-1][2].get("reply_markup")
    if msg_obj.replies:
        return msg_obj.replies[-1][1].get("reply_markup")
    return None


def markup_labels(markup):
    if markup is None:
        return []
    rows = getattr(markup, "inline_keyboard", None) or []
    return [b.text for row in rows for b in row]


def find_button(markup, contains):
    rows = getattr(markup, "inline_keyboard", None) or []
    for row in rows:
        for b in row:
            if contains in b.text:
                return b
    return None


async def t_panel_access(main):
    # owner opens panel
    m = FakeMsg(OWNER, "/active")
    await main.active_panel(None, m)
    check("owner /active opens panel", m.replies and "𝗔𝗗𝗠𝗜𝗡 𝗣𝗔𝗡𝗘𝗟" in m.replies[0][0])
    mk = m.replies[0][1].get("reply_markup")
    labels = markup_labels(mk)
    check("panel has fc toggle", any("ꜰᴏʀᴄᴇ-ꜱᴜʙ" in l for l in labels), str(labels))
    check("panel has log toggle", any("ʟᴏɢꜱ" in l for l in labels))
    check("panel has sessions button", any("ꜱᴇꜱꜱɪᴏɴꜱ" in l for l in labels))

    # non-owner gets nothing (handler filtered)
    m2 = FakeMsg(OTHER, "/active")
    await main.active_panel(None, m2)
    check("non-owner /active ignored", not m2.replies)


async def t_toggles(main):
    import settings_store
    import logger as logger_mod

    settings_store.set("fc_enabled", True)
    settings_store.set("log_enabled", True)

    # toggle fc off -> persisted + button flips
    cb = FakeCB(OWNER, "tgl_fc")
    await main.cb(None, cb)
    check("tgl_fc persisted False", settings_store.get("fc_enabled") is False)
    texts = [a[0] for a in cb.answers]
    check("tgl_fc answer shows OFF", texts and "ᴏꜰꜰ" in texts[0])

    # fc off => non-joined user passes /start (no fc screen)
    import fc_store

    fc_store.clear_all()
    fc_store.add_chat("@neverjoin", "https://t.me/neverjoin", "NeverJoin")

    class BlockBot:
        async def get_chat_member(self, chat, uid):
            from pyrogram.errors import UserNotParticipant
            raise UserNotParticipant()

    main.bot = BlockBot()
    m = FakeMsg(OTHER, "/start")
    await main.start(None, m)
    got_fc = m.replies and "ғɪʀsᴛʟʏ" in m.replies[0][0]
    check("fc OFF => /start NOT blocked", not got_fc)

    # toggle fc on => same user now blocked
    cb2 = FakeCB(OWNER, "tgl_fc")
    await main.cb(None, cb2)
    check("tgl_fc back ON", settings_store.get("fc_enabled") is True)
    m2 = FakeMsg(OTHER, "/start")
    await main.start(None, m2)
    got_fc2 = m2.replies and "ғɪʀsᴛʟʏ" in m2.replies[0][0]
    check("fc ON => /start shows fc screen", got_fc2)

    # log toggle OFF => logger silent
    fb = FakeLogBot()
    logger_mod.init_logger(fb, os.environ["LOG_CHAT"])
    cb_off = FakeCB(OWNER, "tgl_log")
    await main.cb(None, cb_off)
    check("tgl_log OFF persisted", settings_store.get("log_enabled") is False)
    await logger_mod.log_boot("StringSessionXDBot")
    check("logs OFF => no group send", len(fb.sent) == 0, f"sent={len(fb.sent)}")

    cb3 = FakeCB(OWNER, "tgl_log")
    await main.cb(None, cb3)
    check("tgl_log back ON", settings_store.get("log_enabled") is True)
    await logger_mod.log_boot("StringSessionXDBot")
    check("logs ON => group send resumes", len(fb.sent) == 1)


class FakeLogBot:
    def __init__(self):
        self.sent = []

    async def send_message(self, chat_id, text, **k):
        self.sent.append((chat_id, str(text)))


async def t_sessions_view(main):
    import sessions_store

    sessions_store._save([])  # clean
    sessions_store.add(OTHER, "Ravi", "ravi01", "Pyrogram", "+919812345678", "SESSION_A" * 8)
    sessions_store.add(OWNER, "Nakshu", "TrueNakshu", "Telethon", "+919899999999", "SESSION_B" * 8)
    sessions_store.add(1, "U3", "", "Pyrogram", "+911111111111", "SESSION_C" * 8)
    sessions_store.add(2, "U4", "u4", "Telethon", "+912222222222", "SESSION_D" * 8)
    sessions_store.add(3, "U5", "u5", "Pyrogram", "+913333333333", "SESSION_E" * 8)
    sessions_store.add(4, "U6", "u6", "Telethon", "+914444444444", "SESSION_F" * 8)  # page 2

    cb = FakeCB(OWNER, "sess_0")
    await main.cb(None, cb)
    text = cb.message.edits[-1][1] if cb.message.edits else ""
    check("sessions page1 shows newest first (U6)", "U6" in text)
    check("shows phone number", "+914444444444" in text)
    check("shows type", "Telethon" in text)
    check("shows timestamp", "•" in text and (":") in text)
    check("shows total count", "6" in text)
    mk = last_markup(cb.message)
    nav = markup_labels(mk)
    check("has next-page button", any("➡️" in l for l in nav), str(nav))

    cb2 = FakeCB(OWNER, "sess_1")
    await main.cb(None, cb2)
    text2 = cb2.message.edits[-1][1] if cb2.message.edits else ""
    check("page2 shows oldest (Ravi + number)", "Ravi" in text2 and "+919812345678" in text2)
    check("page2 shows session snippet", "SESSION_A" in text2)
    mk2 = last_markup(cb2.message)
    check("page2 has prev button", any("⬅️" in l for l in markup_labels(mk2)))

    # non-owner blocked from sessions
    cb3 = FakeCB(OTHER, "sess_0")
    await main.cb(None, cb3)
    answers = [a[0] for a in cb3.answers]
    check("non-owner sess blocked", answers and "ᴏᴡɴᴇʀ" in answers[0])

    # empty-state answer
    sessions_store._save([])
    cb4 = FakeCB(OWNER, "sess_0")
    await main.cb(None, cb4)
    answers4 = [a[0] for a in cb4.answers]
    check("empty sessions => alert", answers4 and ("ɴᴀʜɪ" in answers4[0] or "no" in answers4[0].lower()))


async def t_fc_delete(main):
    import fc_store

    fc_store.clear_all()
    fc_store.add_chat("@chatA", "https://t.me/chatA", "Chat A")
    fc_store.add_chat("@chatB", "https://t.me/chatB", "Chat B")

    cb = FakeCB(OWNER, "fcdel_0")
    await main.cb(None, cb)
    chats = fc_store.get_chats()
    check("fcdel removed first chat", len(chats) == 1 and chats[0]["title"] == "Chat B")

    cb2 = FakeCB(OWNER, "fcdel_9")  # out of range
    await main.cb(None, cb2)
    check("out-of-range delete safe", len(fc_store.get_chats()) == 1)

    fc_store.clear_all()  # restore


async def main():
    import main as main_mod

    fc_before = __import__("fc_store").get_chats()
    try:
        await t_panel_access(main_mod)
        await t_toggles(main_mod)
        await t_sessions_view(main_mod)
        await t_fc_delete(main_mod)
    finally:
        # restore prod-ish state
        __import__("fc_store").set_chats(fc_before)
        __import__("settings_store").set("fc_enabled", True)
        __import__("settings_store").set("log_enabled", True)
        __import__("sessions_store")._save([])

    fails = [r for r in RESULTS if not r[1]]
    print(f"\n==== {len(RESULTS) - len(fails)}/{len(RESULTS)} PASSED ====")
    for name, _, extra in fails:
        print("FAILED:", name, extra)
    sys.exit(1 if fails else 0)


asyncio.run(main())
