from calendar import month_name
from datetime import datetime
from random import choice
from asyncio import sleep as asleep
from aiohttp import ClientSession
import xml.etree.ElementTree as ET
from anitopy import parse
from bot.core.bot_instance import bot, ani_cache
from config import Var, LOGS
from .ffencoder import ffargs
from .func_utils import handle_logs
from .reporter import rep

CAPTION_FORMAT = """
<b>◆ <i>{title}</i> ◆</b>
<b>Season {anime_season} • Episode {ep_no}</b>
<b>━━━━━━━━━━━━━━━━━━━━━━━━</b>
<b>⌬ Audio:</b> <i>{audio_lang} [ESub]</i>  
<b>⌬ Status:</b> <i>{status}</i>  
<b>⌬ Total Episodes:</b> <i>{t_eps}</i>

<b>✦ Genres:</b> <i>{genres}</i>
<b>━━━━━━━━━━━━━━━━━━━━━━━━</b>
<b>✧ Powered By:</b> <i>{cred}</i>
"""

GENRES_EMOJI = {
    "Action": "👊", "Adventure": choice(['🪂', '🧗‍♀️', '🗺️']), "Comedy": "🤣",
    "Drama": "🎭", "Ecchi": choice(['💋', '🥵']), "Fantasy": choice(['🧞', '🧙‍♂️', '🐉', '🌗']),
    "Hentai": "🔞", "Horror": "☠️", "Mahou Shoujo": "☯️", "Mecha": "🤖", "Mystery": "🔮",
    "Psychological": "♟️", "Romance": "💞", "Sci-Fi": "🛸", "Slice of Life": choice(['☘️', '🍁']),
    "Sports": "⚽️", "Supernatural": "🫧", "Thriller": choice(['🥶', '🔪', '🤯']),
    "Isekai": choice(['🌌', '🌀', '🧙']), "Historical": "🏯", "Music": "🎶", "Martial Arts": "🥋",
    "School": "🏫", "Military": "🎖️", "Demons": "😈", "Vampire": "🧛‍♂️", "Space": "🚀",
    "Game": "🎮", "Crime": "🚓", "Parody": "😂", "Detective": "🕵️‍♂️", "Tragedy": "💔",
    "Yaoi": "👨‍❤️‍👨", "Yuri": "👩‍❤️‍👩", "Kids": "🧒", "Harem": "👸", "Music & Idol": "🎤",
    "Post-Apocalyptic": "☢️", "Cyberpunk": "💽", "Samurai": "🗡️", "Time Travel": "⏳"
}

GENRE_NORMALIZATION = {
    "Action & Adventure": "Action",
    "Romantic Comedy": "Comedy",
    "Shounen": "Action",
    "Shoujo": "Romance",
    "Seinen": "Drama",
    "Josei": "Drama",
    "Slice-of-Life": "Slice of Life",
    "Magical Girl": "Mahou Shoujo",
    "Science Fiction": "Sci-Fi",
    "Psychological Thriller": "Psychological",
    "Suspense": "Thriller",
    "Martial-Arts": "Martial Arts",
    "Fantasy Adventure": "Fantasy",
    "Post Apocalypse": "Post-Apocalyptic",
    "Cyber Punk": "Cyberpunk",
    "Historical Drama": "Historical",
    "Romance Comedy": "Romance",
    "Action Comedy": "Action",
    "Super Power": "Supernatural",
    "Game Based": "Game",
    "Music Idol": "Music & Idol",
    "Sports Drama": "Sports",
    "Military Sci-Fi": "Military",
    "Time-Travel": "Time Travel",
    "Detective Mystery": "Detective"
}

