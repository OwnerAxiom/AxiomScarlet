from pyrogram import filters
from pyrogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup

from AxiomMuzic import app
from AxiomMuzic.utils.stream.thumbnail import (
    toggle_thumbnail_status,
    get_thumbnail_status,
)

from AxiomMuzic.utils.inline.play import (
    stream_markup,
)


@app.on_callback_query(filters.regex("^THUMBTOGGLE"))
async def thumbnail_toggle_callback(_, query: CallbackQuery):

    data = query.data.split("|")

    chat_id = int(data[1])

    new_status = toggle_thumbnail_status(chat_id)

    status_text = (
        "ᴛʜᴜᴍʙɴᴀɪʟ ᴇɴᴀʙʟᴇᴅ"
        if new_status == "on"
        else "ᴛʜᴜᴍʙɴᴀɪʟ ᴅɪsᴀʙʟᴇᴅ"
    )

    try:
        await query.answer(status_text, show_alert=False)

        markup = InlineKeyboardMarkup(
            stream_markup(
                query._,
                "none",
                chat_id,
            )
        )

        await query.message.edit_reply_markup(reply_markup=markup)

    except Exception:
        pass
