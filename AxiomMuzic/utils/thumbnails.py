# -----------------------------------------------
# 🔸 AxiomMusic Project - Simple Random Color Thumbnail
# 🔹 Developed & Maintained by: Axiom Bots
# -----------------------------------------------

import os
import re
import random
import aiofiles
import aiohttp
from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageEnhance
from py_yt import VideosSearch
from config import YOUTUBE_IMG_URL

CACHE_DIR = "cache"
os.makedirs(CACHE_DIR, exist_ok=True)

# 50+ Random Bright Colors
COLOR_PALETTE = [
    (0, 230, 118),    # Green
    (124, 77, 255),   # Purple
    (255, 23, 68),    # Red
    (255, 109, 0),    # Orange
    (0, 176, 255),    # Blue
    (255, 193, 7),    # Yellow
    (233, 30, 99),    # Pink
    (0, 200, 150),    # Teal
    (156, 39, 176),   # Deep Purple
    (255, 87, 34),    # Deep Orange
    (33, 150, 243),   # Light Blue
    (76, 175, 80),    # Light Green
    (255, 152, 0),    # Amber
    (121, 85, 72),    # Brown
    (96, 125, 139),   # Blue Grey
    (244, 67, 54),    # Red 700
    (232, 30, 99),    # Pink 500
    (156, 39, 176),   # Purple 700
    (103, 58, 183),   # Deep Purple 700
    (63, 81, 181),    # Indigo
    (3, 169, 244),    # Light Blue 500
    (0, 188, 212),    # Cyan
    (0, 150, 136),    # Teal 500
    (76, 175, 80),    # Green 500
    (139, 195, 74),   # Light Green 500
    (205, 220, 57),   # Lime
    (255, 235, 59),   # Yellow 500
    (255, 193, 7),    # Amber 500
    (255, 152, 0),    # Orange 500
    (255, 87, 34),    # Deep Orange 500
    (121, 85, 72),    # Brown 500
    (158, 158, 158),  # Grey
    (96, 125, 139),   # Blue Grey 500
    (255, 64, 129),   # Pink A200
    (224, 64, 251),   # Purple A200
    (124, 77, 255),   # Deep Purple A200
    (92, 107, 192),   # Indigo A200
    (68, 138, 255),   # Blue A200
    (0, 229, 255),    # Cyan A200
    (29, 233, 182),   # Teal A200
    (118, 255, 3),    # Green A200
    (176, 255, 0),    # Light Green A200
    (238, 255, 65),   # Lime A200
    (255, 234, 0),    # Yellow A200
    (255, 214, 0),    # Amber A200
    (255, 145, 0),    # Orange A200
    (255, 109, 0),    # Deep Orange A200
    (255, 82, 82),    # Red A200
    (255, 128, 171),  # Pink A100
    (234, 128, 252),  # Purple A100
    (179, 136, 255),  # Deep Purple A100
    (140, 158, 255),  # Indigo A100
    (130, 177, 255),  # Blue A100
    (128, 222, 234),  # Cyan A100
    (167, 255, 235),  # Teal A100
    (186, 255, 136),  # Green A100
    (204, 255, 144),  # Light Green A100
    (245, 255, 141),  # Lime A100
    (255, 255, 141),  # Yellow A100
    (255, 229, 127),  # Amber A100
    (255, 209, 128),  # Orange A100
    (255, 183, 127),  # Deep Orange A100
    (255, 138, 128),  # Red A100
    (255, 179, 207),  # Pink 100
    (234, 199, 255),  # Purple 100
    (209, 196, 233),  # Deep Purple 100
    (197, 202, 233),  # Indigo 100
    (197, 214, 255),  # Blue 100
    (178, 235, 242),  # Cyan 100
    (178, 223, 219),  # Teal 100
    (200, 230, 201),  # Green 100
    (220, 237, 200),  # Light Green 100
    (240, 244, 195),  # Lime 100
    (255, 249, 196),  # Yellow 100
    (255, 236, 179),  # Amber 100
    (255, 224, 178),  # Orange 100
    (255, 204, 188),  # Deep Orange 100
    (255, 205, 210),  # Red 100
    (252, 228, 236),  # Pink 50
    (243, 229, 245),  # Purple 50
    (237, 231, 246),  # Deep Purple 50
    (232, 234, 246),  # Indigo 50
    (227, 242, 253),  # Blue 50
    (224, 247, 250),  # Cyan 50
    (224, 242, 241),  # Teal 50
    (232, 245, 233),  # Green 50
    (241, 248, 233),  # Light Green 50
    (249, 251, 231),  # Lime 50
    (255, 252, 225),  # Yellow 50
    (255, 248, 225),  # Amber 50
    (255, 243, 224),  # Orange 50
    (251, 233, 231),  # Deep Orange 50
    (255, 235, 238),  # Red 50
]

