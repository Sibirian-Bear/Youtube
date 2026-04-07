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
    """Gibt die Top-N Keywords zurück. Fällt auf Seed-Daten zurück wenn keine Feeds erreichbar."""
    all_kw = fetch_all_headlines()
    if not all_kw:
        logger.warning("Keine RSS-Feeds erreichbar – verwende eingebauten Markt-Seed (DE, KI-Tools + Nachrichten).")
        all_kw = _get_seed_keywords()
    return dict(list(all_kw.items())[:limit])


def _get_seed_keywords() -> dict[str, dict[str, Any]]:
    """
    Eingebauter Keyword-Seed basierend auf Marktforschung (Stand Q1 2026).
    Fokus: KI-Tools, Nachrichten, Finanzen, Technologie — DE-Markt, Faceless-geeignet.
    Dient als Fallback wenn RSS-Feeds nicht erreichbar sind.
    """
    return {
        "ki tools": {
            "count": 18, "category": "ki tools", "early_indicator": True,
            "languages": ["de", "en"],
            "headlines": [
                "Die besten KI-Tools 2026 im Vergleich",
                "ChatGPT-Alternativen: Welches KI-Tool lohnt sich?",
                "AI tools for productivity – what's trending in 2026",
            ],
        },
        "chatgpt": {
            "count": 15, "category": "ki tools", "early_indicator": False,
            "languages": ["de", "en"],
            "headlines": [
                "ChatGPT vs. Gemini: Welche KI ist besser?",
                "ChatGPT Enterprise – lohnt sich das Abo?",
                "ChatGPT für Selbstständige: 10 Praxis-Tipps",
            ],
        },
        "künstliche intelligenz": {
            "count": 14, "category": "künstliche intelligenz", "early_indicator": False,
            "languages": ["de"],
            "headlines": [
                "Künstliche Intelligenz revolutioniert den Arbeitsmarkt",
                "KI in Deutschland: Chancen und Risiken",
                "Wie KI die Content-Erstellung verändert",
            ],
        },
        "automatisierung": {
            "count": 12, "category": "automatisierung", "early_indicator": True,
            "languages": ["de", "en"],
            "headlines": [
                "Automatisierung mit KI: So sparst du 10 Stunden pro Woche",
                "Make vs. Zapier: Welches Automatisierungstool gewinnt?",
                "AI automation tools that replace manual work",
            ],
        },
        "nachrichten ki": {
            "count": 11, "category": "ki tools", "early_indicator": True,
            "languages": ["de", "en"],
            "headlines": [
                "KI-generierte Nachrichten: Fluch oder Segen?",
                "AI news channels are booming on YouTube",
                "Automatische Nachrichtenkanäle mit KI erstellen",
            ],
        },
        "etf investieren": {
            "count": 13, "category": "investing", "early_indicator": False,
            "languages": ["de"],
            "headlines": [
                "ETF-Depot aufbauen 2026: Der komplette Guide",
                "Welcher ETF ist der beste für Einsteiger?",
                "MSCI World vs. FTSE All-World: Der große Vergleich",
            ],
        },
        "passives einkommen": {
            "count": 11, "category": "investing", "early_indicator": False,
            "languages": ["de", "en"],
            "headlines": [
                "Passives Einkommen mit ETFs aufbauen",
                "7 Wege zu passivem Einkommen im Jahr 2026",
                "Passive income ideas that actually work in Germany",
            ],
        },
        "steuern sparen": {
            "count": 10, "category": "steuern", "early_indicator": False,
            "languages": ["de"],
            "headlines": [
                "Steuern sparen als Selbstständiger – legale Tricks",
                "Steueroptimierung 2026: Was sich geändert hat",
                "Homeoffice-Pauschale und andere Steuervorteile",
            ],
        },
        "software saas": {
            "count": 9, "category": "saas", "early_indicator": True,
            "languages": ["de", "en"],
            "headlines": [
                "Best SaaS tools for solopreneurs in 2026",
                "SaaS-Tools für Freelancer – diese 5 brauchst du wirklich",
                "Die besten Software-Abos für kleine Unternehmen",
            ],
        },
        "cybersicherheit": {
            "count": 9, "category": "cybersicherheit", "early_indicator": True,
            "languages": ["de", "en"],
            "headlines": [
                "Cybersecurity für Einsteiger: So schützt du dich",
                "Hacker-Angriffe auf KMU nehmen zu",
                "Cybersecurity trends every German business should know",
            ],
        },
        "immobilien investieren": {
            "count": 10, "category": "immobilien", "early_indicator": False,
            "languages": ["de"],
            "headlines": [
                "Immobilien kaufen 2026 – lohnt es sich noch?",
                "REITs als Immobilien-Alternative für Kleinanleger",
                "Passives Einkommen durch Immobilien: So geht's",
            ],
        },
        "krypto bitcoin": {
            "count": 8, "category": "investing", "early_indicator": True,
            "languages": ["de", "en"],
            "headlines": [
                "Bitcoin 2026: Wohin geht die Reise?",
                "Krypto für Einsteiger: Was du wissen musst",
                "Crypto investing strategies for German beginners",
            ],
        },
        "produktivität tipps": {
            "count": 8, "category": "produktivität", "early_indicator": True,
            "languages": ["de", "en"],
            "headlines": [
                "10 Produktivitäts-Hacks für Remote-Worker",
                "KI-Tools für mehr Produktivität im Alltag",
                "Productivity systems that top creators use",
            ],
        },
        "versicherung vergleich": {
            "count": 7, "category": "versicherung", "early_indicator": False,
            "languages": ["de"],
            "headlines": [
                "Die besten Kfz-Versicherungen 2026 im Vergleich",
                "Haftpflichtversicherung: Darauf solltest du achten",
                "Versicherungen für Selbstständige – was ist Pflicht?",
            ],
        },
        "aktien analyse": {
            "count": 7, "category": "finanzen", "early_indicator": False,
            "languages": ["de", "en"],
            "headlines": [
                "Aktienanalyse für Einsteiger: So bewertest du Unternehmen",
                "Dividendenaktien 2026: Die besten Zahler",
                "Growth stocks vs. value stocks – which wins in 2026?",
            ],
        },
        "elektroauto": {
            "count": 6, "category": "elektroauto", "early_indicator": False,
            "languages": ["de"],
            "headlines": [
                "Elektroauto oder Verbrenner: Was lohnt sich 2026?",
                "Die günstigsten E-Autos im Test",
                "Laden vs. Tanken: Der Kostenvergleich",
            ],
        },
        "nachhaltigkeit geld": {
            "count": 6, "category": "nachhaltigkeit", "early_indicator": True,
            "languages": ["de", "en"],
            "headlines": [
                "Nachhaltig investieren: ESG-ETFs im Vergleich",
                "Green finance trends in Germany 2026",
                "Nachhaltige Geldanlagen: Was bringt wirklich etwas?",
            ],
        },
        "online geld verdienen": {
            "count": 9, "category": "business", "early_indicator": False,
            "languages": ["de"],
            "headlines": [
                "Online Geld verdienen 2026: Seriöse Methoden",
                "YouTube Monetarisierung: Was du wirklich verdienen kannst",
                "Freelancing in Deutschland: So startest du durch",
            ],
        },
        "technologie news": {
            "count": 10, "category": "technologie", "early_indicator": False,
            "languages": ["de", "en"],
            "headlines": [
                "Tech-News der Woche: KI dominiert alle Branchen",
                "Apple Vision Pro 2: Was ändert sich?",
                "Technology trends reshaping Europe in 2026",
            ],
        },
        "recht finanzen": {
            "count": 5, "category": "recht", "early_indicator": False,
            "languages": ["de"],
            "headlines": [
                "Mietrecht 2026: Was Vermieter und Mieter wissen müssen",
                "Vertragsrecht für Freelancer: Fallstricke vermeiden",
                "Erbrecht in Deutschland: Die wichtigsten Änderungen",
            ],
        },
    }
