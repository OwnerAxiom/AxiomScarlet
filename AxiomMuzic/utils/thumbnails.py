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
import math
import aiofiles
import aiohttp
from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageEnhance
from py_yt import VideosSearch
from config import YOUTUBE_IMG_URL
from random import choice

# Constants
CACHE_DIR = "cache"
os.makedirs(CACHE_DIR, exist_ok=True)

# Panel dimensions
PANEL_W, PANEL_H = 900, 420
PANEL_X = (1280 - PANEL_W) // 2
PANEL_Y = 150

# Thumbnail dimensions
THUMB_SIZE = 300
THUMB_X = PANEL_X + 40
THUMB_Y = PANEL_Y + 60

# Text positions
TITLE_X = THUMB_X + THUMB_SIZE + 50
TITLE_Y = THUMB_Y + 20
META_Y = TITLE_Y + 50

# Progress bar
BAR_Y = META_Y + 60
BAR_X = TITLE_X
BAR_WIDTH = 450
BAR_HEIGHT = 6

# Icons
ICONS_Y = BAR_Y + 50
ICONS_X = TITLE_X

MAX_TITLE_WIDTH = 480

def trim_text(text: str, font: ImageFont.FreeTypeFont, max_width: int) -> str:
    """Trim text to fit within max_width with ellipsis"""
    if font.getlength(text) <= max_width:
        return text
    
    ellipsis = "…"
    for i in range(len(text) - 1, 0, -1):
        trimmed = text[:i] + ellipsis
        if font.getlength(trimmed) <= max_width:
            return trimmed
    return ellipsis

