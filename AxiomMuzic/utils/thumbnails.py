# -----------------------------------------------
# 🔸 AxiomMusic Project - Perfect Thumbnail
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

# ===== LAYOUT (Sanam Re sample exact) =====
CARD_W, CARD_H = 980, 470
CARD_X = (1280 - CARD_W) // 2
CARD_Y = (720 - CARD_H) // 2
CARD_RADIUS = 55

THUMB_SIZE = 320
THUMB_X = CARD_X + 55
THUMB_Y = CARD_Y + 55
THUMB_RADIUS = 35

TITLE_X = THUMB_X + THUMB_SIZE + 55
TITLE_Y = CARD_Y + 95
META_Y = TITLE_Y + 55

BAR_Y = META_Y + 60
BAR_X = TITLE_X
BAR_WIDTH = 510
BAR_HEIGHT = 5

PILL_W = 340
PILL_H = 75
PILL_RADIUS = 38
PILL_X = TITLE_X
PILL_Y = BAR_Y + 45

MAX_TITLE_WIDTH = 540


def trim_text(text, font, max_width):
    if font.getlength(text) <= max_width:
        return text
    for i in range(len(text) - 1, 0, -1):
        if font.getlength(text[:i] + "…") <= max_width:
            return text[:i] + "…"
    return "…"


