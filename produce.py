#!/usr/bin/env python3
"""
Vollautomatische Video-Produktions-Pipeline

Aus einem Markdown-Skript wird ein fertiges MP4 erzeugt:
  Skript → Voiceover (ElevenLabs) → Grafiken (Pillow)
         → Screenshots (Playwright) → Finales MP4 (MoviePy)

Verwendung:
    ELEVENLABS_API_KEY=xxx python produce.py strategy/skript-video-01.md
    python produce.py strategy/skript-video-01.md --dry-run
    python produce.py strategy/skript-video-01.md --skip-voiceover
    python produce.py strategy/skript-video-01.md --voice luca
"""
import argparse
import logging
import sys
from datetime import date
from pathlib import Path

from colorama import init, Fore, Style

init(autoreset=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)
logging.getLogger("moviepy").setLevel(logging.WARNING)
logging.getLogger("PIL").setLevel(logging.WARNING)
logging.getLogger("playwright").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)


def _step(n: int, total: int, msg: str) -> None:
    print(Fore.CYAN + f"\n[{n}/{total}] {msg}" + Style.RESET_ALL)

def _ok(msg: str) -> None:
    print(Fore.GREEN + f"  ✓ {msg}" + Style.RESET_ALL)

def _warn(msg: str) -> None:
    print(Fore.YELLOW + f"  ⚠ {msg}" + Style.RESET_ALL)

def _err(msg: str) -> None:
    print(Fore.RED + f"  ✗ {msg}" + Style.RESET_ALL)


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="KI-Praxis Video Producer")
    p.add_argument("script", help="Pfad zum Markdown-Skript")
    p.add_argument("--voice", default="daniel",
                   choices=["daniel", "luca", "sarah"],
                   help="ElevenLabs-Stimme (Standard: daniel)")
    p.add_argument("--output-dir", default="output",
                   help="Ausgabe-Verzeichnis (Standard: output/)")
    p.add_argument("--dry-run", action="store_true",
                   help="Nur parsen, keine Dateien erzeugen")
    p.add_argument("--skip-voiceover", action="store_true",
                   help="Voiceover überspringen (MP3s müssen bereits vorhanden sein)")
    p.add_argument("--skip-screenshots", action="store_true",
                   help="Screenshots überspringen (nur Grafiken)")
    p.add_argument("--only-voiceover", action="store_true",
                   help="Nur Voiceover generieren, kein Video")
    p.add_argument("--only-graphics", action="store_true",
                   help="Nur Grafiken generieren, kein Video")
    p.add_argument("--verbose", action="store_true")
    return p.parse_args()


def _select_visual(section, idx: int,
                   graphics_dir: Path, screenshots_dir: Path) -> Path | None:
    """
    Wählt das beste Visual für eine Sektion:
    1. Screenshot (wenn SCREEN-Annotation vorhanden und Datei existiert)
    2. Bewertungskarte (wenn rating_card vorhanden)
    3. Titelkarte
    """
    # Screenshot
    for i, _ in enumerate(section.screens):
        key = f"{section.title[:20]}_{i:02d}"
        fname = f"screen_{key.lower().replace(' ', '_')}.png"
        p = screenshots_dir / fname
        if p.exists():
            return p

    # Bewertungskarte
    rating_fname = f"{idx:02d}_rating.png"
    rp = graphics_dir / rating_fname
    if rp.exists():
        return rp

    # Titelkarte
    title_fname = f"{idx:02d}_title.png"
    tp = graphics_dir / title_fname
    if tp.exists():
        return tp

    return None


