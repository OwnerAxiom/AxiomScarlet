# # -----------------------------------------------
# # 🔸 AxiomMusic Project
# # 🔹 Developed & Maintained by: Axiom Bots (https://t.me/axiombots)
# # 📅 Copyright © 2026 – All Rights Reserved
# #
# # 📖 License:
# # This source code is open for educational and non-commercial use ONLY.
# # You are required to retain this credit in all copies or substantial portions of this file.
# # Commercial use, redistribution, or removal of this notice is strictly prohibited
# # without prior written permission from the author.
# #
# # ❤️ Made with dedication and love by AxiomBots
# # -----------------------------------------------
# import httpx
# from pyrogram import filters
# from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
# from AxiomMuzic.utils.errors import capture_err 
# from AxiomMuzic import app
# from config import BOT_USERNAME

# # Caption Text
# start_txt = """<b>✨ ᴡᴇʟᴄᴏᴍᴇ ᴛᴏ <u>ᴀxɪσϻ ʀᴇᴘᴏs</u></b>

# 🚀 <b>ᴇᴀsʏ ᴅᴇᴘʟᴏʏ</b> –ᴏɴᴇ ᴄʟɪᴄᴋ ʜᴇʀᴏᴋᴜ ᴅᴇᴘʟᴏʏᴍᴇɴᴛ  
# 🛡️ <b>ɴᴏ ʜᴇʀᴏᴋᴜ ᴏʀ ɪᴅ ʙᴀɴ ɪssᴜᴇs</b>  
# 🔋 <b>ᴜɴʟɪᴍɪᴛᴇᴅ ᴅʏɴᴏs</b> – ʀᴜɴ 24/7 ʟᴀɢɢ-ғʀᴇᴇ  
# ⚙️ <b>ғᴜʟʟʏ ғᴜɴᴄᴛɪᴏɴᴀʟ & ᴇʀʀᴏʀ-ғʀᴇᴇ</b>  

# <i>ɴᴇᴇᴅ ʜᴇʟᴘ? sᴇɴᴅ sᴄʀᴇᴇɴsʜᴏᴛ ᴛᴏ ᴛʜᴇ sᴜᴘᴘᴏʀᴛ ɢʀᴏᴜᴘ!</i>"""

# # Repo Command Handler
# @app.on_message(filters.command("repo"))
# async def repo_handler(_, msg):
#     buttons = [
#         [InlineKeyboardButton("➕ ᴀᴅᴅ ᴍᴇ ʙᴀʙʏ", url=f"https://t.me/{app.username}?startgroup=true")],
#         [
#             InlineKeyboardButton("💬 sᴜᴘᴘᴏʀᴛ", url="https://t.me/Axlomm"),
#             InlineKeyboardButton("👤 ᴏᴡɴᴇʀ", url="https://t.me/CreativeAxiom"),
#         ],
#         [InlineKeyboardButton("🧾 ᴜᴘᴅᴀᴛᴇs", url="https://t.me/AxiomBots")]
#     ]

#     await msg.reply_photo(
#         photo="https://files.catbox.moe/jxribw.jpg",
#         caption=start_txt,
#         reply_markup=InlineKeyboardMarkup(buttons)
#     )

   
# # --------------


# @app.on_message(filters.command("repo", prefixes="#", ".", "/"))
# @capture_err
# async def repo(_, message):
#     async with httpx.AsyncClient() as client:
#         response = await client.get("https://api.github.com/repos/maanavbaby/AxiomScarlet/contributors")
    
#     if response.status_code == 200:
#         users = response.json()
#         list_of_users = ""
#         count = 1
#         for user in users:
#             list_of_users += f"{count}. [{user['login']}]({user['html_url']})\n"
#             count += 1

#         text = f"""[Repo](https://github.com/maanavbaby/AxiomScarlet) | [UPDATES](https://t.me/AxiomBots)
# | 𝖢𝖮𝖭𝖳𝖱𝖨𝖡𝖴𝖳𝖮𝖱𝖲 |
# ----------------
# {list_of_users}"""
#         await app.send_message(message.chat.id, text=text, disable_web_page_preview=True)
#     else:
#         await app.send_message(message.chat.id, text="Failed to fetch contributors.")