def make_gradient_glow(size, radius, thickness=14, blur_amount=30):
    """
    Thick rainbow/multi-color glowing border.
    Colors: Pink → Purple → Blue → Cyan → Green → Yellow → Orange → Pink
    """
    w, h = size
    # Canvas bigger for glow
    pad = 80
    canvas = Image.new("RGBA", (w + pad * 2, h + pad * 2), (0, 0, 0, 0))
    draw = ImageDraw.Draw(canvas)

    # Rainbow colors in order (clockwise)
    colors = [
        (255, 60, 140),   # Pink
        (220, 60, 220),   # Magenta
        (140, 80, 255),   # Purple
        (80, 140, 255),   # Blue
        (60, 220, 240),   # Cyan
        (80, 240, 180),   # Green-cyan
        (160, 240, 80),   # Lime
        (240, 220, 60),   # Yellow
        (255, 160, 60),   # Orange
        (255, 100, 80),   # Red-orange
        (255, 60, 140),   # Back to pink
    ]

    num_layers = thickness * 4
    for i in range(num_layers):
        # Color interpolation
        t = i / num_layers
        idx = int(t * (len(colors) - 1))
        idx = min(idx, len(colors) - 2)
        frac = t * (len(colors) - 1) - idx
        c1, c2 = colors[idx], colors[idx + 1]
        r = int(c1[0] + (c2[0] - c1[0]) * frac)
        g = int(c1[1] + (c2[1] - c1[1]) * frac)
        b = int(c1[2] + (c2[2] - c1[2]) * frac)

        # Alpha: full in middle, fade at edges
        if i < num_layers // 3:
            alpha = int(255 * (i / (num_layers // 3)))
        elif i > num_layers * 2 // 3:
            alpha = int(255 * (1 - (i - num_layers * 2 // 3) / (num_layers // 3)))
        else:
            alpha = 255
        alpha = max(40, min(255, alpha))

        offset = pad + i * 0.6
        layer_r = radius + (thickness - i * 0.6)
        if layer_r < 5:
            break

        draw.rounded_rectangle(
            (int(offset), int(offset),
             int(w + pad * 2 - offset), int(h + pad * 2 - offset)),
            radius=int(layer_r),
            outline=(r, g, b, alpha),
            width=2
        )

    # Blur for glow
    glow = canvas.filter(ImageFilter.GaussianBlur(blur_amount))

    # Sharp inner border (3 thin layers)
    sharp = Image.new("RGBA", (w + pad * 2, h + pad * 2), (0, 0, 0, 0))
    sd = ImageDraw.Draw(sharp)
    sharp_colors = [(255, 60, 140), (140, 80, 255), (60, 220, 240), (160, 240, 80), (255, 160, 60)]
    for i in range(3):
        c = sharp_colors[i * 2 % len(sharp_colors)]
        offset = pad + thickness + i
        sd.rounded_rectangle(
            (int(offset), int(offset),
             int(w + pad * 2 - offset), int(h + pad * 2 - offset)),
            radius=int(radius - i),
            outline=c + (255,),
            width=1
        )

    return glow, sharp


# ===== ICONS (proper) =====

def icon_shuffle(draw, x, y, s, color):
    """Crossed arrows shuffle"""
    x, y, s = int(x), int(y), int(s)
    # Two parallel diagonal lines with arrow heads
    draw.line([(x, y + s//3), (x + s//2, y)], fill=color, width=2)
    draw.line([(x + s//4, y), (x + s*3//4, y)], fill=color, width=2)
    draw.polygon([(x + s//2, y), (x + s//2 + 6, y + 4), (x + s//2, y + 8)], fill=color)

    draw.line([(x, y + s*2//3), (x + s//2, y + s)], fill=color, width=2)
    draw.line([(x + s//4, y + s), (x + s*3//4, y + s)], fill=color, width=2)
    draw.polygon([(x + s//2, y + s), (x + s//2 + 6, y + s - 4), (x + s//2, y + s - 8)], fill=color)

    # Cross lines
    draw.line([(x + s//3, y + s//4), (x + s*3//4, y + s*3//4)], fill=color, width=2)
    draw.line([(x + s//3, y + s*3//4), (x + s*3//4, y + s//4)], fill=color, width=2)


def icon_prev(draw, x, y, s, color):
    x, y, s = int(x), int(y), int(s)
    # Triangle pointing left (filled)
    draw.polygon([(x + s*3//4, y + 3), (x + s*3//4, y + s - 3), (x + 3, y + s//2)], fill=color)
    # Vertical bar
    draw.rectangle([(x + s*4//5, y + 3), (x + s - 2, y + s - 3)], fill=color)


def icon_play(draw, x, y, s, circle, triangle):
    x, y, s = int(x), int(y), int(s)
    draw.ellipse([(x, y), (x + s, y + s)], fill=circle)
    # Triangle slightly right for visual center
    draw.polygon([
        (x + s*2//5, y + s//4),
        (x + s*2//5, y + s*3//4),
        (x + s*3//4, y + s//2)
    ], fill=triangle)


def icon_next(draw, x, y, s, color):
    x, y, s = int(x), int(y), int(s)
    draw.rectangle([(x + 2, y + 3), (x + s//5, y + s - 3)], fill=color)
    draw.polygon([(x + s//4, y + 3), (x + s//4, y + s - 3), (x + s - 3, y + s//2)], fill=color)


def icon_repeat(draw, x, y, s, color):
    x, y, s = int(x), int(y), int(s)
    # Top arc (going right)
    draw.arc([(x + 2, y + 2), (x + s - 2, y + s//2 + 2)], 180, 360, fill=color, width=2)
    draw.polygon([(x + s - 6, y + 2), (x + s - 2, y + 2), (x + s - 6, y + 8)], fill=color)
    # Bottom arc (going left)
    draw.arc([(x + 2, y + s//2 - 2), (x + s - 2, y + s - 2)], 0, 180, fill=color, width=2)
    draw.polygon([(x + 2, y + s - 2), (x + 6, y + s - 2), (x + 2, y + s - 8)], fill=color)


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
        # === BACKGROUND: thumbnail blurred (medium blur, not too much) ===
        base = Image.open(thumb_path).convert("RGBA")
        base = base.resize((1280, 720), Image.LANCZOS)

        # Brightness boost
        base = ImageEnhance.Brightness(base).enhance(1.2)
        base = ImageEnhance.Contrast(base).enhance(1.1)
        base = ImageEnhance.Color(base).enhance(1.15)

        # Medium blur (not too much)
        bg = base.filter(ImageFilter.GaussianBlur(12))

        # Darken slightly so card pops
        dark = Image.new("RGBA", bg.size, (0, 0, 0, 90))
        bg = Image.alpha_composite(bg, dark)

        # === CARD: dark frosted glass ===
        card_area = bg.crop((CARD_X, CARD_Y, CARD_X + CARD_W, CARD_Y + CARD_H))
        # Slight blur on card area for frosted effect
        card_area = card_area.filter(ImageFilter.GaussianBlur(4))
        frosted = Image.new("RGBA", (CARD_W, CARD_H), (10, 10, 15, 180))
        card = Image.alpha_composite(card_area, frosted)

        mask = Image.new("L", (CARD_W, CARD_H), 0)
        ImageDraw.Draw(mask).rounded_rectangle((0, 0, CARD_W, CARD_H), radius=CARD_RADIUS, fill=255)
        bg.paste(card, (CARD_X, CARD_Y), mask)

        # === CARD RAINBOW GLOW ===
        card_glow, card_sharp = make_gradient_glow(
            (CARD_W, CARD_H), CARD_RADIUS, thickness=12, blur_amount=35
        )
        bg.paste(card_glow, (CARD_X - 80, CARD_Y - 80), card_glow)
        bg.paste(card_sharp, (CARD_X - 80, CARD_Y - 80), card_sharp)

        # === THUMBNAIL ===
        thumb_img = Image.open(thumb_path).convert("RGBA")
        thumb_img = thumb_img.resize((THUMB_SIZE, THUMB_SIZE), Image.LANCZOS)
        thumb_img = ImageEnhance.Brightness(thumb_img).enhance(1.1)

        thumb_mask = Image.new("L", (THUMB_SIZE, THUMB_SIZE), 0)
        ImageDraw.Draw(thumb_mask).rounded_rectangle(
            (0, 0, THUMB_SIZE, THUMB_SIZE), radius=THUMB_RADIUS, fill=255
        )

        # Shadow
        shadow = Image.new("RGBA", (1280, 720), (0, 0, 0, 0))
        sd = ImageDraw.Draw(shadow)
        sd.rounded_rectangle(
            (THUMB_X - 10, THUMB_Y - 10,
             THUMB_X + THUMB_SIZE + 10, THUMB_Y + THUMB_SIZE + 10),
            radius=THUMB_RADIUS + 12, fill=(0, 0, 0, 150)
        )
        shadow = shadow.filter(ImageFilter.GaussianBlur(18))
        bg = Image.alpha_composite(bg, shadow)

        # Thumbnail rainbow glow
        t_glow, t_sharp = make_gradient_glow(
            (THUMB_SIZE, THUMB_SIZE), THUMB_RADIUS, thickness=10, blur_amount=28
        )
        bg.paste(t_glow, (THUMB_X - 80, THUMB_Y - 80), t_glow)
        bg.paste(t_sharp, (THUMB_X - 80, THUMB_Y - 80), t_sharp)

        bg.paste(thumb_img, (THUMB_X, THUMB_Y), thumb_mask)

        # === TEXT ===
        draw = ImageDraw.Draw(bg)

        try:
            title_font = ImageFont.truetype("AxiomMuzic/assets/assets/font2.ttf", 42)
            meta_font = ImageFont.truetype("AxiomMuzic/assets/assets/font.ttf", 22)
            time_font = ImageFont.truetype("AxiomMuzic/assets/assets/font.ttf", 20)
        except OSError:
            title_font = ImageFont.load_default()
            meta_font = title_font
            time_font = title_font

        trimmed = trim_text(title, title_font, MAX_TITLE_WIDTH)
        draw.text((TITLE_X, TITLE_Y), trimmed, fill="white", font=title_font)
        draw.text((TITLE_X, META_Y), f"{channel}  |  {views}",
                  fill=(170, 170, 170), font=meta_font)

        # === PROGRESS BAR ===
        bar_end = BAR_X + BAR_WIDTH
        progress = int(BAR_WIDTH * 0.30)

        # Background track
        draw.rounded_rectangle(
            [(BAR_X, BAR_Y), (bar_end, BAR_Y + BAR_HEIGHT)],
            radius=3, fill=(70, 70, 70)
        )
        # Progress fill (bright green)
        draw.rounded_rectangle(
            [(BAR_X, BAR_Y), (BAR_X + progress, BAR_Y + BAR_HEIGHT)],
            radius=3, fill=(60, 230, 110)
        )
        # White circle indicator
        cx, cy = BAR_X + progress, BAR_Y + BAR_HEIGHT // 2
        draw.ellipse([(cx - 8, cy - 8), (cx + 8, cy + 8)], fill="white")

        # Times
        draw.text((BAR_X, BAR_Y + 18), "01:13", fill="white", font=time_font)
        total = duration_text if not is_live else "4:30"
        draw.text((bar_end - 42, BAR_Y + 18), total, fill="white", font=time_font)

        # === CONTROL PILL ===
        pill = Image.new("RGBA", (PILL_W, PILL_H), (0, 0, 0, 0))
        pd = ImageDraw.Draw(pill)
        pd.rounded_rectangle((0, 0, PILL_W, PILL_H), radius=PILL_RADIUS,
                             fill=(25, 25, 30, 230))
        pd.rounded_rectangle((1, 1, PILL_W - 1, PILL_H - 1), radius=PILL_RADIUS - 1,
                             outline=(50, 50, 60, 180), width=1)
        bg.paste(pill, (PILL_X, PILL_Y), pill)

        # Icons inside pill - properly spaced
        icon_y = PILL_Y + (PILL_H - 26) // 2
        icon_size = 24
        sx = PILL_X + 28
        gap = 58

        # Shuffle (white)
        icon_shuffle(draw, sx, icon_y, icon_size, "white")
        # Previous (white)
        icon_prev(draw, sx + gap, icon_y, icon_size, "white")
        # Play (large white circle, dark triangle)
        play_size = 42
        play_y = PILL_Y + (PILL_H - play_size) // 2
        icon_play(draw, sx + gap * 2 + 2, play_y, play_size, "white", (20, 20, 25))
        # Next (white)
        icon_next(draw, sx + gap * 3 + 6, icon_y, icon_size, "white")
        # Repeat (GREEN)
        icon_repeat(draw, sx + gap * 4 + 10, icon_y, icon_size, (60, 230, 110))

        # === SAVE ===
        bg = bg.convert("RGB")
        bg.save(cache_path, "PNG", quality=95)

    except Exception as e:
        print(f"Error: {e}")
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
