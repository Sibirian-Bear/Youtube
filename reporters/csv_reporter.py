"""
CSV-Reporter: Schreibt alle Nischen mit vollständigen Scores in eine CSV-Datei.
"""
import csv
import os
from datetime import date
from models.niche import Niche

RESULTS_DIR = "results"

COLUMNS = [
    "rank", "keyword", "category",
    "youtube_score", "instagram_score", "best_platform",
    "cpm_estimate", "affiliate_potential", "sponsoring_potential",
    "trend_direction", "competition_score",
    "faceless_compatible", "early_indicator",
    "headline_count", "headline_languages",
    "cpm_score", "trend_score", "affiliate_score", "headline_score", "faceless_score",
    "engagement_potential", "sponsoring_score",
    "youtube_search_results", "avg_channel_views", "avg_channel_subscribers",
    "source_headlines", "reasoning",
]


def write_csv(niches: list[Niche], filename: str | None = None) -> str:
    """
    Schreibt die Nischen-Liste als CSV.
    Gibt den Dateipfad zurück.
    """
    os.makedirs(RESULTS_DIR, exist_ok=True)
    if not filename:
        filename = f"niche_report_{date.today()}.csv"
    filepath = os.path.join(RESULTS_DIR, filename)

    with open(filepath, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=COLUMNS, extrasaction="ignore")
        writer.writeheader()
        for rank, niche in enumerate(niches, 1):
            row = niche.to_dict()
            row["rank"] = rank
            writer.writerow(row)

    return filepath
