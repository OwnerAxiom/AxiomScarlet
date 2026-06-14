# -----------------------------------------------
# 🔸 AxiomMusic Project - RAINBOW NEON THUMBNAIL
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
CARD_W, CARD_H = 1000, 480
CARD_X = (1280 - CARD_W) // 2
CARD_Y = (720 - CARD_H) // 2
CARD_RADIUS = 55

THUMB_SIZE = 320
THUMB_X = CARD_X + 60
THUMB_Y = CARD_Y + 60
THUMB_RADIUS = 35

TITLE_X = THUMB_X + THUMB_SIZE + 50
TITLE_Y = CARD_Y + 100
META_Y = TITLE_Y + 60

BAR_Y = META_Y + 60
BAR_X = TITLE_X
BAR_WIDTH = 520
BAR_HEIGHT = 6

PILL_W = 360
PILL_H = 80
PILL_RADIUS = 40
PILL_X = TITLE_X
PILL_Y = BAR_Y + 50

MAX_TITLE_WIDTH = 560

def trim_text(text, font, max_width):
    if font.getlength(text) <= max_width:
        return text
    for i in range(len(text) - 1, 0, -1):
        if font.getlength(text[:i] + "…") <= max_width:
            return text[:i] + "…"
    return "…"

def draw_rainbow_border(draw, size, radius, thickness=12):
    """
    Draw THICK rainbow neon border with smooth color transitions
    Colors flow: Pink→Purple→Blue→Cyan→Green→Yellow→Orange→Pink
    """
    w, h = size
    
    # Define rainbow colors in order (clockwise from top-left)
    rainbow = [
        (255, 0, 128),    # Pink (top-left corner)
        (200, 0, 255),    # Purple (going right)
        (100, 100, 255),  # Blue (top-right)
        (0, 200, 255),    # Cyan (going down)
        (0, 255, 128),    # Green (right side)
        (150, 255, 50),   # Lime (going down)
        (255, 200, 0),    # Yellow/Orange (bottom-right)
        (255, 100, 0),    # Orange (going left)
        (255, 50, 80),    # Red-Pink (bottom-left)
        (255, 0, 128),    # Back to Pink (completing loop)
    ]
    
    # Draw multiple concentric rounded rectangles for smooth gradient
    for layer in range(thickness * 3):  # More layers = smoother
        # Calculate which color segment we're in
        progress = layer / (thickness * 3)
        color_idx = int(progress * (len(rainbow) - 1))
        color_idx = min(color_idx, len(rainbow) - 2)
        
        # Interpolate between colors
        t = (progress * (len(rainbow) - 1)) - color_idx
        c1 = rainbow[color_idx]
        c2 = rainbow[color_idx + 1]
        
        r = int(c1[0] + (c2[0] - c1[0]) * t)
        g = int(c1[1] + (c2[1] - c1[1]) * t)
        b = int(c1[2] + (c2[2] - c1[2]) * t)
        
        # Alpha decreases for outer glow
        alpha = 255 if layer < thickness else int(255 * (1 - (layer - thickness) / thickness))
        if alpha < 50:
            alpha = 50
        
        offset = layer * 0.5
        layer_radius = radius + thickness - layer * 0.5
        
        if layer_radius < 10:
            break
        
        draw.rounded_rectangle(
            (int(offset), int(offset), 
             int(w - offset), int(h - offset)),
            radius=int(layer_radius),
            outline=(r, g, b, alpha),
            width=1
        )

def create_glowing_card(size, radius):
    """Create card with intense rainbow neon glow"""
    w, h = size
    
    # Create glow layer (bigger than card)
    glow_size = (w + 120, h + 120)
    glow = Image.new("RGBA", glow_size, (0, 0, 0, 0))
    glow_draw = ImageDraw.Draw(glow)
    
    # Draw rainbow border on glow layer
    draw_rainbow_border(glow_draw, glow_size, radius + 60, thickness=15)
    
    # Heavy blur for neon glow effect
    glow = glow.filter(ImageFilter.GaussianBlur(35))
    
    # Create sharp inner border
    sharp = Image.new("RGBA", size, (0, 0, 0, 0))
    sharp_draw = ImageDraw.Draw(sharp)
    
    # Sharp rainbow border (3 layers)
    rainbow_sharp = [
        (255, 0, 128), (100, 100, 255), (0, 255, 128),
        (255, 200, 0), (255, 50, 80)
    ]
    
    for i in range(3):
        color = rainbow_sharp[i % len(rainbow_sharp)]
        sharp_draw.rounded_rectangle(
            (i, i, w - i, h - i),
            radius=radius - i,
            outline=color + (255,),
            width=1
        )
    
    return glow, sharp

