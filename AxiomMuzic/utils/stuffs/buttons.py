
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message
from pyrogram import Client, filters, enums 
from pyrogram.enums import ButtonStyle

class BUTTONS(object):
    MBUTTON = [
        [
            InlineKeyboardButton("𝐂ʜᴀᴛ-𝐆ᴘᴛ", callback_data="mplus HELP_ChatGPT", style=ButtonStyle.SUCCESS),
            InlineKeyboardButton("ɢʀᴏᴜᴘs", callback_data="mplus HELP_Group", style=ButtonStyle.SUCCESS),
            InlineKeyboardButton("sᴛɪᴄᴋᴇʀs", callback_data="mplus HELP_Sticker", style=ButtonStyle.SUCCESS)
        ],
        [
            InlineKeyboardButton("𝐓ᴀɢ-𝐀ʟʟ", callback_data="mplus HELP_TagAll", style=ButtonStyle.SUCCESS),
            InlineKeyboardButton("𝐈ɴꜰᴏ", callback_data="mplus HELP_Info", style=ButtonStyle.SUCCESS),
            InlineKeyboardButton("ᴇxᴛʀᴀ", callback_data="mplus HELP_Extra", style=ButtonStyle.SUCCESS)
        ],
        [
            InlineKeyboardButton("𝐈ᴍᴀɢᴇ", callback_data="mplus HELP_Image", style=ButtonStyle.SUCCESS),
            InlineKeyboardButton("𝐀ᴄᴛɪᴏɴ", callback_data="mplus HELP_Action", style=ButtonStyle.SUCCESS),
            InlineKeyboardButton("sᴇᴀʀᴄʜ", callback_data="mplus HELP_Search", style=ButtonStyle.SUCCESS)
        ],    
        [
            InlineKeyboardButton("𝐅ᴏɴᴛ", callback_data="mplus HELP_Font", style=ButtonStyle.SUCCESS),
            InlineKeyboardButton("𝐆ᴀᴍᴇs", callback_data="mplus HELP_Game", style=ButtonStyle.SUCCESS),
            InlineKeyboardButton("ᴛ-ɢʀᴀᴘʜ", callback_data="mplus HELP_TG", style=ButtonStyle.SUCCESS)
        ],
        [
            InlineKeyboardButton("𝐈ᴍᴘᴏsᴛᴇʀ", callback_data="mplus HELP_Imposter", style=ButtonStyle.SUCCESS),
            InlineKeyboardButton("𝐓ʀᴜᴛʜ-ᴅᴀʀᴇ", callback_data="mplus HELP_TD", style=ButtonStyle.SUCCESS),
            InlineKeyboardButton("ʜᴀsᴛᴀɢ", callback_data="mplus HELP_HT", style=ButtonStyle.SUCCESS)
        ], 
        [
            InlineKeyboardButton("𝐓ᴛs", callback_data="mplus HELP_TTS", style=ButtonStyle.SUCCESS),
            InlineKeyboardButton("𝐅ᴜɴ", callback_data="mplus HELP_Fun", style=ButtonStyle.SUCCESS),
            InlineKeyboardButton("ǫᴜᴏᴛʟʏ", callback_data="mplus HELP_Q", style=ButtonStyle.SUCCESS)
        ],          
        [
            InlineKeyboardButton("◁", callback_data=f"AxiomOwner", style=ButtonStyle.DANGER), 
            InlineKeyboardButton("▷", callback_data=f"managebot123 AxiomOwner", style=ButtonStyle.DANGER),
        ]
    ]
