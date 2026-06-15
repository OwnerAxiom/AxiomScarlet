# -----------------------------------------------
# 🔸 AxiomMusic Project - Random Color Palette Glow
# 🔹 Based on your original code
# 📅 Copyright © 2026 – All Rights Reserved
# -----------------------------------------------

import os
import re
import random
import aiohttp
import aiofiles
import colorsys
from functools import lru_cache
from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageEnhance
from py_yt import VideosSearch
from config import YOUTUBE_IMG_URL

CACHE_DIR = "cache"
os.makedirs(CACHE_DIR, exist_ok=True)

W, H = 1280, 720
BG_COLOR = (45, 60, 65)
TEXT_WHITE = (255, 255, 255)
TEXT_GRAY = (175, 182, 188)

# ===== LAYOUT =====
CARD_W, CARD_H = 980, 470
CARD_X = (1280 - CARD_W) // 2
CARD_Y = (720 - CARD_H) // 2
CARD_RADIUS = 55

THUMB_SIZE = 320
THUMB_X = CARD_X + 65
THUMB_Y = CARD_Y + 75
THUMB_RADIUS = 35

TITLE_X = THUMB_X + THUMB_SIZE + 60
TITLE_Y = CARD_Y + 90
META_Y = TITLE_Y + 50

BAR_WIDTH = 480
BAR_HEIGHT = 5
BAR_X = TITLE_X
BAR_Y = META_Y + 65

CONTROLS_Y = BAR_Y + 50
CONTROLS_X = TITLE_X

MAX_TITLE_WIDTH = 520


def trim_text(text, font, max_width):
    try:
        if font.getlength(text) <= max_width:
            return text
        for i in range(len(text) - 1, 0, -1):
            if font.getlength(text[:i] + "…") <= max_width:
                return text[:i] + "…"
        return "…"
    except:
        return text[:50] + "..."


def _random_palette():
    """Generate random vibrant color palette"""
    h = random.random()
    
    if 0.08 < h < 0.16:
        h += 0.15
    if 0.45 < h < 0.52:
        h += 0.08
    h %= 1.0
    
    s = random.uniform(0.75, 1.0)
    v = random.uniform(0.8, 1.0)
    
    base = tuple(int(x * 255) for x in colorsys.hsv_to_rgb(h, s, v))
    
    light = tuple(
        int(x * 255)
        for x in colorsys.hsv_to_rgb(h, random.uniform(0.25, 0.5), 1.0)
    )
    
    dark = tuple(
        int(x * 255)
        for x in colorsys.hsv_to_rgb(h, 1.0, random.uniform(0.18, 0.35))
    )
    
    return base, light, dark


def _make_bg_v4():
    """ORIGINAL background - EXACT from your code"""
    base = Image.new("RGB", (W, H), BG_COLOR)
    draw = ImageDraw.Draw(base, "RGBA")
    for y in range(H):
        ratio = y / H
        draw.line([(0, y), (W, y)], fill=(0, 0, 0, int(45 * ratio)))
    vignette = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    vd = ImageDraw.Draw(vignette)
    for i in range(160, 0, -5):
        alpha = int(130 * (1 - i / 160))
        vd.rectangle([0, 0, W, H], outline=(0, 0, 0, alpha), width=i)
    base.paste(vignette.filter(ImageFilter.GaussianBlur(45)), (0, 0), vignette)
    return base


def _draw_card_border_with_random_glow(base: Image.Image, x1, y1, x2, y2, r=55, c_base=(202,215,221), c_light=(225,235,240), c_dark=(140,155,162)) -> Image.Image:
    """Card border with random color glow - EXACT like your thumbnail"""
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    
    # Outer glow layers (like your art shadow)
    for i in range(38, 0, -1):
        alpha = int(95 * (1 - i / 38) ** 1.4)
        d.rounded_rectangle([x1 - i, y1 - i, x2 + i, y2 + i], radius=r + i, fill=(255, 255, 255, alpha))
    
    # Base color glow
    for i in range(18, 0, -1):
        d.rounded_rectangle(
            [x1 - i, y1 - i, x2 + i, y2 + i],
            radius=r + i,
            fill=(*c_base, int(75 * (1 - i / 18)))
        )
    
    # Inner dark background
    d.rounded_rectangle([x1 + 10, y1 + 10, x2 - 10, y2 - 10], radius=max(r - 10, 4), fill=(18, 24, 26, 255))
    
    # Border lines
    for offset, color, bw in [(0, (*c_dark, 255), 5), (2, (*c_base, 255), 3), (4, (255, 255, 255, 180), 2)]:
        d.rounded_rectangle([x1 + offset, y1 + offset, x2 - offset, y2 - offset], radius=max(r - offset, 4), outline=color, width=bw)
    
    return Image.alpha_composite(base.convert("RGBA"), layer).convert("RGB")


