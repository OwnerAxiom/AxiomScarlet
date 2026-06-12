# -----------------------------------------------
# 🔸 AxiomMusic Project
# 🔹 Developed & Maintained by: Axiom Bots (https://t.me/axiombots)
# 📅 Copyright © 2026 – All Rights Reserved
#
# 📖 License:
# This source code is open for educational and non-commercial use ONLY.
# You are required to retain this credit in all copies or substantial portions of this file.
# Commercial use, redistribution, or removal of this notice is strictly prohibited
# without prior written permission from the author.
#
# ❤️ Made with dedication and love by AxiomBots
# -----------------------------------------------
import re
import random
from pyrogram import filters
import asyncio
from time import time, strftime, gmtime
from pyrogram.enums import ChatType
from pyrogram.errors import MessageNotModified
from pyrogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)

from AxiomMuzic import app
from AxiomMuzic.utils.database import (
    add_nonadmin_chat,
    autoplay_off,
    autoplay_on,
    get_authuser,
    get_authuser_names,
    get_playmode,
    get_playtype,
    get_upvote_count,
    is_autoplay,
    is_nonadmin_chat,
    is_skipmode,
    remove_nonadmin_chat,
    set_playmode,
    set_playtype,
    set_upvotes,
    skip_off,
    skip_on,
)
from AxiomMuzic.utils.decorators.admins import ActualAdminCB
from AxiomMuzic.utils.decorators.language import language, languageCB
from AxiomMuzic.utils.inline.settings import (
    auth_users_markup,
    playmode_users_markup,
    setting_markup,
    vote_mode_markup,
)
from AxiomMuzic.utils.inline.start import private_panel
from config import BANNED_USERS, OWNER_ID
import config

TOGGLE_COMMAND_RE = re.compile(
    r"^[!/.](?P<command>autoplay|aplay|thumbnail|thumb|thum)(?:@\w+)?"
    r"(?:\s+(?P<state>on|off|enable|disable|enabled|disabled))?\s*$",
    re.IGNORECASE,
)

def feature_markup(feature: str, status: bool):
    callback_prefix = "autoplay_toggle" if feature == "autoplay" else "thumbnail_toggle"
    toggle_text = "ᴛᴜʀɴ ᴏғғ ❌" if status else "ᴛᴜʀɴ ᴏɴ ✅"
    toggle_state = "off" if status else "on"
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    toggle_text,
                    callback_data=f"{callback_prefix}|{toggle_state}",
                )
            ],
            [InlineKeyboardButton("⋞ ᴄʟᴏsє ⋟", callback_data="close")],
        ]
    )


def autoplay_panel_text(status: bool):
    current = "ᴇɴᴀʙʟᴇᴅ ✅" if status else "ᴅɪsᴀʙʟᴇᴅ ❌"
    return (
        "<b>♬ ᴀᴜᴛᴏᴘʟᴀʏ sᴇᴛᴛɪɴɢs</b>\n\n"
        f"<b>ᴄᴜʀʀᴇɴᴛ sᴛᴀᴛᴜs:</b> {current}\n\n"
        "<b>Quick use:</b> <code>/autoplay on</code> | <code>/autoplay off</code>"
    )


def thumbnail_panel_text(status: bool):
    current = "ᴇɴᴀʙʟᴇᴅ ✅" if status else "ᴅɪsᴀʙʟᴇᴅ ❌"
    return (
        "<b>𝚻ʜ꧊‌𝛖ϻβηᴧιℓ 𝚺ᴇᴛᴛɪɴɢs</b>\n\n"
        f"<b>ᴄᴜʀʀᴇɴᴛ sᴛᴀᴛᴜs:</b> {current}\n\n"
        "<b>Quick use:</b> <code>/thumb on</code> | <code>/thumb off</code>"
    )