def main() -> None:
    args = parse_args()
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    script_path = Path(args.script)
    if not script_path.exists():
        _err(f"Skript nicht gefunden: {script_path}")
        sys.exit(1)

    out_dir        = Path(args.output_dir)
    audio_dir      = out_dir / "audio"
    graphics_dir   = out_dir / "graphics"
    screenshots_dir = out_dir / "screenshots"
    video_stem     = script_path.stem
    video_path     = out_dir / f"{video_stem}-{date.today()}.mp4"

    TOTAL_STEPS = 5

    print(Fore.CYAN + Style.BRIGHT + "\n" + "═" * 65)
    print(Fore.CYAN + Style.BRIGHT + "  KI-PRAXIS — Automatischer Video-Producer")
    print(Fore.CYAN + Style.BRIGHT + f"  Skript: {script_path.name}")
    print(Fore.CYAN + Style.BRIGHT + "═" * 65)

    # ── Schritt 1: Skript parsen ──────────────────────────────────────────
    _step(1, TOTAL_STEPS, "Skript parsen …")
    from producer.script_parser import parse_script
    sections = parse_script(script_path)
    _ok(f"{len(sections)} Sektionen gefunden")
    for s in sections:
        has_rating = "🎯" if s.rating_card else "  "
        screens_n  = len(s.screens)
        print(f"    {has_rating} [{s.start_time}–{s.end_time}] {s.title}"
              f"  ({len(s.voiceover.split())} Wörter, {screens_n} Screens)")

    if args.dry_run:
        print(Fore.YELLOW + "\n  Dry-Run abgeschlossen. Keine Dateien erstellt.")
        return

    # ── Schritt 2: Voiceover generieren ──────────────────────────────────
    _step(2, TOTAL_STEPS, f"Voiceover generieren (ElevenLabs, Stimme: {args.voice}) …")

    import os
    audio_paths: list[Path] = []

    if args.skip_voiceover:
        _warn("Voiceover übersprungen (--skip-voiceover)")
        for i, s in enumerate(sections):
            p = audio_dir / f"{i:02d}_{s.title.lower().replace(' ', '_')[:30]}.mp3"
            if p.exists():
                audio_paths.append(p)
            else:
                _warn(f"MP3 fehlt: {p.name}")
    else:
        if not os.getenv("ELEVENLABS_API_KEY"):
            _warn("ELEVENLABS_API_KEY nicht gesetzt — Voiceover wird übersprungen.")
            _warn("Setze: export ELEVENLABS_API_KEY=dein_key")
            args.skip_voiceover = True
        else:
            from producer.voiceover import generate_all_voiceovers
            audio_paths = generate_all_voiceovers(sections, audio_dir, voice=args.voice)
            _ok(f"{len(audio_paths)} MP3-Dateien in {audio_dir}/")

    if args.only_voiceover:
        _ok("Nur-Voiceover-Modus abgeschlossen.")
        return

    # ── Schritt 3: Grafiken generieren ────────────────────────────────────
    _step(3, TOTAL_STEPS, "Grafiken generieren (Pillow) …")
    from producer.graphics import (
        create_title_card, create_rating_card,
        create_section_header, create_comparison_table,
    )

    graphics_dir.mkdir(parents=True, exist_ok=True)

    for i, section in enumerate(sections):
        title_clean = section.title.strip()

        # Bewertungskarte
        if section.rating_card:
            create_rating_card(
                section.rating_card,
                output_dir=graphics_dir,
                filename=f"{i:02d}_rating.png",
            )

        # Titelkarte (immer als Fallback)
        create_title_card(
            title=title_clean,
            subtitle=section.screens[0][:80] if section.screens else "",
            output_dir=graphics_dir,
            filename=f"{i:02d}_title.png",
        )

    # Vergleichstabelle für Fazit-Sektion
    comparison_tools = [
        {"rank": "#1", "name": "Notion AI",    "rating": "9.5/10", "category": "Workflow"},
        {"rank": "#2", "name": "Claude",        "rating": "9.0/10", "category": "Texte & Recherche"},
        {"rank": "#2", "name": "ElevenLabs",   "rating": "9.0/10", "category": "Audio"},
        {"rank": "#3", "name": "Make.com",     "rating": "8.5/10", "category": "Automatisierung"},
        {"rank": "#4", "name": "Perplexity AI", "rating": "7.5/10", "category": "Suche"},
    ]
    create_comparison_table(comparison_tools, output_dir=graphics_dir,
                            filename="comparison_table.png")
    _ok(f"Grafiken in {graphics_dir}/")

    if args.only_graphics:
        _ok("Nur-Grafiken-Modus abgeschlossen.")
        return

    # ── Schritt 4: Screenshots erfassen ───────────────────────────────────
    _step(4, TOTAL_STEPS, "Screenshots erfassen (Playwright, headless) …")

    from producer.screenshot import capture_all_screens
    screenshots_dir.mkdir(parents=True, exist_ok=True)

    if args.skip_screenshots:
        _warn("Screenshots übersprungen (--skip-screenshots)")
    else:
        screen_map = capture_all_screens(sections, screenshots_dir)
        _ok(f"{len(screen_map)} Screenshots in {screenshots_dir}/")

    # ── Schritt 5: Video zusammenstellen ──────────────────────────────────
    _step(5, TOTAL_STEPS, "Video zusammenstellen (MoviePy/FFmpeg) …")

    if not audio_paths:
        _err("Keine Audio-Dateien vorhanden. Abbruch.")
        sys.exit(1)

    sections_data: list[dict] = []
    for i, (section, audio_p) in enumerate(zip(sections, audio_paths)):
        visual = _select_visual(section, i, graphics_dir, screenshots_dir)
        if visual is None:
            # Fallback: Titelkarte neu generieren
            visual = create_title_card(
                section.title, output_dir=graphics_dir,
                filename=f"{i:02d}_title_fallback.png"
            )
        sections_data.append({
            "audio":  audio_p,
            "visual": visual,
            "title":  section.title,
        })

    from producer.assembler import build_video
    build_video(sections_data, video_path)

    print()
    print(Fore.GREEN + Style.BRIGHT + "═" * 65)
    print(Fore.GREEN + Style.BRIGHT + f"  FERTIG!  →  {video_path}")
    print(Fore.GREEN + Style.BRIGHT + "═" * 65)
    print()


if __name__ == "__main__":
    main()
