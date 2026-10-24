import os
import json
import logging
import threading
from concurrent.futures import ThreadPoolExecutor
from typing import List, Dict, Any, Optional
import requests
from dotenv import load_dotenv

# Load environment variables: local .env for development, environment variable in production
env_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
if os.path.exists(env_file):
    load_dotenv(env_file)
else:
    load_dotenv()
TMDB_API_KEY = os.getenv("TMDB_API_KEY", "")

CACHE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "tmdb_cache.json")
logger = logging.getLogger(__name__)

_cache_lock = threading.Lock()
_memory_cache: Dict[str, Dict[str, Any]] = {}

def _load_cache():
    global _memory_cache
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, "r", encoding="utf-8") as f:
                _memory_cache = json.load(f)
        except Exception as e:
            logger.warning(f"Failed to load TMDB cache file: {e}")
            _memory_cache = {}

def _save_cache():
    try:
        os.makedirs(os.path.dirname(CACHE_FILE), exist_ok=True)
        temp_file = CACHE_FILE + ".tmp"
        with open(temp_file, "w", encoding="utf-8") as f:
            json.dump(_memory_cache, f, ensure_ascii=False)
        if os.path.exists(temp_file):
            if os.path.exists(CACHE_FILE):
                os.replace(temp_file, CACHE_FILE)
            else:
                os.rename(temp_file, CACHE_FILE)
    except Exception as e:
        logger.warning(f"Failed to save TMDB cache file: {e}")

_load_cache()

def get_movie_details(tmdb_id: Optional[Any]) -> Dict[str, Any]:
    default_details = {
        "poster_url": None,
        "backdrop_url": None,
        "overview": None,
        "release_date": None,
        "vote_average": None,
        "runtime": None,
        "tagline": None,
        "cast": [],
        "trailer_key": None
    }
    
    if tmdb_id is None:
        return default_details
        
    try:
        tmdb_str = str(int(float(tmdb_id)))
    except (ValueError, TypeError):
        return default_details

    # Check cache - must contain newly required fields to be considered valid
    with _cache_lock:
        if tmdb_str in _memory_cache:
            cached = _memory_cache[tmdb_str]
            # Old cache entries without backdrop_url or cast must be refetched automatically
            if "backdrop_url" in cached and "cast" in cached and "trailer_key" in cached:
                return cached

    if not TMDB_API_KEY or TMDB_API_KEY == "your_key_here":
        return default_details

    # Single request appending credits and videos
    url = f"https://api.themoviedb.org/3/movie/{tmdb_str}?api_key={TMDB_API_KEY}&append_to_response=credits,videos"
    try:
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            data = response.json()
            poster_path = data.get("poster_path")
            poster_url = f"https://image.tmdb.org/t/p/w500{poster_path}" if poster_path else None
            
            backdrop_path = data.get("backdrop_path")
            backdrop_url = f"https://image.tmdb.org/t/p/w1280{backdrop_path}" if backdrop_path else None

            overview = data.get("overview") or None
            release_date = data.get("release_date") or None
            vote_avg = data.get("vote_average")
            vote_average = round(float(vote_avg), 1) if vote_avg is not None else None
            
            runtime_raw = data.get("runtime")
            runtime = int(runtime_raw) if runtime_raw is not None and str(runtime_raw).isdigit() else None
            tagline = data.get("tagline") or None

            # Top 6 cast members
            cast = []
            credits_data = data.get("credits", {})
            raw_cast = credits_data.get("cast", []) if isinstance(credits_data, dict) else []
            for member in raw_cast[:6]:
                p_path = member.get("profile_path")
                cast.append({
                    "name": member.get("name"),
                    "character": member.get("character"),
                    "profile_url": f"https://image.tmdb.org/t/p/w185{p_path}" if p_path else None
                })

            # YouTube trailer key
            trailer_key = None
            videos_data = data.get("videos", {})
            raw_videos = videos_data.get("results", []) if isinstance(videos_data, dict) else []
            for vid in raw_videos:
                if vid.get("site") == "YouTube" and vid.get("type") == "Trailer" and vid.get("official") is True:
                    trailer_key = vid.get("key")
                    break
            if not trailer_key:
                for vid in raw_videos:
                    if vid.get("site") == "YouTube" and vid.get("type") == "Trailer":
                        trailer_key = vid.get("key")
                        break
            if not trailer_key:
                for vid in raw_videos:
                    if vid.get("site") == "YouTube":
                        trailer_key = vid.get("key")
                        break

            details = {
                "poster_url": poster_url,
                "backdrop_url": backdrop_url,
                "overview": overview,
                "release_date": release_date,
                "vote_average": vote_average,
                "runtime": runtime,
                "tagline": tagline,
                "cast": cast,
                "trailer_key": trailer_key
            }
            with _cache_lock:
                _memory_cache[tmdb_str] = details
                _save_cache()
            return details
        else:
            with _cache_lock:
                _memory_cache[tmdb_str] = default_details
                _save_cache()
            return default_details
    except Exception as e:
        logger.warning(f"TMDB request failed for ID {tmdb_str}: {e}")
        return default_details

def enrich_movie_cards(movie_cards: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    if not movie_cards:
        return []

    def _enrich_single(card: Dict[str, Any]) -> Dict[str, Any]:
        tmdb_id = card.get("tmdbId")
        details = get_movie_details(tmdb_id)
        card_copy = dict(card)
        card_copy["poster_url"] = details.get("poster_url")
        card_copy["backdrop_url"] = details.get("backdrop_url")
        card_copy["overview"] = details.get("overview")
        card_copy["tmdb_rating"] = details.get("vote_average")
        card_copy["runtime"] = details.get("runtime")
        card_copy["tagline"] = details.get("tagline")
        card_copy["cast"] = details.get("cast", [])
        card_copy["trailer_key"] = details.get("trailer_key")
        if not card_copy.get("year") and details.get("release_date"):
            try:
                card_copy["year"] = int(details["release_date"].split("-")[0])
            except Exception:
                pass
        return card_copy

    with ThreadPoolExecutor(max_workers=6) as executor:
        enriched = list(executor.map(_enrich_single, movie_cards))
    return enriched