@app.on_message(filters.create(toggle_command_filter) & filters.group & ~BANNED_USERS, group=-1)
async def autoplay_thumbnail_toggle_command(_, message: Message):
    if not message.from_user:
        return await message.reply_text("<b>Please use this command from a user account.</b>")

    command, state = toggle_state_from_message(message)
    if not command:
        return

    is_auto_command = command in ["autoplay", "aplay"]
    feature = "autoplay" if is_auto_command else "thumbnail"
    chat_id = message.chat.id

    if state in ["on", "enable", "enabled", "off", "disable", "disabled"]:
        if not await can_toggle_feature(chat_id, message.from_user.id):
            return await message.reply_text(f"<b>Only admins can change {feature} mode.</b>")
        enable = state in ["on", "enable", "enabled"]
        if is_auto_command:
            await autoplay_on(chat_id) if enable else await autoplay_off(chat_id)
        else:
            await thumb_on(chat_id) if enable else await thumb_off(chat_id)
        status = enable
    else:
        status = await is_autoplay(chat_id) if is_auto_command else await is_thumbmode(chat_id)

    await message.reply_text(
        autoplay_panel_text(status) if is_auto_command else thumbnail_panel_text(status),
        reply_markup=feature_markup(feature, status),
        disable_web_page_preview=True,
    )


@app.on_callback_query(filters.regex(r"^(autoplay_toggle|thumbnail_toggle)\|(on|off)$") & ~BANNED_USERS, group=-1)
async def autoplay_thumbnail_toggle_callback(_, callback_query: CallbackQuery):
    feature, state = callback_query.data.split("|", 1)
    is_auto_callback = feature == "autoplay_toggle"
    chat_id = callback_query.message.chat.id

    if not await can_toggle_feature(chat_id, callback_query.from_user.id):
        label = "autoplay" if is_auto_callback else "thumbnail"
        return await callback_query.answer(
            f"Only admins can change {label} mode.", show_alert=True
        )

    enable = state == "on"
    if is_auto_callback:
        await autoplay_on(chat_id) if enable else await autoplay_off(chat_id)
        label = "Autoplay"
        text = autoplay_panel_text(enable)
        markup = feature_markup("autoplay", enable)
    else:
        await thumb_on(chat_id) if enable else await thumb_off(chat_id)
        label = "Thumbnail"
        text = thumbnail_panel_text(enable)
        markup = feature_markup("thumbnail", enable)

    await callback_query.answer(
        f"{label} {'enabled ✅' if enable else 'disabled ❌'}",
        show_alert=True,
    )
    await callback_query.edit_message_text(
        text,
        reply_markup=markup,
        disable_web_page_preview=True,
    )


@app.on_message(
    filters.command(["settings", "setting", "config"]) & filters.group & ~BANNED_USERS
)
@language
async def settings_mar(client, message: Message, _):
    buttons = setting_markup(_)
    await message.reply_text(
        _["setting_1"].format(app.mention, message.chat.id, message.chat.title),
        reply_markup=InlineKeyboardMarkup(buttons),
    )


@app.on_callback_query(filters.regex("settings_helper") & ~BANNED_USERS)
@languageCB
async def settings_cb(client, CallbackQuery, _):
    try:
        await CallbackQuery.answer(_["set_cb_5"])
    except:
        pass
    buttons = setting_markup(_)
    return await CallbackQuery.edit_message_text(
        _["setting_1"].format(
            app.mention,
            CallbackQuery.message.chat.id,
            CallbackQuery.message.chat.title,
        ),
        reply_markup=InlineKeyboardMarkup(buttons),
    )
    
@app.on_callback_query(filters.regex("settingsback_helper") & ~BANNED_USERS)
@languageCB
async def settings_back_markup(client, CallbackQuery: CallbackQuery, _):
    try:
        await CallbackQuery.answer()
    except:
        pass
    if CallbackQuery.message.chat.type == ChatType.PRIVATE:
        await app.resolve_peer(OWNER_ID)
        OWNER = OWNER_ID
        buttons = private_panel(_)
        return await CallbackQuery.edit_message_text(
            _["start_2"].format(CallbackQuery.from_user.mention, app.mention),
            reply_markup=InlineKeyboardMarkup(buttons),
        )
    else:
        buttons = setting_markup(_)
        return await CallbackQuery.edit_message_reply_markup(
            reply_markup=InlineKeyboardMarkup(buttons)
        )

