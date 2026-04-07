"""
Analysiert die Wettbewerbssituation einer Nische auf YouTube.

Competition Score ist invers: je weniger Konkurrenz, desto höher der Score.
"""


def get_competition_score(search_results: int, avg_subs: float) -> float:
    """
    Berechnet den Wettbewerbs-Score (0.0–1.0, höher = weniger Konkurrenz).

    Stufen nach YouTube-Suchergebnissen:
    - < 10.000    → 1.0  (Blauer Ozean)
    - 10k–100k   → 0.7  (geringe Konkurrenz)
    - 100k–500k  → 0.5  (mittlere Konkurrenz)
    - 500k–1M    → 0.3  (hohe Konkurrenz)
    - > 1M       → 0.1  (sehr gesättigter Markt)

    Zusätzlicher Malus wenn Top-Kanäle sehr viele Abonnenten haben
    (hohe Eintrittsbarriere).
    """
    # Basis-Score nach Suchergebnis-Anzahl
    if search_results < 10_000:
        base = 1.0
    elif search_results < 100_000:
        base = 0.7
    elif search_results < 500_000:
        base = 0.5
    elif search_results < 1_000_000:
        base = 0.3
    else:
        base = 0.1

    # Malus für sehr große Kanäle (Einstieg schwerer)
    if avg_subs > 500_000:
        base = max(0.05, base - 0.2)
    elif avg_subs > 100_000:
        base = max(0.05, base - 0.1)

    return round(base, 4)


def classify_competition(score: float) -> str:
    """Gibt ein menschenlesbares Label zurück."""
    if score >= 0.8:
        return "sehr niedrig (Blauer Ozean)"
    elif score >= 0.6:
        return "niedrig"
    elif score >= 0.4:
        return "mittel"
    elif score >= 0.2:
        return "hoch"
    else:
        return "sehr hoch (gesättigter Markt)"
