# -----------------------------------------------
# 🔸 AxiomMusic Project - Premium Thumbnail Generator
# 🔹 Developed & Maintained by: Axiom Bots (https://t.me/axiombots)
#  Copyright © 2026 – All Rights Reserved
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

# Panel dimensions
PANEL_W, PANEL_H = 920, 440
PANEL_X = (1280 - PANEL_W) // 2
PANEL_Y = 140
PANEL_RADIUS = 45

# Thumbnail
THUMB_SIZE = 310
THUMB_X = PANEL_X + 45
THUMB_Y = PANEL_Y + 60
THUMB_RADIUS = 28

# Text positions
TITLE_X = THUMB_X + THUMB_SIZE + 55
TITLE_Y = THUMB_Y + 35
META_Y = TITLE_Y + 50

# Progress bar
BAR_Y = META_Y + 60
BAR_X = TITLE_X
BAR_WIDTH = 460
BAR_HEIGHT = 5

# Icons
ICONS_Y = BAR_Y + 45
ICONS_X = TITLE_X

MAX_TITLE_WIDTH = 480

def trim_text(text: str, font: ImageFont.FreeTypeFont, max_width: int) -> str:
    if font.getlength(text) <= max_width:
        return text
    ellipsis = "…"
    for i in range(len(text) - 1, 0, -1):
        trimmed = text[:i] + ellipsis
        if font.getlength(trimmed) <= max_width:
            return trimmed
    return ellipsis

