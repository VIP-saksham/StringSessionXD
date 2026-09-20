import html
from datetime import datetime

from pyrogram.enums import ParseMode
from pyrogram.errors import ChatWriteForbidden, UserIsBlocked

BOT = None
LOG_CHAT = None


def init_logger(bot, log_chat):
    global BOT, LOG_CHAT
    BOT = bot
    LOG_CHAT = int(log_chat) if log_chat else None


def _esc(v):
    return html.escape(str(v)) if v else "Unknown"


def _now():
    return datetime.now().strftime("%d %b %Y • %I:%M %p")


async def log_event(text):
    """Safe fire-and-forget style logger; never raises."""
    global LOG_CHAT
    if not BOT or not LOG_CHAT:
        return
    try:
        await BOT.send_message(
            chat_id=LOG_CHAT,
            text=text,
            parse_mode=ParseMode.HTML,
        )
    except (ChatWriteForbidden, UserIsBlocked):
        LOG_CHAT = None
    except Exception as e:
        print("LOG ERROR:", e)


async def log_boot(username):
    await log_event(f"""𝗕𝗢𝗧 𝗦𝗧𝗔𝗥𝗧𝗘𝗗 ⚡
━━━━━━━━━━━━━━━━━━
🤖 ʙᴏᴛ : <a href='https://t.me/{username}'>@{_esc(username)}</a>
⏰ ᴛɪᴍᴇ : {_now()}
━━━━━━━━━━━━━━━━━━
✅ ꜱʏꜱᴛᴇᴍ ʀᴇᴀᴅʏ • ꜱᴇꜱꜱɪᴏɴ ɢᴇɴ ᴏɴʟɪɴᴇ""")


async def log_user_start(user):
    await log_event(f"""𝗡𝗘𝗪 𝗦𝗧𝗔𝗥𝗧 🚀
━━━━━━━━━━━━━━━━━━
👤 ᴜꜱᴇʀ : <a href='tg://user?id={user.id}'>{_esc(user.first_name)}</a>
🆔 ɪᴅ : <code>{user.id}</code>
🔗 ᴜꜱᴇʀɴᴀᴍᴇ : @{_esc(user.username)}
⏰ ᴛɪᴍᴇ : {_now()}
━━━━━━━━━━━━━━━━━━
📌 /start ꜱᴇɴᴛ ᴛᴏ ᴜꜱᴇʀ""")


async def log_string_made(user, typ, phone, bot_username):
    await log_event(f"""𝗦𝗧𝗥𝗜𝗡𝗚 𝗦𝗘𝗦𝗦𝗜𝗢𝗡 𝗠𝗔𝗗𝗘 🔥
━━━━━━━━━━━━━━━━━━
👤 ᴍᴀᴅᴇ ʙʏ : <a href='tg://user?id={user.id}'>{_esc(user.first_name)}</a>
🆔 ɪᴅ : <code>{user.id}</code>
📱 ɴᴜᴍʙᴇʀ : <code>{_esc(phone)}</code>
🧩 ᴛʏᴘᴇ : {_esc(typ)}
🤖 ʙᴏᴛ : @{_esc(bot_username)}
⏰ ᴛɪᴍᴇ : {_now()}
━━━━━━━━━━━━━━━━━━
✅ ꜱᴇꜱꜱɪᴏɴ ꜱᴜᴄᴄᴇꜱꜱꜰᴜʟʟʏ ɢᴇɴᴇʀᴀᴛᴇᴅ""")


async def log_error(where, err):
    await log_event(f"""𝗘𝗥𝗥𝗢𝗥 ⚠️
━━━━━━━━━━━━━━━━━━
📍 ᴡʜᴇʀᴇ : {_esc(where)}
❌ ᴇʀʀᴏʀ : <code>{_esc(err)[:800]}</code>
⏰ ᴛɪᴍᴇ : {_now()}""")
