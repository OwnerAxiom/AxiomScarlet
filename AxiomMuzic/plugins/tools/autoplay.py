import re
from pyrogram import filters
from pyrogram.enums import ChatMemberStatus, ButtonStyle
from pyrogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message

from AxiomMusic import app
from AxiomMusic.misc import SUDOERS, db
from AxiomMusic.utils.database import (
    autoplay_off, autoplay_on, is_autoplay,
    get_autoplay_lang, set_autoplay_lang,
    get_autoplay_mood, set_autoplay_mood
)
from AxiomMusic.utils.stream.autoplay import queue_autoplay_tracks, convert_to_special_font
from AxiomMusic.utils.decorators.admins import ActualAdminCB, AdminActual
from config import BANNED_USERS

AUTOPLAY_RE = re.compile(
    r"^[!/.](?P<command>autoplay|aplay|auto)(?:@\w+)?"
    r"(?:\s+(?P<state>on|off|enable|disable|enabled|disabled))?\s*$",
    re.IGNORECASE,
)
ON_STATES = {"on", "enable", "enabled"}
OFF_STATES = {"off", "disable", "disabled"}

LANGUAGES = {
    "auto": "Auto Detect", "hindi": "Hindi", "english": "English", "punjabi": "Punjabi",
    "tamil": "Tamil", "telugu": "Telugu", "kannada": "Kannada", "malayalam": "Malayalam",
    "bengali": "Bengali", "marathi": "Marathi", "gujarati": "Gujarati", "bhojpuri": "Bhojpuri",
    "haryanvi": "Haryanvi", "urdu": "Urdu", "arabic": "Arabic", "turkish": "Turkish",
    "korean": "Korean", "japanese": "Japanese", "spanish": "Spanish", "brazilian": "Brazilian",
    "russian": "Russian", "chinese": "Chinese", "french": "French"
}

MOODS = {
    "any": "Any Mood", "romantic": "Romantic", "sad": "Sad", "happy": "Happy",
    "party": "Party", "chill": "Chill", "workout": "Workout", "bhajan": "Bhajan/Devotional",
    "retro": "Retro/Classic", "rap": "Rap/Hip-Hop", "acoustic": "Acoustic/Unplugged",
    "funk": "Funk/Baile", "phonk": "Phonk/Drift"
}

def parse_autoplay_state(message: Message):
    text = (message.text or message.caption or "").strip()
    match = AUTOPLAY_RE.match(text)
    if not match: return None
    state = match.group("state")
    return state.lower() if state else None

async def can_toggle_autoplay(chat_id: int, user_id: int) -> bool:
    if user_id in SUDOERS: return True
    try:
        member = await app.get_chat_member(chat_id, user_id)
    except Exception: return True
    if member.status == ChatMemberStatus.OWNER: return True
    privileges = getattr(member, "privileges", None)
    return bool(member.status == ChatMemberStatus.ADMINISTRATOR and privileges and (getattr(privileges, "can_manage_video_chats", False) or getattr(privileges, "can_manage_chat", False)))

def autoplay_markup(status: bool):
    if status:
        button_text = convert_to_special_font("♬ Autoplay | On")
        toggle_state = "off"
    else:
        button_text = convert_to_special_font("♬ Autoplay | Off")
        toggle_state = "on"
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(button_text, callback_data=f"autoplay_toggle|{toggle_state}", style=ButtonStyle.SUCCESS if status else ButtonStyle.DANGER)],
        [
            InlineKeyboardButton(convert_to_special_font("Lang."), callback_data="autoplay_lang", style=ButtonStyle.PRIMARY),
            InlineKeyboardButton(convert_to_special_font("Mood"), callback_data="autoplay_mood", style=ButtonStyle.PRIMARY)
        ],
    ])

def language_markup(current_lang: str):
    buttons = []
    row = []
    for lang_code, lang_name in LANGUAGES.items():
        display_name = f"✅ {lang_name}" if lang_code == current_lang else lang_name
        row.append(InlineKeyboardButton(convert_to_special_font(display_name), callback_data=f"autoplay_setlang|{lang_code}", style=(ButtonStyle.SUCCESS if lang_code == current_lang else ButtonStyle.DANGER)))
        if len(row) == 4:
            buttons.append(row)
            row = []
    if row: buttons.append(row)
    buttons.append([InlineKeyboardButton(convert_to_special_font("« Back"), callback_data="autoplay_back", style=ButtonStyle.PRIMARY)])
    return InlineKeyboardMarkup(buttons)

