"""
Plattform-spezifisches Scoring für YouTube und Instagram.

YouTube: fokussiert auf CPM + Konkurrenz + Trend
Instagram: fokussiert auf Engagement-Potenzial + Sponsoring
"""
import config


def get_cpm_score(category: str) -> tuple[float, float]:
    """
    Gibt (cpm_score 0–1, cpm_estimate EUR) zurück.
    Normalisiert auf den höchsten CPM in der Tabelle.
    """
    cpm = config.CPM_TABLE.get(category, config.CPM_TABLE["default"])
    max_cpm = max(config.CPM_TABLE.values())
    score = round(cpm / max_cpm, 4)
    return score, cpm


def get_affiliate_score(category: str) -> tuple[float, str]:
    """
    Gibt (affiliate_score 0–1, label) zurück.
    """
    potential = config.AFFILIATE_POTENTIAL.get(category, config.AFFILIATE_POTENTIAL.get("default", "niedrig"))
    score_map = {"sehr hoch": 1.0, "hoch": 0.75, "mittel": 0.45, "niedrig": 0.2}
    return score_map.get(potential, 0.2), potential


def get_sponsoring_score(category: str) -> tuple[float, str]:
    """
    Gibt (sponsoring_score 0–1, label) zurück.
    """
    potential = config.SPONSORING_POTENTIAL.get(category, config.SPONSORING_POTENTIAL.get("default", "niedrig"))
    score_map = {"sehr hoch": 1.0, "hoch": 0.75, "mittel": 0.45, "niedrig": 0.2}
    return score_map.get(potential, 0.2), potential


def get_instagram_engagement_score(category: str) -> float:
    """
    Gibt den Instagram-Engagement-Score (0–1) zurück.
    Basiert auf Save/Share-Wahrscheinlichkeit der Zielgruppe.
    """
    return config.INSTAGRAM_ENGAGEMENT.get(category, config.INSTAGRAM_ENGAGEMENT["default"])


def compute_youtube_score(
    cpm_score: float,
    trend_score: float,
    competition_score: float,
    affiliate_score: float,
    headline_score: float,
    faceless_score: float,
) -> float:
    """Gewichteter YouTube-Gesamt-Score (0–100)."""
    raw = (
        cpm_score          * config.WEIGHTS_YOUTUBE["cpm_score"] +
        trend_score        * config.WEIGHTS_YOUTUBE["trend_score"] +
        competition_score  * config.WEIGHTS_YOUTUBE["competition_score"] +
        affiliate_score    * config.WEIGHTS_YOUTUBE["affiliate_score"] +
        headline_score     * config.WEIGHTS_YOUTUBE["headline_score"] +
        faceless_score     * config.WEIGHTS_YOUTUBE["faceless_score"]
    )
    return round(raw * 100, 2)


def compute_instagram_score(
    engagement_potential: float,
    sponsoring_score: float,
    trend_score: float,
    affiliate_score: float,
    headline_score: float,
) -> float:
    """Gewichteter Instagram-Gesamt-Score (0–100)."""
    raw = (
        engagement_potential * config.WEIGHTS_INSTAGRAM["engagement_potential"] +
        sponsoring_score     * config.WEIGHTS_INSTAGRAM["sponsoring_score"] +
        trend_score          * config.WEIGHTS_INSTAGRAM["trend_score"] +
        affiliate_score      * config.WEIGHTS_INSTAGRAM["affiliate_score"] +
        headline_score       * config.WEIGHTS_INSTAGRAM["headline_score"]
    )
    return round(raw * 100, 2)


def determine_best_platform(yt_score: float, ig_score: float) -> str:
    """Bestimmt die beste Plattform anhand der Scores."""
    diff = abs(yt_score - ig_score)
    if diff < 8:
        return "Beide"
    return "YouTube" if yt_score > ig_score else "Instagram"
