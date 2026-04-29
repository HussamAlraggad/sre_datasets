"""
Unit Tests for AI Teaching Modules
Tests for context_generator, reference_extractor, ai_documentation, and knowledge_base
"""

import tempfile
from datetime import datetime
from pathlib import Path

import pytest

from mini_wiki.ai_teaching.context_generator import ContextGenerator, ContextConfig
from mini_wiki.ai_teaching.reference_extractor import (
    ReferenceExtractor,
    Reference,
    URLExtractor,
    CitationExtractor,
)
from mini_wiki.ai_teaching.ai_documentation import (
    AIDocumentationGenerator,
    DocumentationEntry,
)
from mini_wiki.ai_teaching.knowledge_base import KnowledgeBase


# ============================================================================
# Context Generator Tests
# ============================================================================


class TestSentenceExtractor:
    """Tests for sentence extraction"""

    def test_extract_sentences(self):
        """Test sentence extraction"""
        from mini_wiki.ai_teaching.context_generator import SentenceExtractor

        text = "This is a test. This is another sentence! And a third one?"
        sentences = SentenceExtractor.extract_sentences(text)

        assert len(sentences) == 3
        assert sentences[0].strip().rstrip(".") == "This is a test" or sentences[0] == "This is a test."

    def test_get_sentence_scores(self):
        """Test sentence scoring"""
        from mini_wiki.ai_teaching.context_generator import SentenceExtractor

        sentences = [
            "Machine learning is great",
            "Deep learning is powerful",
            "Machine learning algorithms",
        ]
        query_terms = ["machine", "learning"]

        scores = SentenceExtractor.get_sentence_scores(sentences, query_terms)

        assert len(scores) == 3
        assert scores[0] > scores[1]  # First should score higher


class TestContextGenerator:
    """Tests for context generator"""

    @pytest.fixture
    def context_generator(self):
        """Create context generator"""
        config = ContextConfig(max_context_length=500, max_sentences=5)
        return ContextGenerator(config)

    def test_generate_context(self, context_generator):
        """Test context generation"""
        document = "Machine learning is great. Deep learning is powerful. Neural networks are useful."
        query_terms = ["machine", "learning"]

        context = context_generator.generate_context(
            document, query_terms, document_id=1
        )

        assert context["document_id"] == 1
        assert len(context["context"]) > 0
        assert len(context["key_sentences"]) > 0

    def test_generate_batch_context(self, context_generator):
        """Test batch context generation"""
        documents = [
            "Machine learning is great",
            "Deep learning is powerful",
        ]
        query_terms = ["learning"]

        contexts = context_generator.generate_batch_context(
            documents, query_terms, document_ids=[1, 2]
        )

        assert len(contexts) == 2

    def test_combine_contexts(self, context_generator):
        """Test combining contexts"""
        contexts = [
            {
                "document_id": 1,
                "context": "Machine learning is great",
                "summary": "ML summary",
            },
            {
                "document_id": 2,
                "context": "Deep learning is powerful",
                "summary": "DL summary",
            },
        ]

        combined = context_generator.combine_contexts(contexts)

        assert combined["combined_context"]
        assert len(combined["source_documents"]) == 2

    def test_extract_key_phrases(self, context_generator):
        """Test key phrase extraction"""
        text = "Machine learning machine learning deep learning"

        phrases = context_generator.extract_key_phrases(text, top_k=3)

        assert len(phrases) > 0
        assert phrases[0][0] in ["machine", "learning", "deep"]


# ============================================================================
# Reference Extractor Tests
# ============================================================================


class TestURLExtractor:
    """Tests for URL extraction"""

    def test_extract_urls(self):
        """Test URL extraction"""
        text = "Check out https://example.com and http://test.org for more info"

        urls = URLExtractor.extract_urls(text)

        assert len(urls) == 2
        assert "https://example.com" in urls

    def test_extract_urls_with_context(self):
        """Test URL extraction with context"""
        text = "Visit https://example.com for more information"

        results = URLExtractor.extract_urls_with_context(text)

        assert len(results) > 0
        assert results[0][0] == "https://example.com"


class TestCitationExtractor:
    """Tests for citation extraction"""

    def test_extract_citations(self):
        """Test citation extraction"""
        text = "According to [Smith, 2020] and [Jones, 2021], this is true"

        citations = CitationExtractor.extract_citations(text)

        assert len(citations) >= 2

    def test_extract_author_year(self):
        """Test author-year extraction"""
        text = "Smith (2020) found that learning is important"

        results = CitationExtractor.extract_author_year(text)

        assert len(results) > 0