@app.on_callback_query(filters.regex("OwnerAxiom") & ~BANNED_USERS)
@languageCB
async def support(client, CallbackQuery, _):
    await CallbackQuery.edit_message_text(
        _["ABOUT_1"].format(app.mention),
        reply_markup=InlineKeyboardMarkup(
            [
                [          
                    InlineKeyboardButton(
                        text="ʙᴏᴛ-ᴀᴘɪ-ɪɴғᴏ 💌", callback_data="api_status"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="sᴜᴘᴘᴏʀᴛ", url=config.SUPPORT_CHAT
                    ),
                    InlineKeyboardButton(
                        text="ᴜᴘᴅᴀᴛᴇs", url=config.SUPPORT_CHANNEL
                    ),

                ],
                [          
                    InlineKeyboardButton(
                        text="ʙᴀᴄᴋ", callback_data=f"settingsback_helper"
                    )
                ],
            ]
        ),
    )


@app.on_callback_query(filters.regex("^api_status$"))
async def show_bot_info(c: app, q: CallbackQuery):
    start = time()
    await asyncio.sleep(0.1)
    delta_ping = time() - start
    txt = f"""💌 ʏᴏᴜᴛᴜʙᴇ ᴀᴘɪ sᴛᴀᴛᴜs...

• ᴅᴀᴛᴀʙᴀsᴇ: ᴏɴʟɪɴᴇ
• ʏᴏᴜᴛᴜʙᴇ ᴀᴘɪ: ʀᴇsᴘᴏɴsɪᴠᴇ
• ʙᴏᴛ sᴇʀᴠᴇʀ: ʀᴜɴɴɪɴɢ sᴍᴏᴏᴛʜʟʏ
• ʀᴇsᴘᴏɴsᴇ ᴛɪᴍᴇ: ᴏᴘᴛɪᴍᴀʟ
• ᴀᴘɪ ᴘɪɴɢ: {delta_ping * 1000:.3f} ms   

ᴇᴠᴇʀʏᴛʜɪɴɢ ʟᴏᴏᴋs ɢᴏᴏᴅ!
"""
    await q.answer(txt, show_alert=True)

@app.on_callback_query(
    filters.regex(
        pattern=r"^(SEARCHANSWER|PLAYMODEANSWER|PLAYTYPEANSWER|AUTHANSWER|ANSWERVOMODE|VOTEANSWER|PM|AU|VM)$"
    )
    & ~BANNED_USERS
)
@languageCB
async def without_Admin_rights(client, CallbackQuery, _):
    command = CallbackQuery.matches[0].group(1)
    if command == "SEARCHANSWER":
        try:
            return await CallbackQuery.answer(_["setting_2"], show_alert=True)
        except:
            return
    if command == "PLAYMODEANSWER":
        try:
            return await CallbackQuery.answer(_["setting_5"], show_alert=True)
        except:
            return
    if command == "PLAYTYPEANSWER":
        try:
            return await CallbackQuery.answer(_["setting_6"], show_alert=True)
        except:
            return
    if command == "AUTHANSWER":
        try:
            return await CallbackQuery.answer(_["setting_3"], show_alert=True)
        except:
            return
    if command == "VOTEANSWER":
        try:
            return await CallbackQuery.answer(
                _["setting_8"],
                show_alert=True,
            )
        except:
            return
    if command == "ANSWERVOMODE":
        current = await get_upvote_count(CallbackQuery.message.chat.id)
        try:
            return await CallbackQuery.answer(
                _["setting_9"].format(current),
                show_alert=True,
            )
        except:
            return
    if command == "PM":
        try:
            await CallbackQuery.answer(_["set_cb_2"], show_alert=True)
        except:
            pass
        playmode = await get_playmode(CallbackQuery.message.chat.id)
        if playmode == "Direct":
            Direct = True
        else:
            Direct = None
        is_non_admin = await is_nonadmin_chat(CallbackQuery.message.chat.id)
        if not is_non_admin:
            Group = True
        else:
            Group = None
        playty = await get_playtype(CallbackQuery.message.chat.id)
        if playty == "Everyone":
            Playtype = None
        else:
            Playtype = True
        buttons = playmode_users_markup(_, Direct, Group, Playtype)
    if command == "AU":
        try:
            await CallbackQuery.answer(_["set_cb_1"], show_alert=True)
        except:
            pass
        is_non_admin = await is_nonadmin_chat(CallbackQuery.message.chat.id)
        if not is_non_admin:
            buttons = auth_users_markup(_, True)
        else:
            buttons = auth_users_markup(_)
    if command == "VM":
        mode = await is_skipmode(CallbackQuery.message.chat.id)
        current = await get_upvote_count(CallbackQuery.message.chat.id)
        buttons = vote_mode_markup(_, current, mode)
    try:
        return await CallbackQuery.edit_message_reply_markup(
            reply_markup=InlineKeyboardMarkup(buttons)
        )
    except MessageNotModified:
        return


