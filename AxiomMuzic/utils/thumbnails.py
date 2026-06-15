# -----------------------------------------------
# 🔸 AxiomMusic Project - Transparent Card with Curved Glow
# 🔹 Card transparent + blur, border pe curved glow
# 📅 Copyright © 2026 – All Rights Reserved
# -----------------------------------------------

import os
import re
import random
import colorsys
import aiofiles
import aiohttp
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
THUMB_X = CARD_X + 65
THUMB_Y = CARD_Y + 85
THUMB_RADIUS = 35

TITLE_X = THUMB_X + THUMB_SIZE + 60
TITLE_Y = CARD_Y + 95
META_Y = TITLE_Y + 55

BAR_WIDTH = 480
BAR_HEIGHT = 5
BAR_X = TITLE_X
BAR_Y = META_Y + 70

CONTROLS_Y = BAR_Y + 60
CONTROLS_X = TITLE_X + 20

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
    h = random.random()
    if 0.08 < h < 0.16:
        h += 0.15
    if 0.45 < h < 0.52:
        h += 0.08
    h %= 1.0
    s = random.uniform(0.75, 1.0)
    v = random.uniform(0.8, 1.0)
    base = tuple(int(x * 255) for x in colorsys.hsv_to_rgb(h, s, v))
    light = tuple(int(x * 255) for x in colorsys.hsv_to_rgb(h, random.uniform(0.25, 0.5), 1.0))
    dark = tuple(int(x * 255) for x in colorsys.hsv_to_rgb(h, 1.0, random.uniform(0.18, 0.35)))
    return base, light, dark


def create_curved_glow_border(size, radius, c_base, c_light, c_dark):
    """CURVED glow + shadow around card border - NO black background"""
    try:
        w, h = size
        layer = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        draw = ImageDraw.Draw(layer)
        
        # OUTER WHITE GLOW (curved)
        for i in range(30, 0, -2):
            alpha = int(70 * (1 - i / 30) ** 1.5)
            draw.rounded_rectangle(
                [-i, -i, w + i, h + i],
                radius=radius + i,
                fill=(255, 255, 255, alpha)
            )
        
        # COLOR GLOW (curved)
        for i in range(20, 0, -2):
            alpha = int(90 * (1 - i / 20) ** 1.4)
            draw.rounded_rectangle(
                [-i, -i, w + i, h + i],
                radius=radius + i,
                fill=(*c_base, alpha)
            )
        
        # THIN BORDER LINES (curved)
        draw.rounded_rectangle(
            [0, 0, w, h],
            radius=radius,
            outline=(*c_light, 200),
            width=2
        )
        
        draw.rounded_rectangle(
            [2, 2, w - 2, h - 2],
            radius=radius - 2,
            outline=(*c_base, 255),
            width=2
        )
        
        # Blur for smooth glow
        return layer.filter(ImageFilter.GaussianBlur(4))

    except Exception as e:
        print(f"Glow error: {e}")
        return Image.new("RGBA", size, (0, 0, 0, 0))


def create_thumb_curved_shadow(size, x, y, w, h, radius, c_base):
    """Thumbnail shadow + glow with curves"""
    shadow_layer = Image.new("RGBA", size, (0, 0, 0, 0))
    sd = ImageDraw.Draw(shadow_layer)
    
    off_x, off_y = 8, 12
    
    # Black shadow (curved)
    for i in range(35, 0, -1):
        alpha = int(180 * (1 - i / 35) ** 1.3)
        sd.rounded_rectangle(
            [x + off_x - i, y + off_y - i, x + w + off_x + i, y + h + off_y + i],
            radius=radius + i,
            fill=(0, 0, 0, alpha)
        )
    
    # Color glow (curved)
    for i in range(15, 0, -1):
        alpha = int(80 * (1 - i / 15) ** 1.5)
        sd.rounded_rectangle(
            [x - i, y - i, x + w + i, y + h + i],
            radius=radius + i,
            fill=(*c_base, alpha)
        )
    
    return shadow_layer.filter(ImageFilter.GaussianBlur(15))


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
    except Exception as e:
        print(f"Fetch error: {e}")
        return YOUTUBE_IMG_URL

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
    except Exception as e:
        print(f"Download error: {e}")
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
        bg = base.filter(ImageFilter.GaussianBlur(8))
        dark = Image.new("RGBA", bg.size, (0, 0, 0, 70))
        bg = Image.alpha_composite(bg, dark)

        # === CARD: TRANSPARENT + BLUR (NO BLACK!) ===
        card_area = bg.crop((CARD_X, CARD_Y, CARD_X + CARD_W, CARD_Y + CARD_H))
        card_area = card_area.filter(ImageFilter.GaussianBlur(25))
        # Card ko transparent hi rakhna hai - no black background!
        card = card_area.convert("RGBA")

        mask = Image.new("L", (CARD_W, CARD_H), 0)
        ImageDraw.Draw(mask).rounded_rectangle((0, 0, CARD_W, CARD_H), radius=CARD_RADIUS, fill=255)
        bg.paste(card, (CARD_X, CARD_Y), mask)

        # === CARD BORDER PE CURVED GLOW + SHADOW ===
        card_glow = create_curved_glow_border(
            (CARD_W, CARD_H), CARD_RADIUS, c_base, c_light, c_dark
        )
        bg.paste(card_glow, (CARD_X, CARD_Y), card_glow)

        # === THUMBNAIL with CURVED SHADOW + GLOW ===
        thumb_img = Image.open(thumb_path).convert("RGBA")
        thumb_img = thumb_img.resize((THUMB_SIZE, THUMB_SIZE), Image.LANCZOS)
        thumb_img = ImageEnhance.Brightness(thumb_img).enhance(1.1)

        thumb_shadow = create_thumb_curved_shadow(
            (1280, 720), THUMB_X, THUMB_Y, THUMB_SIZE, THUMB_SIZE, THUMB_RADIUS, c_base
        )
        bg = Image.alpha_composite(bg.convert("RGBA"), thumb_shadow)

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
            radius=3, fill=c_base
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
