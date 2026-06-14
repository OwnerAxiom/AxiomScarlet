# -----------------------------------------------
# 🔸 AxiomMusic Project
# 🔹 Developed & Maintained by: Axiom Bots
# -----------------------------------------------

import asyncio
import importlib
import os
import threading
import time

import requests
from flask import Flask
from pyrogram import idle
from pytgcalls.exceptions import NoActiveGroupCall

import config
from AxiomMuzic import LOGGER, app, userbot
from AxiomMuzic.core.call import Axiom
from AxiomMuzic.misc import sudo
from AxiomMuzic.plugins import ALL_MODULES
from AxiomMuzic.utils.database import get_banned_users, get_gbanned

# If your project has BANNED_USERS somewhere else,
# import it from the correct file.
try:
    from AxiomMuzic import BANNED_USERS
except Exception:
    BANNED_USERS = set()

# ─────────────────────────────────────────────
# Flask Health Server
# ─────────────────────────────────────────────

_flask = Flask(__name__)

@_flask.route("/")
def home():
    return "AxiomMusic is Running ❤️", 200


@_flask.route("/health")
def health():
    return "OK", 200


def run_flask():
    port = int(os.getenv("PORT", 8000))
    _flask.run(
        host="0.0.0.0",
        port=port,
        use_reloader=False,
    )


# ─────────────────────────────────────────────
# Auto Keep Alive
# ─────────────────────────────────────────────

def keep_alive():
    port = os.getenv("PORT", "8000")

    url = os.getenv(
        "RENDER_EXTERNAL_URL",
        f"http://127.0.0.1:{port}"
    )

    while True:
        try:
            requests.get(url, timeout=10)
            LOGGER(__name__).info(f"Keep Alive Ping → {url}")
        except Exception as e:
            LOGGER(__name__).warning(f"Keep Alive Error: {e}")

        time.sleep(300)


# ─────────────────────────────────────────────
# Main Startup
# ─────────────────────────────────────────────

async def init():

    # Start Flask
    threading.Thread(
        target=run_flask,
        daemon=True
    ).start()

    LOGGER(__name__).info("Flask Health Server Started")

    # Start Auto Ping
    threading.Thread(
        target=keep_alive,
        daemon=True
    ).start()

    LOGGER(__name__).info("Keep Alive Thread Started")

    if (
        not config.STRING1
        and not config.STRING2
        and not config.STRING3
        and not config.STRING4
        and not config.STRING5
    ):
        LOGGER(__name__).error(
            "The Axiom String Session may be corrupted or missing."
        )
        return

    await sudo()

    try:
        users = await get_gbanned()
        for user_id in users:
            BANNED_USERS.add(user_id)

        users = await get_banned_users()
        for user_id in users:
            BANNED_USERS.add(user_id)

    except Exception as e:
        LOGGER(__name__).warning(
            f"Ban Users Load Error: {e}"
        )

    await app.start()

    for module in ALL_MODULES:
        try:
            importlib.import_module(
                "AxiomMuzic.plugins" + module
            )
        except Exception as e:
            LOGGER(__name__).error(
                f"Module Load Failed {module}: {e}"
            )

    LOGGER("AxiomMuzic.plugins").info(
        "Axiom all features loaded successfully..."
    )

    await userbot.start()

    await Axiom.start()

    try:
        await Axiom.stream_call(
            "https://te.legra.ph/file/29f784eb49d230ab62e9e.mp4"
        )

    except NoActiveGroupCall:
        LOGGER("AxiomMuzic").error(
            "Please start voice chat in AxiomLogger.\n"
            "AxiomMuzic stopped."
        )
        return

    except Exception as e:
        LOGGER("AxiomMuzic").warning(
            f"Stream Call Error: {e}"
        )

    await Axiom.decorators()

    LOGGER("AxiomMuzic").info(
        "\n╔═════ஜ۩۞۩ஜ════╗\n"
        "  ☠ MADE BY MAANAV\n"
        "╚═════ஜ۩۞۩ஜ════╝"
    )

    await idle()

    await app.stop()
    await userbot.stop()

    LOGGER("AxiomMuzic").info(
        "Stopping AxiomMuzic Bot...."
    )


if __name__ == "__main__":
    asyncio.get_event_loop().run_until_complete(
        init()
    )
