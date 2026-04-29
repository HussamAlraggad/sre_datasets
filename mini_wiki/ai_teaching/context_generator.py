"""
Context Generator Module
Extracts and generates context from ranked documents for AI models

Features:
- Extract key sentences from documents
- Generate summaries using extractive summarization
- Build context windows around query terms
- Combine multiple document contexts
- Format context for AI consumption
"""

import logging
import re
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class ContextConfig:
    """Configuration for context generation

    Attributes:
        max_context_length: Maximum context length in characters (default: 2000)
        max_sentences: Maximum number of sentences to extract (default: 10)
        sentence_overlap: Overlap between context windows (default: 2)
        include_metadata: Include document metadata (default: True)
        include_ranking_info: Include ranking scores (default: True)
        summary_ratio: Ratio of sentences to keep in summary (default: 0.3)
    """

    max_context_length: int = 2000
    max_sentences: int = 10
    sentence_overlap: int = 2
    include_metadata: bool = True
    include_ranking_info: bool = True
    summary_ratio: float = 0.3


class SentenceExtractor:
    """Extract sentences from text"""

    @staticmethod
    def extract_sentences(text: str) -> List[str]:
        """Extract sentences from text

        Args:
            text: Input text

        Returns:
            List of sentences
        """
        if not text:
            return []

        # Split by common sentence delimiters
        sentences = re.split(r'(?<=[.!?])\s+', text.strip())

        # Filter empty sentences
        sentences = [s.strip() for s in sentences if s.strip()]

        return sentences

    @staticmethod
    def get_sentence_scores(
        sentences: List[str], query_terms: List[str]
    ) -> np.ndarray:
        """Score sentences by relevance to query

        Args:
            sentences: List of sentences
            query_terms: List of query terms

        Returns:
            Array of sentence scores
        """
        scores = np.zeros(len(sentences))

        for i, sentence in enumerate(sentences):
            sentence_lower = sentence.lower()

            # Count query term occurrences
            term_count = 0
            for term in query_terms:
                term_count += sentence_lower.count(term.lower())

            # Normalize by sentence length
            words = len(sentence.split())
            if words > 0:
                scores[i] = term_count / words

        return scores

    @staticmethod
    def extract_top_sentences(
        sentences: List[str], scores: np.ndarray, top_k: int
    ) -> List[Tuple[int, str]]:
        """Extract top-k sentences by score

        Args:
            sentences: List of sentences
            scores: Array of sentence scores
            top_k: Number of top sentences to extract

        Returns:
            List of (index, sentence) tuples in original order
        """
        if not sentences:
            return []

        # Get top-k indices
        top_indices = np.argsort(scores)[::-1][:top_k]

        # Sort by original position to maintain order
        top_indices = sorted(top_indices)

        # Return (index, sentence) tuples
        return [(int(idx), sentences[idx]) for idx in top_indices]