def mood_markup(current_mood: str):
    buttons = []
    row = []
    for mood_code, mood_name in MOODS.items():
        display_name = f"✅ {mood_name}" if mood_code == current_mood else mood_name
        row.append(InlineKeyboardButton(convert_to_special_font(display_name), callback_data=f"autoplay_setmood|{mood_code}", style=(ButtonStyle.SUCCESS if mood_code == current_mood else ButtonStyle.DANGER)))
        if len(row) == 3:
            buttons.append(row)
            row = []
    if row: buttons.append(row)
    buttons.append([InlineKeyboardButton(convert_to_special_font("« Back"), callback_data="autoplay_back", style=ButtonStyle.PRIMARY)])
    return InlineKeyboardMarkup(buttons)

def autoplay_text(status: bool, lang: str, mood: str):
    current = convert_to_special_font("Enabled ✅") if status else convert_to_special_font("Disabled ❌")
    lang_name = LANGUAGES.get(lang, "Auto Detect")
    mood_name = MOODS.get(mood, "Any Mood")
    return (
        f"<b>{convert_to_special_font('Autoplay Settings')}</b>\n\n"
        f"<b>{convert_to_special_font('Status:')}</b> {current}\n"
        f"<b>{convert_to_special_font('Language:')}</b> {convert_to_special_font(lang_name)}\n"
        f"<b>{convert_to_special_font('Mood:')}</b> {convert_to_special_font(mood_name)}\n\n"
        f"<b>{convert_to_special_font('Commands:')}</b> <code>/autoplay on</code> | <code>/autoplay off</code>"
    )

@app.on_message(filters.command(["autop", "autoplay", "aplay", "ap"], prefixes=["", "/", "!", "."]) & filters.group & ~BANNED_USERS)
@AdminActual
async def autoplay_command(_, message: Message, __):
    if not message.from_user: return await message.reply_text(convert_to_special_font("Please use this command from a user account."))
    chat_id = message.chat.id
    requested_state = parse_autoplay_state(message)
    if requested_state in ON_STATES | OFF_STATES:
        if not await can_toggle_autoplay(chat_id, message.from_user.id):
            return await message.reply_text(convert_to_special_font("Only admins can change autoplay mode."))
        status = requested_state in ON_STATES
        if status:
            await autoplay_on(chat_id)
            current_queue = db.get(chat_id)
            if current_queue: await queue_autoplay_tracks(chat_id, current_queue[0])
        else: await autoplay_off(chat_id)
    else: status = await is_autoplay(chat_id)
    lang = await get_autoplay_lang(chat_id)
    mood = await get_autoplay_mood(chat_id)
    await message.reply_text(autoplay_text(status, lang, mood), reply_markup=autoplay_markup(status), disable_web_page_preview=True)

@app.on_callback_query(filters.regex(r"^autoplay_toggle\|(on|off)$") & ~BANNED_USERS)
@ActualAdminCB
async def autoplay_callback(_, callback_query: CallbackQuery, __):
    state = callback_query.data.split("|", 1)[1]
    chat_id = callback_query.message.chat.id
    if state == "on":
        await autoplay_on(chat_id)
        status = True
        alert = convert_to_special_font("♬ Autoplay | On")
    else:
        await autoplay_off(chat_id)
        status = False
        alert = convert_to_special_font("♬ Autoplay | Off")
    await callback_query.answer(alert, show_alert=True)
    lang = await get_autoplay_lang(chat_id)
    mood = await get_autoplay_mood(chat_id)
    await callback_query.edit_message_text(autoplay_text(status, lang, mood), reply_markup=autoplay_markup(status), disable_web_page_preview=True)

@app.on_callback_query(filters.regex(r"^autoplay_lang$") & ~BANNED_USERS)
@ActualAdminCB
async def autoplay_lang_menu(_, callback_query: CallbackQuery, __):
    chat_id = callback_query.message.chat.id
    current_lang = await get_autoplay_lang(chat_id)
    await callback_query.edit_message_text(
        f"<b>{convert_to_special_font('Select Autoplay Language')}</b>\n\n{convert_to_special_font('Choose the language for autoplay songs:')}", 
        reply_markup=language_markup(current_lang), 
        disable_web_page_preview=True
    )

@app.on_callback_query(filters.regex(r"^autoplay_setlang\|(.+)$") & ~BANNED_USERS)
@ActualAdminCB
async def autoplay_set_language(_, callback_query: CallbackQuery, __):
    lang = callback_query.data.split("|", 1)[1]
    chat_id = callback_query.message.chat.id
    await set_autoplay_lang(chat_id, lang)
    await callback_query.answer(f"{convert_to_special_font('Language set to')} {LANGUAGES[lang]}", show_alert=False)
    
    # ✅ FIXED: Wapas main autoplay settings page pe jao
    status = await is_autoplay(chat_id)
    mood = await get_autoplay_mood(chat_id)
    await callback_query.edit_message_text(
        autoplay_text(status, lang, mood),
        reply_markup=autoplay_markup(status),
        disable_web_page_preview=True
    )

