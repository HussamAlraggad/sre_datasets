"""
Unit Tests for Ranking Modules
Tests for relevance_scorer, importance_scorer, ranking_engine, and ranking_presets
"""

from datetime import datetime, timedelta

import numpy as np
import pytest

from mini_wiki.ranking.relevance_scorer import (
    RelevanceScorer,
    RelevanceConfig,
    SimilarityScorer,
    TFIDFScorer,
)
from mini_wiki.ranking.importance_scorer import (
    ImportanceScorer,
    ImportanceConfig,
    FrequencyScorer,
    LengthScorer,
    RecencyScorer,
    CitationScorer,
)
from mini_wiki.ranking.ranking_engine import (
    RankingEngine,
    RankingConfig,
    RankingResult,
)
from mini_wiki.ranking.ranking_presets import RankingPresets


# ============================================================================
# Relevance Scorer Tests
# ============================================================================


class TestSimilarityScorer:
    """Tests for similarity scorer"""

    def test_identical_embeddings(self):
        """Test similarity of identical embeddings"""
        config = RelevanceConfig()
        scorer = SimilarityScorer(config)

        embedding = np.array([1.0, 0.0, 0.0])
        similarity = scorer.score(embedding, embedding)

        assert 0.99 <= similarity <= 1.01

    def test_orthogonal_embeddings(self):
        """Test similarity of orthogonal embeddings"""
        config = RelevanceConfig()
        scorer = SimilarityScorer(config)

        e1 = np.array([1.0, 0.0, 0.0])
        e2 = np.array([0.0, 1.0, 0.0])
        similarity = scorer.score(e1, e2)

        assert similarity < 0.1

    def test_batch_similarity(self):
        """Test batch similarity computation"""
        config = RelevanceConfig()
        scorer = SimilarityScorer(config)

        query = np.array([1.0, 0.0, 0.0])
        documents = np.array([
            [1.0, 0.0, 0.0],
            [0.0, 1.0, 0.0],
            [0.5, 0.5, 0.0],
        ])

        similarities = scorer.score_batch(query, documents)

        assert len(similarities) == 3
        assert similarities[0] > similarities[1]  # First should be most similar


class TestTFIDFScorer:
    """Tests for TF-IDF scorer"""

    def test_fit_and_score(self):
        """Test fitting and scoring"""
        config = RelevanceConfig()
        scorer = TFIDFScorer(config)

        documents = [
            "machine learning is great",
            "deep learning is powerful",
            "machine learning and deep learning",
        ]

        scorer.fit(documents)

        score = scorer.score("machine learning", 0)

        assert 0 <= score <= 1

    def test_batch_scoring(self):
        """Test batch scoring"""
        config = RelevanceConfig()
        scorer = TFIDFScorer(config)

        documents = [
            "machine learning",
            "deep learning",
            "machine learning deep learning",
        ]

        scorer.fit(documents)

        scores = scorer.score_batch("machine learning", [0, 1, 2])

        assert len(scores) == 3
        assert scores[0] > scores[1]  # First should score higher


class TestRelevanceScorer:
    """Tests for relevance scorer"""

    @pytest.fixture
    def relevance_scorer(self):
        """Create relevance scorer"""
        config = RelevanceConfig(
            similarity_weight=0.7,
            tfidf_weight=0.3,
        )
        return RelevanceScorer(config)

    def test_score_with_embeddings(self, relevance_scorer):
        """Test scoring with embeddings"""
        query_text = "machine learning"
        query_embedding = np.array([1.0, 0.0, 0.0])

        document_text = "machine learning is great"
        document_embedding = np.array([0.9, 0.1, 0.0])

        score = relevance_scorer.score(
            query_text,
            query_embedding,
            document_text,
            document_embedding,
        )

        assert 0 <= score <= 1

    def test_batch_scoring(self, relevance_scorer):
        """Test batch scoring"""
        query_text = "machine learning"
        query_embedding = np.array([1.0, 0.0, 0.0])

        document_texts = [
            "machine learning is great",
            "deep learning is powerful",
        ]
        document_embeddings = np.array([
            [0.9, 0.1, 0.0],
            [0.1, 0.9, 0.0],
        ])

        scores = relevance_scorer.score_batch(
            query_text,
            query_embedding,
            document_texts,
            document_embeddings,
        )

        assert len(scores) == 2
        assert scores[0] > scores[1]

    def test_set_weights(self, relevance_scorer):
        """Test setting weights"""
        relevance_scorer.set_weights(0.5, 0.5)

        config = relevance_scorer.get_config()

        assert config["similarity_weight"] == 0.5
        assert config["tfidf_weight"] == 0.5


