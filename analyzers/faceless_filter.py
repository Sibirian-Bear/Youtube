"""
Klassifiziert Nischen nach ihrer Eignung für Faceless-Content.

Score 1.0 = perfekt ohne Kamera produzierbar
Score 0.0 = Kamera zwingend nötig (z.B. Fitness-Demo, Kochen)
"""

# Keywords die auf Faceless-Eignung hindeuten
FACELESS_SIGNALS = {
    "ki tools", "künstliche intelligenz", "chatgpt", "ai",
    "software", "saas", "tutorial", "erklärvideo", "erklärung",
    "screen recording", "animation", "slideshow", "voiceover",
    "finanzen", "investing", "steuern", "versicherung", "immobilien",
    "technologie", "automatisierung", "cybersicherheit",
    "produktivität", "news", "nachrichten", "dokumentation",
    "history", "geschichte", "wissenschaft", "bildung", "kurs",
    "elektroauto", "nachhaltigkeit", "wirtschaft", "politik",
    "krypto", "bitcoin", "etf", "aktien", "passives einkommen",
}

# Keywords die Faceless erschweren
FACELESS_BLOCKERS = {
    "fitness", "yoga", "workout", "training", "kochen", "rezept",
    "beauty", "makeup", "haare", "vlog", "challenge", "reaction",
    "prank", "sport", "tanzen", "handwerk", "basteln",
}

# Partial-Match-Score: Nischen die faceless MÖGLICH aber nicht ideal sind
FACELESS_PARTIAL = {
    "reisen",       # Drone-Footage / Stock-Video möglich
    "gaming",       # Screen-Recording möglich
    "gesundheit",   # Infografiken möglich
}


def get_faceless_score(keyword: str, category: str) -> tuple[float, bool]:
    """
    Berechnet den Faceless-Score und gibt (score, compatible) zurück.

    Returns:
        (score 0.0–1.0, faceless_compatible bool)
    """
    kw = keyword.lower()
    cat = category.lower()

    # Hard blocker
    for blocker in FACELESS_BLOCKERS:
        if blocker in kw or blocker in cat:
            return 0.2, False

    # Direkte Faceless-Nische
    for signal in FACELESS_SIGNALS:
        if signal in kw or signal in cat:
            return 1.0, True

    # Partiell möglich
    for partial in FACELESS_PARTIAL:
        if partial in kw or partial in cat:
            return 0.6, True

    # Default: neutral – mit Stock-Footage/AI-Bildern machbar
    return 0.5, True
