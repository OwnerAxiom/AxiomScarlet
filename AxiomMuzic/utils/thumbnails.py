# -----------------------------------------------
# 🔸 AxiomMusic Project - Neon Rainbow Thumbnail
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

# ===== LAYOUT CONSTANTS =====
CARD_W, CARD_H = 1050, 490
CARD_X = (1280 - CARD_W) // 2
CARD_Y = (720 - CARD_H) // 2
CARD_RADIUS = 60

THUMB_SIZE = 340
THUMB_X = CARD_X + 55
THUMB_Y = CARD_Y + 55
THUMB_RADIUS = 40

TITLE_X = THUMB_X + THUMB_SIZE + 60
TITLE_Y = CARD_Y + 110
META_Y = TITLE_Y + 65

BAR_Y = META_Y + 65
BAR_X = TITLE_X
BAR_WIDTH = 540
BAR_HEIGHT = 6

PILL_W = 380
PILL_H = 85
PILL_RADIUS = 42
PILL_X = TITLE_X
PILL_Y = BAR_Y + 55

MAX_TITLE_WIDTH = 580

# ===== RAINBOW COLORS (clockwise: pink→purple→blue→cyan→green→yellow→orange→pink) =====
RAINBOW_COLORS = [
    (255, 50, 150),   # Pink (top-left)
    (230, 60, 200),   # Hot pink
    (200, 70, 230),   # Magenta
    (170, 80, 255),   # Purple
    (130, 90, 255),   # Violet
    (100, 110, 255),  # Blue-purple
    (80, 140, 255),   # Blue
    (80, 180, 255),   # Light blue
    (80, 220, 240),   # Cyan-blue
    (80, 240, 220),   # Cyan
    (80, 255, 200),   # Cyan-green
    (120, 255, 170),  # Green-cyan
    (170, 255, 130),  # Light green
    (220, 255, 100),  # Lime
    (255, 250, 80),   # Yellow-lime
    (255, 230, 70),   # Yellow
    (255, 200, 60),   # Orange-yellow
    (255, 170, 60),   # Orange
    (255, 140, 70),   # Orange-red
    (255, 110, 90),   # Red-orange
    (255, 80, 110),   # Red-pink
    (255, 60, 130),   # Pink-red
    (255, 50, 150),   # Back to pink
]

def trim_text(text, font, max_width):
    if font.getlength(text) <= max_width:
        return text
    ellipsis = "…"
    for i in range(len(text) - 1, 0, -1):
        trimmed = text[:i] + ellipsis
        if font.getlength(trimmed) <= max_width:
            return trimmed
    return ellipsis

