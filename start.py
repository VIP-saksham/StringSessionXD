from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

INFO_TEXT = """┌───── ˹ ɪɴꜰᴏʀᴍᴀᴛɪᴏɴ ˼─── ⏤͟͞●
┆◍ ʜᴇʏ <a href='tg://user?id={uid}'>{name}</a>
┆◍ ɪ'ᴍ : <b>@{bot_username}</b>
└─────────────────────•
 ❀ ɪ'ᴍ ᴀ ꜱᴇꜱꜱɪᴏɴ ɢᴇɴᴇʀᴀᴛᴇ ʙᴏᴛ.
 ❃ ꜱᴜᴘᴘᴏʀᴛ - ᴘʏʀᴏɢʀᴀᴍ | ᴛᴇʟᴇᴛʜᴏɴ.
 ✮ ɴᴏ ɪᴅ ʟᴏɢ ᴏᴜᴛ ɪꜱꜱᴜᴇ & ꜰᴜʟʟ ꜱᴇᴄᴜʀᴇ.
 •───────────────────────•
 ❖ 𝐏ᴏᴡᴇʀᴇᴅ ʙʏ :- <a href='https://t.me/{channel}'>˹ {channel_name} ˼</a> ❤️‍🔥
 •───────────────────────•"""

GEN_TEXT = """★ ᴄʟɪᴄᴋ ʙᴇʟᴏᴡ ʙᴜᴛᴛᴏɴ ᴛᴏ ꜱᴛᴀʀᴛ ɢᴇɴ ꜱᴇꜱꜱɪᴏɴ.

⊚ ʏᴏᴜ ʜᴀᴠᴇ ɴᴏ ᴀᴘɪ ɪᴅ ʜᴀꜱʜ ʏᴏᴜ ᴄᴀɴ ᴜꜱᴇ ᴍʏ

 • ᴀᴘɪ ɪᴅ :- <code>{api_id}</code>
 • ᴀᴘɪ ʜᴀꜱʜ :- <code>{api_hash}</code>

» ᴄʜᴏᴏꜱᴇ ᴏɴᴇ ᴛʜᴀᴛ ʏᴏᴜ ᴡᴀɴᴛ ᴛᴏ ɢᴇɴᴇʀᴀᴛᴇ ꜱᴇꜱꜱɪᴏɴ ✔️"""

ASK_API_ID = """❖ ᴘʟᴇᴀꜱᴇ ꜱᴇɴᴅ ʏᴏᴜʀ <b>ᴀᴘɪ_ɪᴅ</b> ᴛᴏ ᴘʀᴏᴄᴇᴇᴅ.

» ᴄʟɪᴄᴋ ᴏɴ /ꜱᴋɪᴘ ꜰᴏʀ ᴜꜱɪɴɢ ʙᴏᴛ ᴀᴘɪ."""

ASK_API_HASH = """✅ ᴀᴘɪ_ɪᴅ ꜱᴀᴠᴇᴅ!

❖ ɴᴏᴡ ꜱᴇɴᴅ ʏᴏᴜʀ <b>ᴀᴘɪ_ʜᴀꜱʜ</b> ᴛᴏ ᴘʀᴏᴄᴇᴇᴅ.

» ᴄʟɪᴄᴋ ᴏɴ /ꜱᴋɪᴘ ꜰᴏʀ ᴜꜱɪɴɢ ʙᴏᴛ ᴀᴘɪ."""

FC_TEXT = """✦ » ғɪʀsᴛʟʏ ʏᴏᴜ ɴᴇᴇᴅ ᴛᴏ ᴊᴏɪɴ ᴏᴜʀ
ғᴀᴍɪʟʏ ᴛʜᴇɴ ʏᴏᴜ ᴄᴀɴ ᴜsᴇ ᴍᴇ 🔸 ᴏғғɪᴄᴇ 🔸.

ᴀғᴛᴇʀ ᴊᴏɪɴ ❖ /start ❖ ᴍᴇ ᴀɢᴀɪɴ 🌹!"""