ANIME_GRAPHQL_QUERY = """
query ($id: Int, $search: String, $seasonYear: Int) {
  Media(id: $id, type: ANIME, format_not_in: [MOVIE, MUSIC, MANGA, NOVEL, ONE_SHOT], search: $search, seasonYear: $seasonYear) {
    id
    idMal
    title {
      romaji
      english
      native
    }
    type
    format
    status(version: 2)
    description(asHtml: false)
    startDate {
      year
      month
      day
    }
    endDate {
      year
      month
      day
    }
    season
    seasonYear
    episodes
    duration
    chapters
    volumes
    countryOfOrigin
    source
    hashtag
    trailer {
      id
      site
      thumbnail
    }
    updatedAt
    coverImage {
      large
    }
    bannerImage
    genres
    synonyms
    averageScore
    meanScore
    popularity
    trending
    favourites
    studios {
      nodes {
        name
        siteUrl
      }
    }
    isAdult
    nextAiringEpisode {
      airingAt
      timeUntilAiring
      episode
    }
    airingSchedule {
      edges {
        node {
          airingAt
          timeUntilAiring
          episode
        }
      }
    }
    externalLinks {
      url
      site
    }
    siteUrl
  }
}
"""

def normalize_genres(genres: list) -> list:
    normalized = []
    for genre in genres or []:
        genre_key = GENRE_NORMALIZATION.get(genre, genre)
        if genre_key in GENRES_EMOJI:
            normalized.append(genre_key)
    return normalized

class AniLister:
    def __init__(self, anime_name: str, year: int = None) -> None:
        self.__ani_name = anime_name
        self.__api = "https://api.jikan.moe/v4/anime"

    async def get_anidata(self):
        cache_key = f"jikan:{self.__ani_name}"
        if cache_key in ani_cache:
            return ani_cache[cache_key]

        async with ClientSession() as sess:
            # We search Jikan API. 
            async with sess.get(self.__api, params={"q": self.__ani_name, "limit": 1}) as resp:
                if resp.status == 429:
                    await asleep(2)
                    return await self.get_anidata()
                if resp.status == 200:
                    data = await resp.json()
                    results = data.get("data", [])
                    if results:
                        anime = results[0]
                        mal_id = anime.get("mal_id")
                        
                        # Get AniList ID from MALSync to preserve DB compatibility
                        anilist_id = mal_id
                        try:
                            async with sess.get(f"https://api.malsync.moe/mal/anime/{mal_id}") as sync_resp:
                                if sync_resp.status == 200:
                                    sync_data = await sync_resp.json()
                                    anilist_id = sync_data.get("AniListId") or mal_id
                        except:
                            pass

                        score = anime.get("score")
                        mapped = {
                            "id": anilist_id,
                            "idMal": mal_id,
                            "title": {
                                "english": anime.get("title_english"),
                                "romaji": anime.get("title"),
                                "native": anime.get("title_japanese")
                            },
                            "format": anime.get("type"),
                            "status": anime.get("status"),
                            "description": anime.get("synopsis"),
                            "episodes": anime.get("episodes"),
                            "averageScore": int(score * 10) if score else None,
                            "genres": [g.get("name") for g in anime.get("genres", [])] if anime.get("genres") else [],
                            "coverImage": {"large": anime.get("images", {}).get("jpg", {}).get("large_image_url")}
                        }
                        
                        # Map dates
                        aired = anime.get("aired", {})
                        prop = aired.get("prop", {}) if aired else {}
                        from_date = prop.get("from")
                        if from_date and isinstance(from_date, dict):
                            mapped["startDate"] = {"year": from_date.get("year"), "month": from_date.get("month"), "day": from_date.get("day")}
                        to_date = prop.get("to")
                        if to_date and isinstance(to_date, dict):
                            mapped["endDate"] = {"year": to_date.get("year"), "month": to_date.get("month"), "day": to_date.get("day")}
                        
                        ani_cache[cache_key] = mapped
                        return mapped
        return {}

    @handle_logs
    async def get_anilist_id(self, mal_id: int = None, name: str = None, year: int = None):
        return None