def create_gradient_border(size, colors, radius=40, blur=20):
    """Create a smooth gradient border with multiple colors"""
    width, height = size
    img = Image.new("RGBA", size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # Create multi-layer gradient
    for i, color in enumerate(colors):
        offset = i * 4
        alpha = 255 - (i * 30)
        if alpha < 50:
            alpha = 50
        
        draw.rounded_rectangle(
            (offset, offset, width - offset, height - offset),
            radius=radius + offset,
            outline=color + (alpha,),
            width=3
        )
    
    # Apply blur for glow effect
    return img.filter(ImageFilter.GaussianBlur(blur))

def draw_play_icons(draw, x, y, color="white"):
    """Draw custom play control icons"""
    icon_size = 28
    gap = 35
    
    # Shuffle icon (crossed arrows)
    draw.line([(x, y+14), (x+12, y+14)], fill=(100,100,100), width=2)
    draw.polygon([(x+12, y+8), (x+12, y+20), (x+20, y+14)], fill=(100,100,100))
    draw.line([(x+8, y+20), (x+20, y+8)], fill=(100,100,100), width=2)
    
    x += gap
    
    # Previous icon
    draw.polygon([(x, y+8), (x, y+20), (x+16, y+14)], fill=color)
    draw.rectangle([(x+18, y+6), (x+22, y+22)], fill=color)
    
    x += gap
    
    # Play/Pause icon (Play for now)
    draw.polygon([(x, y+4), (x, y+24), (x+24, y+14)], fill=color)
    
    x += gap
    
    # Next icon
    draw.rectangle([(x, y+6), (x+4, y+22)], fill=color)
    draw.polygon([(x+6, y+8), (x+6, y+20), (x+22, y+14)], fill=color)
    
    x += gap
    
    # Repeat icon
    draw.arc([(x, y+4), (x+24, y+24)], 0, 270, fill=(100,100,100), width=2)
    draw.polygon([(x+16, y+2), (x+24, y+2), (x+24, y+10)], fill=(100,100,100))
    draw.line([(x+18, y+18), (x+26, y+18)], fill=(100,100,100), width=2)
    draw.polygon([(x+26, y+14), (x+26, y+22), (x+18, y+18)], fill=(100,100,100))

def draw_heart_icon(draw, x, y, filled=True):
    """Draw heart icon"""
    color = (255, 60, 60) if filled else (100, 100, 100)
    
    # Draw heart shape using two circles and a polygon
    left_center = (x + 8, y + 10)
    right_center = (x + 20, y + 10)
    
    draw.ellipse([(left_center[0]-8, left_center[1]-8), 
                  (left_center[0]+8, left_center[1]+8)], fill=color)
    draw.ellipse([(right_center[0]-8, right_center[1]-8), 
                  (right_center[0]+8, right_center[1]+8)], fill=color)
    draw.polygon([(x, y+10), (x+28, y+10), (x+14, y+26)], fill=color)

def draw_headphones_icon(draw, x, y):
    """Draw headphones icon"""
    # Headband
    draw.arc([(x, y), (x+28, y+20)], 180, 0, fill=(100,100,100), width=3)
    
    # Left ear cup
    draw.ellipse([(x, y+18), (x+10, y+28)], fill=(100,100,100))
    
    # Right ear cup
    draw.ellipse([(x+18, y+18), (x+28, y+28)], fill=(100,100,100))

async def get_thumb(videoid: str) -> str:
    """Generate enhanced thumbnail for video"""
    cache_path = os.path.join(CACHE_DIR, f"{videoid}_enhanced.png")
    
    if os.path.exists(cache_path):
        return cache_path

    # Fetch video data
    thumb_path = os.path.join(CACHE_DIR, f"thumb_{videoid}.png")
    
    try:
        results = VideosSearch(f"https://www.youtube.com/watch?v={videoid}", limit=1)
        results_data = await results.next()
        result_items = results_data.get("result", [])
        
        if not result_items:
            raise ValueError("No results found")
            
        data = result_items[0]
        title = re.sub(r"\W+", " ", data.get("title", "Unsupported Title")).title()
        thumbnail_url = data.get("thumbnails", [{}])[0].get("url", YOUTUBE_IMG_URL)
        duration = data.get("duration")
        views = data.get("viewCount", {}).get("short", "Unknown Views")
        channel = data.get("channel", {}).get("name", "YouTube")
        
    except Exception as e:
        print(f"Error fetching video data: {e}")
        title, thumbnail_url, duration, views, channel = (
            "Unsupported Title", YOUTUBE_IMG_URL, None, "Unknown Views", "YouTube"
        )

    is_live = not duration or str(duration).strip().lower() in {"", "live", "live now"}
    duration_text = "LIVE" if is_live else (duration or "Unknown")

    # Download thumbnail
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(thumbnail_url, timeout=10) as resp:
                if resp.status == 200:
                    async with aiofiles.open(thumb_path, "wb") as f:
                        await f.write(await resp.read())
                else:
                    return YOUTUBE_IMG_URL
    except Exception as e:
        print(f"Error downloading thumbnail: {e}")
        return YOUTUBE_IMG_URL

    try:
        # Create base image with blurred background
        base_thumb = Image.open(thumb_path).convert("RGBA")
        base_thumb = base_thumb.resize((1280, 720), Image.LANCZOS)
        
        # Apply heavy blur to background
        bg = base_thumb.filter(ImageFilter.GaussianBlur(20))
        
        # Darken background
        dark_overlay = Image.new("RGBA", bg.size, (0, 0, 0, 100))
        bg = Image.alpha_composite(bg, dark_overlay)
        
        # Create frosted glass panel
        panel_area = bg.crop((PANEL_X, PANEL_Y, PANEL_X + PANEL_W, PANEL_Y + PANEL_H))
        panel_area = panel_area.filter(ImageFilter.GaussianBlur(3))
        
        # Semi-transparent white overlay for frosted effect
        frosted = Image.new("RGBA", (PANEL_W, PANEL_H), (25, 25, 25, 60))
        panel = Image.alpha_composite(panel_area, frosted)
        
        # Create rounded corner mask
        mask = Image.new("L", (PANEL_W, PANEL_H), 0)
        mask_draw = ImageDraw.Draw(mask)
        mask_draw.rounded_rectangle((0, 0, PANEL_W, PANEL_H), radius=35, fill=255)
        
        # Paste panel with mask
        bg.paste(panel, (PANEL_X, PANEL_Y), mask)
        
        # Create gradient border colors
        gradient_colors = [
            (0, 255, 200),    # Cyan-Green
            (0, 200, 255),    # Cyan-Blue
            (150, 100, 255),  # Purple
            (255, 100, 150),  # Pink
        ]
        
        # Add gradient glow border
        border_glow = create_gradient_border(
            (PANEL_W + 40, PANEL_H + 40),
            gradient_colors,
            radius=38,
            blur=25
        )
        
        bg.paste(
            border_glow,
            (PANEL_X - 20, PANEL_Y - 20),
            border_glow
        )
        
        # Process thumbnail image
        thumb_img = Image.open(thumb_path).convert("RGBA")
        thumb_img = thumb_img.resize((THUMB_SIZE, THUMB_SIZE), Image.LANCZOS)
        
        # Create rounded mask for thumbnail
        thumb_mask = Image.new("L", (THUMB_SIZE, THUMB_SIZE), 0)
        mask_draw = ImageDraw.Draw(thumb_mask)
        mask_draw.rounded_rectangle((0, 0, THUMB_SIZE, THUMB_SIZE), radius=20, fill=255)
        
        # Add thumbnail shadow
        shadow = Image.new("RGBA", (1280, 720), (0, 0, 0, 0))
        shadow_draw = ImageDraw.Draw(shadow)
        shadow_draw.rounded_rectangle(
            (THUMB_X - 5, THUMB_Y - 5, 
             THUMB_X + THUMB_SIZE + 5, THUMB_Y + THUMB_SIZE + 5),
            radius=25,
            fill=(0, 0, 0, 150)
        )
        shadow = shadow.filter(ImageFilter.GaussianBlur(15))
        bg = Image.alpha_composite(bg, shadow)
        
        # Add thumbnail glow border
        thumb_glow = create_gradient_border(
            (THUMB_SIZE + 30, THUMB_SIZE + 30),
            gradient_colors[:3],
            radius=22,
            blur=20
        )
        
        bg.paste(
            thumb_glow,
            (THUMB_X - 15, THUMB_Y - 15),
            thumb_glow
        )
        
        # Paste thumbnail
        bg.paste(thumb_img, (THUMB_X, THUMB_Y), thumb_mask)
        
        # Drawing setup
        draw = ImageDraw.Draw(bg)
        
        # Load fonts
        try:
            title_font = ImageFont.truetype("AxiomMuzic/assets/assets/font2.ttf", 34)
            meta_font = ImageFont.truetype("AxiomMuzic/assets/assets/font.ttf", 20)
            time_font = ImageFont.truetype("AxiomMuzic/assets/assets/font.ttf", 18)
        except OSError:
            title_font = ImageFont.load_default()
            meta_font = title_font
            time_font = title_font
        
        # Draw title
        trimmed_title = trim_text(title, title_font, MAX_TITLE_WIDTH)
        draw.text((TITLE_X, TITLE_Y), trimmed_title, fill="white", font=title_font)
        
        # Draw channel/views
        meta_text = f"{channel} | {views}"
        draw.text((TITLE_X, META_Y), meta_text, fill=(200, 200, 200), font=meta_font)
        
        # Draw progress bar background
        bar_end_x = BAR_X + BAR_WIDTH
        draw.rounded_rectangle(
            [(BAR_X, BAR_Y), (bar_end_x, BAR_Y + BAR_HEIGHT)],
            radius=3,
            fill=(80, 80, 80)
        )
        
        # Draw progress (simulated - you can make this dynamic)
        progress_width = int(BAR_WIDTH * 0.35)  # 35% progress example
        draw.rounded_rectangle(
            [(BAR_X, BAR_Y), (BAR_X + progress_width, BAR_Y + BAR_HEIGHT)],
            radius=3,
            fill=(0, 220, 150)
        )
        
        # Draw progress circle
        circle_x = BAR_X + progress_width
        circle_y = BAR_Y + BAR_HEIGHT // 2
        draw.ellipse(
            [(circle_x - 7, circle_y - 7), (circle_x + 7, circle_y + 7)],
            fill="white"
        )
        
        # Draw time text
        current_time = "01:13"  # You can make this dynamic
        draw.text((BAR_X, BAR_Y + 25), current_time, fill="white", font=time_font)
        
        end_time_x = bar_end_x - (60 if is_live else 40)
        end_color = (0, 220, 150) if is_live else "white"
        draw.text((end_time_x, BAR_Y + 25), duration_text, fill=end_color, font=time_font)
        
        # Draw control icons
        draw_play_icons(draw, ICONS_X, ICONS_Y)
        
        # Draw heart icon
        draw_heart_icon(draw, ICONS_X + 220, ICONS_Y)
        
        # Draw headphones icon
        draw_headphones_icon(draw, ICONS_X + 270, ICONS_Y)
        
        # Save the image
        bg = bg.convert("RGB")
        bg.save(cache_path, "PNG", quality=95)
        
    except Exception as e:
        print(f"Error generating thumbnail: {e}")
        return YOUTUBE_IMG_URL
    
    finally:
        # Cleanup
        try:
            if os.path.exists(thumb_path):
                os.remove(thumb_path)
        except OSError:
            pass

    return cache_path
