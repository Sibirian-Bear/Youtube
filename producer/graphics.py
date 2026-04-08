"""
Grafik-Engine: generiert Titelkarten, Bewertungskarten und Slide-Grafiken
automatisch mit Pillow. Kein manuelles Design nötig.

Design: Dunkles Theme (#0A0A0F Hintergrund, weißer/cyan Text)
Auflösung: 1920 × 1080 (Full-HD, YouTube-Standard)
"""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

# ── Farb-Palette ──────────────────────────────────────────────────────────
BG          = (10,  10,  15)      # fast schwarz
BG_CARD     = (20,  20,  35)      # leicht heller für Karten
ACCENT      = (0,   210, 255)     # Cyan
TEXT_WHITE  = (255, 255, 255)
TEXT_GRAY   = (180, 180, 190)
GREEN       = (80,  220, 120)
RED         = (255, 90,  90)
YELLOW      = (255, 210, 60)
DIM_LINE    = (40,  40,  60)      # trennlinie

W, H = 1920, 1080


# ── Font-Loader ───────────────────────────────────────────────────────────
_FONT_PATHS = {
    "bold":    "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
    "regular": "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
    "italic":  "/usr/share/fonts/truetype/liberation/LiberationSans-BoldItalic.ttf",
}

def _font(style: str = "regular", size: int = 48) -> ImageFont.FreeTypeFont:
    path = _FONT_PATHS.get(style, _FONT_PATHS["regular"])
    try:
        return ImageFont.truetype(path, size)
    except OSError:
        return ImageFont.load_default()


def _canvas() -> tuple[Image.Image, ImageDraw.ImageDraw]:
    """Erstellt einen leeren 1920×1080 Canvas mit Hintergrundfarbe."""
    img = Image.new("RGB", (W, H), BG)
    return img, ImageDraw.Draw(img)


