# Copyright (c) 2025 TheHamkerAlone
# Licensed under the MIT License.
# This file is part of AloneXMusic

import os
import asyncio
import uuid

from pyrogram import errors, filters, types

from AloneX import app, db, lang


_broadcast_lock = asyncio.Lock()
broadcasting = False


def _parse_flags(message: types.Message) -> set[str]:
    """
    /broadcast -user -nochat -copy gibi flag'leri tek yerden toplar.
    Pyrogram: message.command -> ["broadcast", "-user", "-copy", ...]
    """
    cmd = message.command or []
    flags = set(cmd[1:])  # ilk eleman komut adı
    # bazen insanlar /broadcast@BotUsername yazar; pyrogram bunu ayırır ama yine de güvenli olalım
    return {f.strip().lower() for f in flags}


@app.on_message(filters.command(["broadcast"]) & app.sudoers)
@lang.language()
async def _broadcast(_, message: types.Message):
    global broadcasting

    if not message.reply_to_message:
        return await message.reply_text(message.lang["gcast_usage"])

    # Aynı anda 2 broadcast başlamasın diye kilit
    if _broadcast_lock.locked():
        return await message.reply_text(message.lang["gcast_active"])

    async with _broadcast_lock:
        if broadcasting:
            return await message.reply_text(message.lang["gcast_active"])

        broadcasting = True
        msg = message.reply_to_message
        flags = _parse_flags(message)

        count, ucount = 0, 0
        groups, users = [], []

        sent = await message.reply_text(message.lang["gcast_start"])

        # hedef listeleri
        if "-nochat" not in flags:
            groups = await db.get_chats()
        if "-user" in flags:
            users = await db.get_users()

        chats = list(dict.fromkeys(groups + users))  # duplicate temizle, sıra koru

        # logger'a logla (forward + bilgi mesajı)
        try:
            await msg.forward(app.logger)
        except Exception:
            pass

        try:
            log_msg = await app.send_message(
                chat_id=app.logger,
                text=message.lang["gcast_log"].format(
                    message.from_user.id,
                    message.from_user.mention,
                    message.text,
                ),
            )
            try:
                await log_msg.pin(disable_notification=False)
            except errors.ChatAdminRequired:
                pass
            except errors.RPCError:
                pass
        except Exception:
            pass

        await asyncio.sleep(1)

        failed_lines = []

        for chat_id in chats:
            if not broadcasting:
                await sent.edit_text(message.lang["gcast_stopped"].format(count, ucount))
                break

            try:
                if "-copy" in flags:
                    await msg.copy(chat_id, reply_markup=msg.reply_markup)
                else:
                    await msg.forward(chat_id)

                if chat_id in groups:
                    count += 1
                else:
                    ucount += 1

                await asyncio.sleep(0.2)

            except errors.FloodWait as fw:
                # fw.value saniyedir; ekstra tampon iyi olur
                await asyncio.sleep(fw.value + 5)

            except (errors.ChatWriteForbidden, errors.UserIsBlocked, errors.InputUserDeactivated):
                # yazamaz / engelli / kullanıcı kapalı -> normal
                failed_lines.append(f"{chat_id} - write_forbidden_or_blocked")
                continue

            except (errors.PeerIdInvalid, errors.ChannelInvalid):
                failed_lines.append(f"{chat_id} - invalid_peer")
                continue

            except Exception as ex:
                failed_lines.append(f"{chat_id} - {type(ex).__name__}: {ex}")
                continue

        text = message.lang["gcast_end"].format(count, ucount)

        # hata dosyası (unique)
        if failed_lines:
            fname = f"gcast_errors_{uuid.uuid4().hex}.txt"
            with open(fname, "w", encoding="utf-8") as f:
                f.write("\n".join(failed_lines))

            try:
                await message.reply_document(document=fname, caption=text)
            finally:
                try:
                    os.remove(fname)
                except OSError:
                    pass

        broadcasting = False
        await sent.edit_text(text)


@app.on_message(filters.command(["stop_gcast", "stop_broadcast"]) & app.sudoers)
@lang.language()
async def _stop_gcast(_, message: types.Message):
    global broadcasting

    if not broadcasting:
        return await message.reply_text(message.lang["gcast_inactive"])

    broadcasting = False

    # logger'a stop log
    try:
        stop_msg = await app.send_message(
            chat_id=app.logger,
            text=message.lang["gcast_stop_log"].format(
                message.from_user.id,
                message.from_user.mention,
            ),
        )
        try:
            await stop_msg.pin(disable_notification=False)
        except errors.ChatAdminRequired:
            pass
        except errors.RPCError:
            pass
    except Exception:
        pass

    await message.reply_text(message.lang["gcast_stop"])
