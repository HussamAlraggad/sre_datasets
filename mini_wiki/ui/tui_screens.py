"""
TUI Screens Module
Main TUI screens and navigation logic

Features:
- Main menu screen
- Search screen
- Results screen
- Document viewer screen
- Knowledge base screen
- Settings screen
- Screen navigation
"""

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Any, Callable, Dict, List, Optional

from mini_wiki.ui.tui_components import (
    Dialog,
    DialogConfig,
    ProgressBar,
    ProgressBarConfig,
    SearchComponent,
    SearchConfig,
    SelectionList,
    SelectionListConfig,
    StatusBar,
    StatusBarConfig,
    Table,
    TableConfig,
    TextInput,
    TextInputConfig,
)

logger = logging.getLogger(__name__)


class ScreenType(Enum):
    """Screen types"""

    MAIN_MENU = "main_menu"
    SEARCH = "search"
    RESULTS = "results"
    DOCUMENT_VIEWER = "document_viewer"
    KNOWLEDGE_BASE = "knowledge_base"
    SETTINGS = "settings"
    HELP = "help"
    EXIT = "exit"


@dataclass
class ScreenContext:
    """Context passed between screens

    Attributes:
        current_screen: Current screen type
        previous_screen: Previous screen type
        data: Arbitrary data passed between screens
        theme: Current theme
    """

    current_screen: ScreenType
    previous_screen: Optional[ScreenType] = None
    data: Optional[Dict[str, Any]] = None
    theme: Optional[str] = None


class Screen(ABC):
    """Base screen class"""

    def __init__(self, context: ScreenContext):
        """Initialize screen

        Args:
            context: Screen context
        """
        self.context = context
        self.status_bar = StatusBar(StatusBarConfig())

    @abstractmethod
    def render(self) -> str:
        """Render screen

        Returns:
            Rendered screen content
        """
        pass

    @abstractmethod
    def handle_input(self, key: str) -> Optional[ScreenType]:
        """Handle user input

        Args:
            key: Input key

        Returns:
            Next screen type or None
        """
        pass

    def get_status_bar(self) -> StatusBar:
        """Get status bar

        Returns:
            Status bar
        """
        return self.status_bar

    def update_status(self, left: str = "", center: str = "", right: str = "") -> None:
        """Update status bar

        Args:
            left: Left text
            center: Center text
            right: Right text
        """
        if left:
            self.status_bar.update_left(left)
        if center:
            self.status_bar.update_center(center)
        if right:
            self.status_bar.update_right(right)


class MainMenuScreen(Screen):
    """Main menu screen"""

    def __init__(self, context: ScreenContext):
        """Initialize main menu screen

        Args:
            context: Screen context
        """
        super().__init__(context)
        self.menu_items = [
            "Search Documents",
            "View Knowledge Base",
            "Recent Searches",
            "Settings",
            "Help",
            "Exit",
        ]
        self.selection = SelectionList(
            SelectionListConfig(
                items=self.menu_items,
                title="mini_wiki - Main Menu",
                multi_select=False,
                searchable=False,
            )
        )

    def render(self) -> str:
        """Render main menu screen

        Returns:
            Rendered content
        """
        output = []
        output.append("=" * 50)
        output.append("mini_wiki - Universal Research Assistant")
        output.append("=" * 50)
        output.append("")
        output.append("Main Menu:")
        output.append("")

        for i, item in enumerate(self.menu_items):
            prefix = "→ " if i == self.selection.current_index else "  "
            output.append(f"{prefix}{i + 1}. {item}")

        output.append("")
        output.append("Use ↑/↓ to navigate, Enter to select, Q to quit")

        return "\n".join(output)

    def handle_input(self, key: str) -> Optional[ScreenType]:
        """Handle user input

        Args:
            key: Input key

        Returns:
            Next screen type
        """
        if key == "up":
            self.selection.move_up()
        elif key == "down":
            self.selection.move_down()
        elif key == "enter":
            selected_index = self.selection.current_index
            if selected_index == 0:
                return ScreenType.SEARCH
            elif selected_index == 1:
                return ScreenType.KNOWLEDGE_BASE
            elif selected_index == 2:
                return ScreenType.RESULTS
            elif selected_index == 3:
                return ScreenType.SETTINGS
            elif selected_index == 4:
                return ScreenType.HELP
            elif selected_index == 5:
                return ScreenType.EXIT
        elif key == "q":
            return ScreenType.EXIT

        return None


