# -----------------------------------------------
#  AxiomMusic Project - PERFECT Rainbow Glow
# 🔹 Developed & Maintained by: Axiom Bots (https://t.me/axiombots)
# 📅 Copyright © 2026 – All Rights Reserved
# -----------------------------------------------

import os
import re
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
THUMB_X = CARD_X + 55
THUMB_Y = CARD_Y + 65
THUMB_RADIUS = 35

TITLE_X = THUMB_X + THUMB_SIZE + 60
TITLE_Y = CARD_Y + 80
META_Y = TITLE_Y + 60

# Bar - RIGHT SIDE
BAR_WIDTH = 500
BAR_HEIGHT = 5
BAR_X = TITLE_X
BAR_Y = META_Y + 70

# Controls - MORE RIGHT aur NICHE
CONTROLS_Y = BAR_Y + 65  # Zyada niche
CONTROLS_X = TITLE_X + 10  # Thoda right

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


def create_rainbow_border_glow(size, radius, thickness=40, glow_size=120):
    """VERY STRONG VISIBLE RAINBOW GLOW"""
    try:
        w, h = size
        pad = glow_size
        canvas = Image.new("RGBA", (w + pad * 2, h + pad * 2), (0, 0, 0, 0))
        draw = ImageDraw.Draw(canvas)

        colors = [
            (255, 40, 120),
            (220, 40, 220),
            (140, 60, 255),
            (70, 120, 255),
            (40, 200, 255),
            (50, 230, 170),
            (140, 240, 60),
            (240, 210, 40),
            (255, 150, 40),
            (255, 80, 60),
            (255, 40, 120),
        ]

        num_layers = 150
        for i in range(num_layers):
            t = i / num_layers
            idx = int(t * (len(colors) - 1))
            idx = min(idx, len(colors) - 2)
            frac = t * (len(colors) - 1) - idx
            c1, c2 = colors[idx], colors[idx + 1]
            r = int(c1[0] + (c2[0] - c1[0]) * frac)
            g = int(c1[1] + (c2[1] - c1[1]) * frac)
            b = int(c1[2] + (c2[2] - c1[2]) * frac)

            alpha = 255

            offset = pad + (i * thickness / num_layers)
            layer_r = radius + thickness - (i * thickness / num_layers)
            if layer_r < 5:
                break

            draw.rounded_rectangle(
                (int(offset), int(offset),
                 int(w + pad * 2 - offset), int(h + pad * 2 - offset)),
                radius=int(layer_r),
                outline=(r, g, b, alpha),
                width=6
            )

        glow = canvas.filter(ImageFilter.GaussianBlur(5))
        return glow

    except Exception as e:
        print(f"Glow error: {e}")
        return Image.new("RGBA", (size[0] + 300, size[1] + 300), (0, 0, 0, 0))


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
        return cache_path

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
        # === BACKGROUND ===
        base = Image.open(thumb_path).convert("RGBA")
        base = base.resize((1280, 720), Image.LANCZOS)
        base = ImageEnhance.Brightness(base).enhance(1.35)
        base = ImageEnhance.Contrast(base).enhance(1.15)
        base = ImageEnhance.Color(base).enhance(1.2)
        bg = base.filter(ImageFilter.GaussianBlur(8))
        dark = Image.new("RGBA", bg.size, (0, 0, 0, 70))
        bg = Image.alpha_composite(bg, dark)

        # === CARD: FULLY TRANSPARENT with HIGH BLUR ===
        card_area = bg.crop((CARD_X, CARD_Y, CARD_X + CARD_W, CARD_Y + CARD_H))
        card_area = card_area.filter(ImageFilter.GaussianBlur(25))
        card = card_area.convert("RGBA")

        mask = Image.new("L", (CARD_W, CARD_H), 0)
        ImageDraw.Draw(mask).rounded_rectangle((0, 0, CARD_W, CARD_H), radius=CARD_RADIUS, fill=255)
        bg.paste(card, (CARD_X, CARD_Y), mask)

        # === CARD RAINBOW GLOW ON BORDER - STRONG ===
        card_glow = create_rainbow_border_glow(
            (CARD_W, CARD_H), CARD_RADIUS, thickness=40, glow_size=120
        )
        bg.paste(card_glow, (CARD_X - 120, CARD_Y - 120), card_glow)

        # === THUMBNAIL ===
        thumb_img = Image.open(thumb_path).convert("RGBA")
        thumb_img = thumb_img.resize((THUMB_SIZE, THUMB_SIZE), Image.LANCZOS)
        thumb_img = ImageEnhance.Brightness(thumb_img).enhance(1.1)

        thumb_mask = Image.new("L", (THUMB_SIZE, THUMB_SIZE), 0)
        ImageDraw.Draw(thumb_mask).rounded_rectangle(
            (0, 0, THUMB_SIZE, THUMB_SIZE), radius=THUMB_RADIUS, fill=255
        )

        shadow = Image.new("RGBA", (1280, 720), (0, 0, 0, 0))
        sd = ImageDraw.Draw(shadow)
        sd.rounded_rectangle(
            (THUMB_X - 8, THUMB_Y - 8,
             THUMB_X + THUMB_SIZE + 8, THUMB_Y + THUMB_SIZE + 8),
            radius=THUMB_RADIUS + 10, fill=(0, 0, 0, 140)
        )
        shadow = shadow.filter(ImageFilter.GaussianBlur(16))
        bg = Image.alpha_composite(bg, shadow)

        # Thumbnail rainbow glow - STRONG
        t_glow = create_rainbow_border_glow(
            (THUMB_SIZE, THUMB_SIZE), THUMB_RADIUS, thickness=30, glow_size=90
        )
        bg.paste(t_glow, (THUMB_X - 90, THUMB_Y - 90), t_glow)

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
            radius=3, fill=(90, 230, 80)
        )

        cx, cy = BAR_X + progress, BAR_Y + BAR_HEIGHT // 2
        draw.ellipse([(cx - 7, cy - 7), (cx + 7, cy + 7)], fill="white")

        draw.text((BAR_X, BAR_Y + 17), "01:58", fill="white", font=time_font)
        total = duration_text if not is_live else "2:16"
        draw.text((bar_end - 40, BAR_Y + 17), total, fill="white", font=time_font)

        # === CONTROLS - RIGHT aur NICHE ===
        icon_y = CONTROLS_Y
        icon_size = 26
        sx = CONTROLS_X
        gap = 45

        icon_shuffle(draw, sx, icon_y, icon_size, (80, 255, 140))
        icon_repeat(draw, sx + gap, icon_y, icon_size, (255, 210, 70))
        icon_prev(draw, sx + gap * 2, icon_y, icon_size, "white")
        icon_pause(draw, sx + gap * 3, icon_y, icon_size, "white")
        icon_next(draw, sx + gap * 4, icon_y, icon_size, "white")
        icon_heart(draw, sx + gap * 5, icon_y, icon_size, (255, 70, 70))
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
