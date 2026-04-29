"""
UI Package
Terminal User Interface (TUI) components and application

Modules:
- tui_styles: Color schemes, themes, and styling
- tui_components: Reusable UI components and widgets
- tui_screens: Main screens and navigation logic
- tui_app: Main application controller and event loop
"""

from mini_wiki.ui.tui_app import TUIApplication, TUIApplicationBuilder, create_app
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
from mini_wiki.ui.tui_screens import (
    DocumentViewerScreen,
    HelpScreen,
    KnowledgeBaseScreen,
    MainMenuScreen,
    ResultsScreen,
    Screen,
    ScreenContext,
    ScreenFactory,
    ScreenType,
    SearchScreen,
    SettingsScreen,
)
from mini_wiki.ui.tui_styles import (
    Color,
    ColorScheme,
    TextStyle,
    Theme,
    ThemeManager,
    get_dark_theme,
    get_light_theme,
    get_monokai_theme,
)

__all__ = [
    # Application
    "TUIApplication",
    "TUIApplicationBuilder",
    "create_app",
    # Styles
    "Color",
    "ColorScheme",
    "TextStyle",
    "Theme",
    "ThemeManager",
    "get_dark_theme",
    "get_light_theme",
    "get_monokai_theme",
    # Components
    "TextInput",
    "TextInputConfig",
    "SelectionList",
    "SelectionListConfig",
    "SearchComponent",
    "SearchConfig",
    "ProgressBar",
    "ProgressBarConfig",
    "Table",
    "TableConfig",
    "Dialog",
    "DialogConfig",
    "StatusBar",
    "StatusBarConfig",
    # Screens
    "Screen",
    "ScreenContext",
    "ScreenType",
    "ScreenFactory",
    "MainMenuScreen",
    "SearchScreen",
    "ResultsScreen",
    "DocumentViewerScreen",
    "KnowledgeBaseScreen",
    "SettingsScreen",
    "HelpScreen",
]