class TextEditor:
    def __init__(self, name):
        self.__name = name
        self.adata = {}
        self.pdata = parse(name)
        self.anilister = AniLister(self.__name, datetime.now().year)

    async def load_anilist(self):
        cache_names = set()
        # Add a final fallback: Search by cleaned title only (without Season/Year logic)
        variations = [(False, False), (False, True), (True, False), (True, True), "clean"]
        
        for var in variations:
            if var == "clean":
                ani_name = self.pdata.get("anime_title")
            else:
                no_s, no_y = var
                ani_name = await self.parse_name(no_s, no_y)
            
            if not ani_name or ani_name in cache_names:
                continue
            cache_names.add(ani_name)
            self.anilister = AniLister(ani_name, datetime.now().year)
            self.adata = await self.anilister.get_anidata()
            if self.adata:
                break  

    @handle_logs
    async def parse_name(self, no_s=False, no_y=False):
        anime_name = self.pdata.get("anime_title") or self.__name
        anime_season = self.pdata.get("anime_season")
        anime_year = self.pdata.get("anime_year")
        if anime_name:
            pname = anime_name
            if not no_s and self.pdata.get("episode_number") and anime_season:
                pname += f" {anime_season}"
            if not no_y and anime_year:
                pname += f" {anime_year}"
            return pname
        return anime_name

    @handle_logs
    async def get_poster(self):
        cover = self.adata.get("coverImage", {}).get("large")
        if cover:
            return cover
        anime_id = self.adata.get("id")
        if anime_id and str(anime_id).isdigit():
            return f"https://img.anili.st/media/{anime_id}"
        return "https://envs.sh/YsH.jpg"

    @handle_logs
    async def get_upname(self, qual=""):
        anime_name = self.pdata.get("anime_title")
        codec = 'HEVC' if 'libx265' in ffargs[qual] else 'AV1' if 'libaom-av1' in ffargs[qual] else ''
        lang = 'SUB' if 'sub' in self.__name.lower() else 'Sub'
        anime_season = str(ani_s[-1]) if (ani_s := self.pdata.get('anime_season', '01')) and isinstance(ani_s, list) else str(ani_s)
        if anime_name and self.pdata.get("episode_number"):
            titles = self.adata.get('title', {})
            return f"""[S{anime_season}-{'E'+str(self.pdata.get('episode_number')) if self.pdata.get('episode_number') else ''}] {titles.get('english') or titles.get('romaji') or titles.get('native')} {'['+qual+'p]' if qual else ''} {'['+codec.upper()+'] ' if codec else ''}{'['+lang+']'} {Var.BRAND_UNAME}.mkv"""
        return None

    @handle_logs
    async def get_caption(self):
        sd = self.adata.get('startDate', {})
        try:
            month_idx = int(sd.get('month')) if sd.get('month') else None
            startdate = f"{month_name[month_idx]} {sd['day']}, {sd['year']}" if sd.get('day') and sd.get('year') and month_idx else "N/A"
        except (ValueError, TypeError):
            startdate = "N/A"
        ed = self.adata.get('endDate', {})
        try:
            month_idx = int(ed.get('month')) if ed.get('month') else None
            enddate = f"{month_name[month_idx]} {ed['day']}, {sd['year']}" if ed.get('day') and ed.get('year') and month_idx else "N/A"
        except (ValueError, TypeError):
            enddate = "N/A"
        titles = self.adata.get("title", {})
        
        # Determine Audio Language
        audio_lang = "Japanese"
        lower_name = self.__name.lower()
        if "dual" in lower_name or "multi" in lower_name:
             audio_lang = "Dual Audio"
        elif "dub" in lower_name:
             audio_lang = "English"

        return CAPTION_FORMAT.format(
            title=titles.get('english') or titles.get('romaji') or titles.get('native') or "N/A",
            form=self.adata.get("format") or "N/A",
            genres=", ".join(f"{GENRES_EMOJI[x]} #{x.replace(' ', '_').replace('-', '_')}" for x in (self.adata.get('genres') or [])),
            avg_score=f"{sc}%" if (sc := self.adata.get('averageScore')) else "N/A",
            status=self.adata.get("status") or "N/A",
            start_date=startdate,
            end_date=enddate,
            t_eps=self.adata.get("episodes") or "N/A",
            anime_season=str(ani_s[-1]) if (ani_s := self.pdata.get('anime_season', '01')) and isinstance(ani_s, list) else str(ani_s),
            plot=(desc if (desc := self.adata.get("description") or "N/A") and len(desc) < 200 else desc[:200] + "...") if self.adata.get("description") else "N/A",
            ep_no=self.pdata.get("episode_number") or "N/A",
            cred=Var.BRAND_UNAME,
            audio_lang=audio_lang
        )
