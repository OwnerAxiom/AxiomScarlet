import asyncio

import config
from AxiomMusic import LOGGER, YouTube, app
from AxiomMusic.misc import db
from AxiomMusic.utils.database import is_autoplay
from AxiomMusic.utils.stream.queue import put_queue

AUTOPLAY_BATCH_SIZE = 3
AUTOPLAY_REFETCH_THRESHOLD = 1
_autoplay_fetching = {}


def autoplay_seed(track: dict) -> str:
    title = (track or {}).get("title") or "music"
    by = (track or {}).get("by") or ""
    if by and by not in ["Autoplay", "Unknown"]:
        return f"{title} {by}"
    return title


async def queue_autoplay_tracks(chat_id: int, seed_track: dict, limit: int = AUTOPLAY_BATCH_SIZE) -> int:
    if not seed_track or not await is_autoplay(seed_track.get("chat_id", chat_id)):
        return 0
    if _autoplay_fetching.get(chat_id):
        return 0

    _autoplay_fetching[chat_id] = True
    added = 0
    original_chat_id = seed_track.get("chat_id", chat_id)
    requester_id = seed_track.get("user_id", 0)
    streamtype = seed_track.get("streamtype", "audio")
    seed_video_id = seed_track.get("vidid")
    seed_query = autoplay_seed(seed_track)
    queries = [
        f"songs like {seed_query}",
        f"{seed_query} radio",
        f"{seed_query} similar songs",
        f"{seed_query} best songs",
    ]

    try:
        candidates = []
        if seed_video_id and seed_video_id not in ["telegram", "soundcloud"]:
            for _ in range(limit):
                try:
                    related = await YouTube.related_video(seed_video_id, original_chat_id)
                except Exception as exc:
                    LOGGER(__name__).warning(f"[AutoPlay] related lookup failed: {exc}")
                    related = None
                if related and related.get("id"):
                    candidates.append(related)

        for query in queries:
            if len(candidates) >= limit * 2:
                break
            try:
                result, vidid = await YouTube.track(query)
            except Exception as exc:
                LOGGER(__name__).warning(f"[AutoPlay] search failed for {query}: {exc}")
                continue
            if vidid:
                candidates.append(
                    {
                        "id": vidid,
                        "title": result.get("title"),
                        "duration": result.get("duration_min"),
                    }
                )

        seen = {item.get("vidid") for item in db.get(chat_id, [])}
        if seed_video_id:
            seen.add(seed_video_id)

        for candidate in candidates:
            if added >= limit:
                break
            next_id = candidate.get("id")
            if not next_id or next_id in seen:
                continue
            try:
                title, duration_min, duration_sec, _, next_vidid = await YouTube.details(
                    next_id, videoid=True
                )
            except Exception:
                title = candidate.get("title") or "Autoplay Track"
                duration_min = candidate.get("duration") or "0:00"
                duration_sec = 0
                next_vidid = next_id

            if not next_vidid or next_vidid in seen or str(duration_min) == "None":
                continue
            if duration_sec and duration_sec > config.DURATION_LIMIT:
                continue

            await put_queue(
                chat_id,
                original_chat_id,
                f"vid_{next_vidid}",
                title,
                duration_min,
                "Autoplay",
                next_vidid,
                requester_id,
                streamtype,
            )
            seen.add(next_vidid)
            added += 1

        if added:
            try:
                await app.send_message(
                    original_chat_id,
                    f"<b>♬ Autoplay added {added} next song(s) to queue.</b>",
                )
            except Exception:
                pass
        return added
    finally:
        _autoplay_fetching[chat_id] = False


async def maybe_refetch_autoplay(chat_id: int, seed_track: dict):
    if len(db.get(chat_id, [])) <= AUTOPLAY_REFETCH_THRESHOLD:
        asyncio.create_task(queue_autoplay_tracks(chat_id, seed_track))
