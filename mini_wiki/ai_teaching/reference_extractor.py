"""
Reference Extractor Module
Extracts and formats references from documents

Features:
- Extract URLs and links
- Extract citations and references
- Extract author and publication information
- Format references in multiple styles (APA, MLA, Chicago)
- Build reference lists
"""

import logging
import re
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


@dataclass
class Reference:
    """Reference information

    Attributes:
        title: Reference title
        authors: List of authors
        publication: Publication name
        year: Publication year
        url: URL if available
        doi: DOI if available
        pages: Page numbers if available
        metadata: Additional metadata
    """

    title: str
    authors: Optional[List[str]] = None
    publication: Optional[str] = None
    year: Optional[int] = None
    url: Optional[str] = None
    doi: Optional[str] = None
    pages: Optional[str] = None
    metadata: Optional[Dict] = None

    def to_apa(self) -> str:
        """Format reference as APA style

        Returns:
            APA formatted reference
        """
        parts = []

        # Authors
        if self.authors:
            authors_str = ", ".join(self.authors[:3])
            if len(self.authors) > 3:
                authors_str += ", et al."
            parts.append(authors_str)

        # Year
        if self.year:
            parts.append(f"({self.year})")

        # Title
        parts.append(f"{self.title}.")

        # Publication
        if self.publication:
            parts.append(f"*{self.publication}*")

        # Pages
        if self.pages:
            parts.append(f"{self.pages}.")

        # DOI
        if self.doi:
            parts.append(f"https://doi.org/{self.doi}")

        # URL
        elif self.url:
            parts.append(f"Retrieved from {self.url}")

        return " ".join(parts)

    def to_mla(self) -> str:
        """Format reference as MLA style

        Returns:
            MLA formatted reference
        """
        parts = []

        # Authors
        if self.authors:
            authors_str = ", ".join(self.authors[:3])
            if len(self.authors) > 3:
                authors_str += ", et al."
            parts.append(authors_str + ".")

        # Title
        parts.append(f'"{self.title}."')

        # Publication
        if self.publication:
            parts.append(f"*{self.publication}*,")

        # Year
        if self.year:
            parts.append(str(self.year) + ".")

        # Pages
        if self.pages:
            parts.append(f"pp. {self.pages}.")

        # URL
        if self.url:
            parts.append(f"Web. {self.url}")

        return " ".join(parts)

    def to_chicago(self) -> str:
        """Format reference as Chicago style

        Returns:
            Chicago formatted reference
        """
        parts = []

        # Authors
        if self.authors:
            authors_str = ", ".join(self.authors[:3])
            if len(self.authors) > 3:
                authors_str += ", et al."
            parts.append(authors_str + ".")

        # Title
        parts.append(f'"{self.title}."')

        # Publication
        if self.publication:
            parts.append(f"In *{self.publication}*")

        # Year
        if self.year:
            parts.append(f"({self.year})")

        # Pages
        if self.pages:
            parts.append(f"{self.pages}.")

        # DOI
        if self.doi:
            parts.append(f"https://doi.org/{self.doi}")

        # URL
        elif self.url:
            parts.append(f"Accessed at {self.url}")

        return " ".join(parts)

    def to_dict(self) -> Dict:
        """Convert to dictionary

        Returns:
            Dictionary representation
        """
        return {
            "title": self.title,
            "authors": self.authors,
            "publication": self.publication,
            "year": self.year,
            "url": self.url,
            "doi": self.doi,
            "pages": self.pages,
            "metadata": self.metadata,
        }


class URLExtractor:
    """Extract URLs from text"""

    URL_PATTERN = re.compile(
        r'https?://(?:www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b(?:[-a-zA-Z0-9()@:%_\+.~#?&/=]*)'
    )

    @classmethod
    def extract_urls(cls, text: str) -> List[str]:
        """Extract URLs from text

        Args:
            text: Input text

        Returns:
            List of URLs
        """
        if not text:
            return []

        urls = cls.URL_PATTERN.findall(text)
        return list(set(urls))  # Remove duplicates

    @classmethod
    def extract_urls_with_context(
        cls, text: str, context_length: int = 50
    ) -> List[Tuple[str, str]]:
        """Extract URLs with surrounding context

        Args:
            text: Input text
            context_length: Length of context around URL

        Returns:
            List of (url, context) tuples
        """
        if not text:
            return []

        results = []
        for match in cls.URL_PATTERN.finditer(text):
            url = match.group()
            start = max(0, match.start() - context_length)
            end = min(len(text), match.end() + context_length)
            context = text[start:end].strip()

            results.append((url, context))

        return results