# ===== ICONS =====

def draw_shuffle(draw, x, y, size, color):
    s = int(size)
    x, y = int(x), int(y)
    draw.line([(x, y + s//2), (x + s//3, y)], fill=color, width=2)
    draw.line([(x, y + s//2), (x + s//3, y + s)], fill=color, width=2)
    draw.line([(x + s//4, y), (x + s*3//4, y)], fill=color, width=2)
    draw.line([(x + s//4, y + s), (x + s*3//4, y + s)], fill=color, width=2)
    draw.polygon([(x + s//3, y), (x + s//3 + 5, y + 4), (x + s//3, y + 8)], fill=color)
    draw.polygon([(x + s//3, y + s), (x + s//3 + 5, y + s - 4), (x + s//3, y + s - 8)], fill=color)

def draw_prev(draw, x, y, size, color):
    s = int(size)
    x, y = int(x), int(y)
    draw.polygon([(x + s*3//4, y + 2), (x + s*3//4, y + s - 2), (x + 2, y + s//2)], fill=color)
    draw.rectangle([(x + s*4//5, y + 4), (x + s, y + s - 4)], fill=color)

def draw_play(draw, x, y, size, circle_color, triangle_color):
    s = int(size)
    x, y = int(x), int(y)
    draw.ellipse([(x, y), (x + s, y + s)], fill=circle_color)
    draw.polygon([
        (x + s*2//5, y + s//4),
        (x + s*2//5, y + s*3//4),
        (x + s*3//4, y + s//2)
    ], fill=triangle_color)

def draw_next(draw, x, y, size, color):
    s = int(size)
    x, y = int(x), int(y)
    draw.rectangle([(x, y + 4), (x + s//5, y + s - 4)], fill=color)
    draw.polygon([(x + s//4, y + 2), (x + s//4, y + s - 2), (x + s - 2, y + s//2)], fill=color)

def draw_repeat(draw, x, y, size, color):
    s = int(size)
    x, y = int(x), int(y)
    draw.arc([(x, y), (x + s, y + s//2)], 180, 0, fill=color, width=2)
    draw.polygon([(x + s - 4, y), (x + s + 4, y + 4), (x + s - 4, y + 8)], fill=color)
    draw.arc([(x, y + s//2), (x + s, y + s)], 0, 180, fill=color, width=2)
    draw.polygon([(x + 4, y + s), (x - 4, y + s - 4), (x + 4, y + s - 8)], fill=color)

# ===== MAIN =====

async def get_thumb(videoid: str) -> str:
    cache_path = os.path.join(CACHE_DIR, f"{videoid}_rainbow.png")
    
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
        base_thumb = Image.open(thumb_path).convert("RGBA")
        base_thumb = base_thumb.resize((1280, 720), Image.LANCZOS)
        
        bg = base_thumb.filter(ImageFilter.GaussianBlur(30))
        bg = ImageEnhance.Brightness(bg).enhance(0.3)
        bg = ImageEnhance.Contrast(bg).enhance(1.5)
        
        dark = Image.new("RGBA", bg.size, (0, 0, 0, 180))
        bg = Image.alpha_composite(bg, dark)
        
        # === CARD ===
        card_area = bg.crop((CARD_X, CARD_Y, CARD_X + CARD_W, CARD_Y + CARD_H))
        frosted = Image.new("RGBA", (CARD_W, CARD_H), (5, 5, 8, 200))
        card = Image.alpha_composite(card_area, frosted)
        
        mask = Image.new("L", (CARD_W, CARD_H), 0)
        ImageDraw.Draw(mask).rounded_rectangle((0, 0, CARD_W, CARD_H), radius=CARD_RADIUS, fill=255)
        bg.paste(card, (CARD_X, CARD_Y), mask)
        
        # === CARD RAINBOW NEON GLOW ===
        card_glow, card_sharp = create_glowing_card((CARD_W, CARD_H), CARD_RADIUS)
        bg.paste(card_glow, (CARD_X - 60, CARD_Y - 60), card_glow)
        bg.paste(card_sharp, (CARD_X, CARD_Y), card_sharp)
        
        # === THUMBNAIL ===
        thumb_img = Image.open(thumb_path).convert("RGBA")
        thumb_img = thumb_img.resize((THUMB_SIZE, THUMB_SIZE), Image.LANCZOS)
        
        thumb_mask = Image.new("L", (THUMB_SIZE, THUMB_SIZE), 0)
        ImageDraw.Draw(thumb_mask).rounded_rectangle(
            (0, 0, THUMB_SIZE, THUMB_SIZE), radius=THUMB_RADIUS, fill=255
        )
        
        # Shadow
        shadow = Image.new("RGBA", (1280, 720), (0, 0, 0, 0))
        sd = ImageDraw.Draw(shadow)
        sd.rounded_rectangle(
            (THUMB_X - 8, THUMB_Y - 8, 
             THUMB_X + THUMB_SIZE + 8, THUMB_Y + THUMB_SIZE + 8),
            radius=THUMB_RADIUS + 10, fill=(0, 0, 0, 180)
        )
        shadow = shadow.filter(ImageFilter.GaussianBlur(20))
        bg = Image.alpha_composite(bg, shadow)
        
        # Thumbnail rainbow glow
        thumb_glow, thumb_sharp = create_glowing_card((THUMB_SIZE, THUMB_SIZE), THUMB_RADIUS)
        bg.paste(thumb_glow, (THUMB_X - 60, THUMB_Y - 60), thumb_glow)
        bg.paste(thumb_sharp, (THUMB_X, THUMB_Y), thumb_sharp)
        
        bg.paste(thumb_img, (THUMB_X, THUMB_Y), thumb_mask)
        
        # === TEXT ===
        draw = ImageDraw.Draw(bg)
        
        try:
            title_font = ImageFont.truetype("AxiomMuzic/assets/assets/font2.ttf", 40)
            meta_font = ImageFont.truetype("AxiomMuzic/assets/assets/font.ttf", 22)
            time_font = ImageFont.truetype("AxiomMuzic/assets/assets/font.ttf", 20)
        except OSError:
            title_font = ImageFont.load_default()
            meta_font = title_font
            time_font = title_font
        
        trimmed = trim_text(title, title_font, MAX_TITLE_WIDTH)
        draw.text((TITLE_X, TITLE_Y), trimmed, fill="white", font=title_font)
        draw.text((TITLE_X, META_Y), f"{channel}  |  {views}", 
                  fill=(160, 160, 160), font=meta_font)
        
        # === PROGRESS BAR ===
        bar_end = BAR_X + BAR_WIDTH
        progress = int(BAR_WIDTH * 0.32)
        
        draw.rounded_rectangle([(BAR_X, BAR_Y), (bar_end, BAR_Y + BAR_HEIGHT)],
                               radius=3, fill=(60, 60, 60))
        draw.rounded_rectangle([(BAR_X, BAR_Y), (BAR_X + progress, BAR_Y + BAR_HEIGHT)],
                               radius=3, fill=(50, 230, 100))
        
        cx, cy = BAR_X + progress, BAR_Y + BAR_HEIGHT // 2
        draw.ellipse([(cx - 8, cy - 8), (cx + 8, cy + 8)], fill="white")
        
        draw.text((BAR_X, BAR_Y + 20), "01:13", fill="white", font=time_font)
        total = duration_text if not is_live else "03:56"
        draw.text((bar_end - 45, BAR_Y + 20), total, fill="white", font=time_font)
        
        # === CONTROL PILL ===
        pill = Image.new("RGBA", (PILL_W, PILL_H), (0, 0, 0, 0))
        pd = ImageDraw.Draw(pill)
        pd.rounded_rectangle((0, 0, PILL_W, PILL_H), radius=PILL_RADIUS, 
                             fill=(20, 20, 25, 220))
        pd.rounded_rectangle((1, 1, PILL_W - 1, PILL_H - 1), radius=PILL_RADIUS - 1,
                             outline=(40, 40, 50, 150), width=1)
        bg.paste(pill, (PILL_X, PILL_Y), pill)
        
        icon_y = PILL_Y + (PILL_H - 28) // 2
        icon_size = 26
        gap = 60
        sx = PILL_X + 30
        
        draw_shuffle(draw, sx, icon_y, icon_size, "white")
        draw_prev(draw, sx + gap, icon_y, icon_size, "white")
        
        play_size = 44
        play_y = PILL_Y + (PILL_H - play_size) // 2
        draw_play(draw, sx + gap * 2, play_y, play_size, "white", (15, 15, 20))
        
        draw_next(draw, sx + gap * 3 + 8, icon_y, icon_size, "white")
        draw_repeat(draw, sx + gap * 4 + 16, icon_y, icon_size, (50, 230, 100))
        
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
