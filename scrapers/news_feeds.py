"""
Mehrsprachiger RSS-Headline-Scraper (DE + EN + FR + ES).

Strategie:
- Liest alle RSS-Feeds aus config.RSS_FEEDS
- Extrahiert Keywords pro Sprache
- Übersetzt EN→DE via config.KEYWORD_TRANSLATION_EN_DE
- Gibt normalisiertes dict zurück:
    { keyword_de: {"count": int, "headlines": [...], "languages": [...], "early_indicator": bool} }
"""
import re
import time
import logging
from collections import Counter, defaultdict
from typing import Any

import xml.etree.ElementTree as ET
import requests

import config

logger = logging.getLogger(__name__)

# Minimale Wortlänge für Keyword-Extraktion
MIN_WORD_LEN = 4
# Minimum Vorkommen damit ein Keyword als Kandidat gilt
MIN_KEYWORD_COUNT = 2


def _fetch_feed(url: str, timeout: int = 10) -> list[dict] | None:
    """
    Lädt einen RSS/Atom-Feed via requests + ElementTree.
    Gibt Liste von {"title": str, "summary": str} zurück.
    """
    try:
        resp = requests.get(url, timeout=timeout, headers={"User-Agent": "Mozilla/5.0"})
        resp.raise_for_status()
        root = ET.fromstring(resp.content)
        ns = {"atom": "http://www.w3.org/2005/Atom"}
        entries = []

        # RSS 2.0
        for item in root.findall(".//item")[:50]:
            title = item.findtext("title") or ""
            desc  = item.findtext("description") or ""
            entries.append({"title": title, "summary": desc})

        # Atom
        if not entries:
            for entry in root.findall(".//atom:entry", ns)[:50]:
                title   = entry.findtext("atom:title", namespaces=ns) or ""
                summary = entry.findtext("atom:summary", namespaces=ns) or ""
                entries.append({"title": title, "summary": summary})

        return entries if entries else None
    except Exception as e:
        logger.warning(f"Feed nicht erreichbar: {url} → {e}")
        return None


def _tokenize(text: str, lang: str) -> list[str]:
    """Bereinigt Text und gibt Tokens zurück, Stopwords gefiltert."""
    text = text.lower()
    # HTML-Tags entfernen
    text = re.sub(r"<[^>]+>", " ", text)
    # Sonderzeichen normalisieren
    text = re.sub(r"[^a-zäöüßàáâãèéêëìíîïòóôùúûçñ\s\-]", " ", text)
    tokens = text.split()
    stopwords = config.STOPWORDS.get(lang, set())
    return [t for t in tokens if len(t) >= MIN_WORD_LEN and t not in stopwords]


def _extract_bigrams(tokens: list[str]) -> list[str]:
    """Erstellt Bi-Gramme für zusammengesetzte Begriffe wie 'ki tools'."""
    return [f"{tokens[i]} {tokens[i+1]}" for i in range(len(tokens) - 1)]


def _translate_to_german(keyword: str) -> str | None:
    """
    Versucht, ein englisches Keyword auf Deutsch zu mappen.
    Gibt None zurück wenn keine Übersetzung bekannt.
    """
    kw = keyword.lower().strip()
    # Direkter Treffer
    if kw in config.KEYWORD_TRANSLATION_EN_DE:
        return config.KEYWORD_TRANSLATION_EN_DE[kw]
    # Teilweise Übereinstimmung: Keyword enthält bekannten Begriff
    for en, de in config.KEYWORD_TRANSLATION_EN_DE.items():
        if en in kw:
            return de
    return None


def _map_to_category(keyword: str) -> str:
    """Ordnet ein Keyword einer CPM-Kategorie zu."""
    kw = keyword.lower()
    for cat in config.CPM_TABLE:
        if cat in kw or kw in cat:
            return cat
    return "default"


def fetch_all_headlines() -> dict[str, dict[str, Any]]:
    """
    Scrapt alle konfigurierten RSS-Feeds und gibt aggregierte Keyword-Daten zurück.

    Returns:
        {
          "ki tools": {
              "count": 8,
              "headlines": ["KI-Tools für Einsteiger", ...],
              "languages": ["de", "en"],
              "early_indicator": True,   # wenn EN-Quelle aber kein DE
              "category": "ki tools",
          },
          ...
        }
    """
    # Sammlung pro Sprache: keyword → Counter + headlines
    lang_keywords: dict[str, Counter] = {lang: Counter() for lang in config.RSS_FEEDS}
    lang_headlines: dict[str, dict[str, list[str]]] = {lang: defaultdict(list) for lang in config.RSS_FEEDS}

    for lang, urls in config.RSS_FEEDS.items():
        for url in urls:
            logger.info(f"Lade Feed [{lang}]: {url}")
            entries = _fetch_feed(url)
            if not entries:
                continue
            for entry in entries:
                title   = entry.get("title", "") or ""
                summary = entry.get("summary", "") or ""
                text = f"{title} {summary}"
                tokens = _tokenize(text, lang)
                bigrams = _extract_bigrams(tokens)
                all_terms = tokens + bigrams
                for term in all_terms:
                    lang_keywords[lang][term] += 1
                    if len(lang_headlines[lang][term]) < 5:
                        lang_headlines[lang][term].append(title[:120])
            time.sleep(0.3)

    # DE-Keywords direkt verwenden, EN/FR/ES übersetzen
    aggregated: dict[str, dict[str, Any]] = {}

    # 1) Deutschsprachige Keywords
    for kw, count in lang_keywords["de"].most_common(100):
        if count < MIN_KEYWORD_COUNT:
            break
        cat = _map_to_category(kw)
        aggregated[kw] = {
            "count": count,
            "headlines": lang_headlines["de"][kw],
            "languages": ["de"],
            "early_indicator": False,
            "category": cat,
        }

    # 2) Fremdsprachige Keywords übersetzen und zusammenführen
    for lang in ["en", "fr", "es"]:
        for kw, count in lang_keywords[lang].most_common(80):
            if count < MIN_KEYWORD_COUNT:
                break
            de_kw = _translate_to_german(kw) if lang == "en" else _translate_to_german(kw)
            if not de_kw:
                continue
            cat = _map_to_category(de_kw)
            if de_kw in aggregated:
                aggregated[de_kw]["count"] += count
                aggregated[de_kw]["headlines"].extend(lang_headlines[lang][kw][:2])
                if lang not in aggregated[de_kw]["languages"]:
                    aggregated[de_kw]["languages"].append(lang)
                # Frühindikator: im Ausland bekannt, aber noch kaum auf DE
                if "de" not in aggregated[de_kw]["languages"]:
                    aggregated[de_kw]["early_indicator"] = True
            else:
                aggregated[de_kw] = {
                    "count": count,
                    "headlines": lang_headlines[lang][kw][:3],
                    "languages": [lang],
                    "early_indicator": True,   # noch nicht auf DE-Radar
                    "category": cat,
                }

    # Sortiert nach Häufigkeit
    return dict(sorted(aggregated.items(), key=lambda x: x[1]["count"], reverse=True))


def get_top_keywords(limit: int = 50) -> dict[str, dict[str, Any]]:
    """Gibt die Top-N Keywords zurück."""
    all_kw = fetch_all_headlines()
    return dict(list(all_kw.items())[:limit])
