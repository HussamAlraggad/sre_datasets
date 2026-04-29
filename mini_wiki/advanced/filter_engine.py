"""
Filter Engine Module
Advanced filtering and sorting for search results

Features:
- Filter by relevance score
- Filter by importance score
- Filter by date range
- Filter by source/document type
- Filter by tags
- Sort by relevance, importance, date, title
- Combine multiple filters
- Filter statistics
"""

import logging
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


class SortOrder(Enum):
    """Sort order"""

    ASCENDING = "ascending"
    DESCENDING = "descending"


class SortField(Enum):
    """Sort field"""

    RELEVANCE = "relevance"
    IMPORTANCE = "importance"
    DATE = "date"
    TITLE = "title"
    SOURCE = "source"


@dataclass
class FilterCriteria:
    """Filter criteria

    Attributes:
        min_relevance: Minimum relevance score (0-1)
        max_relevance: Maximum relevance score (0-1)
        min_importance: Minimum importance score (0-1)
        max_importance: Maximum importance score (0-1)
        min_date: Minimum date
        max_date: Maximum date
        sources: List of allowed sources
        tags: List of required tags
        document_types: List of allowed document types
    """

    min_relevance: float = 0.0
    max_relevance: float = 1.0
    min_importance: float = 0.0
    max_importance: float = 1.0
    min_date: Optional[datetime] = None
    max_date: Optional[datetime] = None
    sources: List[str] = None
    tags: List[str] = None
    document_types: List[str] = None

    def __post_init__(self):
        """Post-init validation"""
        if self.sources is None:
            self.sources = []
        if self.tags is None:
            self.tags = []
        if self.document_types is None:
            self.document_types = []


@dataclass
class SortCriteria:
    """Sort criteria

    Attributes:
        field: Field to sort by
        order: Sort order (ascending/descending)
    """

    field: SortField = SortField.RELEVANCE
    order: SortOrder = SortOrder.DESCENDING


@dataclass
class FilterResult:
    """Filter result

    Attributes:
        items: Filtered items
        total_count: Total items before filtering
        filtered_count: Items after filtering
        filter_time_ms: Time taken to filter
    """

    items: List[Dict[str, Any]]
    total_count: int
    filtered_count: int
    filter_time_ms: float


class FilterEngine:
    """Advanced filter engine"""

    def __init__(self):
        """Initialize filter engine"""
        self.filters: Dict[str, Callable] = {}
        self._register_default_filters()

    def _register_default_filters(self) -> None:
        """Register default filters"""
        self.register_filter("relevance", self._filter_relevance)
        self.register_filter("importance", self._filter_importance)
        self.register_filter("date", self._filter_date)
        self.register_filter("source", self._filter_source)
        self.register_filter("tags", self._filter_tags)
        self.register_filter("document_type", self._filter_document_type)

    def register_filter(self, name: str, filter_func: Callable) -> None:
        """Register custom filter

        Args:
            name: Filter name
            filter_func: Filter function
        """
        self.filters[name] = filter_func
        logger.info(f"Registered filter: {name}")

    def filter(
        self,
        items: List[Dict[str, Any]],
        criteria: FilterCriteria,
    ) -> FilterResult:
        """Filter items

        Args:
            items: Items to filter
            criteria: Filter criteria

        Returns:
            FilterResult
        """
        import time

        start_time = time.time()
        total_count = len(items)

        # Apply filters
        filtered_items = items
        for filter_name, filter_func in self.filters.items():
            filtered_items = filter_func(filtered_items, criteria)

        filter_time_ms = (time.time() - start_time) * 1000

        return FilterResult(
            items=filtered_items,
            total_count=total_count,
            filtered_count=len(filtered_items),
            filter_time_ms=filter_time_ms,
        )

    def _filter_relevance(
        self, items: List[Dict[str, Any]], criteria: FilterCriteria
    ) -> List[Dict[str, Any]]:
        """Filter by relevance score

        Args:
            items: Items to filter
            criteria: Filter criteria

        Returns:
            Filtered items
        """
        return [
            item
            for item in items
            if criteria.min_relevance
            <= item.get("relevance", 0.0)
            <= criteria.max_relevance
        ]

    def _filter_importance(
        self, items: List[Dict[str, Any]], criteria: FilterCriteria
    ) -> List[Dict[str, Any]]:
        """Filter by importance score

        Args:
            items: Items to filter
            criteria: Filter criteria

        Returns:
            Filtered items
        """
        return [
            item
            for item in items
            if criteria.min_importance
            <= item.get("importance", 0.0)
            <= criteria.max_importance
        ]

    def _filter_date(
        self, items: List[Dict[str, Any]], criteria: FilterCriteria
    ) -> List[Dict[str, Any]]:
        """Filter by date range

        Args:
            items: Items to filter
            criteria: Filter criteria

        Returns:
            Filtered items
        """
        filtered = []
        for item in items:
            date_str = item.get("date")
            if not date_str:
                continue

            try:
                item_date = datetime.fromisoformat(date_str)
                if criteria.min_date and item_date < criteria.min_date:
                    continue
                if criteria.max_date and item_date > criteria.max_date:
                    continue
                filtered.append(item)
            except (ValueError, TypeError):
                continue

        return filtered

    def _filter_source(
        self, items: List[Dict[str, Any]], criteria: FilterCriteria
    ) -> List[Dict[str, Any]]:
        """Filter by source

        Args:
            items: Items to filter
            criteria: Filter criteria

        Returns:
            Filtered items
        """
        if not criteria.sources:
            return items

        return [item for item in items if item.get("source") in criteria.sources]

    def _filter_tags(
        self, items: List[Dict[str, Any]], criteria: FilterCriteria
    ) -> List[Dict[str, Any]]:
        """Filter by tags

        Args:
            items: Items to filter
            criteria: Filter criteria

        Returns:
            Filtered items
        """
        if not criteria.tags:
            return items

        filtered = []
        for item in items:
            item_tags = item.get("tags", [])
            if all(tag in item_tags for tag in criteria.tags):
                filtered.append(item)

        return filtered

    def _filter_document_type(
        self, items: List[Dict[str, Any]], criteria: FilterCriteria
    ) -> List[Dict[str, Any]]:
        """Filter by document type

        Args:
            items: Items to filter
            criteria: Filter criteria

        Returns:
            Filtered items
        """
        if not criteria.document_types:
            return items

        return [
            item
            for item in items
            if item.get("document_type") in criteria.document_types
        ]


