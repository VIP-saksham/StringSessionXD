"""Behavioral lifecycle tests for Saved-Messages delivery (v5).

Drives the REAL handle_pyro / handle_tele handlers end-to-end with an
injected fake user-client: api_id -> api_hash -> phone -> OTP -> sign-in
-> export string -> send to "me" (Saved Messages) -> disconnect -> logger
-> bot notice. Asserts ordering, content, and failure-path resilience.

Run ON the VPS: /root/strxvenv/bin/python test_v5_lifecycle.py
"""
import asyncio
import os
import sys

os.chdir("/root/stringsessionxd")
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
    def __init__(self, uid=777, first="Lifecycle", username="lc_user"):
        self.id, self.first_name, self.username = uid, first, username


class FakeMsg:
    def __init__(self, text="", uid=777):
        self.text = text
        self.from_user = FakeUser(uid)
        self.replies = []

    async def reply(self, text=None, *a, **k):
        self.replies.append(str(text))
        return self

    async def reply_text(self, text=None, **k):
        self.replies.append(str(text))
        return self


class FakeBot:
    def __init__(self, raise_on=False):
        self.sent = []
        self.raise_on = raise_on

    async def send_message(self, chat_id, text, **k):
        if self.raise_on:
            raise RuntimeError("user blocked bot")
        self.sent.append((chat_id, str(text)))
        return self


def make_fake_pyro_client(store, fail_send_me=False):
    """Returns a Client class whose instances record the full call order."""
    from pyrogram.enums import SentCodeType

    class FakeCode:
        type = SentCodeType.SMS
        phone_code_hash = "HASH123"

    class FakeApp:
        def __init__(self, name=None, api_id=None, api_hash=None, in_memory=False, **kw):
            store["init"] = dict(name=name, api_id=api_id, api_hash=api_hash)

        async def connect(self):
            store["order"].append("connect")

        async def send_code(self, phone):
            store["order"].append("send_code")
            store["phone"] = phone
            return FakeCode()

        async def sign_in(self, phone_number=None, phone_code_hash=None, phone_code=None):
            store["order"].append("sign_in")
            if store.get("need_2fa"):
                from pyrogram.errors import SessionPasswordNeeded
                raise SessionPasswordNeeded()

        async def check_password(self, password):
            store["order"].append("check_password")
            if password == "wrongpass":
                from pyrogram.errors import PasswordHashInvalid
                raise PasswordHashInvalid()

        async def export_session_string(self):
            store["order"].append("export")
            return store["string"]

        async def send_message(self, recipient, text, **kw):
            store["order"].append(f"send:{recipient}")
            if fail_send_me:
                raise RuntimeError("flood wait")
            store["sent_me"].append((recipient, str(text)))

        async def disconnect(self):
            store["order"].append("disconnect")

    return FakeApp


def make_fake_telethon_client(store, fail_send_me=False):
    class FakeSession:
        def save(self):
            store["order"].append("save")
            return store["string"]

    class FakeCode:
        phone_code_hash = "THASH"

    class FakeTC:
        def __init__(self, session, api_id, api_hash):
            store["init"] = dict(api_id=api_id, api_hash=api_hash)
            self.session = FakeSession()

        async def connect(self):
            store["order"].append("connect")

        async def send_code_request(self, phone, force_sms=False):
            store["order"].append("send_code")
            assert force_sms is True
            store["phone"] = phone
            return FakeCode()

        async def sign_in(self, phone=None, code=None, phone_code_hash=None, password=None):
            store["order"].append("sign_in" if password is None else "sign_in_pw")
            if password is None and store.get("need_2fa"):
                from telethon.errors import SessionPasswordNeededError
                raise SessionPasswordNeededError()

        async def send_message(self, recipient, text, parse_mode=None):
            store["order"].append(f"send:{recipient}")
            store["sent_me"].append((recipient, str(text)))
            store["last_parse_mode"] = parse_mode
            if fail_send_me:
                raise RuntimeError("flood wait")

        async def disconnect(self):
            store["order"].append("disconnect")

    return FakeTC


def base_asserts(store, tag, expect_string):
    order = store["order"]
    check(f"[{tag}] sent to 'me' (Saved Messages)",
          any(r == "send:me" for r in order))
    me_idx = order.index("send:me") if "send:me" in order else -1
    disc_idx = order.index("disconnect") if "disconnect" in order else len(order)
    check(f"[{tag}] saved-msg BEFORE disconnect", 0 <= me_idx < disc_idx)
    exp_idx = order.index("export" if "export" in order else "save")
    check(f"[{tag}] string exported BEFORE saved-msg", exp_idx < me_idx)
    check(f"[{tag}] saved-msg content has string",
          not store["sent_me"] or expect_string in store["sent_me"][0][1])
    check(f"[{tag}] saved-msg has thanks footer",
          not store["sent_me"] or "ᴛʜᴀɴᴋꜱ ꜰᴏʀ ᴜꜱɪɴɢ @StringSessionXDBot" in store["sent_me"][0][1])
    check(f"[{tag}] saved-msg has ready header",
          not store["sent_me"] or "ꜱᴇꜱꜱɪᴏɴ ʀᴇᴀᴅʏ" in store["sent_me"][0][1])


