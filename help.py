from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

HELP_TEXT = """<blockquote>📖 𝗛𝗘𝗟𝗣 𝗠𝗘𝗡𝗨</blockquote>
━━━━━━━━━━━━━━━━━━━
<b>ꜱᴛᴇᴘ ʙʏ ꜱᴛᴇᴘ ɢᴜɪᴅᴇ</b>
╭──────────────────
├• ❶ ᴘʏʀᴏɢʀᴀᴍ / ᴛᴇʟᴇᴛʜᴏɴ ᴄʜᴏᴏꜱᴇ ᴋʀᴏ
├• ❷ ᴀᴘɪ_ɪᴅ ʙʜᴇᴊᴏ
├• ❸ ᴀᴘɪ_ʜᴀꜱʜ ʙʜᴇᴊᴏ
├• ❹ ᴘʜᴏɴᴇ ɴᴜᴍʙᴇʀ (+91xxxx)
├• ❺ ᴏᴛᴘ ʙʜᴇᴊᴏ
├• ❻ 2ꜰᴀ ʜᴀɪ ᴛᴏ ᴘᴀꜱꜱᴡᴏʀᴅ
╰──────────────────
━━━━━━━━━━━━━━━━━━━
<b>🔑 ᴀᴘɪ ᴋᴀʜᴀɴ ꜱᴇ ᴍɪʟᴇɢᴀ?</b>
👉 <a href="https://my.telegram.org">my.telegram.org</a> ᴘᴇ ᴋʜᴏʟᴏ
→ API development tools → ᴄᴏᴘʏ ɪᴅ + ʜᴀꜱʜ
━━━━━━━━━━━━━━━━━━━
🔐 ꜱᴛʀɪɴɢ = ᴀᴄᴄᴏᴜɴᴛ ᴋᴇʏ!
ꜱʜᴀʀᴇ ᴋɪʏᴀ ᴛᴏ ᴀᴄᴄᴏᴜɴᴛ ɢᴀʏᴀ! ⚠️
"""


def help_buttons():
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "🔙 𝗕𝗮𝗰𝗸",
                    callback_data="back",
                    style="bg_primary",
                )
            ]
        ]
    )
