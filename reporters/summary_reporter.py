"""
Summary-Reporter: Generiert menschenlesbaren Report als Markdown + Console-Output.
"""
import os
from datetime import date
from colorama import init, Fore, Style

from models.niche import Niche

init(autoreset=True)
RESULTS_DIR = "results"


def _trend_arrow(direction: float) -> str:
    if direction > 5:
        return f"↑ +{direction:.0f}"
    elif direction < -5:
        return f"↓ {direction:.0f}"
    return "→ stabil"


def _bar(score: float, width: int = 10) -> str:
    """Einfacher ASCII-Fortschrittsbalken."""
    filled = int(round(score / 10))
    return "█" * filled + "░" * (width - filled)


def print_console_summary(niches: list[Niche], top_n: int = 10) -> None:
    """Gibt Top-N Nischen farbig in der Konsole aus."""
    top = niches[:top_n]
    today = date.today()

    print()
    print(Fore.CYAN + Style.BRIGHT + f"{'='*90}")
    print(Fore.CYAN + Style.BRIGHT + f"  TOP {top_n} NISCHEN  │  DE-Markt │ Faceless │ {today}")
    print(Fore.CYAN + Style.BRIGHT + f"{'='*90}")
    print(
        f"{'#':>3}  {'Nische':<28} {'YT':>6} {'IG':>6}  {'CPM':>5}  {'Trend':>9}  "
        f"{'Affiliate':<10}  {'Plattform':<12}  {'Frühind.'}"
    )
    print(Fore.WHITE + "─" * 90)

    for i, n in enumerate(top, 1):
        early = Fore.YELLOW + "★ EN-Lead" + Style.RESET_ALL if n.early_indicator else ""
        platform_color = Fore.GREEN if n.best_platform == "Beide" else Fore.BLUE
        yt_color = Fore.GREEN if n.youtube_score >= 70 else Fore.YELLOW if n.youtube_score >= 50 else Fore.RED
        ig_color = Fore.GREEN if n.instagram_score >= 70 else Fore.YELLOW if n.instagram_score >= 50 else Fore.RED

        print(
            f"{i:>3}  {n.keyword:<28} "
            f"{yt_color}{n.youtube_score:>6.1f}{Style.RESET_ALL} "
            f"{ig_color}{n.instagram_score:>6.1f}{Style.RESET_ALL}  "
            f"{n.cpm_estimate:>4.0f}€  "
            f"{_trend_arrow(n.trend_direction):>9}  "
            f"{n.affiliate_potential:<10}  "
            f"{platform_color}{n.best_platform:<12}{Style.RESET_ALL}  "
            f"{early}"
        )

    print(Fore.WHITE + "─" * 90)
    print(Fore.WHITE + "  Scores 0–100  │  ★ = Trend noch nicht im DE-Markt angekommen")
    print()

    # Detailansicht Top-3
    print(Fore.CYAN + Style.BRIGHT + "  DETAIL: TOP 3 NISCHEN")
    print(Fore.CYAN + "─" * 90)
    for n in top[:3]:
        yt_bar = _bar(n.youtube_score)
        ig_bar = _bar(n.instagram_score)
        print(f"\n  {Style.BRIGHT}{n.keyword.upper()}{Style.RESET_ALL}  [{n.category}]")
        print(f"  YouTube   {yt_bar} {n.youtube_score:.1f}/100   │  CPM: {n.cpm_estimate:.0f} €  │  "
              f"Affiliate: {n.affiliate_potential}  │  Konkurrenz: {_competition_label(n.competition_score)}")
        print(f"  Instagram {ig_bar} {n.instagram_score:.1f}/100  │  Engagement: {n.engagement_potential:.0%}  │  "
              f"Sponsoring: {n.sponsoring_potential}")
        print(f"  {Fore.WHITE}→ {n.reasoning}{Style.RESET_ALL}")
        if n.source_headlines:
            print(f"  Beispiel-Headlines:")
            for hl in n.source_headlines[:2]:
                print(f"    • {hl[:100]}")
    print()


