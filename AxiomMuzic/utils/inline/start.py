

import random
from pyrogram.types import InlineKeyboardButton
from pyrogram.enums import ButtonStyle

import config
from AxiomMuzic import app

def axiombtn():
    return random.choice([
        ButtonStyle.SUCCESS,
        ButtonStyle.DANGER,
        ButtonStyle.PRIMARY
    ])


def start_panel(_):
    buttons = [
        [
            InlineKeyboardButton(
                text=_["S_B_1"], url=f"https://t.me/{app.username}?startgroup=true", style=axiombtn(),
            ),
            InlineKeyboardButton(text=_["S_B_2"], url=config.SUPPORT_CHAT, style=axiombtn(),),
        ],
    ]
    return buttons


def private_panel(_):
    buttons = [
        [
            InlineKeyboardButton(
                text=_["S_B_3"],
                url=f"https://t.me/{app.username}?startgroup=true", style=axiombtn(),
            )
        ],
        [
            InlineKeyboardButton(text=_["S_B_5"], user_id=config.OWNER_ID, style=axiombtn(),),
            InlineKeyboardButton(text=_["S_B_6"], url=config.SUPPORT_CHANNEL, style=axiombtn(),),
        ],
        [
            InlineKeyboardButton(text=_["S_B_2"], url=config.SUPPORT_CHAT, style=axiombtn(),),
            InlineKeyboardButton(text=_["S_B_10"], callback_data="OwnerAxiom", style=axiombtn(),),
        ],
        [InlineKeyboardButton(text=_["S_B_4"], callback_data="AxiomOwner", style=axiombtn(),)],
    ]
    return buttons
