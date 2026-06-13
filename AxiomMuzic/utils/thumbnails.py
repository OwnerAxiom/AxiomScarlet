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
import os
import re
import aiofiles
import aiohttp
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont
from py_yt import VideosSearch
from config import YOUTUBE_IMG_URL

# Constants
CACHE_DIR = "cache"
os.makedirs(CACHE_DIR, exist_ok=True)

PANEL_W, PANEL_H = 880, 390
PANEL_X = (1280 - PANEL_W) // 2
PANEL_Y = 145

THUMB_W, THUMB_H = 280, 280
THUMB_X = PANEL_X + 35
THUMB_Y = PANEL_Y + 60

TITLE_X = THUMB_X + THUMB_W + 30
TITLE_Y = THUMB_Y + 20

META_X = TITLE_X
META_Y = TITLE_Y + 60

BAR_X = TITLE_X
BAR_Y = META_Y + 70
BAR_TOTAL_LEN = 420
BAR_RED_LEN = 240

ICONS_W, ICONS_H = 320, 38
ICONS_X = TITLE_X + 40
ICONS_Y = BAR_Y + 70

MAX_TITLE_WIDTH = 420

def trim_to_width(text: str, font: ImageFont.FreeTypeFont, max_w: int) -> str:
    ellipsis = "…"
    if font.getlength(text) <= max_w:
        return text
    for i in range(len(text) - 1, 0, -1):
        if font.getlength(text[:i] + ellipsis) <= max_w:
            return text[:i] + ellipsis
    return ellipsis

async def get_thumb(videoid: str) -> str:
    cache_path = os.path.join(CACHE_DIR, f"{videoid}_v4.png")
    if os.path.exists(cache_path):
        return cache_path

    # YouTube video data fetch
    results = VideosSearch(f"https://www.youtube.com/watch?v={videoid}", limit=1)
    try:
        results_data = await results.next()
        result_items = results_data.get("result", [])
        if not result_items:
            raise ValueError("No results found.")
        data = result_items[0]
        title = re.sub(r"\W+", " ", data.get("title", "Unsupported Title")).title()
        thumbnail = data.get("thumbnails", [{}])[0].get("url", YOUTUBE_IMG_URL)
        duration = data.get("duration")
        views = data.get("viewCount", {}).get("short", "Unknown Views")
    except Exception:
        title, thumbnail, duration, views = "Unsupported Title", YOUTUBE_IMG_URL, None, "Unknown Views"

    is_live = not duration or str(duration).strip().lower() in {"", "live", "live now"}
    duration_text = "Live" if is_live else duration or "Unknown Mins"

    # Download thumbnail
    thumb_path = os.path.join(CACHE_DIR, f"thumb{videoid}.png")
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(thumbnail) as resp:
                if resp.status == 200:
                    async with aiofiles.open(thumb_path, "wb") as f:
                        await f.write(await resp.read())
    except Exception:
        return YOUTUBE_IMG_URL

    # Create base image
    base = Image.open(thumb_path).resize((1280, 720)).convert("RGBA")
    
    bg = base.filter(ImageFilter.GaussianBlur(12))
    
    dark = Image.new("RGBA", bg.size, (0, 0, 0, 70))
    bg = Image.alpha_composite(bg, dark)
    
    shadow = shadow.filter(ImageFilter.GaussianBlur(15))
    bg = Image.alpha_composite(bg, shadow)

    # Frosted glass panel
    panel = bg.crop(
        (
            PANEL_X,
            PANEL_Y,
            PANEL_X + PANEL_W,
            PANEL_Y + PANEL_H,
        )
    )
    
    panel = panel.filter(ImageFilter.GaussianBlur(3))
    
    glass = Image.new(
        "RGBA",
        (PANEL_W, PANEL_H),
        (15, 15, 15, 85),
    )
    
    panel = Image.alpha_composite(panel, glass)
    
    mask = Image.new("L", (PANEL_W, PANEL_H), 0)
    
    ImageDraw.Draw(mask).rounded_rectangle(
        (0, 0, PANEL_W, PANEL_H),
        radius=35,
        fill=255,
    )
    
    bg.paste(panel, (PANEL_X, PANEL_Y), mask)

    # Draw details
    draw = ImageDraw.Draw(bg)
    try:
        title_font = ImageFont.truetype("AxiomMuzic/assets/assets/font2.ttf", 36)
        regular_font = ImageFont.truetype("AxiomMuzic/assets/assets/font.ttf", 22)
    except OSError:
        title_font = regular_font = ImageFont.load_default()

    thumb = Image.open(thumb_path).convert("RGBA")
    thumb = thumb.resize((THUMB_W, THUMB_H), Image.LANCZOS)
    tmask = Image.new("L", thumb.size, 0)
    ImageDraw.Draw(tmask).rounded_rectangle((0, 0, THUMB_W, THUMB_H), 28, fill=255)
    #thumbnail shadow added
    shadow = Image.new("RGBA", bg.size, (0,0,0,0))
    sdraw = ImageDraw.Draw(shadow)
    
    sdraw.rounded_rectangle(
        (
            THUMB_X-6,
            THUMB_Y-6,
            THUMB_X+THUMB_W+6,
            THUMB_Y+THUMB_H+6
        ),
        radius=32,
        fill=(0,0,0,120)
    )
    bg.paste(thumb, (THUMB_X, THUMB_Y), tmask)

    draw.text((TITLE_X, TITLE_Y), trim_to_width(title, title_font, MAX_TITLE_WIDTH), fill="white", font=title_font)
    draw.text((META_X, META_Y), f"YouTube | {views}", fill=(220,220,220), font=regular_font)

    # Progress bar
    draw.line(
        [(BAR_X, BAR_Y), (BAR_X + BAR_TOTAL_LEN, BAR_Y)],
        fill=(160,160,160),
        width=6,
    )
    
    draw.line(
        [(BAR_X, BAR_Y), (BAR_X + BAR_RED_LEN, BAR_Y)],
        fill=(80,255,120),
        width=7,
    )
    
    draw.ellipse(
        (
            BAR_X + BAR_RED_LEN - 8,
            BAR_Y - 8,
            BAR_X + BAR_RED_LEN + 8,
            BAR_Y + 8,
        ),
        fill="white",
    )

    draw.text((BAR_X, BAR_Y + 15), "01:13", fill="white", font=regular_font)
    end_text = "Live" if is_live else duration_text
    draw.text((BAR_X + BAR_TOTAL_LEN - (90 if is_live else 30), BAR_Y + 15), end_text, fill=(255,80,80) if is_live else "white", font=regular_font)

    # Icons
    icons_path = "AxiomMuzic/assets/assets/play_icons.png"
    if os.path.isfile(icons_path):
        ic = Image.open(icons_path).resize((ICONS_W, ICONS_H)).convert("RGBA")
        r, g, b, a = ic.split()
        black_ic = Image.merge("RGBA", (r.point(lambda *_: 0), g.point(lambda *_: 0), b.point(lambda *_: 0), a))
        bg.paste(ic, (ICONS_X, ICONS_Y), ic)

    # Cleanup and save
    try:
        os.remove(thumb_path)
    except OSError:
        pass

    bg.save(cache_path)
    return cache_path