class ContextGenerator:
    """Generate context from documents"""

    def __init__(self, config: Optional[ContextConfig] = None):
        """Initialize context generator

        Args:
            config: Context configuration
        """
        self.config = config or ContextConfig()
        self.sentence_extractor = SentenceExtractor()

    def generate_context(
        self,
        document_text: str,
        query_terms: List[str],
        document_id: Optional[int] = None,
        ranking_info: Optional[Dict] = None,
    ) -> Dict:
        """Generate context from single document

        Args:
            document_text: Document text
            query_terms: List of query terms
            document_id: Document ID (optional)
            ranking_info: Ranking information (optional)

        Returns:
            Context dictionary
        """
        if not document_text:
            return {
                "document_id": document_id,
                "context": "",
                "summary": "",
                "key_sentences": [],
                "metadata": {},
            }

        # Extract sentences
        sentences = self.sentence_extractor.extract_sentences(document_text)

        if not sentences:
            return {
                "document_id": document_id,
                "context": "",
                "summary": "",
                "key_sentences": [],
                "metadata": {},
            }

        # Score sentences
        scores = self.sentence_extractor.get_sentence_scores(sentences, query_terms)

        # Extract top sentences
        num_sentences = min(self.config.max_sentences, len(sentences))
        top_sentences = self.sentence_extractor.extract_top_sentences(
            sentences, scores, num_sentences
        )

        # Build context
        context_sentences = [sent for _, sent in top_sentences]
        context = " ".join(context_sentences)

        # Truncate if needed
        if len(context) > self.config.max_context_length:
            context = context[: self.config.max_context_length].rsplit(" ", 1)[0] + "..."

        # Generate summary
        summary_sentences = int(len(sentences) * self.config.summary_ratio)
        summary_sentences = max(1, min(summary_sentences, len(sentences)))
        summary_top = self.sentence_extractor.extract_top_sentences(
            sentences, scores, summary_sentences
        )
        summary = " ".join([sent for _, sent in summary_top])

        # Build metadata
        metadata = {}
        if self.config.include_metadata:
            metadata["document_id"] = document_id
            metadata["total_sentences"] = len(sentences)
            metadata["extracted_sentences"] = len(top_sentences)
            metadata["context_length"] = len(context)

        if self.config.include_ranking_info and ranking_info:
            metadata["ranking_info"] = ranking_info

        logger.info(
            f"Generated context for document {document_id}: "
            f"{len(context)} chars, {len(top_sentences)} sentences"
        )

        return {
            "document_id": document_id,
            "context": context,
            "summary": summary,
            "key_sentences": context_sentences,
            "metadata": metadata,
        }

    def generate_batch_context(
        self,
        document_texts: List[str],
        query_terms: List[str],
        document_ids: Optional[List[int]] = None,
        ranking_infos: Optional[List[Dict]] = None,
    ) -> List[Dict]:
        """Generate context from multiple documents

        Args:
            document_texts: List of document texts
            query_terms: List of query terms
            document_ids: List of document IDs (optional)
            ranking_infos: List of ranking information (optional)

        Returns:
            List of context dictionaries
        """
        if document_ids is None:
            document_ids = list(range(len(document_texts)))

        if ranking_infos is None:
            ranking_infos = [None] * len(document_texts)

        contexts = []
        for text, doc_id, ranking_info in zip(
            document_texts, document_ids, ranking_infos
        ):
            context = self.generate_context(text, query_terms, doc_id, ranking_info)
            contexts.append(context)

        logger.info(f"Generated context for {len(contexts)} documents")

        return contexts

    def combine_contexts(
        self, contexts: List[Dict], max_combined_length: Optional[int] = None
    ) -> Dict:
        """Combine multiple contexts into single context

        Args:
            contexts: List of context dictionaries
            max_combined_length: Maximum combined length (default: config max)

        Returns:
            Combined context dictionary
        """
        if not contexts:
            return {
                "combined_context": "",
                "combined_summary": "",
                "source_documents": [],
                "metadata": {},
            }

        if max_combined_length is None:
            max_combined_length = self.config.max_context_length * 3

        # Combine contexts
        combined_context_parts = []
        combined_summary_parts = []
        source_documents = []

        for context in contexts:
            if context["context"]:
                combined_context_parts.append(context["context"])
                combined_summary_parts.append(context["summary"])
                source_documents.append(context["document_id"])

        # Join with separators
        combined_context = "\n\n".join(combined_context_parts)
        combined_summary = "\n\n".join(combined_summary_parts)

        # Truncate if needed
        if len(combined_context) > max_combined_length:
            combined_context = combined_context[:max_combined_length].rsplit(" ", 1)[0] + "..."

        metadata = {
            "num_documents": len(contexts),
            "num_source_documents": len(source_documents),
            "combined_length": len(combined_context),
            "source_documents": source_documents,
        }

        logger.info(
            f"Combined {len(contexts)} contexts: "
            f"{len(combined_context)} chars, {len(source_documents)} sources"
        )

        return {
            "combined_context": combined_context,
            "combined_summary": combined_summary,
            "source_documents": source_documents,
            "metadata": metadata,
        }

    def extract_key_phrases(
        self, text: str, top_k: int = 10
    ) -> List[Tuple[str, float]]:
        """Extract key phrases from text

        Args:
            text: Input text
            top_k: Number of top phrases to extract

        Returns:
            List of (phrase, score) tuples
        """
        if not text:
            return []

        # Simple phrase extraction: split by common delimiters
        words = text.lower().split()

        # Count word frequencies
        word_freq = {}
        for word in words:
            # Remove punctuation
            word = re.sub(r'[^\w]', '', word)
            if word and len(word) > 3:  # Skip short words
                word_freq[word] = word_freq.get(word, 0) + 1

        # Sort by frequency
        sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)

        # Normalize scores
        max_freq = sorted_words[0][1] if sorted_words else 1
        phrases = [
            (word, freq / max_freq) for word, freq in sorted_words[:top_k]
        ]

        return phrases

    def get_context_stats(self, context: Dict) -> Dict:
        """Get statistics about context

        Args:
            context: Context dictionary

        Returns:
            Statistics dictionary
        """
        return {
            "context_length": len(context.get("context", "")),
            "summary_length": len(context.get("summary", "")),
            "num_key_sentences": len(context.get("key_sentences", [])),
            "document_id": context.get("document_id"),
            "metadata": context.get("metadata", {}),
        }
