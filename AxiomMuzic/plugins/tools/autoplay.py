# -----------------------------------------------
# 🔸 AxiomMuzic Project
# 🔹 Developed & Maintained by: Axiom Bots (https://t.me/axiombots)
# 📅 Copyright © 2026 – All Rights Reserved
# -----------------------------------------------

import re
from pyrogram import filters
from pyrogram.enums import ChatMemberStatus
from pyrogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message

from AxiomMuzic import app
from AxiomMuzic.misc import SUDOERS, db
from AxiomMuzic.utils.database import autoplay_off, autoplay_on, is_autoplay
from AxiomMuzic.utils.stream.autoplay import queue_autoplay_tracks
from AxiomMuzic.utils.decorators.admins import ActualAdminCB, AdminActual
from config import BANNED_USERS

AUTOPLAY_RE = re.compile(
    r"^[!/.](?P<command>autoplay|aplay|auto)(?:@\w+)?"
    r"(?:\s+(?P<state>on|off|enable|disable|enabled|disabled))?\s*$",
    re.IGNORECASE,
)
ON_STATES = {"on", "enable", "enabled"}
OFF_STATES = {"off", "disable", "disabled"}


def autoplay_filter(_, __, message: Message):
    text = message.text or message.caption or ""
    return bool(AUTOPLAY_RE.match(text.strip()))


def parse_autoplay_state(message: Message):
    text = (message.text or message.caption or "").strip()
    match = AUTOPLAY_RE.match(text)
    if not match:
        return None
    state = match.group("state")
    return state.lower() if state else None


async def can_toggle_autoplay(chat_id: int, user_id: int) -> bool:
    if user_id in SUDOERS:
        return True
    try:
        member = await app.get_chat_member(chat_id, user_id)
    except Exception:
        return True
    if member.status == ChatMemberStatus.OWNER:
        return True
    privileges = getattr(member, "privileges", None)
    return bool(
        member.status == ChatMemberStatus.ADMINISTRATOR
        and privileges
        and (
            getattr(privileges, "can_manage_video_chats", False)
            or getattr(privileges, "can_manage_chat", False)
        )
    )


def autoplay_markup(status: bool):
    toggle_text = "ᴛᴜʀɴ ᴏғғ ❌" if status else "ᴛᴜʀɴ ᴏɴ ✅"
    toggle_state = "off" if status else "on"
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    toggle_text,
                    callback_data=f"autoplay_toggle|{toggle_state}",
                )
            ],
            [InlineKeyboardButton("⋞ ᴄʟᴏsє ⋟", callback_data="close")],
        ]
    )


def autoplay_text(status: bool):
    current = "ᴇɴᴀʙʟᴇᴅ ✅" if status else "ᴅɪsᴀʙʟᴇᴅ ❌"
    return (
        "<b>♬ ᴀᴜᴛᴏᴘʟᴀʏ sᴇᴛᴛɪɴɢs</b>\n\n"
        f"<b>ᴄᴜʀʀᴇɴᴛ sᴛᴀᴛᴜs:</b> {current}\n\n"
        "<b>Commands:</b> <code>/autoplay</code> | <code>/autoplay on</code> | "
        "<code>/autoplay off</code>"
    )


@app.on_message(filters.command(["autoplay", "aplay", "ap"], prefixes=["/", "!", ".", ""]) & filters.group & ~BANNED_USERS)
@AdminActual
async def autoplay_command(_, message: Message, __):
    if not message.from_user:
        return await message.reply_text("<b>Please use this command from a user account.</b>")

    chat_id = message.chat.id
    requested_state = parse_autoplay_state(message)

    if requested_state in ON_STATES | OFF_STATES:
        if not await can_toggle_autoplay(chat_id, message.from_user.id):
            return await message.reply_text("<b>Only admins can change autoplay mode.</b>")
        status = requested_state in ON_STATES
        if status:
            await autoplay_on(chat_id)
            current_queue = db.get(chat_id)
            if current_queue:
                await queue_autoplay_tracks(chat_id, current_queue[0])
        else:
            await autoplay_off(chat_id)
    else:
        status = await is_autoplay(chat_id)

    await message.reply_text(
        autoplay_text(status),
        reply_markup=autoplay_markup(status),
        disable_web_page_preview=True,
    )


@app.on_callback_query(filters.regex(r"^autoplay_toggle\|(on|off)$") & ~BANNED_USERS)
@ActualAdminCB
async def autoplay_callback(_, callback_query: CallbackQuery, __):
    state = callback_query.data.split("|", 1)[1]
    chat_id = callback_query.message.chat.id

    if state == "on":
        await autoplay_on(chat_id)
        status = True
        alert = "Autoplay enabled ✅"
    else:
        await autoplay_off(chat_id)
        status = False
        alert = "Autoplay disabled ❌"

    await callback_query.answer(alert, show_alert=True)

    await callback_query.edit_message_text(
        autoplay_text(status),
        reply_markup=autoplay_markup(status),
        disable_web_page_preview=True,
    )