class SearchScreen(Screen):
    """Search screen"""

    def __init__(self, context: ScreenContext):
        """Initialize search screen

        Args:
            context: Screen context
        """
        super().__init__(context)
        self.search = SearchComponent(SearchConfig(placeholder="Enter search query..."))
        self.input = TextInput(
            TextInputConfig(
                prompt="Search Query",
                placeholder="Enter search query...",
            )
        )
        self.search_active = False

    def render(self) -> str:
        """Render search screen

        Returns:
            Rendered content
        """
        output = []
        output.append("=" * 50)
        output.append("Search Documents")
        output.append("=" * 50)
        output.append("")
        output.append("Enter your search query:")
        output.append("")
        output.append(f"> {self.input.get_value()}")
        output.append("")

        if self.search_active and self.search.get_results():
            output.append(f"Found {len(self.search.get_results())} results:")
            output.append("")
            for i, result in enumerate(self.search.get_results()[:10], 1):
                output.append(f"{i}. {result}")

        output.append("")
        output.append("Press Enter to search, Backspace to delete, Q to go back")

        return "\n".join(output)

    def handle_input(self, key: str) -> Optional[ScreenType]:
        """Handle user input

        Args:
            key: Input key

        Returns:
            Next screen type
        """
        if key == "q":
            return ScreenType.MAIN_MENU
        elif key == "enter":
            query = self.input.get_value()
            if query:
                self.search_active = True
                # Simulate search results
                self.search.set_results([f"Result {i} for '{query}'" for i in range(1, 6)])
                self.update_status(right=f"Found {len(self.search.get_results())} results")
        elif key == "backspace":
            current = self.input.get_value()
            if current:
                self.input.set_value(current[:-1])
        elif len(key) == 1 and key.isprintable():
            self.input.set_value(self.input.get_value() + key)

        return None


class ResultsScreen(Screen):
    """Results screen"""

    def __init__(self, context: ScreenContext):
        """Initialize results screen

        Args:
            context: Screen context
        """
        super().__init__(context)
        self.results = [
            ["Document 1", "0.95", "High"],
            ["Document 2", "0.87", "High"],
            ["Document 3", "0.76", "Medium"],
            ["Document 4", "0.65", "Medium"],
            ["Document 5", "0.54", "Low"],
        ]
        self.table = Table(
            TableConfig(
                columns=["Document", "Score", "Relevance"],
                rows=self.results,
                title="Search Results",
            )
        )

    def render(self) -> str:
        """Render results screen

        Returns:
            Rendered content
        """
        output = []
        output.append("=" * 50)
        output.append("Search Results")
        output.append("=" * 50)
        output.append("")

        # Render table header
        header = " | ".join(self.table.config.columns)
        output.append(header)
        output.append("-" * len(header))

        # Render table rows
        for i, row in enumerate(self.table.get_rows()):
            prefix = "→ " if i == self.table.current_row else "  "
            row_str = " | ".join(row)
            output.append(f"{prefix}{row_str}")

        output.append("")
        output.append("Use ↑/↓ to navigate, Enter to view, Q to go back")

        return "\n".join(output)

    def handle_input(self, key: str) -> Optional[ScreenType]:
        """Handle user input

        Args:
            key: Input key

        Returns:
            Next screen type
        """
        if key == "up":
            self.table.move_up()
        elif key == "down":
            self.table.move_down()
        elif key == "enter":
            return ScreenType.DOCUMENT_VIEWER
        elif key == "q":
            return ScreenType.MAIN_MENU

        return None


