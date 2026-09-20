import os
import time

from pyrogram import Client, filters, idle
from pyrogram.enums import ChatMemberStatus
from pyrogram.errors import UserNotParticipant, ChatAdminRequired, RPCError

import fc_store
from start import (
    INFO_TEXT, GEN_TEXT, ASK_API_ID, ASK_API_HASH, FC_TEXT, HELP_TEXT,
    start_buttons, gen_buttons, fc_buttons, help_buttons,
)
from pyrogram_module import handle_pyro
from telethon_module import handle_tele
from logger import init_logger, log_boot, log_user_start, log_error

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


# ---------------- FORCE-SUB CHECK ---------------- #
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
        except (ChatAdminRequired, RPCError) as e:
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
    if fc_store.get_chats() and not await is_user_joined(user.id):
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
        if fc_store.get_chats() and not await is_user_joined(uid):
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
        await cb.message.reply_text(ASK_API_ID)

    elif data == "help":
        await cb.answer()
        await _send(None, HELP_TEXT, help_buttons(), edit_msg=cb.message)

    elif data == "back":
        await cb.answer()
        await send_welcome(cb.message, cb.from_user, edit_msg=cb.message)

    elif data == "verify":
        if await is_user_joined(uid):
            await cb.answer("✅ ᴠᴇʀɪꜰɪᴇᴅ! ᴡᴇʟᴄᴏᴍᴇ 🌹")
            users[uid] = {"mode": None, "step": "choose", "time": time.time()}
            await send_welcome(cb.message, cb.from_user, edit_msg=cb.message)
        else:
            await cb.answer("❌ ᴀʙʜɪ ᴛᴏ ᴊᴏɪɴ ɴᴀʜɪ ᴋɪʏᴀ! ᴘʜɪʟᴇ ᴊᴏɪɴ ᴋʀᴏ 🔸", show_alert=True)

    else:
        await cb.answer()


# ---------------- MESSAGE HANDLER ---------------- #
@bot.on_message(filters.private & filters.text & ~filters.command(["start", "help", "fc"]))
async def msg(client, message):
    uid = message.from_user.id
    data = users.get(uid)
    if not data or not data.get("mode"):
        return

    text = (message.text or "").strip()

    if text.lower() == "/skip" and data["step"] in ("api_id", "api_hash"):
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
        try:
            data["api_id"] = int(text)
        except Exception:
            return await message.reply(ASK_API_ID)
        data["step"] = "api_hash"
        return await message.reply(ASK_API_HASH)

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

    bot.loop.create_task(log_boot(me.username))
    print("Bot Running Successfully")
    idle()