class CitationExtractor:
    """Extract citations from text"""

    # Pattern for citations like [1], [Author, Year], etc.
    CITATION_PATTERN = re.compile(r'\[([^\]]+)\]')

    @classmethod
    def extract_citations(cls, text: str) -> List[str]:
        """Extract citations from text

        Args:
            text: Input text

        Returns:
            List of citations
        """
        if not text:
            return []

        citations = cls.CITATION_PATTERN.findall(text)
        return list(set(citations))  # Remove duplicates

    @classmethod
    def extract_author_year(cls, text: str) -> List[Tuple[str, int]]:
        """Extract author-year citations

        Args:
            text: Input text

        Returns:
            List of (author, year) tuples
        """
        if not text:
            return []

        # Pattern for (Author, Year) or Author (Year)
        pattern = re.compile(r'\(([A-Z][a-z]+),?\s*(\d{4})\)')
        matches = pattern.findall(text)

        return [(author, int(year)) for author, year in matches]


class ReferenceExtractor:
    """Extract and format references from documents"""

    def __init__(self):
        """Initialize reference extractor"""
        self.url_extractor = URLExtractor()
        self.citation_extractor = CitationExtractor()

    def extract_references_from_text(self, text: str) -> List[Reference]:
        """Extract references from text

        Args:
            text: Input text

        Returns:
            List of Reference objects
        """
        references = []

        # Extract URLs
        urls = self.url_extractor.extract_urls(text)
        for url in urls:
            ref = Reference(
                title=url,
                url=url,
                metadata={"source": "url_extraction"},
            )
            references.append(ref)

        # Extract citations
        citations = self.citation_extractor.extract_citations(text)
        for citation in citations:
            ref = Reference(
                title=citation,
                metadata={"source": "citation_extraction"},
            )
            references.append(ref)

        logger.info(f"Extracted {len(references)} references from text")

        return references

    def create_reference(
        self,
        title: str,
        authors: Optional[List[str]] = None,
        publication: Optional[str] = None,
        year: Optional[int] = None,
        url: Optional[str] = None,
        doi: Optional[str] = None,
        pages: Optional[str] = None,
    ) -> Reference:
        """Create reference object

        Args:
            title: Reference title
            authors: List of authors (optional)
            publication: Publication name (optional)
            year: Publication year (optional)
            url: URL (optional)
            doi: DOI (optional)
            pages: Page numbers (optional)

        Returns:
            Reference object
        """
        return Reference(
            title=title,
            authors=authors,
            publication=publication,
            year=year,
            url=url,
            doi=doi,
            pages=pages,
        )

    def format_references(
        self, references: List[Reference], style: str = "apa"
    ) -> List[str]:
        """Format references in specified style

        Args:
            references: List of Reference objects
            style: Citation style ('apa', 'mla', 'chicago')

        Returns:
            List of formatted references

        Raises:
            ValueError: If style not supported
        """
        if style.lower() == "apa":
            return [ref.to_apa() for ref in references]
        elif style.lower() == "mla":
            return [ref.to_mla() for ref in references]
        elif style.lower() == "chicago":
            return [ref.to_chicago() for ref in references]
        else:
            raise ValueError(
                f"Unsupported citation style: {style}. "
                f"Supported: apa, mla, chicago"
            )

    def build_reference_list(
        self, references: List[Reference], style: str = "apa", sort_by: str = "title"
    ) -> str:
        """Build formatted reference list

        Args:
            references: List of Reference objects
            style: Citation style
            sort_by: Sort key ('title', 'author', 'year')

        Returns:
            Formatted reference list as string
        """
        # Sort references
        if sort_by == "author" and references[0].authors:
            references = sorted(references, key=lambda r: r.authors[0] if r.authors else "")
        elif sort_by == "year":
            references = sorted(references, key=lambda r: r.year or 0)
        else:  # title
            references = sorted(references, key=lambda r: r.title)

        # Format references
        formatted = self.format_references(references, style)

        # Build list
        lines = [f"{style.upper()} Style References:\n"]
        for i, ref in enumerate(formatted, 1):
            lines.append(f"{i}. {ref}")

        return "\n".join(lines)

    def extract_author_info(self, text: str) -> Dict:
        """Extract author information from text

        Args:
            text: Input text

        Returns:
            Dictionary with author information
        """
        if not text:
            return {}

        # Look for common author patterns
        author_pattern = re.compile(r'(?:by|author|written by)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)', re.IGNORECASE)
        matches = author_pattern.findall(text)

        authors = list(set(matches))  # Remove duplicates

        return {
            "authors": authors,
            "num_authors": len(authors),
        }

    def extract_publication_info(self, text: str) -> Dict:
        """Extract publication information from text

        Args:
            text: Input text

        Returns:
            Dictionary with publication information
        """
        if not text:
            return {}

        info = {}

        # Extract year
        year_pattern = re.compile(r'\b(19|20)\d{2}\b')
        years = year_pattern.findall(text)
        if years:
            info["years"] = [int(y) for y in years]

        # Extract publication names (capitalized phrases)
        pub_pattern = re.compile(r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s+(?:Journal|Review|Magazine|Press|University)')
        pubs = pub_pattern.findall(text)
        if pubs:
            info["publications"] = list(set(pubs))

        return info
