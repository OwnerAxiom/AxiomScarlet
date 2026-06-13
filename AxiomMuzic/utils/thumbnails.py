# Custom thumbnail.py (starter replacement)
# Drop-in replacement for get_thumb(videoid)

import os, re, aiohttp, aiofiles
from PIL import Image, ImageDraw, ImageFilter, ImageFont
from py_yt import VideosSearch
from config import YOUTUBE_IMG_URL

CACHE_DIR = "cache"
os.makedirs(CACHE_DIR, exist_ok=True)

def trim(text, n=35):
    return text if len(text) <= n else text[:n] + "..."

async def get_thumb(videoid: str) -> str:
    cache = os.path.join(CACHE_DIR, f"{videoid}_glass.png")
    if os.path.exists(cache):
        return cache

    title = "Unknown Title"
    channel = "YouTube"
    duration = "0:00"
    thumb_url = YOUTUBE_IMG_URL

    try:
        results = VideosSearch(f"https://www.youtube.com/watch?v={videoid}", limit=1)
        data = (await results.next())["result"][0]
        title = data.get("title", title)
        channel = data.get("channel", {}).get("name", channel)
        duration = data.get("duration", duration)
        thumb_url = data.get("thumbnails", [{}])[0].get("url", thumb_url)
    except:
        pass

    tmp = os.path.join(CACHE_DIR, f"{videoid}.jpg")

    async with aiohttp.ClientSession() as s:
        async with s.get(thumb_url) as r:
            if r.status == 200:
                async with aiofiles.open(tmp, "wb") as f:
                    await f.write(await r.read())

    base = Image.open(tmp).convert("RGB").resize((1280,720))
    bg = base.filter(ImageFilter.GaussianBlur(20)).convert("RGBA")

    overlay = Image.new("RGBA",(1280,720),(0,0,0,90))
    bg = Image.alpha_composite(bg, overlay)

    draw = ImageDraw.Draw(bg)

    card = (220,145,1060,575)
    draw.rounded_rectangle(card, radius=35, fill=(20,20,20,110))

    colors = [(98,178,255),(120,255,0),(255,220,0),(255,120,180)]
    for i,c in enumerate(colors):
        draw.rounded_rectangle(
            (card[0]-i,card[1]-i,card[2]+i,card[3]+i),
            radius=35, outline=c, width=2
        )

    cover = Image.open(tmp).convert("RGB").resize((340,340))
    mask = Image.new("L",(340,340),0)
    ImageDraw.Draw(mask).rounded_rectangle((0,0,340,340),28,fill=255)
    bg.paste(cover,(255,190),mask)

    try:
        title_font = ImageFont.truetype("AxiomMuzic/assets/assets/font2.ttf", 44)
        meta_font = ImageFont.truetype("AxiomMuzic/assets/assets/font.ttf", 28)
    except:
        title_font = ImageFont.load_default()
        meta_font = ImageFont.load_default()

    draw = ImageDraw.Draw(bg)
    draw.text((640,240), trim(title), fill="white", font=title_font)
    draw.text((640,305), channel, fill=(230,230,230), font=meta_font)

    draw.line((640,400,1010,400), fill=(220,220,220), width=6)
    draw.line((640,400,820,400), fill=(140,255,0), width=6)
    draw.ellipse((810,390,830,410), fill="white")

    draw.text((640,425),"01:58", fill="white", font=meta_font)
    draw.text((960,425),duration, fill="white", font=meta_font)

    bg.save(cache)
    try: os.remove(tmp)
    except: pass
    return cache