def _draw_art_shadow(base: Image.Image, x, y, w, h, r=18, c_base=(202,215,221)) -> Image.Image:
    """Thumbnail shadow with random color glow - EXACT from your code"""
    shadow_layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    sd = ImageDraw.Draw(shadow_layer)

    off_x, off_y = 10, 14

    # Deep black shadow
    for i in range(48, 0, -1):
        alpha = int(230 * (1 - i / 48) ** 1.3)
        sd.rounded_rectangle(
            [x+off_x-i, y+off_y-i, x+w+off_x+i, y+h+off_y+i],
            radius=r+i,
            fill=(0, 0, 0, alpha)
        )

    # Outer glow with random color
    for i in range(22, 0, -1):
        alpha = int(120 * (1 - i / 22) ** 1.6)
        sd.rounded_rectangle(
            [x-i, y-i, x+w+i, y+h+i],
            radius=r+i,
            fill=(*c_base, alpha)
        )

    shadow_layer = shadow_layer.filter(ImageFilter.GaussianBlur(22))
    return Image.alpha_composite(base.convert("RGBA"), shadow_layer).convert("RGB")


def _paste_rounded(base: Image.Image, img: Image.Image, x, y, w, h, r=18) -> Image.Image:
    img = img.resize((w, h), Image.LANCZOS).convert("RGBA")
    mask = Image.new("L", (w, h), 0)
    ImageDraw.Draw(mask).rounded_rectangle([(0, 0), (w - 1, h - 1)], radius=r, fill=255)
    img.putalpha(mask)
    base_r = base.convert("RGBA")
    base_r.paste(img, (x, y), img)
    return base_r.convert("RGB")


