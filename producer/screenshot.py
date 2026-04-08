"""
Screenshot-Automation via Playwright (headless Chromium).

Öffnet Tool-Webseiten automatisch und erstellt Screenshots.
Fallback: Placeholder-Grafik wenn URL nicht erreichbar.
"""
import re
import logging
from pathlib import Path

from producer.graphics import create_placeholder

logger = logging.getLogger(__name__)

# ── URL-Mapping: Schlüsselwort → URL ──────────────────────────────────────
TOOL_URLS: dict[str, str] = {
    "perplexity":       "https://www.perplexity.ai",
    "perplexity.ai":    "https://www.perplexity.ai",
    "elevenlabs":       "https://elevenlabs.io",
    "elevenlabs.io":    "https://elevenlabs.io",
    "make.com":         "https://www.make.com",
    "make":             "https://www.make.com",
    "claude":           "https://claude.ai",
    "claude.ai":        "https://claude.ai",
    "notion":           "https://www.notion.so",
    "notionai":         "https://www.notion.so/product/ai",
    "notion ai":        "https://www.notion.so/product/ai",
    "chatgpt":          "https://chat.openai.com",
    "openai":           "https://chat.openai.com",
    "midjourney":       "https://www.midjourney.com",
    "gemini":           "https://gemini.google.com",
    "copilot":          "https://copilot.microsoft.com",
    "jasper":           "https://www.jasper.ai",
    "canva":            "https://www.canva.com",
    "kling":            "https://klingai.com",
    "sora":             "https://sora.openai.com",
    "runway":           "https://runwayml.com",
}

# CSS-Selektoren um Cookie-Banner automatisch wegzuklicken
COOKIE_SELECTORS = [
    "button[id*='accept']",
    "button[class*='accept']",
    "button[id*='cookie']",
    "button[class*='cookie']",
    "[data-testid*='accept']",
    "button:has-text('Accept')",
    "button:has-text('Akzeptieren')",
    "button:has-text('Alle akzeptieren')",
    "button:has-text('Zustimmen')",
]


def _extract_url(annotation: str) -> str | None:
    """
    Extrahiert eine URL aus einer [SCREEN: ...] Annotation.
    Sucht zuerst nach direkten URLs, dann nach Schlüsselwörtern.
    """
    annotation_lower = annotation.lower()

    # Direkte URL im Text?
    url_match = re.search(r"https?://[^\s]+", annotation)
    if url_match:
        return url_match.group(0)

    # Bekannte Tool-Namen prüfen (längste Übereinstimmung zuerst)
    matches = [(k, v) for k, v in TOOL_URLS.items() if k in annotation_lower]
    if matches:
        best = max(matches, key=lambda x: len(x[0]))
        return best[1]

    return None


def capture_screenshot(url: str, output_path: Path,
                       width: int = 1920, height: int = 1080) -> Path:
    """
    Öffnet eine URL mit Playwright (headless) und erstellt einen Screenshot.

    Returns: output_path (oder Placeholder-Pfad bei Fehler)
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout
    except ImportError:
        logger.warning("Playwright nicht installiert — verwende Placeholder")
        label = url.split("//")[-1].split("/")[0]
        return create_placeholder(label, output_path.parent, output_path.name)

    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch(
                headless=True,
                args=["--no-sandbox", "--disable-dev-shm-usage"],
            )
            context = browser.new_context(
                viewport={"width": width, "height": height},
                locale="de-DE",
                user_agent="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36",
            )
            page = context.new_page()

            # Seite laden (max 15s)
            try:
                page.goto(url, wait_until="networkidle", timeout=15_000)
            except PWTimeout:
                page.goto(url, wait_until="domcontentloaded", timeout=10_000)

            # Kurz warten damit Animationen fertig sind
            page.wait_for_timeout(2000)

            # Cookie-Banner wegklicken
            for selector in COOKIE_SELECTORS:
                try:
                    btn = page.locator(selector).first
                    if btn.is_visible(timeout=1000):
                        btn.click()
                        page.wait_for_timeout(500)
                        break
                except Exception:
                    pass

            page.screenshot(path=str(output_path), full_page=False)
            browser.close()
            logger.info(f"Screenshot: {output_path.name} ← {url}")
            return output_path

    except Exception as e:
        logger.warning(f"Screenshot fehlgeschlagen ({url}): {e} — Placeholder")
        label = url.split("//")[-1].split("/")[0]
        return create_placeholder(label, output_path.parent, output_path.name)


def capture_for_annotation(annotation: str, output_dir: Path,
                            filename: str) -> Path:
    """
    Verarbeitet eine [SCREEN: ...] Annotation und erstellt das passende Visual.

    Logik:
    1. URL aus Annotation extrahieren
    2. Screenshot aufnehmen
    3. Fallback: Placeholder mit Annotation-Text
    """
    url = _extract_url(annotation)
    output_path = Path(output_dir) / filename

    if url:
        return capture_screenshot(url, output_path)
    else:
        # Kein URL-Mapping — beschreibenden Placeholder erstellen
        label = annotation[:50]
        logger.info(f"Kein URL-Mapping für: '{annotation}' — Placeholder")
        return create_placeholder(label, output_dir, filename)


def capture_all_screens(sections: list, output_dir: Path) -> dict[str, Path]:
    """
    Erstellt Screenshots für alle [SCREEN: ...] Annotationen aller Sektionen.

    Returns: { "section_title/screen_index": Path }
    """
    output_dir = Path(output_dir)
    results: dict[str, Path] = {}

    for section in sections:
        for i, screen in enumerate(section.screens):
            key = f"{section.title[:20]}_{i:02d}"
            # Alle ungültigen Zeichen für Dateinamen entfernen (/, \, :, #, *, ?, etc.)
            safe_key = re.sub(r'[^\w\-]', '_', key.lower())
            safe_key = re.sub(r'_+', '_', safe_key).strip('_')
            filename = f"screen_{safe_key}.png"
            path = capture_for_annotation(screen, output_dir, filename)
            results[key] = path

    return results