def create_rainbow_ring(size, radius, thickness=14, num_layers=40):
    """
    Create a smooth rainbow gradient ring with PROPERLY CURVED corners.
    Draws many thin concentric rounded rectangles, each with a different rainbow color.
    """
    w, h = size
    img = Image.new("RGBA", size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    num_colors = len(RAINBOW_COLORS)
    
    for i in range(num_layers):
        # Offset from outside
        offset = i * (thickness / num_layers)
        # Pick color based on position around the ring
        color_idx = int((i / num_layers) * (num_colors - 1))
        color = RAINBOW_COLORS[color_idx]
        
        layer_radius = radius - offset
        if layer_radius < 5:
            break
        
        # Each layer is 1-2 pixels thick for smooth gradient
        layer_width = max(1, int(thickness / num_layers) + 1)
        
        draw.rounded_rectangle(
            (offset, offset, w - offset, h - offset),
            radius=layer_radius,
            outline=color + (255,),
            width=layer_width
        )
    
    return img

def create_glow(ring_img, blur_amount=45):
    """Blur the ring to create glow effect"""
    return ring_img.filter(ImageFilter.GaussianBlur(blur_amount))

def create_sharp_rainbow_border(size, radius, thickness=3):
    """Sharp (non-blurred) rainbow border for crisp inner edge"""
    w, h = size
    img = Image.new("RGBA", size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    num_colors = len(RAINBOW_COLORS)
    
    for i in range(thickness):
        color_idx = int((i / thickness) * (num_colors - 1))
        color = RAINBOW_COLORS[color_idx]
        draw.rounded_rectangle(
            (i, i, w - i, h - i),
            radius=radius - i,
            outline=color + (255,),
            width=1
        )
    
    return img

# ===== ICON DRAWING FUNCTIONS =====

def draw_shuffle(draw, x, y, size, color):
    """Shuffle icon - crossed arrows"""
    s = size
    # Top arrow (left to right, going up)
    draw.line([(x, y + s*0.65), (x + s*0.7, y)], fill=color, width=2)
    draw.polygon([(x + s*0.7, y - s*0.05), (x + s*0.9, y + s*0.05), 
                  (x + s*0.7, y + s*0.2)], fill=color)
    # Bottom arrow (left to right, going down)
    draw.line([(x, y + s*0.35), (x + s*0.7, y + s)], fill=color, width=2)
    draw.polygon([(x + s*0.7, y + s*0.8), (x + s*0.9, y + s*0.95), 
                  (x + s*0.7, y + s*1.05)], fill=color)
    # Horizontal segments
    draw.line([(x + s*0.25, y), (x + s*0.75, y)], fill=color, width=2)
    draw.line([(x + s*0.25, y + s), (x + s*0.75, y + s)], fill=color, width=2)

def draw_prev(draw, x, y, size, color):
    """Previous track - triangle + bar"""
    s = size
    draw.polygon([(x + s*0.75, y), (x + s*0.75, y + s), (x, y + s*0.5)], fill=color)
    draw.rectangle([(x + s*0.85, y + s*0.1), (x + s, y + s*0.9)], fill=color)

def draw_play_button(draw, x, y, size, circle_color, triangle_color):
    """Large play button with circle background"""
    s = size
    # White circle
    draw.ellipse([(x, y), (x + s, y + s)], fill=circle_color)
    # Dark play triangle (slightly offset to look centered)
    draw.polygon([
        (x + s*0.42, y + s*0.25),
        (x + s*0.42, y + s*0.75),
        (x + s*0.72, y + s*0.5)
    ], fill=triangle_color)

def draw_next(draw, x, y, size, color):
    """Next track - bar + triangle"""
    s = size
    draw.rectangle([(x, y + s*0.1), (x + s*0.2, y + s*0.9)], fill=color)
    draw.polygon([(x + s*0.3, y), (x + s*0.3, y + s), (x + s, y + s*0.5)], fill=color)

def draw_repeat(draw, x, y, size, color):
    """Repeat icon - two curved arrows forming a loop"""
    s = size
    # Top arc going right
    draw.arc([(x, y), (x + s, y + s*0.65)], 180, 0, fill=color, width=2)
    draw.polygon([(x + s*0.85, y - s*0.05), (x + s*1.05, y + s*0.05), 
                  (x + s*0.9, y + s*0.2)], fill=color)
    # Bottom arc going left
    draw.arc([(x, y + s*0.35), (x + s, y + s)], 0, 180, fill=color, width=2)
    draw.polygon([(x + s*0.15, y + s*1.05), (x + s*0.0, y + s*0.95), 
                  (x + s*0.15, y + s*0.8)], fill=color)

# ===== MAIN THUMBNAIL GENERATOR =====

async def get_thumb(videoid: str) -> str:
    cache_path = os.path.join(CACHE_DIR, f"{videoid}_neon.png")
    
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
        
        # Enhance for vibrant look
        base_thumb = ImageEnhance.Brightness(base_thumb).enhance(1.25)
        base_thumb = ImageEnhance.Contrast(base_thumb).enhance(1.2)
        base_thumb = ImageEnhance.Color(base_thumb).enhance(1.3)
        
        # Heavy blur
        bg = base_thumb.filter(ImageFilter.GaussianBlur(25))
        
        # Dark overlay (darker so neon pops)
        dark = Image.new("RGBA", bg.size, (0, 0, 0, 140))
        bg = Image.alpha_composite(bg, dark)
        
        # === CARD (frosted glass) ===
        card_area = bg.crop((CARD_X, CARD_Y, CARD_X + CARD_W, CARD_Y + CARD_H))
        frosted = Image.new("RGBA", (CARD_W, CARD_H), (8, 8, 12, 110))
        card = Image.alpha_composite(card_area, frosted)
        card = card.filter(ImageFilter.GaussianBlur(1.5))
        
        mask = Image.new("L", (CARD_W, CARD_H), 0)
        ImageDraw.Draw(mask).rounded_rectangle((0, 0, CARD_W, CARD_H), radius=CARD_RADIUS, fill=255)
        bg.paste(card, (CARD_X, CARD_Y), mask)
        
        # === CARD RAINBOW GLOW ===
        glow_pad = 60
        glow_size = (CARD_W + glow_pad * 2, CARD_H + glow_pad * 2)
        rainbow_ring = create_rainbow_ring(glow_size, CARD_RADIUS + 35, thickness=18, num_layers=45)
        glow = create_glow(rainbow_ring, blur_amount=55)
        bg.paste(glow, (CARD_X - glow_pad, CARD_Y - glow_pad), glow)
        
        # Sharp inner rainbow border on card
        sharp_border = create_sharp_rainbow_border((CARD_W, CARD_H), CARD_RADIUS, thickness=3)
        bg.paste(sharp_border, (CARD_X, CARD_Y), sharp_border)
        
        # === THUMBNAIL ===
        thumb_img = Image.open(thumb_path).convert("RGBA")
        thumb_img = thumb_img.resize((THUMB_SIZE, THUMB_SIZE), Image.LANCZOS)
        thumb_img = ImageEnhance.Brightness(thumb_img).enhance(1.15)
        
        thumb_mask = Image.new("L", (THUMB_SIZE, THUMB_SIZE), 0)
        ImageDraw.Draw(thumb_mask).rounded_rectangle((0, 0, THUMB_SIZE, THUMB_SIZE), 
                                                      radius=THUMB_RADIUS, fill=255)
        
        # Thumbnail shadow
        shadow = Image.new("RGBA", (1280, 720), (0, 0, 0, 0))
        sd = ImageDraw.Draw(shadow)
        sd.rounded_rectangle(
            (THUMB_X - 10, THUMB_Y - 10, THUMB_X + THUMB_SIZE + 10, THUMB_Y + THUMB_SIZE + 10),
            radius=THUMB_RADIUS + 12, fill=(0, 0, 0, 160)
        )
        shadow = shadow.filter(ImageFilter.GaussianBlur(20))
        bg = Image.alpha_composite(bg, shadow)
        
        # Thumbnail rainbow glow
        t_glow_pad = 35
        t_glow_size = (THUMB_SIZE + t_glow_pad * 2, THUMB_SIZE + t_glow_pad * 2)
        t_ring = create_rainbow_ring(t_glow_size, THUMB_RADIUS + 22, thickness=12, num_layers=30)
        t_glow = create_glow(t_ring, blur_amount=38)
        bg.paste(t_glow, (THUMB_X - t_glow_pad, THUMB_Y - t_glow_pad), t_glow)
        
        # Thumbnail sharp border
        t_sharp = create_sharp_rainbow_border((THUMB_SIZE, THUMB_SIZE), THUMB_RADIUS, thickness=3)
        bg.paste(t_sharp, (THUMB_X, THUMB_Y), t_sharp)
        
        bg.paste(thumb_img, (THUMB_X, THUMB_Y), thumb_mask)
        
        # === TEXT ===
        draw = ImageDraw.Draw(bg)
        
        try:
            title_font = ImageFont.truetype("AxiomMuzic/assets/assets/font2.ttf", 42)
            meta_font = ImageFont.truetype("AxiomMuzic/assets/assets/font.ttf", 24)
            time_font = ImageFont.truetype("AxiomMuzic/assets/assets/font.ttf", 22)
        except OSError:
            title_font = ImageFont.load_default()
            meta_font = title_font
            time_font = title_font
        
        # Title (not uppercase - clean like reference)
        trimmed = trim_text(title, title_font, MAX_TITLE_WIDTH)
        draw.text((TITLE_X, TITLE_Y), trimmed, fill="white", font=title_font)
        
        # Meta
        draw.text((TITLE_X, META_Y), f"{channel}  |  {views}", 
                  fill=(180, 180, 180), font=meta_font)
        
        # === PROGRESS BAR ===
        bar_end = BAR_X + BAR_WIDTH
        progress = int(BAR_WIDTH * 0.32)
        
        draw.rounded_rectangle([(BAR_X, BAR_Y), (bar_end, BAR_Y + BAR_HEIGHT)],
                               radius=3, fill=(80, 80, 80))
        draw.rounded_rectangle([(BAR_X, BAR_Y), (BAR_X + progress, BAR_Y + BAR_HEIGHT)],
                               radius=3, fill=(60, 230, 120))
        
        cx, cy = BAR_X + progress, BAR_Y + BAR_HEIGHT // 2
        draw.ellipse([(cx - 9, cy - 9), (cx + 9, cy + 9)], fill="white")
        
        draw.text((BAR_X, BAR_Y + 22), "01:13", fill="white", font=time_font)
        total = duration_text if not is_live else "03:56"
        draw.text((bar_end - 50, BAR_Y + 22), total, fill="white", font=time_font)
        
        # === CONTROLS PILL (dark rounded container) ===
        pill = Image.new("RGBA", (PILL_W, PILL_H), (0, 0, 0, 0))
        pd = ImageDraw.Draw(pill)
        pd.rounded_rectangle((0, 0, PILL_W, PILL_H), radius=PILL_RADIUS, 
                             fill=(28, 28, 32, 210))
        pd.rounded_rectangle((1, 1, PILL_W - 1, PILL_H - 1), radius=PILL_RADIUS - 1,
                             outline=(55, 55, 65, 120), width=1)
        bg.paste(pill, (PILL_X, PILL_Y), pill)
        
        # Icons inside pill
        icon_y = PILL_Y + (PILL_H - 30) // 2
        icon_size = 28
        gap = 62
        sx = PILL_X + 28
        
        # Shuffle - white
        draw_shuffle(draw, sx, icon_y, icon_size, "white")
        # Previous - white
        draw_prev(draw, sx + gap, icon_y, icon_size, "white")
        # PLAY - LARGE with white circle (center focal point)
        play_size = 46
        play_y = PILL_Y + (PILL_H - play_size) // 2
        draw_play_button(draw, sx + gap * 2 - 3, play_y, play_size, "white", "black")
        # Next - white
        draw_next(draw, sx + gap * 3 + 5, icon_y, icon_size, "white")
        # Repeat - GREEN accent
        draw_repeat(draw, sx + gap * 4 + 10, icon_y, icon_size, (60, 230, 120))
        
        # === SAVE ===
        bg = bg.convert("RGB")
        bg.save(cache_path, "PNG", quality=95)
        
    except Exception as e:
        print(f"Error generating thumbnail: {e}")
        return YOUTUBE_IMG_URL
    finally:
        try:
            if os.path.exists(thumb_path):
                os.remove(thumb_path)
        except OSError:
            pass

    return cache_path
