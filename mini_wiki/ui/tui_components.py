"""
TUI Components Module
Reusable TUI components and widgets for the interface

Features:
- Text input component
- Selection list component
- Search component
- Progress bar component
- Table component
- Dialog component
- Status bar component
"""

import logging
from dataclasses import dataclass
from typing import Callable, List, Optional, Dict, Any

logger = logging.getLogger(__name__)


@dataclass
class TextInputConfig:
    """Configuration for text input component

    Attributes:
        prompt: Input prompt text
        default: Default value
        validator: Optional validation function
        placeholder: Placeholder text
    """

    prompt: str
    default: str = ""
    validator: Optional[Callable[[str], bool]] = None
    placeholder: str = ""


class TextInput:
    """Text input component"""

    def __init__(self, config: TextInputConfig):
        """Initialize text input

        Args:
            config: TextInputConfig
        """
        self.config = config
        self.value = config.default

    def validate(self) -> bool:
        """Validate input

        Returns:
            True if valid, False otherwise
        """
        if self.config.validator:
            return self.config.validator(self.value)
        return True

    def get_value(self) -> str:
        """Get input value

        Returns:
            Input value
        """
        return self.value

    def set_value(self, value: str) -> None:
        """Set input value

        Args:
            value: New value
        """
        self.value = value

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary

        Returns:
            Dictionary representation
        """
        return {
            "prompt": self.config.prompt,
            "value": self.value,
            "valid": self.validate(),
        }


@dataclass
class SelectionListConfig:
    """Configuration for selection list component

    Attributes:
        items: List of items to select from
        title: List title
        multi_select: Allow multiple selections
        searchable: Enable search functionality
    """

    items: List[str]
    title: str = "Select an item"
    multi_select: bool = False
    searchable: bool = True


class SelectionList:
    """Selection list component"""

    def __init__(self, config: SelectionListConfig):
        """Initialize selection list

        Args:
            config: SelectionListConfig
        """
        self.config = config
        self.selected: List[int] = []
        self.current_index = 0
        self.search_query = ""

    def select(self, index: int) -> None:
        """Select item by index

        Args:
            index: Item index
        """
        if 0 <= index < len(self.config.items):
            if self.config.multi_select:
                if index in self.selected:
                    self.selected.remove(index)
                else:
                    self.selected.append(index)
            else:
                self.selected = [index]
            self.current_index = index

    def get_selected(self) -> List[str]:
        """Get selected items

        Returns:
            List of selected items
        """
        return [self.config.items[i] for i in self.selected]

    def get_selected_indices(self) -> List[int]:
        """Get selected indices

        Returns:
            List of selected indices
        """
        return self.selected

    def move_up(self) -> None:
        """Move selection up"""
        if self.current_index > 0:
            self.current_index -= 1

    def move_down(self) -> None:
        """Move selection down"""
        if self.current_index < len(self.config.items) - 1:
            self.current_index += 1

    def filter_items(self, query: str) -> List[str]:
        """Filter items by search query

        Args:
            query: Search query

        Returns:
            Filtered items
        """
        if not query:
            return self.config.items
        return [item for item in self.config.items if query.lower() in item.lower()]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary

        Returns:
            Dictionary representation
        """
        return {
            "title": self.config.title,
            "items": self.config.items,
            "selected": self.get_selected(),
            "current_index": self.current_index,
        }


@dataclass
class SearchConfig:
    """Configuration for search component

    Attributes:
        placeholder: Search placeholder
        min_length: Minimum search length
        debounce_ms: Debounce delay in milliseconds
    """

    placeholder: str = "Search..."
    min_length: int = 1
    debounce_ms: int = 300


class SearchComponent:
    """Search component"""

    def __init__(self, config: SearchConfig):
        """Initialize search component

        Args:
            config: SearchConfig
        """
        self.config = config
        self.query = ""
        self.results: List[str] = []

    def update_query(self, query: str) -> None:
        """Update search query

        Args:
            query: Search query
        """
        self.query = query

    def get_query(self) -> str:
        """Get search query

        Returns:
            Current query
        """
        return self.query

    def set_results(self, results: List[str]) -> None:
        """Set search results

        Args:
            results: Search results
        """
        self.results = results

    def get_results(self) -> List[str]:
        """Get search results

        Returns:
            Current results
        """
        return self.results

    def clear(self) -> None:
        """Clear search"""
        self.query = ""
        self.results = []

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary

        Returns:
            Dictionary representation
        """
        return {
            "query": self.query,
            "results_count": len(self.results),
            "results": self.results,
        }


@dataclass
class ProgressBarConfig:
    """Configuration for progress bar component

    Attributes:
        total: Total progress value
        current: Current progress value
        label: Progress label
    """

    total: int
    current: int = 0
    label: str = "Progress"


class ProgressBar:
    """Progress bar component"""

    def __init__(self, config: ProgressBarConfig):
        """Initialize progress bar

        Args:
            config: ProgressBarConfig
        """
        self.config = config
        self.current = config.current

    def update(self, value: int) -> None:
        """Update progress

        Args:
            value: New progress value
        """
        self.current = min(value, self.config.total)

    def increment(self, amount: int = 1) -> None:
        """Increment progress

        Args:
            amount: Amount to increment
        """
        self.update(self.current + amount)

    def get_percentage(self) -> float:
        """Get progress percentage

        Returns:
            Progress percentage (0-100)
        """
        if self.config.total == 0:
            return 0.0
        return (self.current / self.config.total) * 100

    def is_complete(self) -> bool:
        """Check if progress is complete

        Returns:
            True if complete
        """
        return self.current >= self.config.total

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary

        Returns:
            Dictionary representation
        """
        return {
            "label": self.config.label,
            "current": self.current,
            "total": self.config.total,
            "percentage": self.get_percentage(),
            "complete": self.is_complete(),
        }