def create_curved_glow(size, colors, radius, blur_amount, spread=25):
    """Create a PROPERLY CURVED glow border with rounded corners"""
    width, height = size
    # Make canvas bigger to fit glow
    canvas_size = (width + spread * 2, height + spread * 2)
    img = Image.new("RGBA", canvas_size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # Draw multiple rounded rectangles with increasing radius
    for i, color in enumerate(colors):
        offset = i * 4
        alpha = 200 - (i * 40)
        if alpha < 80:
            alpha = 80
        
        # Each layer has properly curved corners
        layer_radius = radius + offset + 5
        draw.rounded_rectangle(
            (offset, offset, canvas_size[0] - offset, canvas_size[1] - offset),
            radius=layer_radius,
            outline=color + (alpha,),
            width=6
        )
    
    # Blur for smooth glow
    return img.filter(ImageFilter.GaussianBlur(blur_amount))

def draw_icon_shuffle(draw, x, y, color):
    """Draw shuffle icon properly"""
    # Two crossing arrows
    draw.line([(x, y+14), (x+10, y+4)], fill=color, width=2)
    draw.polygon([(x+10, y+2), (x+14, y+4), (x+10, y+6)], fill=color)
    draw.line([(x, y+14), (x+10, y+24)], fill=color, width=2)
    draw.polygon([(x+10, y+22), (x+14, y+24), (x+10, y+26)], fill=color)
    draw.line([(x+8, y+4), (x+20, y+4)], fill=color, width=2)
    draw.line([(x+8, y+24), (x+20, y+24)], fill=color, width=2)

def draw_icon_repeat(draw, x, y, color):
    """Draw repeat icon properly"""
    # Curved arrow forming a loop
    draw.arc([(x, y+2), (x+22, y+26)], 90, 360, fill=color, width=2)
    # Arrow head at top
    draw.polygon([(x+18, y), (x+24, y+2), (x+20, y+6)], fill=color)

def draw_icon_prev(draw, x, y, color):
    """Draw previous icon"""
    # Triangle pointing left
    draw.polygon([(x+16, y+4), (x+16, y+24), (x, y+14)], fill=color)
    # Vertical bar
    draw.rectangle([(x+18, y+2), (x+22, y+26)], fill=color)

def draw_icon_play(draw, x, y, color):
    """Draw play icon"""
    draw.polygon([(x, y+2), (x, y+26), (x+22, y+14)], fill=color)

def draw_icon_pause(draw, x, y, color):
    """Draw pause icon - two vertical bars"""
    draw.rectangle([(x, y+2), (x+8, y+26)], fill=color)
    draw.rectangle([(x+14, y+2), (x+22, y+26)], fill=color)

def draw_icon_next(draw, x, y, color):
    """Draw next icon"""
    # Vertical bar
    draw.rectangle([(x, y+2), (x+4, y+26)], fill=color)
    # Triangle pointing right
    draw.polygon([(x+6, y+4), (x+6, y+24), (x+22, y+14)], fill=color)

def draw_icon_heart(draw, x, y, color):
    """Draw heart icon properly"""
    # Two circles for top lobes
    draw.ellipse([(x+2, y+4), (x+12, y+14)], fill=color)
    draw.ellipse([(x+10, y+4), (x+20, y+14)], fill=color)
    # Bottom triangle
    draw.polygon([(x+2, y+10), (x+20, y+10), (x+11, y+22)], fill=color)

def draw_icon_headphones(draw, x, y, color):
    """Draw headphones icon properly"""
    # Headband arc
    draw.arc([(x+2, y), (x+22, y+18)], 180, 0, fill=color, width=2)
    # Left ear cup
    draw.rounded_rectangle([(x, y+14), (x+8, y+26)], radius=2, fill=color)
    # Right ear cup
    draw.rounded_rectangle([(x+16, y+14), (x+24, y+26)], radius=2, fill=color)

async def get_thumb(videoid: str) -> str:
    cache_path = os.path.join(CACHE_DIR, f"{videoid}_premium.png")
    
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
        # Open thumbnail
        base_thumb = Image.open(thumb_path).convert("RGBA")
        base_thumb = base_thumb.resize((1280, 720), Image.LANCZOS)
        
        # HIGH BRIGHTNESS - Make it bright like sample
        enhancer = ImageEnhance.Brightness(base_thumb)
        base_thumb = enhancer.enhance(1.45)  # 45% brighter
        
        enhancer = ImageEnhance.Contrast(base_thumb)
        base_thumb = enhancer.enhance(1.25)
        
        enhancer = ImageEnhance.Color(base_thumb)
        base_thumb = enhancer.enhance(1.3)  # More vibrant colors
        
        # Blur background heavily
        bg = base_thumb.filter(ImageFilter.GaussianBlur(20))
        
        # Lighter dark overlay for brightness
        dark_overlay = Image.new("RGBA", bg.size, (0, 0, 0, 60))
        bg = Image.alpha_composite(bg, dark_overlay)
        
        # Create panel area
        panel_area = bg.crop((PANEL_X, PANEL_Y, PANEL_X + PANEL_W, PANEL_Y + PANEL_H))
        
        # Frosted glass effect
        frosted = Image.new("RGBA", (PANEL_W, PANEL_H), (20, 20, 25, 55))
        panel = Image.alpha_composite(panel_area, frosted)
        panel = panel.filter(ImageFilter.GaussianBlur(1))
        
        # Rounded mask
        mask = Image.new("L", (PANEL_W, PANEL_H), 0)
        mask_draw = ImageDraw.Draw(mask)
        mask_draw.rounded_rectangle((0, 0, PANEL_W, PANEL_H), radius=PANEL_RADIUS, fill=255)
        
        bg.paste(panel, (PANEL_X, PANEL_Y), mask)
        
        # CARD GLOW - PROPERLY CURVED with multi-color gradient
        card_glow_colors = [
            (60, 140, 255),    # Blue
            (60, 240, 160),    # Green
            (200, 100, 240),   # Purple
            (255, 120, 160),   # Pink
        ]
        
        card_glow = create_curved_glow(
            (PANEL_W, PANEL_H),
            card_glow_colors,
            radius=PANEL_RADIUS,
            blur_amount=35,
            spread=30
        )
        bg.paste(card_glow, (PANEL_X - 30, PANEL_Y - 30), card_glow)
        
        # Inner subtle border on card
        inner_border = Image.new("RGBA", (PANEL_W, PANEL_H), (0, 0, 0, 0))
        ib_draw = ImageDraw.Draw(inner_border)
        ib_draw.rounded_rectangle(
            (4, 4, PANEL_W - 4, PANEL_H - 4),
            radius=PANEL_RADIUS - 2,
            outline=(255, 255, 255, 30),
            width=1
        )
        bg.paste(inner_border, (PANEL_X, PANEL_Y), inner_border)
        
        # Process thumbnail
        thumb_img = Image.open(thumb_path).convert("RGBA")
        thumb_img = thumb_img.resize((THUMB_SIZE, THUMB_SIZE), Image.LANCZOS)
        
        # Brightness for thumb
        enhancer = ImageEnhance.Brightness(thumb_img)
        thumb_img = enhancer.enhance(1.25)
        
        # Thumbnail mask
        thumb_mask = Image.new("L", (THUMB_SIZE, THUMB_SIZE), 0)
        mask_draw = ImageDraw.Draw(thumb_mask)
        mask_draw.rounded_rectangle((0, 0, THUMB_SIZE, THUMB_SIZE), radius=THUMB_RADIUS, fill=255)
        
        # Thumbnail shadow
        shadow = Image.new("RGBA", (1280, 720), (0, 0, 0, 0))
        shadow_draw = ImageDraw.Draw(shadow)
        shadow_draw.rounded_rectangle(
            (THUMB_X - 6, THUMB_Y - 6, 
             THUMB_X + THUMB_SIZE + 6, THUMB_Y + THUMB_SIZE + 6),
            radius=THUMB_RADIUS + 8,
            fill=(0, 0, 0, 130)
        )
        shadow = shadow.filter(ImageFilter.GaussianBlur(18))
        bg = Image.alpha_composite(bg, shadow)
        
        # THUMBNAIL GLOW - Same multi-color gradient as card
        thumb_glow_colors = [
            (60, 140, 255),    # Blue
            (60, 240, 160),    # Green
            (200, 100, 240),   # Purple
        ]
        
        thumb_glow = create_curved_glow(
            (THUMB_SIZE, THUMB_SIZE),
            thumb_glow_colors,
            radius=THUMB_RADIUS,
            blur_amount=28,
            spread=22
        )
        bg.paste(thumb_glow, (THUMB_X - 22, THUMB_Y - 22), thumb_glow)
        
        # Paste thumbnail
        bg.paste(thumb_img, (THUMB_X, THUMB_Y), thumb_mask)
        
        # Drawing
        draw = ImageDraw.Draw(bg)
        
        # Fonts
        try:
            title_font = ImageFont.truetype("AxiomMuzic/assets/assets/font2.ttf", 38)
            meta_font = ImageFont.truetype("AxiomMuzic/assets/assets/font.ttf", 23)
            time_font = ImageFont.truetype("AxiomMuzic/assets/assets/font.ttf", 20)
        except OSError:
            title_font = ImageFont.load_default()
            meta_font = title_font
            time_font = title_font
        
        # Title
        trimmed_title = trim_text(title.upper(), title_font, MAX_TITLE_WIDTH)
        draw.text((TITLE_X, TITLE_Y), trimmed_title, fill="white", font=title_font)
        
        # Channel name
        draw.text((TITLE_X, META_Y), channel, fill=(220, 220, 220), font=meta_font)
        
        # Progress bar
        bar_end_x = BAR_X + BAR_WIDTH
        progress_width = int(BAR_WIDTH * 0.35)
        
        # Bar background
        draw.rounded_rectangle(
            [(BAR_X, BAR_Y), (bar_end_x, BAR_Y + BAR_HEIGHT)],
            radius=3,
            fill=(100, 100, 100)
        )
        
        # Progress - bright green
        draw.rounded_rectangle(
            [(BAR_X, BAR_Y), (BAR_X + progress_width, BAR_Y + BAR_HEIGHT)],
            radius=3,
            fill=(80, 245, 110)
        )
        
        # Circle indicator
        circle_x = BAR_X + progress_width
        circle_y = BAR_Y + BAR_HEIGHT // 2
        draw.ellipse(
            [(circle_x - 7, circle_y - 7), (circle_x + 7, circle_y + 7)],
            fill="white"
        )
        
        # Times
        current_time = "01:58"
        total_time = duration_text if not is_live else "2:16"
        
        draw.text((BAR_X, BAR_Y + 22), current_time, fill="white", font=time_font)
        draw.text((bar_end_x - 40, BAR_Y + 22), total_time, fill="white", font=time_font)
        
        # CONTROL ICONS - PROPERLY DRAWN AND SPACED
        icon_y = ICONS_Y
        icon_size = 24
        icon_gap = 32
        start_x = ICONS_X
        
        # 1. Shuffle - GREEN
        draw_icon_shuffle(draw, start_x, icon_y, (80, 255, 150))
        
        # 2. Repeat - ORANGE/YELLOW
        draw_icon_repeat(draw, start_x + icon_gap, icon_y, (255, 210, 80))
        
        # 3. Previous - WHITE
        draw_icon_prev(draw, start_x + icon_gap * 2, icon_y, "white")
        
        # 4. Pause - WHITE (two bars)
        draw_icon_pause(draw, start_x + icon_gap * 3, icon_y, "white")
        
        # 5. Next - WHITE
        draw_icon_next(draw, start_x + icon_gap * 4, icon_y, "white")
        
        # 6. Heart - RED
        draw_icon_heart(draw, start_x + icon_gap * 5 + 5, icon_y, (255, 70, 70))
        
        # 7. Headphones - WHITE
        draw_icon_headphones(draw, start_x + icon_gap * 6 + 10, icon_y, "white")
        
        # Save
        bg = bg.convert("RGB")
        bg.save(cache_path, "PNG", quality=95)
        
    except Exception as e:
        print(f"Error: {e}")
        return YOUTUBE_IMG_URL
    
    finally:
        try:
            if os.path.exists(thumb_path):
                os.remove(thumb_path)
        except OSError:
            pass

    return cache_path
    
