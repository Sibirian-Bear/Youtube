"""
Google Trends Scraper für den DE-Markt via pytrends.

Features:
- Batch-Verarbeitung (max 5 Keywords pro Request)
- Rate-Limiting
- Berechnet Trend-Richtung (steigend / fallend)
- Gibt normalisierte Scores zurück (0.0–1.0)
"""
import time
import logging
from typing import Any

try:
    from pytrends.request import TrendReq
    PYTRENDS_AVAILABLE = True
except ImportError:
    PYTRENDS_AVAILABLE = False

import config

logger = logging.getLogger(__name__)

BATCH_SIZE = 5   # pytrends-Limit pro Request


def _build_client() -> Any | None:
    if not PYTRENDS_AVAILABLE:
        logger.warning("pytrends nicht installiert – Google Trends deaktiviert.")
        return None
    try:
        return TrendReq(hl="de-DE", tz=60, timeout=(10, 30), retries=2, backoff_factor=0.5)
    except Exception as e:
        logger.error(f"pytrends Client konnte nicht erstellt werden: {e}")
        return None


def _fetch_batch(client: Any, keywords: list[str]) -> dict[str, dict[str, Any]]:
    """
    Ruft Trend-Daten für eine Batch von max. 5 Keywords ab.
    Gibt dict zurück: { keyword: {"values": [...], "avg": float, "direction": float, "score": float} }
    """
    results: dict[str, dict[str, Any]] = {}
    try:
        client.build_payload(
            kw_list=keywords,
            timeframe=config.TRENDS_TIMEFRAME,
            geo=config.MARKET_GEO,
        )
        df = client.interest_over_time()
        if df is None or df.empty:
            return {kw: _zero_result() for kw in keywords}

        for kw in keywords:
            if kw not in df.columns:
                results[kw] = _zero_result()
                continue
            values = df[kw].tolist()
            avg = sum(values) / len(values) if values else 0.0
            # Trend-Richtung: Steigung über letztes Drittel vs. erstes Drittel
            third = max(1, len(values) // 3)
            recent_avg = sum(values[-third:]) / third
            early_avg = sum(values[:third]) / third
            direction = recent_avg - early_avg   # positiv = wachsend
            # Score: aktuellster Wert normalisiert + Richtungsbonus
            latest = values[-1] if values else 0
            raw_score = min(1.0, latest / 100.0)
            if direction > 5:
                raw_score = min(1.0, raw_score + 0.2)
            results[kw] = {
                "values": [int(v) for v in values],
                "avg": round(avg, 2),
                "direction": round(direction, 2),
                "score": round(raw_score, 4),
            }
    except Exception as e:
        logger.warning(f"Trends-Fehler für Batch {keywords}: {e}")
        for kw in keywords:
            results[kw] = _zero_result()
    return results


def _zero_result() -> dict[str, Any]:
    return {"values": [], "avg": 0.0, "direction": 0.0, "score": 0.0}


def get_trend_scores(keywords: list[str]) -> dict[str, dict[str, Any]]:
    """
    Gibt Trend-Daten für alle übergebenen Keywords zurück.
    Verarbeitet in Batches von 5, mit Rate-Limiting.
    """
    if not keywords:
        return {}

    client = _build_client()
    if not client:
        # Fallback: neutrale Scores
        return {kw: _zero_result() for kw in keywords}

    all_results: dict[str, dict[str, Any]] = {}
    batches = [keywords[i:i + BATCH_SIZE] for i in range(0, len(keywords), BATCH_SIZE)]

    for i, batch in enumerate(batches):
        logger.info(f"Trends-Batch {i+1}/{len(batches)}: {batch}")
        batch_results = _fetch_batch(client, batch)
        all_results.update(batch_results)
        if i < len(batches) - 1:
            time.sleep(config.PYTRENDS_DELAY)

    return all_results
