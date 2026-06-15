# -----------------------------------------------
# 🔸 AxiomMusic Project - Random Rainbow Glow
# 🔹 Developed & Maintained by: Axiom Bots (https://t.me/axiombots)
# 📅 Copyright © 2026 – All Rights Reserved
# -----------------------------------------------

import os
import re
import random
import aiofiles
import aiohttp
import colorsys
from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageEnhance
from py_yt import VideosSearch
from config import YOUTUBE_IMG_URL

CACHE_DIR = "cache"
os.makedirs(CACHE_DIR, exist_ok=True)

# ===== LAYOUT =====
CARD_W, CARD_H = 980, 470
CARD_X = (1280 - CARD_W) // 2
CARD_Y = (720 - CARD_H) // 2
CARD_RADIUS = 55

THUMB_SIZE = 320
THUMB_X = CARD_X + 65  # Thoda right
THUMB_Y = CARD_Y + 75  # Thoda niche
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
    
    # Avoid muddy colors
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


def create_card_border_with_glow(size, radius, c_base, c_light, c_dark):
    """Create card border with shadow and glow - exactly like your reference"""
    w, h = size
    layer = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(layer)
    
    # Outer glow/shadow layers
    for i in range(38, 0, -1):
        alpha = int(95 * (1 - i / 38) ** 1.4)
        draw.rounded_rectangle(
            [0 - i, 0 - i, w + i, h + i],
            radius=radius + i,
            fill=(255, 255, 255, alpha)
        )
    
    # Base color glow
    for i in range(18, 0, -1):
        draw.rounded_rectangle(
            [0 - i, 0 - i, w + i, h + i],
            radius=radius + i,
            fill=(*c_base, int(75 * (1 - i / 18)))
        )
    
    # Inner dark background
    draw.rounded_rectangle(
        [10, 10, w - 10, h - 10],
        radius=max(radius - 10, 4),
        fill=(18, 24, 26, 255)
    )
    
    # Border lines
    for offset, color, bw in [
        (0, (*c_dark, 255), 5),
        (2, (*c_base, 255), 3),
        (4, (255, 255, 255, 180), 2)
    ]:
        draw.rounded_rectangle(
            [offset, offset, w - offset, h - offset],
            radius=max(radius - offset, 4),
            outline=color,
            width=bw
        )
    
    return layer