class SortEngine:
    """Advanced sort engine"""

    def __init__(self):
        """Initialize sort engine"""
        self.sorters: Dict[SortField, Callable] = {}
        self._register_default_sorters()

    def _register_default_sorters(self) -> None:
        """Register default sorters"""
        self.sorters[SortField.RELEVANCE] = self._sort_relevance
        self.sorters[SortField.IMPORTANCE] = self._sort_importance
        self.sorters[SortField.DATE] = self._sort_date
        self.sorters[SortField.TITLE] = self._sort_title
        self.sorters[SortField.SOURCE] = self._sort_source

    def register_sorter(self, field: SortField, sorter_func: Callable) -> None:
        """Register custom sorter

        Args:
            field: Sort field
            sorter_func: Sorter function
        """
        self.sorters[field] = sorter_func
        logger.info(f"Registered sorter: {field.value}")

    def sort(
        self,
        items: List[Dict[str, Any]],
        criteria: SortCriteria,
    ) -> List[Dict[str, Any]]:
        """Sort items

        Args:
            items: Items to sort
            criteria: Sort criteria

        Returns:
            Sorted items
        """
        sorter = self.sorters.get(criteria.field)
        if not sorter:
            logger.warning(f"Sorter not found for field: {criteria.field.value}")
            return items

        reverse = criteria.order == SortOrder.DESCENDING
        return sorter(items, reverse)

    def _sort_relevance(
        self, items: List[Dict[str, Any]], reverse: bool = True
    ) -> List[Dict[str, Any]]:
        """Sort by relevance

        Args:
            items: Items to sort
            reverse: Reverse order

        Returns:
            Sorted items
        """
        return sorted(items, key=lambda x: x.get("relevance", 0.0), reverse=reverse)

    def _sort_importance(
        self, items: List[Dict[str, Any]], reverse: bool = True
    ) -> List[Dict[str, Any]]:
        """Sort by importance

        Args:
            items: Items to sort
            reverse: Reverse order

        Returns:
            Sorted items
        """
        return sorted(items, key=lambda x: x.get("importance", 0.0), reverse=reverse)

    def _sort_date(
        self, items: List[Dict[str, Any]], reverse: bool = True
    ) -> List[Dict[str, Any]]:
        """Sort by date

        Args:
            items: Items to sort
            reverse: Reverse order

        Returns:
            Sorted items
        """

        def get_date(item):
            date_str = item.get("date")
            if not date_str:
                return datetime.min
            try:
                return datetime.fromisoformat(date_str)
            except (ValueError, TypeError):
                return datetime.min

        return sorted(items, key=get_date, reverse=reverse)

    def _sort_title(
        self, items: List[Dict[str, Any]], reverse: bool = False
    ) -> List[Dict[str, Any]]:
        """Sort by title

        Args:
            items: Items to sort
            reverse: Reverse order

        Returns:
            Sorted items
        """
        return sorted(items, key=lambda x: x.get("title", "").lower(), reverse=reverse)

    def _sort_source(
        self, items: List[Dict[str, Any]], reverse: bool = False
    ) -> List[Dict[str, Any]]:
        """Sort by source

        Args:
            items: Items to sort
            reverse: Reverse order

        Returns:
            Sorted items
        """
        return sorted(items, key=lambda x: x.get("source", "").lower(), reverse=reverse)


class FilterSortEngine:
    """Combined filter and sort engine"""

    def __init__(self):
        """Initialize filter and sort engine"""
        self.filter_engine = FilterEngine()
        self.sort_engine = SortEngine()

    def process(
        self,
        items: List[Dict[str, Any]],
        filter_criteria: Optional[FilterCriteria] = None,
        sort_criteria: Optional[SortCriteria] = None,
    ) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        """Process items with filtering and sorting

        Args:
            items: Items to process
            filter_criteria: Filter criteria (optional)
            sort_criteria: Sort criteria (optional)

        Returns:
            Tuple of (processed items, statistics)
        """
        stats = {
            "total_items": len(items),
            "filtered_items": len(items),
            "filter_time_ms": 0.0,
            "sort_time_ms": 0.0,
        }

        # Apply filters
        if filter_criteria:
            filter_result = self.filter_engine.filter(items, filter_criteria)
            items = filter_result.items
            stats["filtered_items"] = filter_result.filtered_count
            stats["filter_time_ms"] = filter_result.filter_time_ms

        # Apply sorting
        if sort_criteria:
            import time

            start_time = time.time()
            items = self.sort_engine.sort(items, sort_criteria)
            stats["sort_time_ms"] = (time.time() - start_time) * 1000

        return items, stats

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary

        Returns:
            Dictionary representation
        """
        return {
            "filter_engine": "FilterEngine",
            "sort_engine": "SortEngine",
            "filters": list(self.filter_engine.filters.keys()),
            "sorters": [f.value for f in self.sort_engine.sorters.keys()],
        }