class TestReference:
    """Tests for Reference class"""

    def test_reference_to_apa(self):
        """Test APA formatting"""
        ref = Reference(
            title="Machine Learning Basics",
            authors=["Smith, J.", "Jones, M."],
            publication="Journal of ML",
            year=2020,
        )

        apa = ref.to_apa()

        assert "Smith" in apa
        assert "2020" in apa

    def test_reference_to_mla(self):
        """Test MLA formatting"""
        ref = Reference(
            title="Machine Learning Basics",
            authors=["Smith, J."],
            publication="Journal of ML",
            year=2020,
        )

        mla = ref.to_mla()

        assert "Smith" in mla
        assert "2020" in mla

    def test_reference_to_chicago(self):
        """Test Chicago formatting"""
        ref = Reference(
            title="Machine Learning Basics",
            authors=["Smith, J."],
            year=2020,
        )

        chicago = ref.to_chicago()

        assert "Smith" in chicago


class TestReferenceExtractor:
    """Tests for reference extractor"""

    @pytest.fixture
    def reference_extractor(self):
        """Create reference extractor"""
        return ReferenceExtractor()

    def test_extract_references_from_text(self, reference_extractor):
        """Test reference extraction"""
        text = "See https://example.com and [Smith, 2020] for details"

        references = reference_extractor.extract_references_from_text(text)

        assert len(references) > 0

    def test_create_reference(self, reference_extractor):
        """Test reference creation"""
        ref = reference_extractor.create_reference(
            title="Test Paper",
            authors=["Smith, J."],
            year=2020,
        )

        assert ref.title == "Test Paper"
        assert ref.year == 2020

    def test_format_references(self, reference_extractor):
        """Test reference formatting"""
        references = [
            Reference(title="Paper 1", authors=["Smith"], year=2020),
            Reference(title="Paper 2", authors=["Jones"], year=2021),
        ]

        formatted = reference_extractor.format_references(references, style="apa")

        assert len(formatted) == 2

    def test_build_reference_list(self, reference_extractor):
        """Test reference list building"""
        references = [
            Reference(title="Paper 1", authors=["Smith"], year=2020),
            Reference(title="Paper 2", authors=["Jones"], year=2021),
        ]

        ref_list = reference_extractor.build_reference_list(references)

        assert "Paper 1" in ref_list
        assert "Paper 2" in ref_list


# ============================================================================
# AI Documentation Tests
# ============================================================================


class TestDocumentationEntry:
    """Tests for documentation entry"""

    def test_documentation_entry_to_dict(self):
        """Test converting to dictionary"""
        entry = DocumentationEntry(
            topic="Machine Learning",
            context="ML is great",
            summary="Summary",
            key_points=["Point 1", "Point 2"],
            references=[],
        )

        data = entry.to_dict()

        assert data["topic"] == "Machine Learning"
        assert len(data["key_points"]) == 2

    def test_documentation_entry_to_yaml(self):
        """Test converting to YAML"""
        entry = DocumentationEntry(
            topic="Machine Learning",
            context="ML is great",
            summary="Summary",
            key_points=["Point 1"],
            references=[],
        )

        yaml_str = entry.to_yaml()

        assert "Machine Learning" in yaml_str

    def test_documentation_entry_to_json(self):
        """Test converting to JSON"""
        entry = DocumentationEntry(
            topic="Machine Learning",
            context="ML is great",
            summary="Summary",
            key_points=["Point 1"],
            references=[],
        )

        json_str = entry.to_json()

        assert "Machine Learning" in json_str

    def test_documentation_entry_to_markdown(self):
        """Test converting to Markdown"""
        entry = DocumentationEntry(
            topic="Machine Learning",
            context="ML is great",
            summary="Summary",
            key_points=["Point 1"],
            references=[],
        )

        md = entry.to_markdown()

        assert "# Machine Learning" in md


class TestAIDocumentationGenerator:
    """Tests for AI documentation generator"""

    @pytest.fixture
    def doc_generator(self):
        """Create documentation generator"""
        return AIDocumentationGenerator()

    def test_generate_documentation(self, doc_generator):
        """Test documentation generation"""
        contexts = [
            {
                "document_id": 1,
                "context": "Machine learning is great",
                "summary": "ML summary",
                "key_sentences": ["ML is great"],
                "metadata": {},
            }
        ]

        entry = doc_generator.generate_documentation(
            topic="Machine Learning",
            contexts=contexts,
        )

        assert entry.topic == "Machine Learning"
        assert entry.context

    def test_generate_batch_documentation(self, doc_generator):
        """Test batch documentation generation"""
        topics = ["ML", "DL"]
        contexts_list = [
            [{"document_id": 1, "context": "ML", "summary": "ML", "key_sentences": [], "metadata": {}}],
            [{"document_id": 2, "context": "DL", "summary": "DL", "key_sentences": [], "metadata": {}}],
        ]

        entries = doc_generator.generate_batch_documentation(topics, contexts_list)

        assert len(entries) == 2

    def test_save_and_load_documentation(self, doc_generator, tmp_path):
        """Test saving and loading documentation"""
        entry = DocumentationEntry(
            topic="ML",
            context="Content",
            summary="Summary",
            key_points=[],
            references=[],
        )

        filepath = tmp_path / "doc.yaml"
        doc_generator.save_documentation(entry, str(filepath), format="yaml")

        loaded = doc_generator.load_documentation(str(filepath))

        assert loaded.topic == "ML"

    def test_format_for_ai_training(self, doc_generator):
        """Test formatting for AI training"""
        entry = DocumentationEntry(
            topic="ML",
            context="Content",
            summary="Summary",
            key_points=["Point 1"],
            references=[],
        )

        formatted = doc_generator.format_for_ai_training(entry)

        assert "Topic: ML" in formatted
        assert "Summary: Summary" in formatted


