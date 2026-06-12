
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message
from pyrogram import Client, filters, enums 

class BUTTONS(object):
    MBUTTON = [[InlineKeyboardButton("𝐂ʜᴀᴛ-𝐆ᴘᴛ", callback_data="mplus HELP_ChatGPT"),InlineKeyboardButton("ɢʀᴏᴜᴘs", callback_data="mplus HELP_Group"),InlineKeyboardButton("sᴛɪᴄᴋᴇʀs", callback_data="mplus HELP_Sticker")],
    [InlineKeyboardButton("𝐓ᴀɢ-𝐀ʟʟ", callback_data="mplus HELP_TagAll"),
    InlineKeyboardButton("𝐈ɴꜰᴏ", callback_data="mplus HELP_Info"),InlineKeyboardButton("ᴇxᴛʀᴀ", callback_data="mplus HELP_Extra")],
    [InlineKeyboardButton("𝐈ᴍᴀɢᴇ", callback_data="mplus HELP_Image"),
    InlineKeyboardButton("𝐀ᴄᴛɪᴏɴ", callback_data="mplus HELP_Action"),InlineKeyboardButton("sᴇᴀʀᴄʜ", callback_data="mplus HELP_Search")],    
    [InlineKeyboardButton("𝐅ᴏɴᴛ", callback_data="mplus HELP_Font"),
    InlineKeyboardButton("𝐆ᴀᴍᴇs", callback_data="mplus HELP_Game"),InlineKeyboardButton("ᴛ-ɢʀᴀᴘʜ", callback_data="mplus HELP_TG")],
    [InlineKeyboardButton("𝐈ᴍᴘᴏsᴛᴇʀ", callback_data="mplus HELP_Imposter"),
    InlineKeyboardButton("𝐓ʀᴜᴛʜ-ᴅᴀʀᴇ", callback_data="mplus HELP_TD"),InlineKeyboardButton("ʜᴀsᴛᴀɢ", callback_data="mplus HELP_HT")], 
    [InlineKeyboardButton("𝐓ᴛs", callback_data="mplus HELP_TTS"),
    InlineKeyboardButton("𝐅ᴜɴ", callback_data="mplus HELP_Fun"),InlineKeyboardButton("ǫᴜᴏᴛʟʏ", callback_data="mplus HELP_Q")],          
    [InlineKeyboardButton("◁", callback_data=f"AxiomOwner"), 
    InlineKeyboardButton("▷", callback_data=f"managebot123 AxiomOwner"),
    ]]