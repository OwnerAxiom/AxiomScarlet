# -----------------------------------------------
# 🔸 AxiomMusic Project - PERFECT NEON THUMBNAIL
#  Developed & Maintained by: Axiom Bots (https://t.me/axiombots)
# 📅 Copyright © 2026 – All Rights Reserved
# -----------------------------------------------

import os
import re
import aiofiles
import aiohttp
from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageEnhance, ImageMath
from py_yt import VideosSearch
from config import YOUTUBE_IMG_URL

CACHE_DIR = "cache"
os.makedirs(CACHE_DIR, exist_ok=True)

# ===== LAYOUT CONSTANTS =====
CANVAS_W, CANVAS_H = 1280, 720

# Card Dimensions
CARD_W, CARD_H = 960, 460
CARD_X = (CANVAS_W - CARD_W) // 2
CARD_Y = (CANVAS_H - CARD_H) // 2
CARD_RADIUS = 50

# Thumbnail Dimensions
THUMB_SIZE = 320
THUMB_X = CARD_X + 50
THUMB_Y = CARD_Y + 70
THUMB_RADIUS = 30

# Text Positions
TITLE_X = THUMB_X + THUMB_SIZE + 50
TITLE_Y = CARD_Y + 90
META_Y = TITLE_Y + 60

# Progress Bar
BAR_Y = META_Y + 55
BAR_X = TITLE_X
BAR_WIDTH = 480
BAR_HEIGHT = 6

# Control Pill
PILL_W = 340
PILL_H = 70
PILL_RADIUS = 35
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