class DocumentViewerScreen(Screen):
    """Document viewer screen"""

    def __init__(self, context: ScreenContext):
        """Initialize document viewer screen

        Args:
            context: Screen context
        """
        super().__init__(context)
        self.document_content = """
Document Title: Sample Research Paper

Abstract:
This is a sample document showing the document viewer functionality.
It displays the full content of a selected document with proper formatting.

Content:
Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed do eiusmod tempor
incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis
nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat.

References:
1. Author, A. (2023). Title of paper. Journal Name, 10(2), 123-145.
2. Author, B. (2022). Another paper. Conference Proceedings, 45-67.
"""
        self.scroll_position = 0

    def render(self) -> str:
        """Render document viewer screen

        Returns:
            Rendered content
        """
        output = []
        output.append("=" * 50)
        output.append("Document Viewer")
        output.append("=" * 50)
        output.append("")

        lines = self.document_content.split("\n")
        visible_lines = lines[self.scroll_position : self.scroll_position + 20]
        output.extend(visible_lines)

        output.append("")
        output.append("Use ↑/↓ to scroll, Q to go back")

        return "\n".join(output)

    def handle_input(self, key: str) -> Optional[ScreenType]:
        """Handle user input

        Args:
            key: Input key

        Returns:
            Next screen type
        """
        if key == "up":
            if self.scroll_position > 0:
                self.scroll_position -= 1
        elif key == "down":
            max_scroll = max(0, len(self.document_content.split("\n")) - 20)
            if self.scroll_position < max_scroll:
                self.scroll_position += 1
        elif key == "q":
            return ScreenType.RESULTS

        return None


class KnowledgeBaseScreen(Screen):
    """Knowledge base screen"""

    def __init__(self, context: ScreenContext):
        """Initialize knowledge base screen

        Args:
            context: Screen context
        """
        super().__init__(context)
        self.kb_items = [
            "Machine Learning Basics",
            "Natural Language Processing",
            "Computer Vision",
            "Deep Learning",
            "Reinforcement Learning",
        ]
        self.selection = SelectionList(
            SelectionListConfig(
                items=self.kb_items,
                title="Knowledge Base",
                multi_select=False,
                searchable=True,
            )
        )

    def render(self) -> str:
        """Render knowledge base screen

        Returns:
            Rendered content
        """
        output = []
        output.append("=" * 50)
        output.append("Knowledge Base")
        output.append("=" * 50)
        output.append("")
        output.append("Available Topics:")
        output.append("")

        for i, item in enumerate(self.kb_items):
            prefix = "→ " if i == self.selection.current_index else "  "
            output.append(f"{prefix}{i + 1}. {item}")

        output.append("")
        output.append("Use ↑/↓ to navigate, Enter to view, Q to go back")

        return "\n".join(output)

    def handle_input(self, key: str) -> Optional[ScreenType]:
        """Handle user input

        Args:
            key: Input key

        Returns:
            Next screen type
        """
        if key == "up":
            self.selection.move_up()
        elif key == "down":
            self.selection.move_down()
        elif key == "enter":
            return ScreenType.DOCUMENT_VIEWER
        elif key == "q":
            return ScreenType.MAIN_MENU

        return None


