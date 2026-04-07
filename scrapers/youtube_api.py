"""
YouTube Data API v3 Wrapper mit Fallback-Scraping.

Mit API Key:
  - search.list für Suchergebnisanzahl
  - channels.list für Kanal-Statistiken

Ohne API Key:
  - Schätzungen basierend auf Kategorie-Defaults
"""
import time
import logging
from typing import Any

YOUTUBE_API_AVAILABLE = False
try:
    from googleapiclient.discovery import build  # noqa: F401
    YOUTUBE_API_AVAILABLE = True
except BaseException:
    pass

import config

logger = logging.getLogger(__name__)

# Fallback-Schätzwerte nach Kategorie (ohne API Key)
COMPETITION_DEFAULTS: dict[str, dict[str, Any]] = {
    "ki tools":               {"results": 85_000,  "avg_views": 45_000,  "avg_subs": 25_000},
    "künstliche intelligenz": {"results": 120_000, "avg_views": 38_000,  "avg_subs": 20_000},
    "finanzen":               {"results": 950_000, "avg_views": 55_000,  "avg_subs": 40_000},
    "investing":              {"results": 800_000, "avg_views": 48_000,  "avg_subs": 35_000},
    "steuern":                {"results": 320_000, "avg_views": 28_000,  "avg_subs": 15_000},
    "versicherung":           {"results": 250_000, "avg_views": 22_000,  "avg_subs": 12_000},
    "immobilien":             {"results": 420_000, "avg_views": 35_000,  "avg_subs": 22_000},
    "software":               {"results": 1_200_000,"avg_views": 30_000, "avg_subs": 18_000},
    "technologie":            {"results": 2_000_000,"avg_views": 40_000, "avg_subs": 30_000},
    "nachrichten":            {"results": 3_000_000,"avg_views": 15_000, "avg_subs": 10_000},
    "automatisierung":        {"results": 180_000, "avg_views": 32_000,  "avg_subs": 18_000},
    "produktivität":          {"results": 350_000, "avg_views": 28_000,  "avg_subs": 16_000},
    "gesundheit":             {"results": 1_500_000,"avg_views": 25_000, "avg_subs": 15_000},
    "gaming":                 {"results": 5_000_000,"avg_views": 80_000, "avg_subs": 60_000},
    "reisen":                 {"results": 1_800_000,"avg_views": 20_000, "avg_subs": 12_000},
    "default":                {"results": 500_000, "avg_views": 25_000,  "avg_subs": 15_000},
}


def _get_client() -> Any | None:
    if not YOUTUBE_API_AVAILABLE or not config.YOUTUBE_API_KEY:
        return None
    try:
        from googleapiclient.discovery import build
        return build("youtube", "v3", developerKey=config.YOUTUBE_API_KEY)
    except Exception as e:
        logger.error(f"YouTube API Client Fehler: {e}")
        return None


def _search_results_count(client: Any, keyword: str) -> int:
    """Gibt die approximierte Anzahl an Suchergebnissen zurück."""
    try:
        response = client.search().list(
            q=keyword,
            part="snippet",
            type="video",
            regionCode="DE",
            relevanceLanguage="de",
            maxResults=1,
        ).execute()
        time.sleep(config.YOUTUBE_API_DELAY)
        # YouTube gibt keine genaue Zahl – nutzen wir pageInfo.totalResults
        return int(response.get("pageInfo", {}).get("totalResults", 0))
    except Exception as e:
        logger.warning(f"YouTube search Fehler für '{keyword}': {e}")
        return 0


def _get_top_channel_stats(client: Any, keyword: str, max_results: int = 10) -> dict[str, float]:
    """Holt Statistiken der Top-Kanäle für ein Keyword."""
    try:
        search_resp = client.search().list(
            q=keyword,
            part="snippet",
            type="channel",
            regionCode="DE",
            relevanceLanguage="de",
            maxResults=max_results,
        ).execute()
        time.sleep(config.YOUTUBE_API_DELAY)

        channel_ids = [
            item["id"]["channelId"]
            for item in search_resp.get("items", [])
            if item.get("id", {}).get("kind") == "youtube#channel"
        ]
        if not channel_ids:
            return {"avg_views": 0.0, "avg_subs": 0.0}

        stats_resp = client.channels().list(
            id=",".join(channel_ids),
            part="statistics",
        ).execute()
        time.sleep(config.YOUTUBE_API_DELAY)

        views, subs = [], []
        for item in stats_resp.get("items", []):
            stats = item.get("statistics", {})
            try:
                views.append(int(stats.get("viewCount", 0)))
                subs.append(int(stats.get("subscriberCount", 0)))
            except (ValueError, TypeError):
                pass

        return {
            "avg_views": sum(views) / len(views) if views else 0.0,
            "avg_subs": sum(subs) / len(subs) if subs else 0.0,
        }
    except Exception as e:
        logger.warning(f"YouTube channel stats Fehler für '{keyword}': {e}")
        return {"avg_views": 0.0, "avg_subs": 0.0}


def _fallback_data(category: str) -> dict[str, Any]:
    """Gibt Schätzwerte zurück wenn kein API Key vorhanden."""
    data = COMPETITION_DEFAULTS.get(category, COMPETITION_DEFAULTS["default"])
    return {
        "search_results": data["results"],
        "avg_views": float(data["avg_views"]),
        "avg_subs": float(data["avg_subs"]),
        "source": "fallback",
    }


def get_youtube_data(keywords_with_categories: dict[str, str]) -> dict[str, dict[str, Any]]:
    """
    Holt YouTube-Daten für alle Keywords.

    Args:
        keywords_with_categories: { keyword: category }

    Returns:
        { keyword: {"search_results": int, "avg_views": float, "avg_subs": float, "source": str} }
    """
    client = _get_client()
    results: dict[str, dict[str, Any]] = {}

    for keyword, category in keywords_with_categories.items():
        if client:
            count = _search_results_count(client, keyword)
            stats = _get_top_channel_stats(client, keyword)
            results[keyword] = {
                "search_results": count,
                "avg_views": stats["avg_views"],
                "avg_subs": stats["avg_subs"],
                "source": "api",
            }
        else:
            results[keyword] = _fallback_data(category)

    if not client:
        logger.info("YouTube API nicht verfügbar – verwende Kategorie-Fallback-Werte.")

    return results