async def pyro_full_flow(fail_send_me=False, need_2fa=False, bot_raise=False):
    import pyrogram_module as pm
    store = {"order": [], "sent_me": [], "string": f"PYRO_FAKE_{fail_send_me}_{need_2fa}",
             "need_2fa": need_2fa}
    pm.Client = make_fake_pyro_client(store, fail_send_me)

    logs = []

    async def rec(user, typ, phone, string):
        logs.append((user.id, typ, phone, string))

    pm.set_string_logger(rec)

    bot = FakeBot(raise_on=bot_raise)
    data = {"mode": "pyro", "step": "api_id"}
    uid = 777 if not fail_send_me else 778

    m1 = FakeMsg("12345", uid)
    await pm.handle_pyro(None, m1, data, {uid: data}, bot)
    m2 = FakeMsg("deadbeef", uid)
    await pm.handle_pyro(None, m2, data, {uid: data}, bot)
    m3 = FakeMsg("+919999888877", uid)
    await pm.handle_pyro(None, m3, data, {uid: data}, bot)
    m4 = FakeMsg("1 2 3 4 5", uid)
    await pm.handle_pyro(None, m4, data, {uid: data}, bot)

    if need_2fa:
        check("[pyro2fa] 2fa step prompt", any("2ꜰᴀ" in r for r in m4.replies))
        m5 = FakeMsg("mypassword", uid)
        await pm.handle_pyro(None, m5, data, {uid: data}, bot)
        check("[pyro2fa] check_password called", "check_password" in store["order"])

    tag = f"pyro{'2fa' if need_2fa else ''}{'+failme' if fail_send_me else ''}{'+botfail' if bot_raise else ''}"
    base_asserts(store, tag, store["string"])

    check(f"[{tag}] logger got (uid,'Pyrogram',phone,string)",
          logs and logs[0] == (uid, "Pyrogram", "+919999888877", store["string"]))
    check(f"[{tag}] client inited with user api creds",
          store["init"]["api_id"] == 12345 and store["init"]["api_hash"] == "deadbeef")
    if not bot_raise:
        # bot DM backup delivery = full string + thanks; chat notice mentions Saved Messages
        check(f"[{tag}] bot DM backup has full string+thanks",
              bot.sent and store["string"] in bot.sent[0][1]
              and "ᴛʜᴀɴᴋꜱ ꜰᴏʀ ᴜꜱɪɴɢ @StringSessionXDBot" in bot.sent[0][1])
        if not fail_send_me:
            last_replies = m4.replies if not need_2fa else m5.replies
            check(f"[{tag}] chat notice = saved-messages info",
                  last_replies and "ꜱᴀᴠᴇᴅ ᴍᴇꜱꜱᴀɢᴇꜱ" in last_replies[-1])
    if fail_send_me:
        # saved-msg send raised, but user STILL got string via bot DM
        check(f"[{tag}] saved-msg failed => no crash, bot DM still delivered",
              bot.sent and store["string"] in bot.sent[0][1])
    if bot_raise:
        check(f"[{tag}] bot blocked => fallback reply has FULL string",
              m4.replies and store["string"] in m4.replies[-1] and "ᴛʜᴀɴᴋꜱ" in m4.replies[-1])
    return store


async def tele_full_flow(fail_send_me=False):
    import telethon_module as tm
    store = {"order": [], "sent_me": [], "string": f"TELE_FAKE_{fail_send_me}", "need_2fa": False}
    tm.TelegramClient = make_fake_telethon_client(store, fail_send_me)

    logs = []

    async def rec(user, typ, phone, string):
        logs.append((user.id, typ, phone, string))

    tm.set_string_logger(rec)

    bot = FakeBot()
    data = {"mode": "tele", "step": "api_id"}
    uid = 888

    await tm.handle_tele(None, FakeMsg("12345", uid), data, {uid: data}, bot)
    await tm.handle_tele(None, FakeMsg("deadbeef", uid), data, {uid: data}, bot)
    await tm.handle_tele(None, FakeMsg("+918888777666", uid), data, {uid: data}, bot)
    m4 = FakeMsg("1 2 3 4 5", uid)
    await tm.handle_tele(None, m4, data, {uid: data}, bot)

    base_asserts(store, f"tele{'+failme' if fail_send_me else ''}", store["string"])
    check("[tele] parse_mode html passed", store.get("last_parse_mode") == "html")
    check("[tele] logger got (uid,'Telethon',phone,string)",
          logs and logs[0] == (888, "Telethon", "+918888777666", store["string"]))
    if not fail_send_me:
        check("[tele] bot DM backup has full string+thanks",
              bot.sent and store["string"] in bot.sent[0][1]
              and "ᴛʜᴀɴᴋꜱ ꜰᴏʀ ᴜꜱɪɴɢ @StringSessionXDBot" in bot.sent[0][1])
        check("[tele] chat notice = saved-messages info",
              m4.replies and "ꜱᴀᴠᴇᴅ ᴍᴇꜱꜱᴀɢᴇꜱ" in m4.replies[-1])
    else:
        check("[tele+failme] saved-msg failed => no crash, bot DM still delivered",
              "disconnect" in store["order"] and bot.sent
              and store["string"] in bot.sent[0][1])
    return store


async def main():
    await pyro_full_flow()                      # happy path
    await pyro_full_flow(need_2fa=True)         # 2FA path
    await pyro_full_flow(fail_send_me=True)     # saved-msg send fails => no crash
    await pyro_full_flow(bot_raise=True)        # bot blocked => fallback full string in chat
    await tele_full_flow()                      # telethon happy path
    await tele_full_flow(fail_send_me=True)     # telethon saved-msg fails => no crash

    fails = [r for r in RESULTS if not r[1]]
    print(f"\n==== {len(RESULTS) - len(fails)}/{len(RESULTS)} PASSED ====")
    for name, _, extra in fails:
        print("FAILED:", name, extra)
    sys.exit(1 if fails else 0)


asyncio.run(main())