# ============================================================================
# Importance Scorer Tests
# ============================================================================


class TestFrequencyScorer:
    """Tests for frequency scorer"""

    def test_frequency_scoring(self):
        """Test frequency scoring"""
        config = ImportanceConfig()
        scorer = FrequencyScorer(config)

        query_terms = ["machine", "learning"]
        document = "machine learning is about machine learning algorithms"

        score = scorer.score(query_terms, document)

        assert 0 <= score <= 1
        assert score > 0  # Should have some score

    def test_batch_frequency_scoring(self):
        """Test batch frequency scoring"""
        config = ImportanceConfig()
        scorer = FrequencyScorer(config)

        query_terms = ["machine"]
        documents = [
            "machine learning",
            "deep learning",
            "machine machine machine",
        ]

        scores = scorer.score_batch(query_terms, documents)

        assert len(scores) == 3
        assert scores[2] > scores[1]  # Third should score higher


class TestLengthScorer:
    """Tests for length scorer"""

    def test_length_scoring_without_fit(self):
        """Test length scoring without fitting"""
        config = ImportanceConfig()
        scorer = LengthScorer(config)

        document = "This is a test document with some words"
        score = scorer.score(document)

        assert 0 <= score <= 1

    def test_length_scoring_with_fit(self):
        """Test length scoring with fitting"""
        config = ImportanceConfig()
        scorer = LengthScorer(config)

        documents = [
            "short",
            "this is a medium length document",
            "this is a very long document " * 10,
        ]

        scorer.fit(documents)

        scores = scorer.score_batch(documents)

        assert len(scores) == 3
        assert all(0 <= s <= 1 for s in scores)


class TestRecencyScorer:
    """Tests for recency scorer"""

    def test_recency_scoring(self):
        """Test recency scoring"""
        config = ImportanceConfig()
        scorer = RecencyScorer(config)

        now = datetime.now()
        old_date = now - timedelta(days=365)

        score_now = scorer.score(now)
        score_old = scorer.score(old_date)

        assert score_now > score_old

    def test_batch_recency_scoring(self):
        """Test batch recency scoring"""
        config = ImportanceConfig()
        scorer = RecencyScorer(config)

        now = datetime.now()
        dates = [
            now,
            now - timedelta(days=30),
            now - timedelta(days=365),
        ]

        scores = scorer.score_batch(dates)

        assert len(scores) == 3
        assert scores[0] > scores[1] > scores[2]


class TestCitationScorer:
    """Tests for citation scorer"""

    def test_citation_scoring_without_fit(self):
        """Test citation scoring without fitting"""
        config = ImportanceConfig()
        scorer = CitationScorer(config)

        score = scorer.score(10)

        assert 0 <= score <= 1

    def test_citation_scoring_with_fit(self):
        """Test citation scoring with fitting"""
        config = ImportanceConfig()
        scorer = CitationScorer(config)

        citation_counts = [0, 10, 50, 100]
        scorer.fit(citation_counts)

        scores = scorer.score_batch(citation_counts)

        assert len(scores) == 4
        assert scores[3] > scores[2] > scores[1] > scores[0]


class TestImportanceScorer:
    """Tests for importance scorer"""

    @pytest.fixture
    def importance_scorer(self):
        """Create importance scorer"""
        config = ImportanceConfig(
            frequency_weight=0.3,
            length_weight=0.2,
            recency_weight=0.3,
            citation_weight=0.2,
        )
        return ImportanceScorer(config)

    def test_score(self, importance_scorer):
        """Test scoring"""
        query_terms = ["machine", "learning"]
        document = "machine learning is great"
        date = datetime.now()
        citations = 10

        score = importance_scorer.score(
            query_terms,
            document,
            date,
            citations,
        )

        assert 0 <= score <= 1

    def test_batch_scoring(self, importance_scorer):
        """Test batch scoring"""
        query_terms = ["machine"]
        documents = [
            "machine learning",
            "deep learning",
        ]
        dates = [datetime.now(), datetime.now()]
        citations = [10, 5]

        scores = importance_scorer.score_batch(
            query_terms,
            documents,
            dates,
            citations,
        )

        assert len(scores) == 2

    def test_set_weights(self, importance_scorer):
        """Test setting weights"""
        importance_scorer.set_weights(0.25, 0.25, 0.25, 0.25)

        config = importance_scorer.get_config()

        assert config["frequency_weight"] == 0.25
        assert config["length_weight"] == 0.25
        assert config["recency_weight"] == 0.25
        assert config["citation_weight"] == 0.25