@dataclass
class TableConfig:
    """Configuration for table component

    Attributes:
        columns: Column names
        rows: Table rows
        title: Table title
    """

    columns: List[str]
    rows: List[List[str]]
    title: str = "Table"


class Table:
    """Table component"""

    def __init__(self, config: TableConfig):
        """Initialize table

        Args:
            config: TableConfig
        """
        self.config = config
        self.rows = config.rows
        self.current_row = 0

    def add_row(self, row: List[str]) -> None:
        """Add row to table

        Args:
            row: Row data
        """
        if len(row) == len(self.config.columns):
            self.rows.append(row)

    def remove_row(self, index: int) -> None:
        """Remove row from table

        Args:
            index: Row index
        """
        if 0 <= index < len(self.rows):
            self.rows.pop(index)

    def get_row(self, index: int) -> Optional[List[str]]:
        """Get row by index

        Args:
            index: Row index

        Returns:
            Row data or None
        """
        if 0 <= index < len(self.rows):
            return self.rows[index]
        return None

    def get_rows(self) -> List[List[str]]:
        """Get all rows

        Returns:
            All rows
        """
        return self.rows

    def move_up(self) -> None:
        """Move selection up"""
        if self.current_row > 0:
            self.current_row -= 1

    def move_down(self) -> None:
        """Move selection down"""
        if self.current_row < len(self.rows) - 1:
            self.current_row += 1

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary

        Returns:
            Dictionary representation
        """
        return {
            "title": self.config.title,
            "columns": self.config.columns,
            "rows": self.rows,
            "current_row": self.current_row,
            "row_count": len(self.rows),
        }


@dataclass
class DialogConfig:
    """Configuration for dialog component

    Attributes:
        title: Dialog title
        message: Dialog message
        buttons: Dialog buttons
    """

    title: str
    message: str
    buttons: List[str]


class Dialog:
    """Dialog component"""

    def __init__(self, config: DialogConfig):
        """Initialize dialog

        Args:
            config: DialogConfig
        """
        self.config = config
        self.selected_button = 0

    def select_button(self, index: int) -> None:
        """Select button by index

        Args:
            index: Button index
        """
        if 0 <= index < len(self.config.buttons):
            self.selected_button = index

    def get_selected_button(self) -> str:
        """Get selected button

        Returns:
            Selected button text
        """
        return self.config.buttons[self.selected_button]

    def move_left(self) -> None:
        """Move selection left"""
        if self.selected_button > 0:
            self.selected_button -= 1

    def move_right(self) -> None:
        """Move selection right"""
        if self.selected_button < len(self.config.buttons) - 1:
            self.selected_button += 1

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary

        Returns:
            Dictionary representation
        """
        return {
            "title": self.config.title,
            "message": self.config.message,
            "buttons": self.config.buttons,
            "selected_button": self.selected_button,
        }


@dataclass
class StatusBarConfig:
    """Configuration for status bar component

    Attributes:
        left_text: Left side text
        center_text: Center text
        right_text: Right side text
    """

    left_text: str = ""
    center_text: str = ""
    right_text: str = ""


class StatusBar:
    """Status bar component"""

    def __init__(self, config: StatusBarConfig):
        """Initialize status bar

        Args:
            config: StatusBarConfig
        """
        self.config = config

    def update_left(self, text: str) -> None:
        """Update left text

        Args:
            text: New text
        """
        self.config.left_text = text

    def update_center(self, text: str) -> None:
        """Update center text

        Args:
            text: New text
        """
        self.config.center_text = text

    def update_right(self, text: str) -> None:
        """Update right text

        Args:
            text: New text
        """
        self.config.right_text = text

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary

        Returns:
            Dictionary representation
        """
        return {
            "left": self.config.left_text,
            "center": self.config.center_text,
            "right": self.config.right_text,
        }