@app.on_callback_query(filters.regex("FERRARIUDTI") & ~BANNED_USERS)
@ActualAdminCB
async def addition(client, CallbackQuery, _):
    callback_data = CallbackQuery.data.strip()
    mode = callback_data.split(None, 1)[1]
    if not await is_skipmode(CallbackQuery.message.chat.id):
        return await CallbackQuery.answer(_["setting_10"], show_alert=True)
    current = await get_upvote_count(CallbackQuery.message.chat.id)
    if mode == "M":
        final = current - 2
        print(final)
        if final == 0:
            return await CallbackQuery.answer(
                _["setting_11"],
                show_alert=True,
            )
        if final <= 2:
            final = 2
        await set_upvotes(CallbackQuery.message.chat.id, final)
    else:
        final = current + 2
        print(final)
        if final == 17:
            return await CallbackQuery.answer(
                _["setting_12"],
                show_alert=True,
            )
        if final >= 15:
            final = 15
        await set_upvotes(CallbackQuery.message.chat.id, final)
    buttons = vote_mode_markup(_, final, True)
    try:
        return await CallbackQuery.edit_message_reply_markup(
            reply_markup=InlineKeyboardMarkup(buttons)
        )
    except MessageNotModified:
        return


@app.on_callback_query(
    filters.regex(pattern=r"^(MODECHANGE|CHANNELMODECHANGE|PLAYTYPECHANGE)$")
    & ~BANNED_USERS
)
@ActualAdminCB
async def playmode_ans(client, CallbackQuery, _):
    command = CallbackQuery.matches[0].group(1)
    if command == "CHANNELMODECHANGE":
        is_non_admin = await is_nonadmin_chat(CallbackQuery.message.chat.id)
        if not is_non_admin:
            await add_nonadmin_chat(CallbackQuery.message.chat.id)
            Group = None
        else:
            await remove_nonadmin_chat(CallbackQuery.message.chat.id)
            Group = True
        playmode = await get_playmode(CallbackQuery.message.chat.id)
        if playmode == "Direct":
            Direct = True
        else:
            Direct = None
        playty = await get_playtype(CallbackQuery.message.chat.id)
        if playty == "Everyone":
            Playtype = None
        else:
            Playtype = True
        buttons = playmode_users_markup(_, Direct, Group, Playtype)
    if command == "MODECHANGE":
        try:
            await CallbackQuery.answer(_["set_cb_3"], show_alert=True)
        except:
            pass
        playmode = await get_playmode(CallbackQuery.message.chat.id)
        if playmode == "Direct":
            await set_playmode(CallbackQuery.message.chat.id, "Inline")
            Direct = None
        else:
            await set_playmode(CallbackQuery.message.chat.id, "Direct")
            Direct = True
        is_non_admin = await is_nonadmin_chat(CallbackQuery.message.chat.id)
        if not is_non_admin:
            Group = True
        else:
            Group = None
        playty = await get_playtype(CallbackQuery.message.chat.id)
        if playty == "Everyone":
            Playtype = False
        else:
            Playtype = True
        buttons = playmode_users_markup(_, Direct, Group, Playtype)
    if command == "PLAYTYPECHANGE":
        try:
            await CallbackQuery.answer(_["set_cb_3"], show_alert=True)
        except:
            pass
        playty = await get_playtype(CallbackQuery.message.chat.id)
        if playty == "Everyone":
            await set_playtype(CallbackQuery.message.chat.id, "Admin")
            Playtype = False
        else:
            await set_playtype(CallbackQuery.message.chat.id, "Everyone")
            Playtype = True
        playmode = await get_playmode(CallbackQuery.message.chat.id)
        if playmode == "Direct":
            Direct = True
        else:
            Direct = None
        is_non_admin = await is_nonadmin_chat(CallbackQuery.message.chat.id)
        if not is_non_admin:
            Group = True
        else:
            Group = None
        buttons = playmode_users_markup(_, Direct, Group, Playtype)
    try:
        return await CallbackQuery.edit_message_reply_markup(
            reply_markup=InlineKeyboardMarkup(buttons)
        )
    except MessageNotModified:
        return


