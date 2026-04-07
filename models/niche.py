"""
Niche-Datenmodell: hält alle Rohdaten und berechneten Scores
für YouTube und Instagram.
"""
from dataclasses import dataclass, field, asdict
from typing import Any


@dataclass
class Niche:
    # --- Basisdaten ---
    keyword: str
    category: str
    source_headlines: list[str] = field(default_factory=list)
    headline_languages: list[str] = field(default_factory=list)   # z.B. ["de", "en"]
    headline_count: int = 0

    # --- Rohdaten (Trends & YouTube) ---
    trend_interest_over_time: list[int] = field(default_factory=list)  # pytrends 0–100
    trend_direction: float = 0.0          # positiv = wachsend, negativ = fallend
    youtube_search_results: int = 0
    avg_channel_views: float = 0.0
    avg_channel_subscribers: float = 0.0

    # --- YouTube-Scores (0.0–1.0) ---
    cpm_score: float = 0.0
    trend_score: float = 0.0
    competition_score: float = 0.0
    affiliate_score: float = 0.0
    headline_score: float = 0.0
    faceless_score: float = 0.0
    youtube_score: float = 0.0            # gewichtetes Gesamt-Score YT (0–100)

    # --- Instagram-Scores (0.0–1.0) ---
    engagement_potential: float = 0.0    # Wahrscheinlichkeit für Saves/Shares
    sponsoring_score: float = 0.0        # Brand-Deal-Attraktivität
    instagram_score: float = 0.0         # gewichtetes Gesamt-Score IG (0–100)

    # --- Schätzwerte & Labels ---
    cpm_estimate: float = 0.0            # EUR
    affiliate_potential: str = ""        # "sehr hoch" / "hoch" / "mittel" / "niedrig"
    sponsoring_potential: str = ""
    faceless_compatible: bool = True
    best_platform: str = ""              # "YouTube" | "Instagram" | "Beide"
    early_indicator: bool = False        # True wenn EN-Headlines vor DE-Trend
    reasoning: str = ""

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        # Listen für CSV lesbar machen
        d["source_headlines"] = " | ".join(self.source_headlines[:3])
        d["headline_languages"] = ",".join(sorted(set(self.headline_languages)))
        d["trend_interest_over_time"] = str(self.trend_interest_over_time[-3:]) if self.trend_interest_over_time else "[]"
        return d

    @property
    def combined_score(self) -> float:
        """Mittelwert YT + IG für Ranking nach Gesamt-Potenzial."""
        scores = [s for s in [self.youtube_score, self.instagram_score] if s > 0]
        return sum(scores) / len(scores) if scores else 0.0