def create_rainbow_gradient_mask(size, radius, thickness=20):
    """
    Creates a THICK, MULTI-COLOR rainbow glow effect.
    Draws many concentric rectangles with shifting colors, then blurs them.
    """
    w, h = size
    # Make canvas slightly larger for glow
    glow_pad = thickness * 2
    img_size = (w + glow_pad * 2, h + glow_pad * 2)
    img = Image.new("RGBA", img_size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # Rainbow Colors (Pink -> Purple -> Blue -> Cyan -> Green -> Yellow -> Orange -> Red)
    colors = [
        (255, 0, 100),   # Pink (Top Left)
        (180, 0, 255),   # Purple
        (0, 100, 255),   # Blue (Top Right)
        (0, 200, 255),   # Cyan
        (0, 255, 100),   # Green (Right)
        (200, 255, 0),   # Yellow-Green
        (255, 200, 0),   # Yellow (Bottom Right)
        (255, 100, 0),   # Orange
        (255, 0, 50),    # Red (Bottom Left)
    ]
    
    num_colors = len(colors)
    
    # Draw layers from outside in
    for i in range(thickness * 2):
        # Calculate color based on position in the loop
        # We want the color to rotate around the border
        # For a simple thick blur, we can blend colors based on layer index to simulate rotation
        
        # Interpolate colors to make it smooth
        idx = int((i / (thickness * 2)) * (num_colors - 1))
        next_idx = min(idx + 1, num_colors - 1)
        t = (i / (thickness * 2)) * (num_colors - 1) - idx
        
        c1 = colors[idx]
        c2 = colors[next_idx]
        
        r = int(c1[0] + (c2[0] - c1[0]) * t)
        g = int(c1[1] + (c2[1] - c1[1]) * t)
        b = int(c1[2] + (c2[2] - c1[2]) * t)
        
        # Alpha is highest in the middle layers for glow intensity
        alpha = 200 if i < thickness else int(200 * (1 - (i - thickness)/thickness))
        if alpha < 50: alpha = 50
        
        offset = i * 1.5  # Spacing
        layer_radius = radius + thickness - i
        
        if layer_radius < 5:
            break
            
        draw.rounded_rectangle(
            (int(offset), int(offset), int(img_size[0] - offset), int(img_size[1] - offset)),
            radius=int(layer_radius),
            outline=(r, g, b, alpha),
            width=2
        )
    
    # BLUR THE RESULT TO CREATE GLOW
    return img.filter(ImageFilter.GaussianBlur(25))

def draw_icon_shuffle(draw, x, y, size, color):
    s = int(size)
    x, y = int(x), int(y)
    # X shape
    draw.line([(x, y + s//2), (x + s//2, y)], fill=color, width=2)
    draw.line([(x, y + s//2), (x + s//2, y + s)], fill=color, width=2)
    # Horizontal bars
    draw.line([(x + s//4, y), (x + s*3//4, y)], fill=color, width=2)
    draw.line([(x + s//4, y + s), (x + s*3//4, y + s)], fill=color, width=2)
    # Arrow heads
    draw.polygon([(x + s//2, y), (x + s//2 + 5, y + 4), (x + s//2, y + 8)], fill=color)
    draw.polygon([(x + s//2, y + s), (x + s//2 + 5, y + s - 4), (x + s//2, y + s - 8)], fill=color)

def draw_icon_prev(draw, x, y, size, color):
    s = int(size)
    x, y = int(x), int(y)
    # Triangle Left
    draw.polygon([(x + s*3//4, y + 2), (x + s*3//4, y + s - 2), (x + 2, y + s//2)], fill=color)
    # Bar
    draw.rectangle([(x + s*4//5, y + 4), (x + s, y + s - 4)], fill=color)

def draw_icon_play(draw, x, y, size, circle_color, triangle_color):
    s = int(size)
    x, y = int(x), int(y)
    # White Circle
    draw.ellipse([(x, y), (x + s, y + s)], fill=circle_color)
    # Black Triangle
    draw.polygon([
        (x + s*2//5, y + s//4),
        (x + s*2//5, y + s*3//4),
        (x + s*3//4, y + s//2)
    ], fill=triangle_color)

def draw_icon_next(draw, x, y, size, color):
    s = int(size)
    x, y = int(x), int(y)
    # Bar
    draw.rectangle([(x, y + 4), (x + s//5, y + s - 4)], fill=color)
    # Triangle Right
    draw.polygon([(x + s//4, y + 2), (x + s//4, y + s - 2), (x + s - 2, y + s//2)], fill=color)

def draw_icon_repeat(draw, x, y, size, color):
    s = int(size)
    x, y = int(x), int(y)
    # Top Arc
    draw.arc([(x, y), (x + s, y + s//2)], 180, 0, fill=color, width=2)
    # Top Arrow Head
    draw.polygon([(x + s - 4, y), (x + s + 4, y + 4), (x + s - 4, y + 8)], fill=color)
    # Bottom Arc
    draw.arc([(x, y + s//2), (x + s, y + s)], 0, 180, fill=color, width=2)
    # Bottom Arrow Head
    draw.polygon([(x + 4, y + s), (x - 4, y + s - 4), (x + 4, y + s - 8)], fill=color)

async def get_thumb(videoid: str) -> str:
    cache_path = os.path.join(CACHE_DIR, f"{videoid}_neon_perfect.png")
    
    if os.path.exists(cache_path):
        return cache_path

    thumb_path = os.path.join(CACHE_DIR, f"thumb_{videoid}.png")
    
    # --- DATA FETCHING ---
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

    # --- DOWNLOAD THUMB ---
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
        # 1. LOAD ORIGINAL THUMB
        base_img = Image.open(thumb_path).convert("RGBA")
        base_img = base_img.resize((CANVAS_W, CANVAS_H), Image.LANCZOS)
        
        # 2. BACKGROUND PROCESSING (Blur + Brightness but not too dark)
        # Blur it lightly
        bg_blur = base_img.filter(ImageFilter.GaussianBlur(15))
        # Increase brightness so it's vibrant
        bg_blur = ImageEnhance.Brightness(bg_blur).enhance(1.2)
        bg_blur = ImageEnhance.Contrast(bg_blur).enhance(1.1)
        
        # Darken slightly for contrast, but keep it visible (Alpha 180/255)
        dark_layer = Image.new("RGBA", base_img.size, (0, 0, 0, 180))
        final_bg = Image.alpha_composite(bg_blur, dark_layer)

        # 3. CREATE CARD GLOW LAYER
        # This creates the thick rainbow blur behind the card
        card_glow = create_rainbow_gradient_mask((CARD_W, CARD_H), CARD_RADIUS, thickness=25)
        # Paste glow centered behind where the card will be
        final_bg.paste(card_glow, (CARD_X - 50, CARD_Y - 50), card_glow)

        # 4. CREATE CARD BODY (Dark solid rectangle)
        card_body = Image.new("RGBA", (CARD_W, CARD_H), (10, 10, 15, 240))
        card_mask = Image.new("L", (CARD_W, CARD_H), 0)
        ImageDraw.Draw(card_mask).rounded_rectangle((0, 0, CARD_W, CARD_H), radius=CARD_RADIUS, fill=255)
        final_bg.paste(card_body, (CARD_X, CARD_Y), card_mask)

        # 5. THUMBNAIL PROCESSING
        # Crop original thumb to square
        w, h = base_img.size
        min_dim = min(w, h)
        left = (w - min_dim) // 2
        top = (h - min_dim) // 2
        square_crop = base_img.crop((left, top, left + min_dim, top + min_dim))
        square_crop = square_crop.resize((THUMB_SIZE, THUMB_SIZE), Image.LANCZOS)
        
        # Create Thumbnail Glow
        thumb_glow = create_rainbow_gradient_mask((THUMB_SIZE, THUMB_SIZE), THUMB_RADIUS, thickness=15)
        final_bg.paste(thumb_glow, (THUMB_X - 25, THUMB_Y - 25), thumb_glow)
        
        # Paste Thumbnail with rounded corners
        t_mask = Image.new("L", (THUMB_SIZE, THUMB_SIZE), 0)
        ImageDraw.Draw(t_mask).rounded_rectangle((0, 0, THUMB_SIZE, THUMB_SIZE), radius=THUMB_RADIUS, fill=255)
        final_bg.paste(square_crop, (THUMB_X, THUMB_Y), t_mask)

        # 6. TEXT DRAWING
        draw = ImageDraw.Draw(final_bg)
        
        # Font Loading
        try:
            title_font = ImageFont.truetype("AxiomMuzic/assets/assets/font2.ttf", 38)
            meta_font = ImageFont.truetype("AxiomMuzic/assets/assets/font.ttf", 20)
            time_font = ImageFont.truetype("AxiomMuzic/assets/assets/font.ttf", 18)
        except OSError:
            title_font = ImageFont.load_default()
            meta_font = title_font
            time_font = title_font
        
        # Title
        clean_title = trim_text(title, title_font, MAX_TITLE_WIDTH)
        draw.text((TITLE_X, TITLE_Y), clean_title, fill="white", font=title_font)
        
        # Meta (Channel | Views)
        draw.text((TITLE_X, META_Y), f"{channel}  |  {views}", fill=(170, 170, 170), font=meta_font)
        
        # 7. PROGRESS BAR
        bar_end = BAR_X + BAR_WIDTH
        progress_width = int(BAR_WIDTH * 0.35) # Simulated progress
        
        # Bar Background
        draw.rounded_rectangle([(BAR_X, BAR_Y), (bar_end, BAR_Y + BAR_HEIGHT)], radius=3, fill=(60, 60, 60))
        # Bar Progress (Green)
        draw.rounded_rectangle([(BAR_X, BAR_Y), (BAR_X + progress_width, BAR_Y + BAR_HEIGHT)], radius=3, fill=(50, 230, 100))
        # Dot
        dot_x = BAR_X + progress_width
        dot_y = BAR_Y + BAR_HEIGHT // 2
        draw.ellipse([(dot_x - 8, dot_y - 8), (dot_x + 8, dot_y + 8)], fill="white")
        
        # Times
        draw.text((BAR_X, BAR_Y + 20), "01:13", fill="white", font=time_font)
        total = duration_text if not is_live else "04:30"
        draw.text((bar_end - 40, BAR_Y + 20), total, fill="white", font=time_font)
        
        # 8. CONTROL PILL & ICONS
        pill = Image.new("RGBA", (PILL_W, PILL_H), (0, 0, 0, 0))
        pd = ImageDraw.Draw(pill)
        pd.rounded_rectangle((0, 0, PILL_W, PILL_H), radius=PILL_RADIUS, fill=(20, 20, 25, 210))
        final_bg.paste(pill, (PILL_X, PILL_Y), pill)
        
        icon_y = PILL_Y + (PILL_H - 26) // 2
        icon_size = 26
        gap = 55
        sx = PILL_X + 25
        
        # Shuffle (White)
        draw_icon_shuffle(draw, sx, icon_y, icon_size, "white")
        
        # Prev (White)
        draw_icon_prev(draw, sx + gap, icon_y, icon_size, "white")
        
        # Play (Big White Circle)
        play_size = 42
        play_y = PILL_Y + (PILL_H - play_size) // 2
        draw_icon_play(draw, sx + gap * 2 - 2, play_y, play_size, "white", (20, 20, 25))
        
        # Next (White)
        draw_icon_next(draw, sx + gap * 3 + 8, icon_y, icon_size, "white")
        
        # Repeat (Green Accent)
        draw_icon_repeat(draw, sx + gap * 4 + 16, icon_y, icon_size, (50, 230, 100))
        
        # 9. SAVE
        final_img = final_bg.convert("RGB")
        final_img.save(cache_path, "PNG", quality=95)
        
    except Exception as e:
        print(f"Error generating thumbnail: {e}")
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