def _centered_text(draw: ImageDraw.ImageDraw, y: int, text: str,
                   font: ImageFont.FreeTypeFont, color: tuple) -> int:
    """Schreibt zentrierten Text und gibt die neue Y-Position zurück."""
    bbox = draw.textbbox((0, 0), text, font=font)
    tw = bbox[2] - bbox[0]
    draw.text(((W - tw) // 2, y), text, font=font, fill=color)
    return y + (bbox[3] - bbox[1]) + 20


def _wrap_text(text: str, font: ImageFont.FreeTypeFont,
               max_width: int, draw: ImageDraw.ImageDraw) -> list[str]:
    """Bricht langen Text in Zeilen um."""
    words = text.split()
    lines, current = [], ""
    for word in words:
        test = f"{current} {word}".strip()
        bbox = draw.textbbox((0, 0), test, font=font)
        if bbox[2] - bbox[0] <= max_width:
            current = test
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


def _accent_bar(draw: ImageDraw.ImageDraw, y: int, width: int = 120, height: int = 6) -> None:
    """Zeichnet einen Cyan-Akzentbalken zentriert."""
    x = (W - width) // 2
    draw.rectangle([x, y, x + width, y + height], fill=ACCENT)


def _channel_tag(draw: ImageDraw.ImageDraw) -> None:
    """Kleines Kanal-Label unten rechts."""
    f = _font("bold", 28)
    draw.text((W - 260, H - 55), "KI-PRAXIS", font=f, fill=ACCENT)


# ── Öffentliche Funktionen ────────────────────────────────────────────────

def create_title_card(title: str, subtitle: str = "",
                      output_dir: Path | None = None,
                      filename: str = "title_card.png") -> Path:
    """
    Erstellt eine Titelkarte (z.B. 'TOOL #4 — ElevenLabs').

    Returns: Pfad zur PNG-Datei
    """
    img, draw = _canvas()

    # Hintergrund-Gradient-Effekt (vereinfacht: Overlay-Rechteck)
    overlay = Image.new("RGB", (W, H), (0, 30, 60))
    img = Image.blend(img, overlay, alpha=0.3)
    draw = ImageDraw.Draw(img)

    y = 340
    # Akzent-Linie oben
    _accent_bar(draw, y - 60, width=200)

    # Haupttitel
    f_title = _font("bold", 88)
    lines = _wrap_text(title, f_title, W - 200, draw)
    for line in lines:
        y = _centered_text(draw, y, line, f_title, TEXT_WHITE)

    # Untertitel
    if subtitle:
        y += 20
        f_sub = _font("regular", 48)
        sub_lines = _wrap_text(subtitle, f_sub, W - 300, draw)
        for line in sub_lines:
            y = _centered_text(draw, y, line, f_sub, TEXT_GRAY)

    # Akzent-Linie unten
    _accent_bar(draw, y + 30, width=200)
    _channel_tag(draw)

    path = _save(img, output_dir, filename)
    return path


def create_rating_card(card: dict,
                       output_dir: Path | None = None,
                       filename: str = "rating_card.png") -> Path:
    """
    Erstellt eine Bewertungskarte aus einem rating_card-dict.

    card = {"name": "ElevenLabs", "pros": [...], "cons": [...],
            "for_whom": "...", "rating": "9.0 / 10"}
    """
    img, draw = _canvas()

    # Karten-Hintergrund (leicht heller, zentriert)
    card_x, card_y = 160, 80
    card_w, card_h = W - 320, H - 160
    draw.rectangle([card_x, card_y, card_x + card_w, card_y + card_h],
                   fill=BG_CARD, outline=ACCENT, width=2)

    y = card_y + 60

    # Tool-Name
    f_name = _font("bold", 72)
    y = _centered_text(draw, y, card.get("name", "Tool"), f_name, ACCENT)

    # Trennlinie
    draw.line([(card_x + 60, y + 10), (card_x + card_w - 60, y + 10)],
              fill=DIM_LINE, width=2)
    y += 40

    f_item = _font("regular", 38)
    x_left = card_x + 80

    # Pros (grün)
    for pro in card.get("pros", [])[:4]:
        draw.text((x_left, y), "✓", font=_font("bold", 38), fill=GREEN)
        draw.text((x_left + 55, y), pro[:60], font=f_item, fill=TEXT_WHITE)
        y += 52

    y += 10

    # Cons (rot)
    for con in card.get("cons", [])[:3]:
        draw.text((x_left, y), "✗", font=_font("bold", 38), fill=RED)
        draw.text((x_left + 55, y), con[:60], font=f_item, fill=TEXT_GRAY)
        y += 52

    # Trennlinie
    draw.line([(card_x + 60, y + 20), (card_x + card_w - 60, y + 20)],
              fill=DIM_LINE, width=2)
    y += 50

    # Für wen
    if card.get("for_whom"):
        f_small = _font("italic", 34)
        draw.text((x_left, y), f"Für wen:  {card['for_whom'][:70]}", font=f_small, fill=TEXT_GRAY)
        y += 52

    # Bewertung — groß, gelb, rechts
    rating = card.get("rating", "")
    if rating:
        f_rating = _font("bold", 80)
        draw.text((card_x + card_w - 320, card_y + card_h - 120),
                  rating, font=f_rating, fill=YELLOW)
        f_label = _font("regular", 30)
        draw.text((card_x + card_w - 295, card_y + card_h - 150),
                  "BEWERTUNG", font=f_label, fill=TEXT_GRAY)

    _channel_tag(draw)

    path = _save(img, output_dir, filename)
    return path


def create_section_header(text: str, tag: str = "",
                          output_dir: Path | None = None,
                          filename: str = "section_header.png") -> Path:
    """
    Einfacher Text-Slide für Übergänge / Abschnitte.
    z.B. "Perplexity AI — Die Google-Alternative?"
    """
    img, draw = _canvas()

    y = H // 2 - 80
    if tag:
        f_tag = _font("bold", 36)
        y = _centered_text(draw, y - 60, tag, f_tag, ACCENT)
        y += 10

    f_main = _font("bold", 72)
    lines = _wrap_text(text, f_main, W - 200, draw)
    for line in lines:
        y = _centered_text(draw, y, line, f_main, TEXT_WHITE)

    _accent_bar(draw, H // 2 + 100)
    _channel_tag(draw)

    path = _save(img, output_dir, filename)
    return path


def create_placeholder(label: str,
                       output_dir: Path | None = None,
                       filename: str = "placeholder.png") -> Path:
    """
    Fallback-Grafik wenn Screenshot nicht verfügbar.
    Zeigt Tool-Namen mit 'Demo'-Label auf dunklem Hintergrund.
    """
    img, draw = _canvas()

    # Gestrichelter Rahmen
    draw.rectangle([80, 80, W - 80, H - 80], outline=DIM_LINE, width=3)

    y = H // 2 - 80
    f_label = _font("bold", 36)
    y = _centered_text(draw, y - 60, "SCREEN-DEMO", f_label, ACCENT)
    y += 20
    f_main = _font("bold", 76)
    lines = _wrap_text(label, f_main, W - 200, draw)
    for line in lines:
        y = _centered_text(draw, y, line, f_main, TEXT_WHITE)

    _channel_tag(draw)
    path = _save(img, output_dir, filename)
    return path


def create_comparison_table(tools: list[dict],
                             output_dir: Path | None = None,
                             filename: str = "comparison.png") -> Path:
    """
    Erstellt eine Vergleichstabelle für das Fazit.

    tools = [{"rank": "#1", "name": "Notion AI", "rating": "9.5/10", "category": "Workflow"}, ...]
    """
    img, draw = _canvas()

    f_head = _font("bold", 56)
    y = _centered_text(draw, 60, "ALLE 5 TOOLS IM VERGLEICH", f_head, ACCENT)
    _accent_bar(draw, y + 10, width=400)
    y += 60

    f_row  = _font("bold", 44)
    f_cat  = _font("regular", 36)
    row_h  = 110
    x_rank, x_name, x_rating, x_cat = 120, 260, 1450, 1680

    for i, tool in enumerate(tools[:5]):
        row_bg = (18, 18, 30) if i % 2 == 0 else BG_CARD
        draw.rectangle([80, y, W - 80, y + row_h], fill=row_bg)
        draw.text((x_rank,   y + 28), tool.get("rank", ""),   font=f_row,  fill=ACCENT)
        draw.text((x_name,   y + 28), tool.get("name", ""),   font=f_row,  fill=TEXT_WHITE)
        draw.text((x_rating, y + 28), tool.get("rating", ""), font=f_row,  fill=YELLOW)
        draw.text((x_cat,    y + 34), tool.get("category", ""), font=f_cat, fill=TEXT_GRAY)
        y += row_h

    _channel_tag(draw)
    path = _save(img, output_dir, filename)
    return path


# ── Hilfsfunktion ─────────────────────────────────────────────────────────

def _save(img: Image.Image, output_dir: Path | None, filename: str) -> Path:
    """Speichert das Bild und gibt den Pfad zurück."""
    out_dir = Path(output_dir) if output_dir else Path("output/graphics")
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / filename
    img.save(str(path), "PNG")
    return path