# ============================================================================
# Ranking Engine Tests
# ============================================================================


class TestRankingEngine:
    """Tests for ranking engine"""

    @pytest.fixture
    def ranking_engine(self):
        """Create ranking engine"""
        config = RankingConfig(
            relevance_weight=0.6,
            importance_weight=0.4,
        )
        return RankingEngine(config)

    def test_rank(self, ranking_engine):
        """Test ranking"""
        query_text = "machine learning"
        query_embedding = np.array([1.0, 0.0, 0.0])

        documents = [
            "machine learning is great",
            "deep learning is powerful",
        ]
        embeddings = np.array([
            [0.9, 0.1, 0.0],
            [0.1, 0.9, 0.0],
        ])

        results = ranking_engine.rank(
            query_text,
            query_embedding,
            documents,
            embeddings,
        )

        assert len(results) == 2
        assert results[0].rank == 1
        assert results[0].final_score >= results[1].final_score

    def test_rank_with_top_k(self, ranking_engine):
        """Test ranking with top-k"""
        query_text = "machine"
        query_embedding = np.array([1.0, 0.0, 0.0])

        documents = [
            "machine learning",
            "deep learning",
            "machine vision",
        ]
        embeddings = np.array([
            [0.9, 0.1, 0.0],
            [0.1, 0.9, 0.0],
            [0.8, 0.2, 0.0],
        ])

        results = ranking_engine.rank(
            query_text,
            query_embedding,
            documents,
            embeddings,
            top_k=2,
        )

        assert len(results) == 2

    def test_ranking_result_to_dict(self):
        """Test RankingResult to_dict"""
        result = RankingResult(
            record_id=1,
            relevance_score=0.8,
            importance_score=0.7,
            final_score=0.75,
            rank=1,
        )

        result_dict = result.to_dict()

        assert result_dict["record_id"] == 1
        assert result_dict["rank"] == 1

    def test_get_stats(self, ranking_engine):
        """Test getting statistics"""
        results = [
            RankingResult(1, 0.8, 0.7, 0.75, 1),
            RankingResult(2, 0.6, 0.5, 0.55, 2),
            RankingResult(3, 0.4, 0.3, 0.35, 3),
        ]

        stats = ranking_engine.get_stats(results)

        assert stats["count"] == 3
        assert stats["max_final"] == 0.75
        assert stats["min_final"] == 0.35

    def test_set_weights(self, ranking_engine):
        """Test setting weights"""
        ranking_engine.set_weights(0.7, 0.3)

        config = ranking_engine.get_config()

        assert config["relevance_weight"] == 0.7
        assert config["importance_weight"] == 0.3


# ============================================================================
# Ranking Presets Tests
# ============================================================================


class TestRankingPresets:
    """Tests for ranking presets"""

    def test_get_preset(self):
        """Test getting preset"""
        preset = RankingPresets.get_preset("balanced")

        assert preset is not None
        assert preset.name == "balanced"

    def test_list_presets(self):
        """Test listing presets"""
        presets = RankingPresets.list_presets()

        assert len(presets) > 0
        assert "balanced" in presets
        assert "research_focused" in presets

    def test_get_engine(self):
        """Test getting engine from preset"""
        engine = RankingPresets.get_engine("balanced")

        assert engine is not None
        assert isinstance(engine, RankingEngine)

    def test_create_custom(self):
        """Test creating custom preset"""
        preset = RankingPresets.create_custom(
            name="custom",
            description="Custom preset",
            relevance_weight=0.5,
            importance_weight=0.5,
        )

        assert preset.name == "custom"
        assert preset.ranking_config.relevance_weight == 0.5

    def test_invalid_preset(self):
        """Test getting invalid preset"""
        with pytest.raises(ValueError):
            RankingPresets.get_engine("invalid_preset")

    def test_all_presets_valid(self):
        """Test that all presets are valid"""
        for name in RankingPresets.list_presets().keys():
            engine = RankingPresets.get_engine(name)
            assert engine is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
