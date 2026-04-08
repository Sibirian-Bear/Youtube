"""
Script Parser: liest das Markdown-Skript und zerlegt es in
strukturierte Sektionen mit Voiceover-Text und Produktions-Anweisungen.
"""
import re
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class Section:
    title: str                        # z.B. "INTRO / HOOK"
    start_time: str                   # z.B. "0:00"
    end_time: str                     # z.B. "0:35"
    voiceover: str                    # Nur der gesprochene Text
    screens: list[str] = field(default_factory=list)   # [SCREEN: ...] Anweisungen
    graphics: list[str] = field(default_factory=list)  # [GRAFIK: ...] Anweisungen
    rating_card: dict | None = None   # Bewertungskarte falls vorhanden


def _extract_rating_card(block: str) -> dict | None:
    """
    Erkennt Bewertungskarten (Code-Blöcke mit ✅/❌).
    Gibt strukturiertes dict zurück.
    """
    lines = [l.strip() for l in block.strip().splitlines() if l.strip()]
    if not lines or not any("✅" in l or "❌" in l for l in lines):
        return None

    card: dict = {"name": "", "pros": [], "cons": [], "for_whom": "", "rating": ""}
    for line in lines:
        if line.startswith("✅"):
            card["pros"].append(line[1:].strip())
        elif line.startswith("❌"):
            card["cons"].append(line[1:].strip())
        elif line.lower().startswith("für wen"):
            card["for_whom"] = line.split(":", 1)[-1].strip()
        elif line.lower().startswith("bewertung"):
            card["rating"] = line.split(":", 1)[-1].strip()
        elif not card["name"]:
            card["name"] = line
    return card


def parse_script(path: str | Path) -> list[Section]:
    """
    Liest eine Markdown-Skript-Datei und gibt eine Liste von Sektionen zurück.
    """
    text = Path(path).read_text(encoding="utf-8")
    sections: list[Section] = []

    # Sektionen durch ### Überschriften trennen
    raw_sections = re.split(r"^###\s+", text, flags=re.MULTILINE)

    for raw in raw_sections:
        if not raw.strip():
            continue

        # Zeitstempel aus Überschrift extrahieren (z.B. "🎬 INTRO / HOOK (0:00 – 0:35)")
        header_line = raw.splitlines()[0].strip()
        time_match = re.search(r"\((\d+:\d+)\s*[–-]\s*(\d+:\d+)\)", header_line)
        start_t = time_match.group(1) if time_match else "0:00"
        end_t   = time_match.group(2) if time_match else "0:00"

        # Titel bereinigen
        title = re.sub(r"\(.*?\)", "", header_line)
        title = re.sub(r"[🎬📋🔢🥇📊📢]", "", title).strip()

        body = "\n".join(raw.splitlines()[1:])

        # [SCREEN: ...] und [GRAFIK: ...] Anweisungen extrahieren
        screens  = re.findall(r"`\[SCREEN:\s*(.+?)\]`", body)
        graphics = re.findall(r"`\[GRAFIK:\s*(.+?)\]`", body)

        # Bewertungskarten aus Code-Blöcken extrahieren
        rating_card = None
        code_blocks = re.findall(r"```\n(.*?)```", body, re.DOTALL)
        for block in code_blocks:
            card = _extract_rating_card(block)
            if card:
                rating_card = card
                break

        # Voiceover: nur Zeilen die mit > beginnen, Code-Blöcke und Anweisungen entfernen
        body_clean = re.sub(r"```.*?```", "", body, flags=re.DOTALL)
        body_clean = re.sub(r"`\[(?:SCREEN|GRAFIK|SCHNITT):.*?\]`", "", body_clean)
        vo_lines = []
        for line in body_clean.splitlines():
            line = line.strip()
            if line.startswith(">"):
                # Markdown-Fettdruck und Sonderzeichen bereinigen
                clean = re.sub(r"\*\*(.*?)\*\*", r"\1", line[1:]).strip()
                if clean:
                    vo_lines.append(clean)

        voiceover = "\n\n".join(vo_lines)

        if not voiceover.strip():
            continue

        sections.append(Section(
            title=title,
            start_time=start_t,
            end_time=end_t,
            voiceover=voiceover,
            screens=screens,
            graphics=graphics,
            rating_card=rating_card,
        ))

    return sections


def get_full_voiceover(sections: list[Section]) -> str:
    """Gibt den kompletten Voiceover-Text als einen String zurück."""
    return "\n\n".join(s.voiceover for s in sections if s.voiceover)