def start_buttons(channel):
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("★ 𝗦𝗧𝗔𝗥𝗧 𝗚𝗘𝗡 𝗦𝗘𝗦𝗦𝗜𝗢𝗡 ★", callback_data="gen", style="bg_primary")
            ],
            [
                InlineKeyboardButton("💫 𝗢𝘄𝗻𝗲𝗿", url="https://t.me/TrueNakshu", style="bg_primary"),
                InlineKeyboardButton("🫆 𝗖𝗵𝗮𝗻𝗻𝗲𝗹", url=f"https://t.me/{channel}", style="bg_primary"),
            ],
            [
                InlineKeyboardButton("🤝 𝗦𝘂𝗽𝗽𝗼𝗿𝘁", url="https://t.me/Sunshine_gc", style="bg_primary"),
                InlineKeyboardButton("🕸️ 𝗛𝗲𝗹𝗽", callback_data="help", style="bg_primary"),
            ],
        ]
    )


def gen_buttons():
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("🔥 𝗣𝘆𝗿𝗼𝗴𝗿𝗮𝗺", callback_data="pyro", style="bg_primary"),
                InlineKeyboardButton("🍂 𝗧𝗲𝗹𝗲𝘁𝗵𝗼𝗻", callback_data="tele", style="bg_primary"),
            ],
            [
                InlineKeyboardButton("🔙 𝗕𝗮𝗰𝗸", callback_data="back", style="bg_primary")
            ],
        ]
    )


def fc_buttons(chats):
    rows = []
    for i, c in enumerate(chats, 1):
        rows.append([InlineKeyboardButton(f"🔸 𝗝𝗢𝗜𝗡 𝗖𝗛𝗔𝗧 {i} 🔸", url=c["url"], style="bg_primary")])
    rows.append([InlineKeyboardButton("🔄 𝗩𝗲𝗿𝗶𝗳𝘆 𝗡𝗼𝘄 ✓", callback_data="verify", style="bg_primary")])
    return InlineKeyboardMarkup(rows)


def help_buttons():
    return InlineKeyboardMarkup([[InlineKeyboardButton("🔙 𝗕𝗮𝗰𝗸", callback_data="back", style="bg_primary")]])


HELP_TEXT = """<blockquote>📖 𝗛𝗘𝗟𝗣 𝗠𝗘𝗡𝗨</blockquote>
━━━━━━━━━━━━━━━━━━━
<b>ꜱᴛᴇᴘ ʙʏ ꜱᴛᴇᴘ ɢᴜɪᴅᴇ</b>
╭──────────────────
├• ❶ ★ ꜱᴛᴀʀᴛ ɢᴇɴ ꜱᴇꜱꜱɪᴏɴ ᴘʀᴇꜱꜱ ᴋʀᴏ
├• ❷ ᴘʏʀᴏɢʀᴀᴍ / ᴛᴇʟᴇᴛʜᴏɴ ᴄʜᴏᴏꜱᴇ ᴋʀᴏ
├• ❸ ᴀᴘɪ_ɪᴅ / ᴀᴘɪ_ʜᴀꜱʜ ʙʜᴇᴊᴏ (ʏᴀ /ꜱᴋɪᴘ)
├• ❹ ᴘʜᴏɴᴇ ɴᴜᴍʙᴇʀ (+91xxxx)
├• ❺ ᴏᴛᴘ ʙʜᴇᴊᴏ
├• ❻ 2ꜰᴀ ʜᴀɪ ᴛᴏ ᴘᴀꜱꜱᴡᴏʀᴅ
╰──────────────────
━━━━━━━━━━━━━━━━━━━
<b>🔑 ᴀᴘɪ ᴋᴀʜᴀɴ ꜱᴇ ᴍɪʟᴇɢᴀ?</b>
👉 <a href="https://my.telegram.org">my.telegram.org</a>
━━━━━━━━━━━━━━━━━━━
🔐 ꜱᴛʀɪɴɢ = ᴀᴄᴄᴏᴜɴᴛ ᴋᴇʏ! ꜱʜᴀʀᴇ ᴍᴀᴛ ᴋʀɴᴀ ⚠️"""