def _draw_bar(base: Image.Image, bx, by_top, by_bot, progress: float = 0.06,
              c_base=(202,215,221), c_light=(225,235,240), c_dark=(140,155,162)) -> Image.Image:

    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)

    bw = 8
    knob_y = by_top + int((by_bot - by_top) * progress)
    kr = 14

    # Inactive line
    d.rounded_rectangle(
        [(bx - bw//2, by_top), (bx + bw//2, by_bot)],
        radius=4,
        fill=(90, 95, 110, 255)
    )

    # Active line with random color
    if knob_y > by_top:
        d.rounded_rectangle(
            [(bx - bw//2, by_top), (bx + bw//2, knob_y)],
            radius=4,
            fill=(*c_base, 255)
        )

    # Glow rings
    d.ellipse(
        [(bx - kr - 16, knob_y - kr - 16),
         (bx + kr + 16, knob_y + kr + 16)],
        fill=(*c_base, 35)
    )

    d.ellipse(
        [(bx - kr - 9, knob_y - kr - 9),
         (bx + kr + 9, knob_y + kr + 9)],
        fill=(*c_base, 70)
    )

    # Main knob
    d.ellipse(
        [(bx - kr, knob_y - kr),
         (bx + kr, knob_y + kr)],
        fill=(*c_base, 255)
    )

    return Image.alpha_composite(base.convert("RGBA"), layer).convert("RGB")


# ===== ICONS =====

def icon_shuffle(draw, x, y, s, color):
    x, y, s = int(x), int(y), int(s)
    draw.line([(x, y + s//3), (x + s//2, y)], fill=color, width=2)
    draw.line([(x + s//4, y), (x + s*3//4, y)], fill=color, width=2)
    draw.polygon([(x + s//2, y), (x + s//2 + 5, y + 3), (x + s//2, y + 6)], fill=color)
    draw.line([(x, y + s*2//3), (x + s//2, y + s)], fill=color, width=2)
    draw.line([(x + s//4, y + s), (x + s*3//4, y + s)], fill=color, width=2)
    draw.polygon([(x + s//2, y + s), (x + s//2 + 5, y + s - 3), (x + s//2, y + s - 6)], fill=color)


def icon_repeat(draw, x, y, s, color):
    x, y, s = int(x), int(y), int(s)
    draw.arc([(x, y), (x + s, y + s//2)], 180, 360, fill=color, width=2)
    draw.polygon([(x + s - 5, y), (x + s, y + 3), (x + s - 5, y + 6)], fill=color)
    draw.arc([(x, y + s//2), (x + s, y + s)], 0, 180, fill=color, width=2)
    draw.polygon([(x, y + s), (x + 5, y + s - 3), (x + 5, y + s - 6)], fill=color)


def icon_prev(draw, x, y, s, color):
    x, y, s = int(x), int(y), int(s)
    draw.polygon([(x + s*3//4, y + 2), (x + s*3//4, y + s - 2), (x + 2, y + s//2)], fill=color)
    draw.rectangle([(x + s*4//5, y + 2), (x + s - 1, y + s - 2)], fill=color)


def icon_pause(draw, x, y, s, color):
    x, y, s = int(x), int(y), int(s)
    draw.rectangle([(x, y + 2), (x + s//3, y + s - 2)], fill=color)
    draw.rectangle([(x + s*2//3, y + 2), (x + s, y + s - 2)], fill=color)


def icon_next(draw, x, y, s, color):
    x, y, s = int(x), int(y), int(s)
    draw.rectangle([(x + 1, y + 2), (x + s//4, y + s - 2)], fill=color)
    draw.polygon([(x + s//3, y + 2), (x + s//3, y + s - 2), (x + s - 2, y + s//2)], fill=color)


def icon_heart(draw, x, y, s, color):
    x, y, s = int(x), int(y), int(s)
    draw.ellipse([(x + 2, y + 4), (x + s//2, y + s//2 + 2)], fill=color)
    draw.ellipse([(x + s//2, y + 4), (x + s - 2, y + s//2 + 2)], fill=color)
    draw.polygon([(x + 3, y + s//2), (x + s - 3, y + s//2), (x + s//2, y + s - 2)], fill=color)


def icon_headphones(draw, x, y, s, color):
    x, y, s = int(x), int(y), int(s)
    draw.arc([(x + 3, y), (x + s - 3, y + s//2 + 5)], 180, 0, fill=color, width=2)
    draw.ellipse([(x, y + s//2 + 2), (x + s//3, y + s - 2)], fill=color)
    draw.ellipse([(x + s*2//3, y + s//2 + 2), (x + s, y + s - 2)], fill=color)


# ===== MAIN =====

async def get_thumb(videoid: str) -> str:
    output = f"cache/{videoid}_final.png"
    cache = f"cache/thumb_{videoid}.png"
    os.makedirs("cache", exist_ok=True)

    # Fetch metadata
    url = f"https://www.youtube.com/watch?v={videoid}"
    try:
        data = (await VideosSearch(url, limit=1).next())["result"][0]
        title = re.sub(r"[\x00-\x1f\x7f]", "", data.get("title", "Unknown")).strip()
        duration = data.get("duration", "00:00") or "00:00"
        thumbnail_url = data.get("thumbnails", [{}])[-1].get("url", "").split("?")[0]
        v_raw = str(data.get("viewCount", {}).get("short", "N/A"))
        vc = re.sub(r'\s*views?\s*', '', v_raw, flags=re.IGNORECASE).strip()
        views, channel = f"{vc} views", data.get("channel", {}).get("name", "Unknown")
    except Exception:
        return YOUTUBE_IMG_URL

    # Download thumbnail
    try:
        async with aiohttp.ClientSession() as sess:
            async with sess.get(thumbnail_url, timeout=aiohttp.ClientTimeout(total=10)) as r:
                async with aiofiles.open(cache, "wb") as f:
                    await f.write(await r.read())
        song_img = Image.open(cache).convert("RGBA")
    except Exception:
        return YOUTUBE_IMG_URL

    try:
        # === RANDOM PALETTE ===
        c_base, c_light, c_dark = _random_palette()
        
        # === ORIGINAL BACKGROUND (EXACT from your code) ===
        base = _make_bg_v4()
        
        # Add nebula effects (from your code)
        bg = Image.new("RGBA", (W, H), (4, 5, 18, 255))
        
        nebula = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        ndraw = ImageDraw.Draw(nebula)
        
        for _ in range(8):
            color = (
                random.randint(40, 255),
                random.randint(40, 255),
                random.randint(40, 255),
                random.randint(30, 70)
            )
            x = random.randint(-200, W)
            y = random.randint(-200, H)
            size = random.randint(250, 600)
            ndraw.ellipse((x, y, x + size, y + size), fill=color)
        
        nebula = nebula.filter(ImageFilter.GaussianBlur(130))
        bg = Image.alpha_composite(bg, nebula)
        
        # Stars
        stars = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        sdraw = ImageDraw.Draw(stars)
        
        for _ in range(2500):
            x = random.randint(0, W)
            y = random.randint(0, H)
            size = random.randint(1, 3)
            alpha = random.randint(80, 220)
            sdraw.ellipse((x, y, x + size, y + size), fill=(255, 255, 255, alpha))
        
        stars = stars.filter(ImageFilter.GaussianBlur(0.4))
        bg = Image.alpha_composite(bg, stars)
        
        # Planet
        planet = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        pdraw = ImageDraw.Draw(planet)
        
        planet_x = random.randint(70, 1150)
        planet_y = random.randint(60, 550)
        r = random.randint(35, 70)
        
        planet_color = (
            random.randint(80, 255),
            random.randint(80, 255),
            random.randint(80, 255),
            120
        )
        
        pdraw.ellipse(
            (planet_x-r, planet_y-r, planet_x+r, planet_y+r),
            fill=planet_color
        )
        
        planet = planet.filter(ImageFilter.GaussianBlur(8))
        bg = Image.alpha_composite(bg, planet)
        
        base = bg.convert("RGB")
        
        # === CARD with TRANSPARENT BLUR (EXACT from your code) ===
        card_area = base.crop((CARD_X, CARD_Y, CARD_X + CARD_W, CARD_Y + CARD_H))
        card_area = card_area.filter(ImageFilter.GaussianBlur(25))
        
        # Card with random color border glow
        base = _draw_card_border_with_random_glow(
            base,
            CARD_X, CARD_Y, CARD_X + CARD_W, CARD_Y + CARD_H,
            CARD_RADIUS,
            c_base, c_light, c_dark
        )
        
        # === THUMBNAIL with SHADOW + GLOW (EXACT from your code) ===
        base = _draw_art_shadow(base, THUMB_X, THUMB_Y, THUMB_SIZE, THUMB_SIZE, THUMB_RADIUS, c_base)
        base = _paste_rounded(base, song_img, THUMB_X, THUMB_Y, THUMB_SIZE, THUMB_SIZE, THUMB_RADIUS)
        
        # Glass effect
        glass = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        gd = ImageDraw.Draw(glass)
        
        gd.rounded_rectangle(
            [THUMB_X + 3, THUMB_Y + 3, THUMB_X + THUMB_SIZE - 3, THUMB_Y + THUMB_SIZE - 3],
            radius=THUMB_RADIUS - 3,
            fill=(255, 255, 255, 8)
        )
        
        glass = glass.filter(ImageFilter.GaussianBlur(4))
        base = Image.alpha_composite(base.convert("RGBA"), glass).convert("RGB")
        
        # === PROGRESS BAR ===
        base = _draw_bar(base, BAR_X, BAR_Y, BAR_Y + BAR_HEIGHT, 0.35, c_base, c_light, c_dark)
        
        draw = ImageDraw.Draw(base)
        
        try:
            title_font = ImageFont.truetype("AxiomMuzic/assets/assets/font2.ttf", 40)
            meta_font = ImageFont.truetype("AxiomMuzic/assets/assets/font.ttf", 22)
            time_font = ImageFont.truetype("AxiomMuzic/assets/assets/font.ttf", 19)
        except OSError:
            title_font = ImageFont.load_default()
            meta_font = title_font
            time_font = title_font

        trimmed = trim_text(title, title_font, MAX_TITLE_WIDTH)
        draw.text((TITLE_X, TITLE_Y), trimmed, fill="white", font=title_font)
        draw.text((TITLE_X, META_Y), channel, fill=(190, 190, 190), font=meta_font)

        # Progress bar times
        draw.text((BAR_X, BAR_Y + 17), "01:17", fill="white", font=time_font)
        total = duration if not is_live else "2:16"
        draw.text((BAR_X + BAR_WIDTH - 40, BAR_Y + 17), total, fill="white", font=time_font)

        # === CONTROLS ===
        icon_y = CONTROLS_Y
        icon_size = 26
        sx = CONTROLS_X
        gap = 45

        icon_shuffle(draw, sx, icon_y, icon_size, c_light)
        icon_repeat(draw, sx + gap, icon_y, icon_size, c_light)
        icon_prev(draw, sx + gap * 2, icon_y, icon_size, "white")
        icon_pause(draw, sx + gap * 3, icon_y, icon_size, "white")
        icon_next(draw, sx + gap * 4, icon_y, icon_size, "white")
        icon_heart(draw, sx + gap * 5, icon_y, icon_size, c_base)
        icon_headphones(draw, sx + gap * 6, icon_y, icon_size, "white")

        # === SAVE ===
        base = base.convert("RGB")
        base.save(output, "PNG", quality=95)

    except Exception as e:
        import traceback
        traceback.print_exc()
        return YOUTUBE_IMG_URL
    finally:
        try:
            if os.path.exists(cache):
                os.remove(cache)
        except OSError:
            pass

    return output