def create_art_shadow(size, x, y, w, h, radius, c_base):
    """Create artistic shadow for thumbnail"""
    shadow_layer = Image.new("RGBA", size, (0, 0, 0, 0))
    sd = ImageDraw.Draw(shadow_layer)
    
    off_x, off_y = 10, 14
    
    # Deep black shadow
    for i in range(48, 0, -1):
        alpha = int(230 * (1 - i / 48) ** 1.3)
        sd.rounded_rectangle(
            [x + off_x - i, y + off_y - i, x + w + off_x + i, y + h + off_y + i],
            radius=radius + i,
            fill=(0, 0, 0, alpha)
        )
    
    # Outer glow
    for i in range(22, 0, -1):
        alpha = int(120 * (1 - i / 22) ** 1.6)
        sd.rounded_rectangle(
            [x - i, y - i, x + w + i, y + h + i],
            radius=radius + i,
            fill=(*c_base, alpha)
        )
    
    shadow_layer = shadow_layer.filter(ImageFilter.GaussianBlur(22))
    return shadow_layer


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
    cache_path = os.path.join(CACHE_DIR, f"{videoid}_final.png")
    if os.path.exists(cache_path):
        try:
            os.remove(cache_path)
        except:
            pass

    thumb_path = os.path.join(CACHE_DIR, f"thumb_{videoid}.png")

    try:
        results = VideosSearch(f"https://www.youtube.com/watch?v={videoid}", limit=1)
        results_data = await results.next()
        result_items = results_data.get("result", [])
        if not result_items:
            raise ValueError("No results")
        data = result_items[0]
        title = re.sub(r"\W+", " ", data.get("title", "Unsupported Title")).title()
        thumbnail_url = data.get("thumbnails", [{}])[0].get("url", YOUTUBE_IMG_URL)
        duration = data.get("duration")
        views = data.get("viewCount", {}).get("short", "Unknown Views")
        channel = data.get("channel", {}).get("name", "YouTube")
    except Exception:
        title, thumbnail_url, duration, views, channel = (
            "Unsupported Title", YOUTUBE_IMG_URL, None, "Unknown Views", "YouTube"
        )

    is_live = not duration or str(duration).strip().lower() in {"", "live", "live now"}
    duration_text = "LIVE" if is_live else (duration or "Unknown")

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(thumbnail_url, timeout=10) as resp:
                if resp.status == 200:
                    async with aiofiles.open(thumb_path, "wb") as f:
                        await f.write(await resp.read())
                else:
                    return YOUTUBE_IMG_URL
    except Exception:
        return YOUTUBE_IMG_URL

    try:
        # === RANDOM PALETTE ===
        c_base, c_light, c_dark = _random_palette()

        # === BACKGROUND ===
        base = Image.open(thumb_path).convert("RGBA")
        base = base.resize((1280, 720), Image.LANCZOS)
        base = ImageEnhance.Brightness(base).enhance(1.35)
        base = ImageEnhance.Contrast(base).enhance(1.15)
        base = ImageEnhance.Color(base).enhance(1.2)
        bg = base.filter(ImageFilter.GaussianBlur(55))
        
        # Dark overlay
        dark_overlay = Image.new("RGBA", bg.size, (3, 5, 12, 210))
        bg = Image.alpha_composite(bg.convert("RGBA"), dark_overlay)
        
        # Nebula effects (like your code)
        nebula = Image.new("RGBA", (1280, 720), (0, 0, 0, 0))
        ndraw = ImageDraw.Draw(nebula)
        
        for _ in range(8):
            color = (
                random.randint(40, 255),
                random.randint(40, 255),
                random.randint(40, 255),
                random.randint(30, 70)
            )
            x = random.randint(-200, 1280)
            y = random.randint(-200, 720)
            size = random.randint(250, 600)
            ndraw.ellipse((x, y, x + size, y + size), fill=color)
        
        nebula = nebula.filter(ImageFilter.GaussianBlur(130))
        bg = Image.alpha_composite(bg, nebula)
        
        # Stars
        stars = Image.new("RGBA", (1280, 720), (0, 0, 0, 0))
        sdraw = ImageDraw.Draw(stars)
        
        for _ in range(2500):
            x = random.randint(0, 1280)
            y = random.randint(0, 720)
            size = random.randint(1, 3)
            alpha = random.randint(80, 220)
            sdraw.ellipse((x, y, x + size, y + size), fill=(255, 255, 255, alpha))
        
        stars = stars.filter(ImageFilter.GaussianBlur(0.4))
        bg = Image.alpha_composite(bg, stars)

        # === CARD with BORDER GLOW ===
        card_area = bg.crop((CARD_X, CARD_Y, CARD_X + CARD_W, CARD_Y + CARD_H))
        card_area = card_area.filter(ImageFilter.GaussianBlur(25))
        
        # Create card with border glow
        card_with_border = Image.new("RGBA", (CARD_W, CARD_H), (0, 0, 0, 0))
        border_layer = create_card_border_with_glow(
            (CARD_W, CARD_H), CARD_RADIUS, c_base, c_light, c_dark
        )
        
        # Paste blurred card area inside border
        card_mask = Image.new("L", (CARD_W, CARD_H), 0)
        ImageDraw.Draw(card_mask).rounded_rectangle(
            (10, 10, CARD_W - 10, CARD_H - 10),
            radius=max(CARD_RADIUS - 10, 4),
            fill=255
        )
        card_with_border.paste(card_area, (0, 0), card_mask)
        
        # Composite border
        card_final = Image.alpha_composite(card_with_border, border_layer)
        bg.paste(card_final, (CARD_X, CARD_Y), card_final)

        # === THUMBNAIL with SHADOW ===
        thumb_img = Image.open(thumb_path).convert("RGBA")
        thumb_img = thumb_img.resize((THUMB_SIZE, THUMB_SIZE), Image.LANCZOS)
        thumb_img = ImageEnhance.Brightness(thumb_img).enhance(1.1)

        # Create shadow
        shadow_layer = create_art_shadow(
            (1280, 720), THUMB_X, THUMB_Y, THUMB_SIZE, THUMB_SIZE,
            THUMB_RADIUS, c_base
        )
        bg = Image.alpha_composite(bg.convert("RGBA"), shadow_layer)

        # Thumbnail mask
        thumb_mask = Image.new("L", (THUMB_SIZE, THUMB_SIZE), 0)
        ImageDraw.Draw(thumb_mask).rounded_rectangle(
            (0, 0, THUMB_SIZE, THUMB_SIZE), radius=THUMB_RADIUS, fill=255
        )

        bg.paste(thumb_img, (THUMB_X, THUMB_Y), thumb_mask)

        # === TEXT ===
        draw = ImageDraw.Draw(bg)

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

        # === PROGRESS BAR ===
        bar_end = BAR_X + BAR_WIDTH
        progress = int(BAR_WIDTH * 0.35)

        draw.rounded_rectangle(
            [(BAR_X, BAR_Y), (bar_end, BAR_Y + BAR_HEIGHT)],
            radius=3, fill=(85, 85, 85)
        )
        draw.rounded_rectangle(
            [(BAR_X, BAR_Y), (BAR_X + progress, BAR_Y + BAR_HEIGHT)],
            radius=3, fill=c_base  # Use random palette color
        )

        cx, cy = BAR_X + progress, BAR_Y + BAR_HEIGHT // 2
        draw.ellipse([(cx - 7, cy - 7), (cx + 7, cy + 7)], fill="white")

        draw.text((BAR_X, BAR_Y + 17), "01:58", fill="white", font=time_font)
        total = duration_text if not is_live else "2:16"
        draw.text((bar_end - 40, BAR_Y + 17), total, fill="white", font=time_font)

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
        bg = bg.convert("RGB")
        bg.save(cache_path, "PNG", quality=95)

    except Exception as e:
        import traceback
        traceback.print_exc()
        return YOUTUBE_IMG_URL
    finally:
        try:
            if os.path.exists(thumb_path):
                os.remove(thumb_path)
        except OSError:
            pass

    return cache_path