class SettingsScreen(Screen):
    """Settings screen"""

    def __init__(self, context: ScreenContext):
        """Initialize settings screen

        Args:
            context: Screen context
        """
        super().__init__(context)
        self.settings_items = [
            "Theme: Dark",
            "Language: English",
            "Results per page: 10",
            "Auto-save: Enabled",
            "Back to Menu",
        ]
        self.selection = SelectionList(
            SelectionListConfig(
                items=self.settings_items,
                title="Settings",
                multi_select=False,
                searchable=False,
            )
        )

    def render(self) -> str:
        """Render settings screen

        Returns:
            Rendered content
        """
        output = []
        output.append("=" * 50)
        output.append("Settings")
        output.append("=" * 50)
        output.append("")

        for i, item in enumerate(self.settings_items):
            prefix = "→ " if i == self.selection.current_index else "  "
            output.append(f"{prefix}{item}")

        output.append("")
        output.append("Use ↑/↓ to navigate, Enter to change, Q to go back")

        return "\n".join(output)

    def handle_input(self, key: str) -> Optional[ScreenType]:
        """Handle user input

        Args:
            key: Input key

        Returns:
            Next screen type
        """
        if key == "up":
            self.selection.move_up()
        elif key == "down":
            self.selection.move_down()
        elif key == "enter":
            if self.selection.current_index == len(self.settings_items) - 1:
                return ScreenType.MAIN_MENU
        elif key == "q":
            return ScreenType.MAIN_MENU

        return None


class HelpScreen(Screen):
    """Help screen"""

    def __init__(self, context: ScreenContext):
        """Initialize help screen

        Args:
            context: Screen context
        """
        super().__init__(context)
        self.help_text = """
mini_wiki - Universal Research Assistant

KEYBOARD SHORTCUTS:
  ↑/↓        Navigate menu items
  Enter      Select menu item
  Q          Go back to previous screen
  Ctrl+C     Exit application

MAIN MENU:
  Search Documents    - Search across loaded documents
  View Knowledge Base - Browse knowledge base topics
  Recent Searches     - View recent search history
  Settings           - Configure application settings
  Help               - Display this help screen
  Exit               - Exit the application

SEARCH:
  Type your query and press Enter to search
  Results are ranked by relevance and importance
  Click on a result to view the full document

KNOWLEDGE BASE:
  Browse topics organized by category
  Each topic contains curated information
  View references and citations

SETTINGS:
  Theme              - Change color theme
  Language           - Select interface language
  Results per page   - Adjust pagination
  Auto-save          - Enable/disable auto-saving
"""

    def render(self) -> str:
        """Render help screen

        Returns:
            Rendered content
        """
        output = []
        output.append("=" * 50)
        output.append("Help")
        output.append("=" * 50)
        output.append(self.help_text)
        output.append("")
        output.append("Press Q to go back")

        return "\n".join(output)

    def handle_input(self, key: str) -> Optional[ScreenType]:
        """Handle user input

        Args:
            key: Input key

        Returns:
            Next screen type
        """
        if key == "q":
            return ScreenType.MAIN_MENU

        return None


class ScreenFactory:
    """Factory for creating screens"""

    _screens: Dict[ScreenType, type] = {
        ScreenType.MAIN_MENU: MainMenuScreen,
        ScreenType.SEARCH: SearchScreen,
        ScreenType.RESULTS: ResultsScreen,
        ScreenType.DOCUMENT_VIEWER: DocumentViewerScreen,
        ScreenType.KNOWLEDGE_BASE: KnowledgeBaseScreen,
        ScreenType.SETTINGS: SettingsScreen,
        ScreenType.HELP: HelpScreen,
    }

    @classmethod
    def create_screen(cls, screen_type: ScreenType, context: ScreenContext) -> Screen:
        """Create screen by type

        Args:
            screen_type: Screen type
            context: Screen context

        Returns:
            Screen instance
        """
        screen_class = cls._screens.get(screen_type)
        if screen_class:
            return screen_class(context)
        raise ValueError(f"Unknown screen type: {screen_type}")

    @classmethod
    def register_screen(cls, screen_type: ScreenType, screen_class: type) -> None:
        """Register custom screen

        Args:
            screen_type: Screen type
            screen_class: Screen class
        """
        cls._screens[screen_type] = screen_class
        logger.info(f"Registered screen: {screen_type.value}")