# ============================================================================
# Knowledge Base Tests
# ============================================================================


class TestKnowledgeBase:
    """Tests for knowledge base"""

    @pytest.fixture
    def knowledge_base(self, tmp_path):
        """Create knowledge base"""
        return KnowledgeBase(base_path=tmp_path / "kb")

    def test_add_entry(self, knowledge_base):
        """Test adding entry"""
        entry = DocumentationEntry(
            topic="ML",
            context="Content",
            summary="Summary",
            key_points=[],
            references=[],
        )

        entry_id = knowledge_base.add_entry("Machine Learning", entry, tags=["ml"])

        assert entry_id
        assert entry_id in knowledge_base.index

    def test_get_entry(self, knowledge_base):
        """Test getting entry"""
        entry = DocumentationEntry(
            topic="ML",
            context="Content",
            summary="Summary",
            key_points=[],
            references=[],
        )

        entry_id = knowledge_base.add_entry("ML", entry)
        retrieved = knowledge_base.get_entry(entry_id)

        assert retrieved is not None
        assert retrieved.topic == "ML"

    def test_search_by_topic(self, knowledge_base):
        """Test topic search"""
        entry = DocumentationEntry(
            topic="Machine Learning",
            context="Content",
            summary="Summary",
            key_points=[],
            references=[],
        )

        knowledge_base.add_entry("Machine Learning", entry)

        results = knowledge_base.search_by_topic("Machine")

        assert len(results) > 0

    def test_search_by_tag(self, knowledge_base):
        """Test tag search"""
        entry = DocumentationEntry(
            topic="ML",
            context="Content",
            summary="Summary",
            key_points=[],
            references=[],
        )

        knowledge_base.add_entry("ML", entry, tags=["ml", "ai"])

        results = knowledge_base.search_by_tag("ml")

        assert len(results) > 0

    def test_list_entries(self, knowledge_base):
        """Test listing entries"""
        entry = DocumentationEntry(
            topic="ML",
            context="Content",
            summary="Summary",
            key_points=[],
            references=[],
        )

        knowledge_base.add_entry("ML", entry, tags=["ml"])

        entries = knowledge_base.list_entries()

        assert len(entries) > 0

    def test_update_entry(self, knowledge_base):
        """Test updating entry"""
        entry = DocumentationEntry(
            topic="ML",
            context="Content",
            summary="Summary",
            key_points=[],
            references=[],
        )

        entry_id = knowledge_base.add_entry("ML", entry)

        updated_entry = DocumentationEntry(
            topic="ML Updated",
            context="New content",
            summary="New summary",
            key_points=[],
            references=[],
        )

        success = knowledge_base.update_entry(entry_id, updated_entry)

        assert success

    def test_delete_entry(self, knowledge_base):
        """Test deleting entry"""
        entry = DocumentationEntry(
            topic="ML",
            context="Content",
            summary="Summary",
            key_points=[],
            references=[],
        )

        entry_id = knowledge_base.add_entry("ML", entry)

        success = knowledge_base.delete_entry(entry_id)

        assert success
        assert entry_id not in knowledge_base.index

    def test_get_stats(self, knowledge_base):
        """Test getting statistics"""
        entry = DocumentationEntry(
            topic="ML",
            context="Content",
            summary="Summary",
            key_points=[],
            references=[],
        )

        knowledge_base.add_entry("ML", entry, tags=["ml"], difficulty="beginner")

        stats = knowledge_base.get_stats()

        assert stats["total_entries"] == 1
        assert "beginner" in stats["difficulty_counts"]

    def test_export_import(self, knowledge_base, tmp_path):
        """Test export and import"""
        entry = DocumentationEntry(
            topic="ML",
            context="Content",
            summary="Summary",
            key_points=[],
            references=[],
        )

        knowledge_base.add_entry("ML", entry)

        export_file = tmp_path / "export.json"
        knowledge_base.export_to_json(str(export_file))

        # Create new KB and import
        new_kb = KnowledgeBase(base_path=tmp_path / "kb2")
        count = new_kb.import_from_json(str(export_file))

        assert count > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