# Layout
THUMB_SIZE = 420
THUMB_X = 60
THUMB_Y = (720 - THUMB_SIZE) // 2
THUMB_RADIUS = 45

TITLE_X = THUMB_X + THUMB_SIZE + 60
TITLE_Y = 180
META_Y = TITLE_Y + 75
VIEWS_Y = META_Y + 55

BAR_X = TITLE_X
BAR_Y = VIEWS_Y + 80
BAR_WIDTH = 680
BAR_HEIGHT = 8

MAX_TITLE_WIDTH = 700


def trim_text(text, font, max_width):
    try:
        if font.getlength(text) <= max_width:
            return text
        for i in range(len(text) - 1, 0, -1):
            if font.getlength(text[:i] + "…") <= max_width:
                return text[:i] + "…"
        return "…"
    except:
        return text[:60]


async def get_thumb(videoid: str) -> str:
    cache_path = os.path.join(CACHE_DIR, f"{videoid}_simple.png")
    if os.path.exists(cache_path):
        return cache_path

    thumb_path = os.path.join(CACHE_DIR, f"thumb_{videoid}.png")

    # Pick random color
    accent = random.choice(COLOR_PALETTE)

    try:
        results = VideosSearch(f"https://www.youtube.com/watch?v={videoid}", limit=1)
        results_data = await results.next()
        data = results_data.get("result", [{}])[0]
        title = re.sub(r"\W+", " ", data.get("title", "Song")).title()
        thumbnail_url = data.get("thumbnails", [{}])[0].get("url", YOUTUBE_IMG_URL)
        duration = data.get("duration")
        views = data.get("viewCount", {}).get("short", "Unknown")
        channel = data.get("channel", {}).get("name", "YouTube")
    except:
        title, thumbnail_url, duration, views, channel = (
            "Song", YOUTUBE_IMG_URL, None, "Unknown", "YouTube"
        )

    is_live = not duration or str(duration).strip().lower() in {"", "live"}
    duration_text = "LIVE" if is_live else (duration or "0:00")

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(thumbnail_url, timeout=10) as resp:
                if resp.status == 200:
                    async with aiofiles.open(thumb_path, "wb") as f:
                        await f.write(await resp.read())
    except:
        return YOUTUBE_IMG_URL

    try:
        # BACKGROUND
        base = Image.open(thumb_path).convert("RGBA")
        base = base.resize((1280, 720), Image.LANCZOS)
        base = ImageEnhance.Brightness(base).enhance(1.1)
        bg = base.filter(ImageFilter.GaussianBlur(15))
        dark = Image.new("RGBA", bg.size, (0, 0, 0, 100))
        bg = Image.alpha_composite(bg, dark)

        # THICK OUTER BORDER (full image border)
        border_layer = Image.new("RGBA", (1280, 720), (0, 0, 0, 0))
        bd = ImageDraw.Draw(border_layer)
        border_thickness = 18
        bd.rectangle(
            (0, 0, 1279, 719),
            outline=accent + (255,),
            width=border_thickness
        )
        bg = Image.alpha_composite(bg, border_layer)

        # THUMBNAIL
        thumb_img = Image.open(thumb_path).convert("RGBA")
        thumb_img = thumb_img.resize((THUMB_SIZE, THUMB_SIZE), Image.LANCZOS)
        thumb_img = ImageEnhance.Brightness(thumb_img).enhance(1.1)

        thumb_mask = Image.new("L", (THUMB_SIZE, THUMB_SIZE), 0)
        ImageDraw.Draw(thumb_mask).rounded_rectangle(
            (0, 0, THUMB_SIZE, THUMB_SIZE), radius=THUMB_RADIUS, fill=255
        )

        # Thumbnail shadow
        shadow = Image.new("RGBA", (1280, 720), (0, 0, 0, 0))
        sd = ImageDraw.Draw(shadow)
        sd.rounded_rectangle(
            (THUMB_X - 5, THUMB_Y - 5,
             THUMB_X + THUMB_SIZE + 5, THUMB_Y + THUMB_SIZE + 5),
            radius=THUMB_RADIUS + 8, fill=(0, 0, 0, 140)
        )
        shadow = shadow.filter(ImageFilter.GaussianBlur(15))
        bg = Image.alpha_composite(bg, shadow)

        # Thumbnail colored border (thick)
        thumb_border = Image.new("RGBA", (1280, 720), (0, 0, 0, 0))
        tbd = ImageDraw.Draw(thumb_border)
        # Outer glow
        for spread in [12, 8, 4]:
            alpha = 80 if spread == 12 else 150 if spread == 8 else 255
            tbd.rounded_rectangle(
                (THUMB_X - spread, THUMB_Y - spread,
                 THUMB_X + THUMB_SIZE + spread, THUMB_Y + THUMB_SIZE + spread),
                radius=THUMB_RADIUS + spread,
                outline=accent + (alpha,),
                width=3
            )
        bg = Image.alpha_composite(bg, thumb_border)

        bg.paste(thumb_img, (THUMB_X, THUMB_Y), thumb_mask)

        # DRAWING
        draw = ImageDraw.Draw(bg)

        # Fonts
        try:
            title_font = ImageFont.truetype("AxiomMuzic/assets/assets/cfont.ttf", 52)
            meta_font = ImageFont.truetype("AxiomMuzic/assets/assets/f.ttf", 32)
            time_font = ImageFont.truetype("AxiomMuzic/assets/assets/f.ttf", 28)
        except OSError:
            title_font = ImageFont.load_default()
            meta_font = title_font
            time_font = title_font

        # Title - Bold white
        trimmed = trim_text(title, title_font, MAX_TITLE_WIDTH)
        draw.text((TITLE_X, TITLE_Y), trimmed, fill="white", font=title_font)

        # Artist
        draw.text((TITLE_X, META_Y), f"Artist: {channel}",
                  fill=(200, 200, 200), font=meta_font)

        # Views
        draw.text((TITLE_X, VIEWS_Y), f"Views: {views}",
                  fill=(180, 180, 180), font=meta_font)

        # Progress bar background
        bar_end = BAR_X + BAR_WIDTH
        draw.rounded_rectangle(
            [(BAR_X, BAR_Y), (bar_end, BAR_Y + BAR_HEIGHT)],
            radius=4, fill=(80, 80, 80)
        )

        # Progress fill (accent color)
        progress = int(BAR_WIDTH * 0.70)
        draw.rounded_rectangle(
            [(BAR_X, BAR_Y), (BAR_X + progress, BAR_Y + BAR_HEIGHT)],
            radius=4, fill=accent
        )

        # White circle indicator with glow
        cx, cy = BAR_X + progress, BAR_Y + BAR_HEIGHT // 2
        # Glow
        draw.ellipse([(cx - 18, cy - 18), (cx + 18, cy + 18)],
                     fill=accent + (80,) if len(accent) == 3 else accent[:3] + (80,))
        # White circle
        draw.ellipse([(cx - 10, cy - 10), (cx + 10, cy + 10)], fill="white")

        # Times
        draw.text((BAR_X, BAR_Y + 22), "0:00", fill=(220, 220, 220), font=time_font)
        total = duration_text if not is_live else "3:45"
        draw.text((bar_end - 50, BAR_Y + 22), total, fill=(220, 220, 220), font=time_font)

        # SAVE
        bg = bg.convert("RGB")
        bg.save(cache_path, "PNG", quality=95)
        print(f"✓ Thumbnail saved with color RGB{accent}")

    except Exception as e:
        import traceback
        print(f"Error: {e}")
        traceback.print_exc()
        return YOUTUBE_IMG_URL
    finally:
        try:
            if os.path.exists(thumb_path):
                os.remove(thumb_path)
        except:
            pass

    return cache_path