@app.on_callback_query(filters.regex(pattern=r"^(AUTH|AUTHLIST)$") & ~BANNED_USERS)
@ActualAdminCB
async def authusers_mar(client, CallbackQuery, _):
    command = CallbackQuery.matches[0].group(1)
    if command == "AUTHLIST":
        _authusers = await get_authuser_names(CallbackQuery.message.chat.id)
        if not _authusers:
            try:
                return await CallbackQuery.answer(_["setting_4"], show_alert=True)
            except:
                return
        else:
            try:
                await CallbackQuery.answer(_["set_cb_4"], show_alert=True)
            except:
                pass
            j = 0
            await CallbackQuery.edit_message_text(_["auth_6"])
            msg = _["auth_7"].format(CallbackQuery.message.chat.title)
            for note in _authusers:
                _note = await get_authuser(CallbackQuery.message.chat.id, note)
                user_id = _note["auth_user_id"]
                admin_id = _note["admin_id"]
                admin_name = _note["admin_name"]
                try:
                    user = await app.get_users(user_id)
                    user = user.first_name
                    j += 1
                except:
                    continue
                msg += f"{j}➤ {user}[<code>{user_id}</code>]\n"
                msg += f"   {_['auth_8']} {admin_name}[<code>{admin_id}</code>]\n\n"
            upl = InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            text=_["BACK_BUTTON"], callback_data=f"AU"
                        ),
                        InlineKeyboardButton(
                            text=_["CLOSE_BUTTON"],
                            callback_data=f"close",
                        ),
                    ]
                ]
            )
            try:
                return await CallbackQuery.edit_message_text(msg, reply_markup=upl)
            except MessageNotModified:
                return
    try:
        await CallbackQuery.answer(_["set_cb_3"], show_alert=True)
    except:
        pass
    if command == "AUTH":
        is_non_admin = await is_nonadmin_chat(CallbackQuery.message.chat.id)
        if not is_non_admin:
            await add_nonadmin_chat(CallbackQuery.message.chat.id)
            buttons = auth_users_markup(_)
        else:
            await remove_nonadmin_chat(CallbackQuery.message.chat.id)
            buttons = auth_users_markup(_, True)
    try:
        return await CallbackQuery.edit_message_reply_markup(
            reply_markup=InlineKeyboardMarkup(buttons)
        )
    except MessageNotModified:
        return


@app.on_callback_query(filters.regex("VOMODECHANGE") & ~BANNED_USERS)
@ActualAdminCB
async def vote_change(client, CallbackQuery, _):
    command = CallbackQuery.matches[0].group(1)
    try:
        await CallbackQuery.answer(_["set_cb_3"], show_alert=True)
    except:
        pass
    mod = None
    if await is_skipmode(CallbackQuery.message.chat.id):
        await skip_off(CallbackQuery.message.chat.id)
    else:
        mod = True
        await skip_on(CallbackQuery.message.chat.id)
    current = await get_upvote_count(CallbackQuery.message.chat.id)
    buttons = vote_mode_markup(_, current, mod)

    try:
        return await CallbackQuery.edit_message_reply_markup(
            reply_markup=InlineKeyboardMarkup(buttons)
        )
    except MessageNotModified:
        return
