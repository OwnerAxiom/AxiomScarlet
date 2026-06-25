import os
import re
import aiohttp
import aiofiles
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from functools import lru_cache

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ASSETS = os.path.join(BASE_DIR, "..", "assets")
FONT_TITLE = os.path.join(ASSETS, "f.ttf")
FONT_NORMAL = os.path.join(ASSETS, "cfont.ttf")
TEMPLATE_PATH = os.path.join(ASSETS, "thumb1.png")

@lru_cache(maxsize=4)
def _get_font(path: str, size: int):
    try:
        return ImageFont.truetype(path, size)
    except:
        return ImageFont.load_default()

def _create_rounded_image(img, radius):
    mask = Image.new("L", img.size, 0)
    ImageDraw.Draw(mask).rounded_rectangle([0, 0, img.size[0]-1, img.size[1]-1], radius=radius, fill=255)
    result = Image.new("RGBA", img.size, (0, 0, 0, 0))
    result.paste(img, (0, 0), mask)
    return result

def _add_soft_glow(img, glow_color=(90, 170, 90), num_layers=15):
    """Add multiple soft glow layers around thumbnail - edges ko soft karega"""
    # Create larger canvas for glow layers
    expand_size = num_layers * 3
    glow_size = (img.size[0] + expand_size * 2, img.size[1] + expand_size * 2)
    glow_img = Image.new("RGBA", glow_size, (0, 0, 0, 0))
    glow_draw = ImageDraw.Draw(glow_img)
    
    # Draw 15 layers of expanding rounded rectangles (soft fade effect)
    for layer in range(num_layers, 0, -1):
        opacity = int(35 * (layer / num_layers))  # 35 se 0 tak fade
        expand = layer * 2
        
        glow_draw.rounded_rectangle(
            [expand, expand, glow_size[0] - expand, glow_size[1] - expand],
            radius=35 + layer,  # 35 se 50 tak
            fill=(*glow_color, opacity)
        )
    
    # Heavy blur for ultra-soft glow
    glow_img = glow_img.filter(ImageFilter.GaussianBlur(15))
    
    # Paste original image in center
    paste_x = expand_size // 2
    paste_y = expand_size // 2
    glow_img.paste(img, (paste_x, paste_y), img if img.mode == "RGBA" else None)
    
    return glow_img

