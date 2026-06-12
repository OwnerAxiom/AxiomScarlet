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
from pyrogram import Client, filters
from AxiomMuzic import app
from config import BOT_USERNAME


def hex_to_text(hex_string):
    try:
        text = bytes.fromhex(hex_string).decode('utf-8')
        return text
    except Exception as e:
        return f"Error decoding hex: {str(e)}"


def text_to_hex(text):
    hex_representation = ' '.join(format(ord(char), 'x') for char in text)
    return hex_representation


@app.on_message(filters.command("code", "decode"))
def convert_text(_, message):
    if len(message.command) > 1:
        input_text = " ".join(message.command[1:])

        hex_representation = text_to_hex(input_text)
        decoded_text = hex_to_text(input_text)

        response_text = f"Input Text➪\n {input_text}\n\nHez Representation➪\n {hex_representation}\n\n𝗗𝗲𝗰𝗼𝗱𝗲𝗱 𝗧𝗲𝘅𝘁➪\n {decoded_text}\n\n\nBy ➪@{BOT_USERNAME}"

        message.reply_text(response_text)
    else:
        message.reply_text("Please provide text after the /code command.")
