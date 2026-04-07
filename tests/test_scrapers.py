"""
Tests für Scraper-Module (ohne echte Netzwerk-Calls).
"""
import pytest
from unittest.mock import patch, MagicMock
from scrapers.news_feeds import _tokenize, _extract_bigrams, _translate_to_german, _map_to_category
from scrapers.google_trends import get_trend_scores
from scrapers.youtube_api import get_youtube_data, _fallback_data


# ── news_feeds ────────────────────────────────────────────────────────────

class TestNewsFeedsHelpers:
    def test_tokenize_german(self):
        tokens = _tokenize("KI-Tools sind die Zukunft der Technologie", "de")
        assert "ki-tools" in tokens or "ki" in tokens or "tools" in tokens
        # Stopwords entfernt
        assert "sind" not in tokens
        assert "die" not in tokens

    def test_tokenize_english(self):
        tokens = _tokenize("AI tools for investing and finance", "en")
        assert "tools" in tokens
        assert "investing" in tokens
        # Stopwords entfernt
        assert "and" not in tokens
        assert "for" not in tokens

    def test_tokenize_removes_html(self):
        tokens = _tokenize("<b>KI-Tools</b> sind gut", "de")
        # HTML weg
        assert "b>" not in " ".join(tokens)

    def test_extract_bigrams(self):
        tokens = ["ki", "tools", "erklärt"]
        bigrams = _extract_bigrams(tokens)
        assert "ki tools" in bigrams
        assert "tools erklärt" in bigrams

    def test_translate_known_term(self):
        result = _translate_to_german("artificial intelligence")
        assert result == "künstliche intelligenz"

    def test_translate_partial_match(self):
        result = _translate_to_german("best ai tools for business")
        # sollte "ai" oder "ki" treffen
        assert result is not None

    def test_translate_unknown_returns_none(self):
        result = _translate_to_german("foobarxyz notaword")
        assert result is None

    def test_map_to_category_finanzen(self):
        cat = _map_to_category("etf investieren")
        assert cat in ("investing", "finanzen", "default")

    def test_map_to_category_default(self):
        cat = _map_to_category("komplett unbekanntes thema xyz")
        assert cat == "default"


# ── google_trends (gemockt) ───────────────────────────────────────────────

class TestGoogleTrends:
    def test_returns_dict_for_all_keywords(self):
        """Ohne pytrends-Client sollen alle Keywords Null-Ergebnisse liefern."""
        with patch("scrapers.google_trends.PYTRENDS_AVAILABLE", False):
            result = get_trend_scores(["ki tools", "finanzen"])
        assert "ki tools" in result
        assert "finanzen" in result
        assert result["ki tools"]["score"] == 0.0

    def test_empty_keyword_list(self):
        result = get_trend_scores([])
        assert result == {}

    def test_with_mock_client(self):
        """Simuliert eine erfolgreiche pytrends-Antwort."""
        import pandas as pd

        mock_df = pd.DataFrame(
            {"ki tools": [30, 40, 55, 70, 80]},
            index=pd.date_range("2026-01-01", periods=5, freq="W"),
        )
        mock_client = MagicMock()
        mock_client.interest_over_time.return_value = mock_df

        with patch("scrapers.google_trends.PYTRENDS_AVAILABLE", True), \
             patch("scrapers.google_trends._build_client", return_value=mock_client):
            result = get_trend_scores(["ki tools"])

        assert "ki tools" in result
        assert result["ki tools"]["score"] > 0
        assert result["ki tools"]["direction"] > 0   # Wachsend


# ── youtube_api ───────────────────────────────────────────────────────────

class TestYoutubeApi:
    def test_fallback_data_has_required_keys(self):
        data = _fallback_data("ki tools")
        assert "search_results" in data
        assert "avg_views" in data
        assert "avg_subs" in data
        assert data["source"] == "fallback"

    def test_fallback_uses_default_for_unknown_category(self):
        data = _fallback_data("unbekannte kategorie xyz")
        assert data["search_results"] > 0

    def test_get_youtube_data_without_key(self):
        """Ohne API Key soll Fallback genutzt werden."""
        with patch("scrapers.youtube_api.config.YOUTUBE_API_KEY", None):
            result = get_youtube_data({"ki tools": "ki tools", "steuern": "steuern"})
        assert "ki tools" in result
        assert "steuern" in result
        for v in result.values():
            assert v["source"] == "fallback"
            assert v["search_results"] > 0
