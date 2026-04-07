"""
Zentrale Konfiguration für das YouTube + Instagram Nischen-Research-Tool.
Alle API-Keys kommen aus Umgebungsvariablen.
"""
import os

# ---------------------------------------------------------------------------
# API Keys (optional – Tool funktioniert auch ohne)
# ---------------------------------------------------------------------------
YOUTUBE_API_KEY: str | None = os.getenv("YOUTUBE_API_KEY")

# ---------------------------------------------------------------------------
# Allgemein
# ---------------------------------------------------------------------------
TOP_N_NICHES: int = 20
MARKET_GEO: str = "DE"
TRENDS_TIMEFRAME: str = "today 3-m"
PYTRENDS_DELAY: float = 1.5       # Sekunden zwischen pytrends-Requests
YOUTUBE_API_DELAY: float = 0.5

# ---------------------------------------------------------------------------
# Mehrsprachige RSS-Feeds  (DE + EN + FR + ES)
# EN/FR/ES = Frühindikatoren, da Trends dort 4–8 Wochen früher auftauchen
# ---------------------------------------------------------------------------
RSS_FEEDS: dict[str, list[str]] = {
    "de": [
        "https://www.tagesschau.de/xml/rss2/",
        "https://www.spiegel.de/schlagzeilen/index.rss",
        "https://www.handelsblatt.com/contentexport/feed/top-themen",
        "https://www.focus.de/finanzen/index.rss",
        "https://www.golem.de/rss.php",           # Tech DE
        "https://www.reddit.com/r/de/.rss",
        "https://www.reddit.com/r/finanzen/.rss",
        "https://www.reddit.com/r/Finanzen/.rss",
        "https://www.reddit.com/r/artificial/.rss",
    ],
    "en": [
        "https://news.google.com/rss?hl=en-US&gl=US&ceid=US:en",
        "https://feeds.feedburner.com/TechCrunch",
        "https://www.reddit.com/r/personalfinance/.rss",
        "https://www.reddit.com/r/investing/.rss",
        "https://www.reddit.com/r/Entrepreneur/.rss",
        "https://www.reddit.com/r/artificial/.rss",
        "https://www.reddit.com/r/MachineLearning/.rss",
        "https://rss.nytimes.com/services/xml/rss/nyt/Technology.xml",
        "https://feeds.arstechnica.com/arstechnica/index",
    ],
    "fr": [
        "https://www.lemonde.fr/rss/une.xml",
        "https://www.lefigaro.fr/rss/figaro_actualites.xml",
    ],
    "es": [
        "https://feeds.elpais.com/mrss-s/pages/ep/site/elpais.com/portada",
        "https://www.elmundo.es/rss/portada.xml",
    ],
}

# ---------------------------------------------------------------------------
# Keyword-Übersetzungs-Mapping  EN → DE  (kein externer Dienst nötig)
# ---------------------------------------------------------------------------
KEYWORD_TRANSLATION_EN_DE: dict[str, str] = {
    "artificial intelligence": "künstliche intelligenz",
    "ai tools": "ki tools",
    "ai": "ki",
    "machine learning": "maschinelles lernen",
    "chatgpt": "chatgpt",
    "investing": "investieren",
    "investment": "investment",
    "stocks": "aktien",
    "etf": "etf",
    "crypto": "krypto",
    "cryptocurrency": "kryptowährung",
    "bitcoin": "bitcoin",
    "real estate": "immobilien",
    "insurance": "versicherung",
    "taxes": "steuern",
    "tax": "steuer",
    "finance": "finanzen",
    "personal finance": "persönliche finanzen",
    "passive income": "passives einkommen",
    "side hustle": "nebeneinkommen",
    "entrepreneurship": "unternehmertum",
    "software": "software",
    "saas": "saas",
    "technology": "technologie",
    "tech": "technik",
    "automation": "automatisierung",
    "productivity": "produktivität",
    "health": "gesundheit",
    "fitness": "fitness",
    "nutrition": "ernährung",
    "mental health": "mentale gesundheit",
    "education": "bildung",
    "online course": "online kurs",
    "travel": "reisen",
    "news": "nachrichten",
    "politics": "politik",
    "economy": "wirtschaft",
    "electric vehicle": "elektroauto",
    "solar energy": "solarenergie",
    "sustainability": "nachhaltigkeit",
    "gaming": "gaming",
    "smartphone": "smartphone",
    "cybersecurity": "cybersicherheit",
}

# ---------------------------------------------------------------------------
# CPM-Schätzwerte (EUR, DE-Markt, konservative Mittelwerte)
# DE-Markt liegt ~30% über US-Durchschnitt
# ---------------------------------------------------------------------------
CPM_TABLE: dict[str, float] = {
    "versicherung":           32.0,
    "steuern":                30.0,
    "finanzen":               28.0,
    "investing":              26.0,
    "immobilien":             25.0,
    "recht":                  22.0,
    "ki tools":               20.0,
    "künstliche intelligenz": 20.0,
    "software":               18.0,
    "saas":                   18.0,
    "technologie":            15.0,
    "cybersicherheit":        15.0,
    "business":               17.0,
    "marketing":              14.0,
    "automatisierung":        16.0,
    "bildung":                11.0,
    "gesundheit":             13.0,
    "nachhaltigkeit":         10.0,
    "elektroauto":            12.0,
    "produktivität":          12.0,
    "reisen":                  6.0,
    "kochen":                  5.5,
    "fitness":                 8.0,
    "gaming":                  4.0,
    "nachrichten":             8.0,
    "default":                 5.0,
}

