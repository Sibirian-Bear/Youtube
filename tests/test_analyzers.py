"""
Tests für alle Analyzer-Module.
"""
import pytest
from analyzers.faceless_filter import get_faceless_score
from analyzers.competition_analyzer import get_competition_score, classify_competition
from analyzers.platform_scorer import (
    get_cpm_score, get_affiliate_score, get_sponsoring_score,
    compute_youtube_score, compute_instagram_score, determine_best_platform,
)
from analyzers.niche_scorer import score_niches


# ── faceless_filter ────────────────────────────────────────────────────────

class TestFacelessFilter:
    def test_ki_tools_is_faceless(self):
        score, compatible = get_faceless_score("ki tools", "ki tools")
        assert compatible is True
        assert score >= 0.9

    def test_fitness_not_faceless(self):
        score, compatible = get_faceless_score("fitness workout", "fitness")
        assert compatible is False
        assert score < 0.5

    def test_finanzen_is_faceless(self):
        score, compatible = get_faceless_score("etf investieren", "finanzen")
        assert compatible is True

    def test_unknown_defaults_to_compatible(self):
        score, compatible = get_faceless_score("unbekannte nische xyz", "default")
        assert compatible is True
        assert 0.0 <= score <= 1.0


# ── competition_analyzer ──────────────────────────────────────────────────

class TestCompetitionAnalyzer:
    def test_blue_ocean(self):
        score = get_competition_score(5_000, 0)
        assert score == 1.0

    def test_low_competition(self):
        score = get_competition_score(50_000, 10_000)
        assert 0.6 <= score <= 0.8

    def test_saturated_market(self):
        score = get_competition_score(5_000_000, 0)
        assert score <= 0.15

    def test_high_subs_penalizes(self):
        score_low_subs = get_competition_score(200_000, 10_000)
        score_high_subs = get_competition_score(200_000, 600_000)
        assert score_low_subs > score_high_subs

    def test_classify_labels(self):
        assert "Ozean" in classify_competition(0.9)
        assert "sehr hoch" in classify_competition(0.05)


# ── platform_scorer ───────────────────────────────────────────────────────

class TestPlatformScorer:
    def test_cpm_versicherung_highest(self):
        score_v, cpm_v = get_cpm_score("versicherung")
        score_g, cpm_g = get_cpm_score("gaming")
        assert cpm_v > cpm_g
        assert score_v > score_g

    def test_cpm_score_range(self):
        score, cpm = get_cpm_score("finanzen")
        assert 0.0 <= score <= 1.0
        assert cpm > 0

    def test_affiliate_sehr_hoch(self):
        score, label = get_affiliate_score("versicherung")
        assert label == "sehr hoch"
        assert score == 1.0

    def test_affiliate_niedrig(self):
        score, label = get_affiliate_score("gaming")
        assert score < 0.5

    def test_youtube_score_range(self):
        yt = compute_youtube_score(0.8, 0.7, 0.6, 0.9, 0.5, 1.0)
        assert 0.0 <= yt <= 100.0

    def test_instagram_score_range(self):
        ig = compute_instagram_score(0.8, 0.7, 0.6, 0.9, 0.5)
        assert 0.0 <= ig <= 100.0

    def test_best_platform_both_when_close(self):
        result = determine_best_platform(75.0, 73.0)
        assert result == "Beide"

    def test_best_platform_youtube_when_higher(self):
        result = determine_best_platform(85.0, 60.0)
        assert result == "YouTube"

    def test_best_platform_instagram_when_higher(self):
        result = determine_best_platform(55.0, 80.0)
        assert result == "Instagram"


# ── niche_scorer (Integration) ────────────────────────────────────────────

SAMPLE_HEADLINES = {
    "ki tools": {
        "count": 8, "category": "ki tools",
        "headlines": ["ChatGPT Tools erklärt", "Beste KI-Tools 2026"],
        "languages": ["de", "en"], "early_indicator": True,
    },
    "fitness workout": {
        "count": 5, "category": "fitness",
        "headlines": ["Fitness Workout Zuhause"],
        "languages": ["de"], "early_indicator": False,
    },
    "etf investieren": {
        "count": 6, "category": "finanzen",
        "headlines": ["ETF Depot aufbauen"],
        "languages": ["de"], "early_indicator": False,
    },
}

SAMPLE_TRENDS = {
    "ki tools":        {"values": [40, 50, 65, 70, 80], "avg": 61.0, "direction": 20.0, "score": 0.8},
    "fitness workout": {"values": [60, 55, 50, 48, 45], "avg": 51.6, "direction": -5.0, "score": 0.45},
    "etf investieren": {"values": [30, 35, 40, 42, 45], "avg": 38.4, "direction": 8.0,  "score": 0.55},
}

SAMPLE_YT = {
    "ki tools":        {"search_results": 80_000,  "avg_views": 40_000, "avg_subs": 20_000, "source": "fallback"},
    "fitness workout": {"search_results": 900_000, "avg_views": 80_000, "avg_subs": 50_000, "source": "fallback"},
    "etf investieren": {"search_results": 200_000, "avg_views": 35_000, "avg_subs": 18_000, "source": "fallback"},
}


class TestNicheScorer:
    def test_faceless_only_removes_fitness(self):
        niches = score_niches(SAMPLE_HEADLINES, SAMPLE_TRENDS, SAMPLE_YT, faceless_only=True)
        keywords = [n.keyword for n in niches]
        assert "fitness workout" not in keywords

    def test_ki_tools_in_results(self):
        niches = score_niches(SAMPLE_HEADLINES, SAMPLE_TRENDS, SAMPLE_YT, faceless_only=True)
        keywords = [n.keyword for n in niches]
        assert "ki tools" in keywords

    def test_scores_in_range(self):
        niches = score_niches(SAMPLE_HEADLINES, SAMPLE_TRENDS, SAMPLE_YT, faceless_only=False)
        for n in niches:
            assert 0 <= n.youtube_score <= 100, f"YT Score out of range: {n.youtube_score}"
            assert 0 <= n.instagram_score <= 100, f"IG Score out of range: {n.instagram_score}"

    def test_early_indicator_set(self):
        niches = score_niches(SAMPLE_HEADLINES, SAMPLE_TRENDS, SAMPLE_YT, faceless_only=True)
        ki = next(n for n in niches if n.keyword == "ki tools")
        assert ki.early_indicator is True

    def test_sorted_by_youtube_score(self):
        niches = score_niches(SAMPLE_HEADLINES, SAMPLE_TRENDS, SAMPLE_YT, faceless_only=False)
        scores = [n.youtube_score for n in niches]
        assert scores == sorted(scores, reverse=True)

    def test_niche_has_reasoning(self):
        niches = score_niches(SAMPLE_HEADLINES, SAMPLE_TRENDS, SAMPLE_YT, faceless_only=True)
        for n in niches:
            assert len(n.reasoning) > 0

    def test_best_platform_set(self):
        niches = score_niches(SAMPLE_HEADLINES, SAMPLE_TRENDS, SAMPLE_YT, faceless_only=True)
        for n in niches:
            assert n.best_platform in ("YouTube", "Instagram", "Beide")