async def get_thumb(videoid: str, user_name: str = "AxiomUser") -> str:
    output = f"cache/{videoid}.png"
    os.makedirs("cache", exist_ok=True)
    
    try:
        template = Image.open(TEMPLATE_PATH).convert("RGBA")
    except:
        raise FileNotFoundError(f"Template not found: {TEMPLATE_PATH}")
    
    draw = ImageDraw.Draw(template)
    
    # Fetch metadata
    url = f"https://www.youtube.com/watch?v={videoid}"
    title = "Unknown Song"
    duration = "00:00"
    views = "0 views"
    channel = "Unknown"
    thumb_url = ""
    
    try:
        from py_yt import VideosSearch
        data = (await VideosSearch(url, limit=1).next())["result"][0]
        title = re.sub(r"[\x00-\x1f\x7f]", "", data.get("title", "Unknown")).strip()
        duration = data.get("duration", "00:00") or "00:00"
        thumb_url = data.get("thumbnails", [{}])[-1].get("url", "").split("?")[0]
        v_raw = str(data.get("viewCount", {}).get("short", "N/A"))
        vc = re.sub(r'\s*views?\s*', '', v_raw, flags=re.IGNORECASE).strip()
        views = f"{vc} views"
        channel = data.get("channel", {}).get("name", "Unknown")
    except Exception as e:
        print(f"[ERROR] Metadata: {e}")
    
    # Download album art
    album_size = 305
    album_img = Image.new("RGBA", (album_size, album_size), (76, 175, 80))
    if thumb_url:
        try:
            cache_file = f"cache/album_{videoid}.jpg"
            async with aiohttp.ClientSession() as sess:
                async with sess.get(thumb_url, timeout=aiohttp.ClientTimeout(total=10)) as r:
                    async with aiofiles.open(cache_file, "wb") as f:
                        await f.write(await r.read())
            album_img = Image.open(cache_file).resize((album_size, album_size), Image.LANCZOS).convert("RGBA")
            album_img = _create_rounded_image(album_img, 35)
            
            # Add soft glow around edges (green color to match card)
            album_img = _add_soft_glow(album_img, glow_color=(100, 180, 100), glow_radius=15, glow_strength=120)
            
            if os.path.exists(cache_file):
                os.remove(cache_file)
        except Exception as e:
            print(f"[ERROR] Album art: {e}")
    
    # Album art position
    template.paste(album_img, (140, 129), album_img)
    
    # Fonts
    font_title = _get_font(FONT_TITLE, 60)
    font_subtitle = _get_font(FONT_NORMAL, 35)
    font_time = _get_font(FONT_NORMAL, 30)
    font_requested = _get_font(FONT_TITLE, 28)  # f.ttf for requested by
    
    # Truncate title
    max_title_width = 900
    title_text = title
    while draw.textlength(title_text, font=font_title) > max_title_width and len(title_text) > 3:
        title_text = title_text[:-1]
    if len(title_text) < len(title):
        title_text = title_text[:-3] + "…"
    
    # Title position
    title_x = 500
    title_y = 120
    
    # Green glow layers
    for i in range(3, 0, -1):
        draw.text((title_x + i, title_y + i), title_text, 
                  fill=(50, 180, 50, 80), font=font_title)
    
    # Main title
    draw.text((title_x, title_y), title_text, fill=(220, 255, 100), font=font_title)
    
    # Channel
    subtitle_y = 200
    draw.text((title_x, subtitle_y), channel, fill=(210, 220, 210), font=font_subtitle)
    
    # Pipe + Views
    channel_width = draw.textlength(channel, font=font_subtitle)
    draw.text((title_x + channel_width + 12, subtitle_y), "|", fill=(210, 220, 210), font=font_subtitle)
    draw.text((title_x + channel_width + 32, subtitle_y), views, fill=(210, 220, 210), font=font_subtitle)
    
    # ============ REQUESTED BY + DEV (NEW SECTION) ============
    requested_y = 250  # Channel/views ke niche
    
    # Clean user name (purane wale logic se - unidecode)
    try:
        from unidecode import unidecode
        clean_name = re.sub(r'<[^>]+>', '', str(user_name))
        clean_name = unidecode(clean_name).strip()
    except:
        clean_name = re.sub(r'<[^>]+>', '', str(user_name)).strip()
    
    # Empty check
    if not clean_name:
        clean_name = "AxiomUser"
    
    # Autoplay check
    if clean_name.lower() in ["autoplay", "auto", "autobot"]:
        clean_name = "Autoplay"
    
    # Accent color (lime green - title ka same color)
    accent = (0, 0, 0)
    
    # "Requested By | " - gray color
    prefix_text = "Requested By:- "
    draw.text((title_x, requested_y), prefix_text, 
              fill=(220, 255, 100), font=font_requested)
    
    # User name - accent color
    prefix_width = draw.textlength(prefix_text, font=font_requested)
    draw.text((title_x + prefix_width, requested_y), clean_name, 
              fill=accent, font=font_requested)
    
    # Pipe + Dev credit
    name_width = draw.textlength(clean_name, font=font_requested)
    dev_start_x = title_x + prefix_width + name_width + 15
    draw.text((dev_start_x, requested_y), "|", fill=(210, 220, 210), font=font_requested)
    
    dev_text = " Dev:- CreativeAxiom"
    draw.text((dev_start_x + 15, requested_y), dev_text, fill=(220, 255, 100), font=font_requested)
    # ==========================================================
    
    # Calculate current time
    try:
        parts = duration.split(":")
        total_seconds = int(parts[0]) * 60 + int(parts[1]) if len(parts) == 2 else 225
    except:
        total_seconds = 225
    
    current_seconds = int(total_seconds * 0.30)
    current_min = current_seconds // 60
    current_sec = current_seconds % 60
    current_time = f"{current_min}:{current_sec:02d}"
    
    # Time position
    time_y = 520
    
    # Current time - LEFT
    draw.text((135, time_y), current_time, fill=(220, 255, 100), font=font_time)
    
    # Duration - RIGHT
    dur_width = draw.textlength(duration, font=font_time)
    draw.text((1480 - dur_width, time_y), duration, fill=(220, 255, 100), font=font_time)
    
    # Save
    final = template.convert("RGB")
    final.save(output, "PNG", quality=100)
    
    return output