# ---------------------------------------------------------------------------
# Affiliate-Potenzial je Kategorie
# ---------------------------------------------------------------------------
AFFILIATE_POTENTIAL: dict[str, str] = {
    "versicherung":           "sehr hoch",
    "finanzen":               "sehr hoch",
    "investing":              "sehr hoch",
    "steuern":                "hoch",
    "immobilien":             "hoch",
    "software":               "sehr hoch",
    "saas":                   "sehr hoch",
    "ki tools":               "sehr hoch",
    "künstliche intelligenz": "hoch",
    "technologie":            "hoch",
    "cybersicherheit":        "hoch",
    "business":               "hoch",
    "produktivität":          "hoch",
    "automatisierung":        "hoch",
    "gesundheit":             "mittel",
    "bildung":                "mittel",
    "nachhaltigkeit":         "mittel",
    "elektroauto":            "mittel",
    "reisen":                 "mittel",
    "fitness":                "mittel",
    "gaming":                 "niedrig",
    "kochen":                 "niedrig",
    "default":                "niedrig",
}

# ---------------------------------------------------------------------------
# Sponsoring-Potenzial je Kategorie (Instagram / YouTube Brand Deals)
# ---------------------------------------------------------------------------
SPONSORING_POTENTIAL: dict[str, str] = {
    "finanzen":               "sehr hoch",
    "investing":              "sehr hoch",
    "versicherung":           "hoch",
    "steuern":                "hoch",
    "technologie":            "sehr hoch",
    "software":               "sehr hoch",
    "saas":                   "sehr hoch",
    "ki tools":               "sehr hoch",
    "künstliche intelligenz": "hoch",
    "automatisierung":        "hoch",
    "cybersicherheit":        "hoch",
    "business":               "hoch",
    "produktivität":          "hoch",
    "gesundheit":             "hoch",
    "fitness":                "hoch",
    "nachhaltigkeit":         "mittel",
    "reisen":                 "hoch",
    "bildung":                "mittel",
    "gaming":                 "mittel",
    "kochen":                 "mittel",
    "default":                "niedrig",
}

# ---------------------------------------------------------------------------
# Instagram-Engagement-Potenzial je Kategorie
# (Wahrscheinlichkeit für Saves/Shares – relevant für Reels & Feed)
# ---------------------------------------------------------------------------
INSTAGRAM_ENGAGEMENT: dict[str, float] = {
    "ki tools":               0.85,
    "künstliche intelligenz": 0.82,
    "produktivität":          0.80,
    "investing":              0.75,
    "finanzen":               0.75,
    "passives einkommen":     0.78,
    "automatisierung":        0.78,
    "technologie":            0.70,
    "software":               0.65,
    "gesundheit":             0.72,
    "fitness":                0.68,
    "nachhaltigkeit":         0.65,
    "reisen":                 0.70,
    "bildung":                0.62,
    "business":               0.65,
    "gaming":                 0.55,
    "kochen":                 0.60,
    "default":                0.50,
}

# ---------------------------------------------------------------------------
# Scoring-Gewichte
# ---------------------------------------------------------------------------
WEIGHTS_YOUTUBE: dict[str, float] = {
    "cpm_score":          0.30,
    "trend_score":        0.20,
    "competition_score":  0.20,
    "affiliate_score":    0.15,
    "headline_score":     0.10,
    "faceless_score":     0.05,
}

WEIGHTS_INSTAGRAM: dict[str, float] = {
    "engagement_potential": 0.30,
    "sponsoring_score":     0.25,
    "trend_score":          0.20,
    "affiliate_score":      0.15,
    "headline_score":       0.10,
}

# Sicherheitscheck – Gewichte müssen 1.0 ergeben
assert abs(sum(WEIGHTS_YOUTUBE.values()) - 1.0) < 1e-9, "YT-Gewichte != 1.0"
assert abs(sum(WEIGHTS_INSTAGRAM.values()) - 1.0) < 1e-9, "IG-Gewichte != 1.0"

# ---------------------------------------------------------------------------
# Stopwords (für Keyword-Extraktion aus Headlines)
# ---------------------------------------------------------------------------
STOPWORDS: dict[str, set[str]] = {
    "de": {
        "der", "die", "das", "und", "in", "im", "ist", "zu", "von", "mit",
        "auf", "für", "an", "bei", "nach", "aus", "als", "durch", "über",
        "auch", "sich", "wie", "nicht", "ein", "eine", "einer", "eines",
        "dem", "den", "des", "er", "sie", "es", "wir", "ihr", "sie",
        "hat", "haben", "wird", "werden", "war", "waren", "sein", "sind",
        "mehr", "aber", "oder", "wenn", "dann", "dass", "so", "doch",
        "noch", "schon", "nur", "jetzt", "neue", "neuer", "neues",
    },
    "en": {
        "the", "a", "an", "and", "in", "is", "to", "of", "for", "on",
        "with", "at", "by", "from", "as", "or", "are", "was", "were",
        "be", "been", "has", "have", "will", "would", "could", "should",
        "it", "its", "this", "that", "these", "those", "not", "but",
        "new", "more", "how", "why", "what", "when", "who", "which",
        "says", "say", "said", "about", "up", "out", "into", "over",
    },
    "fr": {
        "le", "la", "les", "de", "du", "des", "un", "une", "et", "en",
        "à", "au", "aux", "est", "sont", "pour", "dans", "sur", "par",
        "avec", "que", "qui", "ne", "pas", "plus", "ou", "ce", "se",
    },
    "es": {
        "el", "la", "los", "las", "de", "del", "un", "una", "y", "en",
        "es", "son", "para", "con", "por", "que", "no", "se", "al", "su",
        "una", "más", "pero", "como", "este", "esta",
    },
}