@app.on_callback_query(filters.regex(r"^autoplay_mood$") & ~BANNED_USERS)
@ActualAdminCB
async def autoplay_mood_menu(_, callback_query: CallbackQuery, __):
    chat_id = callback_query.message.chat.id
    current_mood = await get_autoplay_mood(chat_id)
    await callback_query.edit_message_text(
        f"<b>{convert_to_special_font('Select Autoplay Mood')}</b>\n\n{convert_to_special_font('Choose the mood for autoplay songs:')}", 
        reply_markup=mood_markup(current_mood), 
        disable_web_page_preview=True
    )

@app.on_callback_query(filters.regex(r"^autoplay_setmood\|(.+)$") & ~BANNED_USERS)
@ActualAdminCB
async def autoplay_set_mood(_, callback_query: CallbackQuery, __):
    mood = callback_query.data.split("|", 1)[1]
    chat_id = callback_query.message.chat.id
    await set_autoplay_mood(chat_id, mood)
    await callback_query.answer(f"{convert_to_special_font('Mood set to')} {MOODS[mood]}", show_alert=False)
    
    # ✅ FIXED: Wapas main autoplay settings page pe jao
    status = await is_autoplay(chat_id)
    lang = await get_autoplay_lang(chat_id)
    await callback_query.edit_message_text(
        autoplay_text(status, lang, mood),
        reply_markup=autoplay_markup(status),
        disable_web_page_preview=True
    )

@app.on_callback_query(filters.regex(r"^autoplay_back$") & ~BANNED_USERS)
@ActualAdminCB
async def autoplay_back(_, callback_query: CallbackQuery, __):
    chat_id = callback_query.message.chat.id
    status = await is_autoplay(chat_id)
    lang = await get_autoplay_lang(chat_id)
    mood = await get_autoplay_mood(chat_id)
    await callback_query.edit_message_text(autoplay_text(status, lang, mood), reply_markup=autoplay_markup(status), disable_web_page_preview=True)

@app.on_callback_query(filters.regex(r"^autoplay_inline_config\|(.+)$") & ~BANNED_USERS)
@ActualAdminCB
async def autoplay_inline_config(_, callback_query: CallbackQuery, __):
    chat_id = int(callback_query.data.split("|", 1)[1])
    status = await is_autoplay(chat_id)
    lang = await get_autoplay_lang(chat_id)
    mood = await get_autoplay_mood(chat_id)
    
    await callback_query.answer()
    await callback_query.edit_message_text(
        autoplay_text(status, lang, mood),
        reply_markup=autoplay_markup(status),
        disable_web_page_preview=True,
    )

@app.on_callback_query(filters.regex(r"^autoplay_from_player\|(.+)$") & ~BANNED_USERS)
@ActualAdminCB
async def autoplay_from_player_callback(_, callback_query: CallbackQuery, __):
    chat_id = int(callback_query.data.split("|", 1)[1])
    status = await is_autoplay(chat_id)
    lang = await get_autoplay_lang(chat_id)
    mood = await get_autoplay_mood(chat_id)
    
    markup = InlineKeyboardMarkup([
        [InlineKeyboardButton(convert_to_special_font("♬ Autoplay | Oɴ" if status else "♬ Autoplay | Oғғ"), 
         callback_data=f"autoplay_toggle|{'off' if status else 'on'}", 
         style=ButtonStyle.SUCCESS if status else ButtonStyle.DANGER)],
        [
            InlineKeyboardButton(convert_to_special_font("Lang."), callback_data="autoplay_lang", style=ButtonStyle.PRIMARY),
            InlineKeyboardButton(convert_to_special_font("Mood"), callback_data="autoplay_mood", style=ButtonStyle.PRIMARY)
        ],
        [InlineKeyboardButton(convert_to_special_font("« Back to Player"), callback_data="back_to_player", style=ButtonStyle.DANGER)],
    ])
    
    await callback_query.edit_message_text(
        autoplay_text(status, lang, mood),
        reply_markup=markup,
        disable_web_page_preview=True,
    )

@app.on_callback_query(filters.regex(r"^back_to_player$") & ~BANNED_USERS)
@ActualAdminCB
async def back_to_player(_, callback_query: CallbackQuery, __):
    from AxiomMusic.utils.inline.play import stream_markup
    
    chat_id = callback_query.message.chat.id
    
    # ✅ Player buttons wapas dikhao with updated status
    try:
        await callback_query.edit_message_text(
            text="🎵 **ʟᴀᴇʀ ᴏɴᴛʀᴏʟs**",
            reply_markup=InlineKeyboardMarkup(stream_markup(_, chat_id)),
            disable_web_page_preview=True,
        )
    except:
        await callback_query.answer("Back to player", show_alert=False)
    
