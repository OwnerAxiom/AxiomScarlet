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
import asyncio
import importlib
from pyrogram import idle
from pytgcalls.exceptions import NoActiveGroupCall
import config
from AxiomMuzic import LOGGER, app, userbot
from AxiomMuzic.core.call import Axiom
from AxiomMuzic.misc import sudo
from AxiomMuzic.plugins import ALL_MODULES
from AxiomMuzic.utils.database import get_banned_users, get_gbanned

async def init():
    if (
        not config.STRING1
        and not config.STRING2
        and not config.STRING3
        and not config.STRING4
        and not config.STRING5
    ):
        LOGGER(__name__).error("The Axiom String Session may be currepted filles or not filled yet any session string")
        exit()
    await sudo()
    try:
        users = await get_gbanned()
        for user_id in users:
            BANNED_USERS.add(user_id)
        users = await get_banned_users()
        for user_id in users:
            BANNED_USERS.add(user_id)
    except:
        pass
    await app.start()
    for all_module in ALL_MODULES:
        importlib.import_module("AxiomMuzic.plugins" + all_module)
    LOGGER("AxiomMuzic.plugins").info("Axiom all features loaded successfully...")
    await userbot.start()
    await Axiom.start()
    try:
        await Axiom.stream_call("https://te.legra.ph/file/29f784eb49d230ab62e9e.mp4")
    except NoActiveGroupCall:
        LOGGER("AxiomMuzic").error(
            "Please go and start voice chat AxiomLogger\n\nAxiomMuzic bot stopped........"
        )
        exit()
    except:
        pass
    await Axiom.decorators()
    LOGGER("AxiomMuzic").info(
        "╔═════ஜ۩۞۩ஜ════╗\n  ☠︎︎MADE BY MAANAV\n╚═════ஜ۩۞۩ஜ════╝"
    )
    await idle()
    await app.stop()
    await userbot.stop()
    LOGGER("AxiomMuzic").info("Stopping AxiomMuzic Bot....")


if __name__ == "__main__":
    asyncio.get_event_loop().run_until_complete(init())