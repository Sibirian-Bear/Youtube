"""
Haupt-Scoring-Engine: Baut Niche-Objekte aus Rohdaten auf und berechnet
alle Scores für YouTube und Instagram.
"""
import logging
from typing import Any

from models.niche import Niche
from analyzers.faceless_filter import get_faceless_score
from analyzers.competition_analyzer import get_competition_score, classify_competition
from analyzers.platform_scorer import (
    get_cpm_score,
    get_affiliate_score,
    get_sponsoring_score,
    get_instagram_engagement_score,
    compute_youtube_score,
    compute_instagram_score,
    determine_best_platform,
)

logger = logging.getLogger(__name__)


def _headline_score(count: int, early_indicator: bool) -> float:
    """
    Normalisiert Headline-Häufigkeit auf 0–1.
    Frühindikator (EN-Quelle, noch kein DE-Trend) gibt +20% Bonus.
    """
    base = min(1.0, count / 10.0)
    if early_indicator and base < 0.8:
        base = min(1.0, base + 0.2)
    return round(base, 4)


def _build_reasoning(niche: Niche) -> str:
    """Generiert einen kurzen Begründungstext."""
    parts = []
    if niche.youtube_score >= 70:
        parts.append(f"Starkes YT-Potenzial ({niche.youtube_score:.0f}/100)")
    if niche.instagram_score >= 70:
        parts.append(f"Starkes IG-Potenzial ({niche.instagram_score:.0f}/100)")
    if niche.cpm_estimate >= 20:
        parts.append(f"Sehr hoher CPM ({niche.cpm_estimate:.0f} €)")
    if niche.affiliate_potential in ("sehr hoch", "hoch"):
        parts.append(f"Affiliate: {niche.affiliate_potential}")
    if niche.early_indicator:
        parts.append("EN-Frühindikator – DE-Trend erwartet")
    if niche.trend_direction > 5:
        parts.append(f"Wachsender Trend (+{niche.trend_direction:.0f})")
    competition_label = classify_competition(niche.competition_score)
    parts.append(f"Konkurrenz: {competition_label}")
    return " | ".join(parts) if parts else "Moderate Nische"


def score_niches(
    headline_data: dict[str, dict[str, Any]],
    trend_data: dict[str, dict[str, Any]],
    youtube_data: dict[str, dict[str, Any]],
    faceless_only: bool = True,
) -> list[Niche]:
    """
    Kombiniert alle Rohdaten zu bewerteten Niche-Objekten.

    Args:
        headline_data:  Ergebnis aus news_feeds.get_top_keywords()
        trend_data:     Ergebnis aus google_trends.get_trend_scores()
        youtube_data:   Ergebnis aus youtube_api.get_youtube_data()
        faceless_only:  Wenn True, werden Nischen mit faceless_compatible=False gefiltert

    Returns:
        Liste von Niche-Objekten, sortiert nach youtube_score (absteigend)
    """
    niches: list[Niche] = []

    for keyword, hdata in headline_data.items():
        category = hdata.get("category", "default")

        # --- Faceless Filter ---
        faceless_score, faceless_compatible = get_faceless_score(keyword, category)
        if faceless_only and not faceless_compatible:
            logger.debug(f"Gefiltert (nicht faceless): {keyword}")
            continue

        # --- Scores berechnen ---
        # Headline
        hl_score = _headline_score(hdata.get("count", 0), hdata.get("early_indicator", False))

        # Trend
        tdata = trend_data.get(keyword, {})
        trend_score = tdata.get("score", 0.0)
        trend_direction = tdata.get("direction", 0.0)
        trend_values = tdata.get("values", [])

        # YouTube-Daten
        yt_raw = youtube_data.get(keyword, {})
        search_results = yt_raw.get("search_results", 0)
        avg_views = yt_raw.get("avg_views", 0.0)
        avg_subs = yt_raw.get("avg_subs", 0.0)
        competition_score = get_competition_score(search_results, avg_subs)

        # CPM
        cpm_score, cpm_estimate = get_cpm_score(category)

        # Affiliate
        affiliate_score, affiliate_label = get_affiliate_score(category)

        # Sponsoring
        sponsoring_score, sponsoring_label = get_sponsoring_score(category)

        # Instagram Engagement
        ig_engagement = get_instagram_engagement_score(category)

        # --- Gesamt-Scores ---
        yt_score = compute_youtube_score(
            cpm_score, trend_score, competition_score,
            affiliate_score, hl_score, faceless_score
        )
        ig_score = compute_instagram_score(
            ig_engagement, sponsoring_score, trend_score, affiliate_score, hl_score
        )
        best_platform = determine_best_platform(yt_score, ig_score)

        niche = Niche(
            keyword=keyword,
            category=category,
            source_headlines=hdata.get("headlines", []),
            headline_languages=hdata.get("languages", []),
            headline_count=hdata.get("count", 0),
            trend_interest_over_time=trend_values,
            trend_direction=trend_direction,
            youtube_search_results=search_results,
            avg_channel_views=avg_views,
            avg_channel_subscribers=avg_subs,
            # YT Scores
            cpm_score=cpm_score,
            trend_score=trend_score,
            competition_score=competition_score,
            affiliate_score=affiliate_score,
            headline_score=hl_score,
            faceless_score=faceless_score,
            youtube_score=yt_score,
            # IG Scores
            engagement_potential=ig_engagement,
            sponsoring_score=sponsoring_score,
            instagram_score=ig_score,
            # Labels
            cpm_estimate=cpm_estimate,
            affiliate_potential=affiliate_label,
            sponsoring_potential=sponsoring_label,
            faceless_compatible=faceless_compatible,
            best_platform=best_platform,
            early_indicator=hdata.get("early_indicator", False),
        )
        niche.reasoning = _build_reasoning(niche)
        niches.append(niche)

    # Sortierung: primär YT-Score, sekundär IG-Score
    niches.sort(key=lambda n: (n.youtube_score, n.instagram_score), reverse=True)
    return niches
