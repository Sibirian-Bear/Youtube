#!/usr/bin/env python3
"""
YouTube + Instagram Nischen-Research-Tool
Deutscher Markt | Faceless-Strategie | Mehrsprachige Headline-Analyse

Verwendung:
    python main.py --platform both --top 20
    python main.py --platform youtube --categories finanzen,ki tools
    YOUTUBE_API_KEY=xxx python main.py --platform both --top 15
"""
import argparse
import logging
import sys
import os
from datetime import datetime

from colorama import init, Fore, Style

# Scrapers
from scrapers.news_feeds import get_top_keywords
from scrapers.google_trends import get_trend_scores
from scrapers.youtube_api import get_youtube_data

# Analyzers
from analyzers.niche_scorer import score_niches

# Reporters
from reporters.csv_reporter import write_csv
from reporters.summary_reporter import print_console_summary, write_markdown_report

init(autoreset=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)
# Unterdrücke noisy Bibliotheks-Logs
logging.getLogger("pytrends").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)
logging.getLogger("googleapiclient").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="YouTube + Instagram Nischen-Research-Tool (DE, Faceless)"
    )
    parser.add_argument(
        "--platform",
        choices=["youtube", "instagram", "both"],
        default="both",
        help="Plattform für Scoring-Fokus (Standard: both)",
    )
    parser.add_argument(
        "--top",
        type=int,
        default=20,
        help="Anzahl Top-Nischen im Report (Standard: 20)",
    )
    parser.add_argument(
        "--keywords",
        type=int,
        default=50,
        help="Max. Keywords aus Headlines (Standard: 50)",
    )
    parser.add_argument(
        "--categories",
        type=str,
        default=None,
        help="Komma-getrennte Kategorien filtern, z.B. 'finanzen,ki tools'",
    )
    parser.add_argument(
        "--no-faceless-filter",
        action="store_true",
        help="Alle Nischen anzeigen, nicht nur Faceless-geeignete",
    )
    parser.add_argument(
        "--no-trends",
        action="store_true",
        help="Google Trends überspringen (schneller, weniger genau)",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="results",
        help="Ausgabe-Verzeichnis für Reports (Standard: results/)",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Ausführliche Log-Ausgabe",
    )
    return parser.parse_args()


def _step(msg: str) -> None:
    print(Fore.CYAN + f"\n▶ {msg}" + Style.RESET_ALL)


def _ok(msg: str) -> None:
    print(Fore.GREEN + f"  ✓ {msg}" + Style.RESET_ALL)


def _warn(msg: str) -> None:
    print(Fore.YELLOW + f"  ⚠ {msg}" + Style.RESET_ALL)


def main() -> None:
    args = parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    print(Fore.CYAN + Style.BRIGHT + "\n" + "═" * 60)
    print(Fore.CYAN + Style.BRIGHT + "  YouTube + Instagram Nischen-Research-Tool")
    print(Fore.CYAN + Style.BRIGHT + f"  Markt: DE  │  Strategie: Faceless  │  {datetime.now():%Y-%m-%d %H:%M}")
    print(Fore.CYAN + Style.BRIGHT + "═" * 60 + "\n")

    if not os.getenv("YOUTUBE_API_KEY"):
        _warn("YOUTUBE_API_KEY nicht gesetzt – nutze Fallback-Schätzwerte.")
        _warn("Für präzisere Daten: export YOUTUBE_API_KEY=dein_key")

    # ── Schritt 1: Headlines scrapen ──────────────────────────────────────
    _step(f"Scrappe mehrsprachige Headlines (DE/EN/FR/ES) ...")
    try:
        headline_data = get_top_keywords(limit=args.keywords)
        _ok(f"{len(headline_data)} Keyword-Kandidaten gefunden")
    except Exception as e:
        print(Fore.RED + f"  ✗ Headlines-Fehler: {e}")
        sys.exit(1)

    # Kategorie-Filter anwenden
    if args.categories:
        cats = [c.strip().lower() for c in args.categories.split(",")]
        headline_data = {
            k: v for k, v in headline_data.items()
            if any(cat in v.get("category", "") or cat in k.lower() for cat in cats)
        }
        _ok(f"Nach Kategorien-Filter: {len(headline_data)} Keywords")
        if not headline_data:
            _warn("Keine Keywords nach Filter – erweitere --categories oder entferne den Filter.")
            sys.exit(0)

    keywords_list = list(headline_data.keys())
    keywords_with_cats = {k: headline_data[k].get("category", "default") for k in keywords_list}

    # ── Schritt 2: Google Trends ──────────────────────────────────────────
    if args.no_trends:
        _warn("Google Trends übersprungen (--no-trends).")
        trend_data = {kw: {"values": [], "avg": 0.0, "direction": 0.0, "score": 0.0} for kw in keywords_list}
    else:
        _step(f"Analysiere Google Trends (DE) für {len(keywords_list)} Keywords ...")
        try:
            trend_data = get_trend_scores(keywords_list)
            trending_up = sum(1 for v in trend_data.values() if v.get("direction", 0) > 5)
            _ok(f"Trend-Daten geladen – {trending_up} Keywords mit wachsendem Trend")
        except Exception as e:
            _warn(f"Google Trends Fehler: {e} – fahre mit Null-Trends fort")
            trend_data = {kw: {"values": [], "avg": 0.0, "direction": 0.0, "score": 0.0} for kw in keywords_list}

    # ── Schritt 3: YouTube-Daten ──────────────────────────────────────────
    _step(f"Lade YouTube-Daten für {len(keywords_list)} Keywords ...")
    try:
        youtube_data = get_youtube_data(keywords_with_cats)
        from scrapers.youtube_api import YOUTUBE_API_AVAILABLE
        source = "API" if (YOUTUBE_API_AVAILABLE and os.getenv("YOUTUBE_API_KEY")) else "Fallback-Schätzwerte"
        _ok(f"YouTube-Daten geladen ({source})")
    except Exception as e:
        _warn(f"YouTube-Daten Fehler: {e} – nutze Defaults")
        youtube_data = {}

    # ── Schritt 4: Scoring ────────────────────────────────────────────────
    _step("Berechne Nischen-Scores (YT + IG) ...")
    faceless_only = not args.no_faceless_filter
    niches = score_niches(headline_data, trend_data, youtube_data, faceless_only=faceless_only)

    if not niches:
        print(Fore.RED + "  ✗ Keine geeigneten Nischen gefunden. Prüfe --no-faceless-filter oder --categories.")
        sys.exit(1)

    _ok(f"{len(niches)} Nischen bewertet")

    early_count = sum(1 for n in niches if n.early_indicator)
    if early_count:
        _ok(f"{early_count} EN-Frühindikatoren identifiziert (First-Mover-Potenzial!)")

    # ── Schritt 5: Report ausgeben ────────────────────────────────────────
    _step("Erstelle Reports ...")

    # Console
    print_console_summary(niches, top_n=min(args.top, len(niches)))

    # CSV
    csv_path = write_csv(niches)
    _ok(f"CSV-Report: {csv_path}")

    # Markdown
    md_path = write_markdown_report(niches, top_n=args.top)
    _ok(f"Markdown-Report: {md_path}")

    print(Fore.GREEN + Style.BRIGHT + f"\n  Fertig! Top-Nische: {niches[0].keyword.title()} "
          f"(YT: {niches[0].youtube_score:.0f} | IG: {niches[0].instagram_score:.0f})\n")


if __name__ == "__main__":
    main()