def _competition_label(score: float) -> str:
    if score >= 0.8:
        return "sehr niedrig"
    elif score >= 0.6:
        return "niedrig"
    elif score >= 0.4:
        return "mittel"
    elif score >= 0.2:
        return "hoch"
    return "sehr hoch"


def write_markdown_report(niches: list[Niche], top_n: int = 20, filename: str | None = None) -> str:
    """
    Schreibt einen Markdown-Report mit Top-N Nischen.
    Gibt den Dateipfad zurück.
    """
    os.makedirs(RESULTS_DIR, exist_ok=True)
    today = date.today()
    if not filename:
        filename = f"top_niches_{today}.md"
    filepath = os.path.join(RESULTS_DIR, filename)

    top = niches[:top_n]

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(f"# YouTube + Instagram Nischen-Report\n")
        f.write(f"**Datum:** {today}  |  **Markt:** DE  |  **Strategie:** Faceless  \n\n")
        f.write(f"---\n\n")

        # Übersichtstabelle
        f.write("## Top-Nischen Übersicht\n\n")
        f.write("| # | Nische | YT-Score | IG-Score | CPM (€) | Trend | Affiliate | Beste Plattform | Frühindikator |\n")
        f.write("|---|--------|----------|----------|---------|-------|-----------|-----------------|---------------|\n")
        for i, n in enumerate(top, 1):
            early = "★ EN-Lead" if n.early_indicator else ""
            trend = _trend_arrow(n.trend_direction)
            f.write(
                f"| {i} | **{n.keyword}** | {n.youtube_score:.1f} | {n.instagram_score:.1f} | "
                f"{n.cpm_estimate:.0f} € | {trend} | {n.affiliate_potential} | "
                f"{n.best_platform} | {early} |\n"
            )

        f.write("\n---\n\n")

        # Detail-Karten Top-10
        f.write("## Nischen-Details (Top 10)\n\n")
        for i, n in enumerate(top[:10], 1):
            f.write(f"### {i}. {n.keyword.title()}\n\n")
            f.write(f"**Kategorie:** {n.category}  |  **Beste Plattform:** {n.best_platform}  ")
            if n.early_indicator:
                f.write("  ⭐ *EN-Frühindikator: Trend noch nicht im DE-Markt*")
            f.write("\n\n")
            f.write(f"| Metrik | YouTube | Instagram |\n")
            f.write(f"|--------|---------|----------|\n")
            f.write(f"| **Gesamt-Score** | {n.youtube_score:.1f}/100 | {n.instagram_score:.1f}/100 |\n")
            f.write(f"| CPM / Engagement | {n.cpm_estimate:.0f} € | {n.engagement_potential:.0%} Save-Rate |\n")
            f.write(f"| Affiliate | {n.affiliate_potential} | {n.affiliate_potential} |\n")
            f.write(f"| Sponsoring | {n.sponsoring_potential} | {n.sponsoring_potential} |\n")
            f.write(f"| Konkurrenz | {_competition_label(n.competition_score)} | – |\n")
            f.write(f"| Trend | {_trend_arrow(n.trend_direction)} | {_trend_arrow(n.trend_direction)} |\n")
            f.write(f"\n**Begründung:** {n.reasoning}\n\n")
            if n.source_headlines:
                f.write(f"**Beispiel-Headlines:**\n")
                for hl in n.source_headlines[:3]:
                    f.write(f"- {hl}\n")
                f.write("\n")
            f.write("---\n\n")

        # Frühindikatoren-Sektion
        early_niches = [n for n in niches if n.early_indicator]
        if early_niches:
            f.write("## EN-Frühindikatoren\n\n")
            f.write("Diese Nischen sind im englischsprachigen Raum bereits trending,\n")
            f.write("aber noch nicht im deutschen Markt angekommen – **First-Mover-Chance!**\n\n")
            for n in early_niches[:5]:
                langs = ", ".join(n.headline_languages).upper()
                f.write(f"- **{n.keyword}** – {n.headline_count} Headlines ({langs}) | "
                        f"YT: {n.youtube_score:.0f} | IG: {n.instagram_score:.0f}\n")
            f.write("\n")

        f.write(f"---\n")
        f.write(f"*Generiert mit YouTube + Instagram Nischen-Research-Tool*\n")

    return filepath
