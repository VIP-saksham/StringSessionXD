from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

WELCOME_TEXT = """<blockquote>✦ 𝗦𝗧𝗥𝗜𝗡𝗚 𝗚𝗘𝗡 𝟮.𝟬 ✦</blockquote>
━━━━━━━━━━━━━━━━━━━
👋 ꜱᴏʀʀʏ <b>{name}</b>! 🎀
ꜱᴇꜱꜱɪᴏɴ ꜱᴛʀɪɴɢ ʙᴀɴᴀᴏ ꜱɪᴍᴘʟᴇ ꜱᴛᴇᴘꜱ ᴍᴇ!
━━━━━━━━━━━━━━━━━━━
<b>⚡ ꜰᴇᴀᴛᴜʀᴇꜱ</b>
╭──────────────────
├• ⚡ ꜰᴀꜱᴛ & ᴄʟᴇᴀʀ ɢᴇɴᴇʀᴀᴛɪᴏɴ
├• 🍂 ᴛᴇʟᴇᴛʜᴏɴ + 🔥 ᴘʏʀᴏɢʀᴀᴍ
├• 🔐 2ꜰᴀ ꜱᴜᴘᴘᴏʀᴛ
├• 🛡️ ꜱᴇᴄᴜʀᴇ • ᴘʀɪᴠᴀᴛᴇ • ᴛʀᴜꜱᴛᴇᴅ
╰──────────────────
━━━━━━━━━━━━━━━━━━━
<b>📌 ʜᴏᴡ ᴛᴏ ᴜꜱᴇ</b>
❶ ʟɪʙʀᴀʀʏ ꜱᴇʟᴇᴄᴛ ᴋʀᴏ
❷ ᴀᴘɪ ᴅᴇᴛᴀɪʟꜱ ᴅᴏ
❸ ꜱᴇꜱꜱɪᴏɴ ʀᴇᴀᴅʏ! 🎉
━━━━━━━━━━━━━━━━━━━
<b>💡 ᴛɪᴘ:</b> ꜱᴛʀɪɴɢ ᴋᴏ ꜱᴇᴄʀᴇᴛ ʀᴀᴋʜᴏ —
ᴋɪꜱɪ ᴋᴏ ᴍᴀᴛ ᴅᴇɴᴀ! 🔐
"""


def start_buttons(channel):
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "💫 𝗢𝘄𝗻𝗲𝗿",
                    url="https://t.me/TrueNakshu",
                    style="bg_primary",
                ),
                InlineKeyboardButton(
                    "🫆 𝗖𝗵𝗮𝗻𝗻𝗲𝗹",
                    url=f"https://t.me/{channel}",
                    style="bg_primary",
                ),
            ],
            [
                InlineKeyboardButton(
                    "🤝 𝗦𝘂𝗽𝗽𝗼𝗿𝘁",
                    url="https://t.me/Sunshine_gc",
                    style="bg_primary",
                ),
            ],
            [
                InlineKeyboardButton(
                    "🍂 𝗧𝗲𝗹𝗲𝘁𝗵𝗼𝗻",
                    callback_data="tele",
                    style="bg_primary",
                ),
                InlineKeyboardButton(
                    "🔥 𝗣𝘆𝗿𝗼𝗴𝗿𝗮𝗺",
                    callback_data="pyro",
                    style="bg_primary",
                ),
            ],
            [
                InlineKeyboardButton(
                    "🕸️ 𝗛𝗲𝗹𝗽",
                    callback_data="help",
                    style="bg_primary",
                ),
            ],
        ]
    )
