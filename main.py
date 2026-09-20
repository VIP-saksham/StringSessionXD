import os
import time

from pyrogram import Client, filters, idle

from start import WELCOME_TEXT, start_buttons
from help import HELP_TEXT, help_buttons
from pyrogram_module import handle_pyro, set_string_logger as set_pyro_logger
from telethon_module import handle_tele, set_string_logger as set_tele_logger
from logger import init_logger, log_boot, log_user_start, log_string_made, log_error

# ---------------- CONFIG ---------------- #
API_ID = int(os.getenv("API_ID", "0"))
API_HASH = os.getenv("API_HASH", "")
BOT_TOKEN = os.getenv("BOT_TOKEN", "")
CHANNEL = os.getenv("CHANNEL", "TheHellBots")
OWNER_ID = int(os.getenv("OWNER_ID", "0"))
LOG_CHAT = os.getenv("LOG_CHAT", "")
BOT_USERNAME = os.getenv("BOT_USERNAME", "StringSessionXDBot")

if not API_ID or not API_HASH or not BOT_TOKEN:
    raise SystemExit("Missing API_ID / API_HASH / BOT_TOKEN in .env")

# ---------------- BOT ---------------- #
bot = Client(
    "string_bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN,
)

users = {}


def _notify_logger(fn):
    def inner(user, typ, phone):
        try:
            fn(user, typ, phone, BOT_USERNAME)
        except TypeError:
            fn(user, typ, phone)
    return inner


def _wire_loggers():
    from logger import log_string_made as _lsm

    async def _pyro_log(user, typ, phone):
        await _lsm(user, typ, phone, BOT_USERNAME)

    async def _tele_log(user, typ, phone):
        await _lsm(user, typ, phone, BOT_USERNAME)

    set_pyro_logger(_pyro_log)
    set_tele_logger(_tele_log)


STEP_TEXT = {
    "pyro": (
        "<blockquote>🔥 𝗣𝗬𝗥𝗢𝗚𝗥𝗔𝗠 ꜱᴇʟᴇᴄᴛᴇᴅ</blockquote>\n"
        "━━━━━━━━━━━━━━━━━━━\n"
        "📥 ɴᴏᴡ ꜱᴇɴᴅ ᴍᴇ ʏᴏᴜʀ <b>ᴀᴘɪ ɪᴅ</b>\n"
        "(ᴍʏ.ᴛᴇʟᴇɢʀᴀᴍ.ᴏʀɢ ꜱᴇ ᴍɪʟᴇɢᴀ)"
    ),
    "tele": (
        "<blockquote>🍂 𝗧𝗘𝗟𝗘𝗧𝗛𝗢𝗡 ꜱᴇʟᴇᴄᴛᴇᴅ</blockquote>\n"
        "━━━━━━━━━━━━━━━━━━━\n"
        "📥 ɴᴏᴡ ꜱᴇɴᴅ ᴍᴇ ʏᴏᴜʀ <b>ᴀᴘɪ ɪᴅ</b>\n"
        "(ᴍʏ.ᴛᴇʟᴇɢʀᴀᴍ.ᴏʀɢ ꜱᴇ ᴍɪʟᴇɢᴀ)"
    ),
}


# ---------------- START ---------------- #
@bot.on_message(filters.private & filters.command("start"))
async def start(client, message):
    user = message.from_user
    users[user.id] = {"mode": None, "step": "choose", "time": time.time()}
    try:
        await message.reply(
            WELCOME_TEXT.format(name=user.first_name),
            reply_markup=start_buttons(CHANNEL),
        )
    except Exception as e:
        await log_error("start", e)
    await log_user_start(user)


# ---------------- HELP ---------------- #
@bot.on_message(filters.private & filters.command("help"))
async def help_cmd(client, message):
    await message.reply(HELP_TEXT, reply_markup=help_buttons())


# ---------------- CALLBACK ---------------- #
@bot.on_callback_query()
async def cb(client, cb):
    uid = cb.from_user.id
    data = cb.data

    if data == "pyro":
        users[uid] = {"mode": "pyro", "step": "api_id", "time": time.time()}
        await cb.answer("🔥 Pyrogram selected!")
        await cb.message.reply_text(STEP_TEXT["pyro"])

    elif data == "tele":
        users[uid] = {"mode": "tele", "step": "api_id", "time": time.time()}
        await cb.answer("🍂 Telethon selected!")
        await cb.message.reply_text(STEP_TEXT["tele"])

    elif data == "help":
        await cb.answer()
        try:
            await cb.message.edit_text(HELP_TEXT, reply_markup=help_buttons())
        except Exception:
            await cb.message.reply_text(HELP_TEXT, reply_markup=help_buttons())

    elif data == "back":
        await cb.answer()
        try:
            await cb.message.edit_text(
                WELCOME_TEXT.format(name=cb.from_user.first_name),
                reply_markup=start_buttons(CHANNEL),
                disable_web_page_preview=True,
            )
        except Exception:
            await cb.message.reply_text(
                WELCOME_TEXT.format(name=cb.from_user.first_name),
                reply_markup=start_buttons(CHANNEL),
            )

    else:
        await cb.answer()


# ---------------- MESSAGE HANDLER ---------------- #
@bot.on_message(filters.private & filters.text & ~filters.command(["start", "help"]))
async def msg(client, message):
    uid = message.from_user.id
    data = users.get(uid)
    if not data or not data.get("mode"):
        return
    try:
        if data["mode"] == "pyro":
            await handle_pyro(client, message, data, users, bot)
        elif data["mode"] == "tele":
            await handle_tele(client, message, data, users, bot)
    except Exception as e:
        users.pop(uid, None)
        await message.reply(
            "⚠️ <b>ꜱᴏᴍᴇᴛʜɪɴɢ ᴡᴇɴᴛ ᴡʀᴏɴɢ</b>\n"
            "━━━━━━━━━━━━━━━━━━━\n"
            f"<code>{e}</code>\n"
            "🔄 /start ꜱᴇ ᴅᴏʙᴀʀᴀ ᴛʀʏ ᴋʀᴏ"
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
    _wire_loggers()

    import asyncio
    bot.loop.create_task(log_boot(me.username))

    print("Bot Running Successfully")
    idle()
