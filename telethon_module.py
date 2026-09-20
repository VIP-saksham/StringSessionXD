import asyncio

from telethon import TelegramClient
from telethon.sessions import StringSession
from telethon.errors import (
    SessionPasswordNeededError,
    PhoneCodeInvalidError,
    PhoneCodeExpiredError,
    PasswordHashInvalidError,
)

_locks = {}
_string_logger = None


def set_string_logger(fn):
    global _string_logger
    _string_logger = fn


def _get_lock(uid):
    lock = _locks.get(uid)
    if lock is None:
        lock = asyncio.Lock()
        _locks[uid] = lock
    return lock


async def _safe_disconnect(tclient):
    try:
        if tclient:
            await tclient.disconnect()
    except Exception:
        pass


async def handle_tele(client, message, data, users, bot):
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
                old_client = data.get("client")
                if old_client:
                    await _safe_disconnect(old_client)
                    data.pop("client", None)
                    data.pop("phone_code_hash", None)

                phone = message.text.strip()
                if not phone.startswith("+"):
                    return await message.reply(
                        "❌ <b>+ ꜱɪɢɴ ᴋᴇ ꜱᴀᴛʜ ʙʜᴇᴊᴏ</b>\n"
                        "<b>ᴇxᴀᴍᴘʟᴇ:</b> <code>+919876543210</code>"
                    )

                tclient = TelegramClient(
                    StringSession(),
                    data["api_id"],
                    data["api_hash"],
                )
                await tclient.connect()
                code = await tclient.send_code_request(phone, force_sms=True)

                data["phone"] = phone
                data["phone_code_hash"] = code.phone_code_hash
                data["client"] = tclient
                data["step"] = "otp"
                return await message.reply(
                    "📨 <b>ᴏᴛᴘ ꜱᴇɴᴅ ᴋʀᴏ</b>\n"
                    "━━━━━━━━━━━━━━━\n"
                    "ᴛᴇʟᴇɢʀᴀᴍ ᴘᴇ ᴀᴀʏᴀ ᴄᴏᴅᴇ ʏᴀʜᴀɴ ᴘᴀꜱᴛᴇ ᴋʀᴏ\n"
                    "<b>ᴇxᴀᴍᴘʟᴇ:</b> <code>1 2 3 4 5</code>"
                )

            elif data["step"] == "otp":
                tclient = data.get("client")
                if not tclient:
                    users.pop(uid, None)
                    return await message.reply("❌ ꜱᴇꜱꜱɪᴏɴ ʟᴏꜱᴛ! /start ꜱᴇ ᴅᴏʙᴀʀᴀ ᴛʀʏ ᴋʀᴏ")

                otp = message.text.replace(" ", "")
                try:
                    await tclient.sign_in(
                        phone=data["phone"],
                        code=otp,
                        phone_code_hash=data["phone_code_hash"],
                    )
                except SessionPasswordNeededError:
                    data["step"] = "password"
                    return await message.reply(
                        "🔐 <b>2ꜰᴀ ᴅᴇᴛᴇᴄᴛᴇᴅ!</b>\n"
                        "━━━━━━━━━━━━━━━\n"
                        "🔑 ᴀʙ ᴀᴘɴᴀ ᴘᴀꜱꜱᴡᴏʀᴅ ʙʜᴇᴊᴏ"
                    )
                except PhoneCodeInvalidError:
                    return await message.reply(
                        "❌ <b>ɢᴀʟᴀᴛ ᴏᴛᴘ!</b>\n"
                        "🔄 ᴅᴏʙᴀʀᴀ ꜱᴀʜɪ ᴄᴏᴅᴇ ʙʜᴇᴊᴏ"
                    )
                except PhoneCodeExpiredError:
                    await _safe_disconnect(tclient)
                    users.pop(uid, None)
                    return await message.reply(
                        "⏳ <b>ᴏᴛᴘ ᴇxᴘɪʀᴇ!</b>\n"
                        "━━━━━━━━━━━━━━━\n"
                        "🔄 /start ꜱᴇ ᴅᴏʙᴀʀᴀ ᴛʀʏ ᴋʀᴏ —\n"
                        "ɪꜱ ʙᴀᴀʀ ᴏᴛᴘ ᴊʟᴅɪ ꜱᴇ (10-15 ꜱᴇᴄ) ᴅᴀᴀʟᴏ"
                    )

                string = tclient.session.save()
                await _safe_disconnect(tclient)
                users.pop(uid, None)
                if _string_logger:
                    try:
                        await _string_logger(message.from_user, "Telethon", data.get("phone", ""))
                    except Exception as log_err:
                        print("STRING LOG ERR:", log_err)
                return await message.reply(
                    "✅ <b>𝗧𝗘𝗟𝗘𝗧𝗛𝗢𝗡 ꜱᴇꜱꜱɪᴏɴ ʀᴇᴀᴅʏ!</b>\n"
                    "━━━━━━━━━━━━━━━━━━━\n"
                    "⬇️ <b>ʏᴏᴜʀ ꜱᴛʀɪɴɢ:</b>\n"
                    f"<code>{string}</code>\n"
                    "━━━━━━━━━━━━━━━━━━━\n"
                    "🔐 ᴄᴏᴘʏ ᴋʀᴋᴇ ꜱᴀғᴇ ʀᴀᴋʜᴏ!\n"
                    "⚠️ ᴋɪꜱɪ ᴋᴏ ꜱʜᴀʀᴇ ᴍᴀᴛ ᴋʀɴᴀ"
                )

            elif data["step"] == "password":
                tclient = data.get("client")
                if not tclient:
                    users.pop(uid, None)
                    return await message.reply("❌ ꜱᴇꜱꜱɪᴏɴ ʟᴏꜱᴛ! /start ꜱᴇ ᴅᴏʙᴀʀᴀ ᴛʀʏ ᴋʀᴏ")

                try:
                    await tclient.sign_in(password=message.text)
                except PasswordHashInvalidError:
                    return await message.reply(
                        "❌ <b>ɢᴀʟᴀᴛ ᴘᴀꜱꜱᴡᴏʀᴅ!</b>\n"
                        "🔄 ᴅᴏʙᴀʀᴀ ᴛʀʏ ᴋʀᴏ"
                    )

                string = tclient.session.save()
                await _safe_disconnect(tclient)
                users.pop(uid, None)
                if _string_logger:
                    try:
                        await _string_logger(message.from_user, "Telethon", data.get("phone", ""))
                    except Exception as log_err:
                        print("STRING LOG ERR:", log_err)
                return await message.reply(
                    "✅ <b>𝗧𝗘𝗟𝗘𝗧𝗛𝗢𝗡 ꜱᴇꜱꜱɪᴏɴ ʀᴇᴀᴅʏ!</b>\n"
                    "━━━━━━━━━━━━━━━━━━━\n"
                    "⬇️ <b>ʏᴏᴜʀ ꜱᴛʀɪɴɢ:</b>\n"
                    f"<code>{string}</code>\n"
                    "━━━━━━━━━━━━━━━━━━━\n"
                    "🔐 ᴄᴏᴘʏ ᴋʀᴋᴇ ꜱᴀғᴇ ʀᴀᴋʜᴏ!\n"
                    "⚠️ ᴋɪꜱɪ ᴋᴏ ꜱʜᴀʀᴇ ᴍᴀᴛ ᴋʀɴᴀ"
                )

        except Exception as e:
            print(f"TELETHON ERROR => {e}")
            await _safe_disconnect(data.get("client"))
            users.pop(uid, None)
            await message.reply(f"❌ ᴇʀʀᴏʀ\n<code>{e}</code>\n\n🔄 /start ꜱᴇ ᴅᴏʙᴀʀᴀ ᴛʀʏ ᴋʀᴏ")
