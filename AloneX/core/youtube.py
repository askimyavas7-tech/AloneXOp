# Copyright (c) 2025 TheHamkerAlone
# Licensed under the MIT License.
# This file is part of AloneX

import os
import re
import yt_dlp
import random
import asyncio
import aiohttp
from pathlib import Path

from py_yt import Playlist, VideosSearch

from AloneX import logger
from AloneX.helpers import Track, utils


class YouTube:
    def __init__(self):
        self.base = "https://www.youtube.com/watch?v="
        self.cookies = []
        self.checked = False
        self.cookie_dir = "AloneX/cookies"
        self.warned = False
        self.regex = re.compile(
            r"(https?://)?(www\.|m\.|music\.)?"
            r"(youtube\.com/(watch\?v=|shorts/|playlist\?list=)|youtu\.be/)"
            r"([A-Za-z0-9_-]{11}|PL[A-Za-z0-9_-]+)([&?][^\s]*)?"
        )

    def get_cookies(self):
        if not self.checked:
            try:
                os.makedirs(self.cookie_dir, exist_ok=True)
                for file in os.listdir(self.cookie_dir):
                    if file.endswith(".txt"):
                        self.cookies.append(f"{self.cookie_dir}/{file}")
            except Exception:
                pass
            self.checked = True

        if not self.cookies:
            if not self.warned:
                self.warned = True
                logger.warning("Cookies are missing; downloads might fail.")
            return None
        return random.choice(self.cookies)

    async def save_cookies(self, urls: list[str]) -> None:
        """
        Downloads cookies from provided URLs and saves them as .txt files.
        IMPORTANT: Must download RAW Netscape cookies content, not batbin API JSON.
        Supports:
          - https://batbin.me/raw/<id>
          - https://batbin.me/<id>
        """
        logger.info("Saving cookies from urls...")
        os.makedirs(self.cookie_dir, exist_ok=True)

        async with aiohttp.ClientSession() as session:
            for i, url in enumerate(urls):
                u = (url or "").strip()

                # If raw is already provided, use it. Otherwise convert paste to raw.
                if "/raw/" in u:
                    link = u
                else:
                    paste_id = u.split("/")[-1].strip()
                    link = f"https://batbin.me/raw/{paste_id}"

                path = f"{self.cookie_dir}/cookie_{i}.txt"

                async with session.get(link) as resp:
                    resp.raise_for_status()
                    content = await resp.read()
                    with open(path, "wb") as fw:
                        fw.write(content)

        # reset cookie cache so new files are picked up
        self.cookies = []
        self.checked = False
        logger.info(f"Cookies saved in {self.cookie_dir}.")

    def valid(self, url: str) -> bool:
        return bool(re.match(self.regex, url))

    async def search(self, query: str, m_id: int, video: bool = False) -> Track | None:
        _search = VideosSearch(query, limit=1, with_live=False)
        results = await _search.next()
        if results and results.get("result"):
            data = results["result"][0]
            return Track(
                id=data.get("id"),
                channel_name=data.get("channel", {}).get("name"),
                duration=data.get("duration"),
                duration_sec=utils.to_seconds(data.get("duration")),
                message_id=m_id,
                title=(data.get("title") or "")[:25],
                thumbnail=(data.get("thumbnails", [{}])[-1].get("url") or "").split("?")[0],
                url=data.get("link"),
                view_count=data.get("viewCount", {}).get("short"),
                video=video,
            )
        return None

    async def playlist(self, limit: int, user: str, url: str, video: bool) -> list[Track | None]:
        tracks = []
        try:
            plist = await Playlist.get(url)
            for data in plist.get("videos", [])[:limit]:
                track = Track(
                    id=data.get("id"),
                    channel_name=data.get("channel", {}).get("name", ""),
                    duration=data.get("duration"),
                    duration_sec=utils.to_seconds(data.get("duration")),
                    title=(data.get("title") or "")[:25],
                    thumbnail=(data.get("thumbnails")[-1].get("url") or "").split("?")[0],
                    url=(data.get("link") or "").split("&list=")[0],
                    user=user,
                    view_count="",
                    video=video,
                )
                tracks.append(track)
        except Exception:
            pass
        return tracks

    async def download(self, video_id: str, video: bool = False) -> str | None:
        url = self.base + video_id
        ext = "mp4" if video else "webm"
        filename = f"downloads/{video_id}.{ext}"

        if Path(filename).exists():
            return filename

        cookie = self.get_cookies()

        # ✅ Anti-bot improvements:
        # Force android client + mobile UA (helps with "Sign in to confirm you're not a bot")
        base_opts = {
            "outtmpl": "downloads/%(id)s.%(ext)s",
            "quiet": True,
            "noplaylist": True,
            "geo_bypass": True,
            "no_warnings": True,
            "overwrites": False,
            "nocheckcertificate": True,
            "cookiefile": cookie,

            "extractor_args": {
                "youtube": {
                    "player_client": ["android"]
                }
            },
            "http_headers": {
                "User-Agent": (
                    "Mozilla/5.0 (Linux; Android 10) AppleWebKit/537.36 "
                    "(KHTML, like Gecko) Chrome/120.0 Mobile Safari/537.36"
                )
            },
        }

        if video:
            ydl_opts = {
                **base_opts,
                "format": "(bestvideo[height<=?720][width<=?1280][ext=mp4])+(bestaudio)",
                "merge_output_format": "mp4",
            }
        else:
            ydl_opts = {
                **base_opts,
                "format": "bestaudio[ext=webm][acodec=opus]/bestaudio/best",
            }

        def _download():
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                try:
                    ydl.download([url])
                except (yt_dlp.utils.DownloadError, yt_dlp.utils.ExtractorError) as ex:
                    logger.warning("Download failed (yt-dlp): %s", ex)
                    if cookie and cookie in self.cookies:
                        try:
                            self.cookies.remove(cookie)
                        except Exception:
                            pass
                    return None
                except Exception as ex:
                    logger.warning("Download failed: %s", ex)
                    return None
            return filename

        return await asyncio.to_thread(_download)
