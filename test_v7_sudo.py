"""Tests for the /active fix + sudo system (v7).

Root cause being tested: pyrogram runs only the FIRST matching handler of
the lowest group; the catch-all text handler used to swallow /active.
After fix: /active (group=1) fires for owner AND sudos; msg handler excludes
admin commands; sudo store persists.

Run ON the VPS: /root/strxvenv/bin/python test_v7_sudo.py
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

OWNER = int(os.environ["OWNER_ID"])
SUDO_USER = 777888999
RANDOM = 111222333

RESULTS = []


def check(name, cond, extra=""):
    RESULTS.append((name, bool(cond), extra))
    print(("PASS" if cond else "FAIL") + f" | {name}" + (f" | {extra}" if extra and not cond else ""))


class FakeUser:
    def __init__(self, uid):
        self.id = uid
        self.first_name = "T"
        self.username = "t"


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

    async def reply(self, text=None, **k):
        return await self.reply_text(text, **k)


def pyro_command(name, text):
    """Simulate what filters.command checks: entities + text prefix."""
    return text.startswith("/" + name)


async def main():
    import main as main_mod
    import sudo_store
    import fc_store

    sudo_store._save([])
    fc_before = fc_store.get_chats()
    fc_store.clear_all()

    try:
        # ---- /active for owner ----
        m = FakeMsg(OWNER, "/active")
        await main_mod.active_panel(None, m)
        check("owner /active opens panel", m.replies and "𝗔𝗗𝗠𝗜𝗡 𝗣𝗔𝗡𝗘𝗟" in m.replies[0][0])

        # ---- /active for random user => ignored ----
        m2 = FakeMsg(RANDOM, "/active")
        await main_mod.active_panel(None, m2)
        check("random /active ignored", not m2.replies)

        # ---- msg handler no longer swallows admin commands ----
        import inspect

        src = inspect.getsource(main_mod.msg)
        for cmd in ("active", "addsudo", "rmsudo", "sudolist", "broadcast"):
            check(f"msg handler excludes /{cmd}", f'"{cmd}"' in src)

        # ---- /addsudo (owner) ----
        m3 = FakeMsg(OWNER, f"/addsudo {SUDO_USER}")
        await main_mod.addsudo_cmd(None, m3)
        check("addsudo persisted", sudo_store.is_sudo(SUDO_USER))
        check("addsudo reply confirms", m3.replies and "ᴀᴅᴅᴇᴅ" in m3.replies[0][0])

        # ---- now sudo can open /active ----
        m4 = FakeMsg(SUDO_USER, "/active")
        await main_mod.active_panel(None, m4)
        check("sudo /active opens panel", m4.replies and "𝗔𝗗𝗠𝗜𝗡 𝗣𝗔𝗡𝗘𝗟" in m4.replies[0][0])

        # ---- random user still cannot ----
        m5 = FakeMsg(RANDOM, "/active")
        await main_mod.active_panel(None, m5)
        check("random still ignored", not m5.replies)

        # ---- sudolist (admin only) ----
        m6 = FakeMsg(SUDO_USER, "/sudolist")
        await main_mod.sudolist_cmd(None, m6)
        check("sudolist shows for sudo", m6.replies and str(SUDO_USER) in m6.replies[0][0])

        # ---- /rmsudo (owner) ----
        m7 = FakeMsg(OWNER, f"/rmsudo {SUDO_USER}")
        await main_mod.rmsudo_cmd(None, m7)
        check("rmsudo removed", not sudo_store.is_sudo(SUDO_USER))

        # ---- removed sudo loses /active ----
        m8 = FakeMsg(SUDO_USER, "/active")
        await main_mod.active_panel(None, m8)
        check("removed sudo /active ignored", not m8.replies)

        # ---- non-owner cannot addsudo (filtered by pyrogram user filter) ----
        # simulate: filters.user would reject; call handler directly must be safe
        m9 = FakeMsg(RANDOM, "/addsudo 999")
        # pyrogram would not deliver this; emulate guard by direct call:
        # handler has no in-body guard, but filters.user blocks delivery.
        # verify filter is present:
        hsrc = inspect.getsource(main_mod.addsudo_cmd)
        reg = inspect.getsource(main_mod)
        check("addsudo registered owner-only", 'filters.user(OWNER_ID) & filters.command("addsudo")' in reg)

        # ---- owner always admin ----
        check("owner is admin by default", main_mod._is_admin(OWNER))
        check("sudo flagged admin", (sudo_store.add_sudo(SUDO_USER), main_mod._is_admin(SUDO_USER))[1])
        check("random not admin", not main_mod._is_admin(RANDOM))
        sudo_store._save([])

        # ---- sudo can also use panel buttons (tgl_log roundtrip) ----
        class FakeCB:
            def __init__(self, uid, data):
                self.from_user = FakeUser(uid)
                self.data = data
                self.message = type("M", (), {"edits": [], "captions": [], "replies": []})()
                self.answers = []

                async def edit_text(inner_self, text=None, **k):
                    inner_self.edits.append((str(text), k))

                async def edit_caption(inner_self, caption=None, **k):
                    inner_self.captions.append((str(caption), k))

                async def reply_text(inner_self, text=None, **k):
                    inner_self.replies.append(str(text))

            async def answer(self, text=None, show_alert=False):
                self.answers.append((str(text or ""), show_alert))

        sudo_store.add_sudo(SUDO_USER)
        import settings_store

        before = settings_store.get("log_enabled")
        cb = FakeCB(SUDO_USER, "tgl_log")
        await main_mod.cb(None, cb)
        check("sudo can toggle logs", settings_store.get("log_enabled") == (not before))
        cb2 = FakeCB(OWNER, "tgl_log")
        await main_mod.cb(None, cb2)
        check("owner toggle restores", settings_store.get("log_enabled") == before)
        sudo_store._save([])

    finally:
        sudo_store._save([])
        fc_store.set_chats(fc_before)

    fails = [r for r in RESULTS if not r[1]]
    print(f"\n==== {len(RESULTS) - len(fails)}/{len(RESULTS)} PASSED ====")
    for name, _, extra in fails:
        print("FAILED:", name, extra)
    sys.exit(1 if fails else 0)


asyncio.run(main())
