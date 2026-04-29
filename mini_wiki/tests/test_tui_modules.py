"""
Unit tests for TUI modules

Test coverage:
- TUI styles (themes, colors, text styles)
- TUI components (input, selection, search, progress, table, dialog, status)
- TUI screens (main menu, search, results, document viewer, knowledge base, settings, help)
- TUI application (CursesTUI initialization, navigation, rendering)
"""

import pytest
from unittest.mock import MagicMock, patch
from mini_wiki.ui.tui_app import CursesTUI, run_tui
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


# ============================================================================
# TUI Styles Tests
# ============================================================================


class TestColor:
    """Test Color enum"""

    def test_color_values(self):
        """Test color values"""
        assert Color.BLACK.value == "black"
        assert Color.WHITE.value == "white"
        assert Color.RED.value == "red"
        assert Color.GREEN.value == "green"

    def test_bright_colors(self):
        """Test bright colors"""
        assert Color.BRIGHT_RED.value == "bright_red"
        assert Color.BRIGHT_GREEN.value == "bright_green"


class TestColorScheme:
    """Test ColorScheme"""

    def test_color_scheme_creation(self):
        """Test color scheme creation"""
        scheme = ColorScheme(
            primary="blue",
            secondary="cyan",
            accent="yellow",
            success="green",
            warning="yellow",
            error="red",
            info="blue",
            background="black",
            foreground="white",
        )
        assert scheme.primary == "blue"
        assert scheme.secondary == "cyan"
        assert scheme.accent == "yellow"


class TestTextStyle:
    """Test TextStyle"""

    def test_text_style_creation(self):
        """Test text style creation"""
        style = TextStyle(color="red", bold=True, underline=True)
        assert style.color == "red"
        assert style.bold is True
        assert style.underline is True

    def test_text_style_to_dict(self):
        """Test text style to dict"""
        style = TextStyle(color="blue", italic=True)
        style_dict = style.to_dict()
        assert style_dict["color"] == "blue"
        assert style_dict["italic"] is True


class TestTheme:
    """Test Theme"""

    def test_theme_creation(self):
        """Test theme creation"""
        scheme = ColorScheme(
            primary="blue",
            secondary="cyan",
            accent="yellow",
            success="green",
            warning="yellow",
            error="red",
            info="blue",
            background="black",
            foreground="white",
        )
        theme = Theme(name="test", color_scheme=scheme)
        assert theme.name == "test"
        assert theme.color_scheme == scheme

    def test_theme_get_style(self):
        """Test get style"""
        scheme = ColorScheme(
            primary="blue",
            secondary="cyan",
            accent="yellow",
            success="green",
            warning="yellow",
            error="red",
            info="blue",
            background="black",
            foreground="white",
        )
        styles = {"title": TextStyle(color="blue", bold=True)}
        theme = Theme(name="test", color_scheme=scheme, styles=styles)
        title_style = theme.get_style("title")
        assert title_style is not None
        assert title_style.color == "blue"

    def test_theme_to_dict(self):
        """Test theme to dict"""
        scheme = ColorScheme(
            primary="blue",
            secondary="cyan",
            accent="yellow",
            success="green",
            warning="yellow",
            error="red",
            info="blue",
            background="black",
            foreground="white",
        )
        theme = Theme(name="test", color_scheme=scheme)
        theme_dict = theme.to_dict()
        assert theme_dict["name"] == "test"
        assert "color_scheme" in theme_dict


class TestThemeManager:
    """Test ThemeManager"""

    def test_get_dark_theme(self):
        """Test get dark theme"""
        theme = ThemeManager.get_theme("dark")
        assert theme is not None
        assert theme.name == "dark"

    def test_get_light_theme(self):
        """Test get light theme"""
        theme = ThemeManager.get_theme("light")
        assert theme is not None
        assert theme.name == "light"

    def test_get_monokai_theme(self):
        """Test get monokai theme"""
        theme = ThemeManager.get_theme("monokai")
        assert theme is not None
        assert theme.name == "monokai"

    def test_get_nonexistent_theme(self):
        """Test get nonexistent theme"""
        theme = ThemeManager.get_theme("nonexistent")
        assert theme is None

    def test_list_themes(self):
        """Test list themes"""
        themes = ThemeManager.list_themes()
        assert "dark" in themes
        assert "light" in themes
        assert "monokai" in themes

    def test_create_custom_theme(self):
        """Test create custom theme"""
        scheme = ColorScheme(
            primary="blue",
            secondary="cyan",
            accent="yellow",
            success="green",
            warning="yellow",
            error="red",
            info="blue",
            background="black",
            foreground="white",
        )
        theme = ThemeManager.create_custom_theme("custom", scheme)
        assert theme.name == "custom"
        assert theme.color_scheme == scheme


class TestThemeConvenience:
    """Test theme convenience functions"""

    def test_get_dark_theme_function(self):
        """Test get dark theme function"""
        theme = get_dark_theme()
        assert theme.name == "dark"

    def test_get_light_theme_function(self):
        """Test get light theme function"""
        theme = get_light_theme()
        assert theme.name == "light"

    def test_get_monokai_theme_function(self):
        """Test get monokai theme function"""
        theme = get_monokai_theme()
        assert theme.name == "monokai"


# ============================================================================
# TUI Components Tests
# ============================================================================


class TestTextInput:
    """Test TextInput component"""

    def test_text_input_creation(self):
        """Test text input creation"""
        config = TextInputConfig(prompt="Enter name", default="John")
        input_field = TextInput(config)
        assert input_field.get_value() == "John"

    def test_text_input_set_value(self):
        """Test set value"""
        config = TextInputConfig(prompt="Enter name")
        input_field = TextInput(config)
        input_field.set_value("Jane")
        assert input_field.get_value() == "Jane"

    def test_text_input_validate(self):
        """Test validation"""
        config = TextInputConfig(
            prompt="Enter age", validator=lambda x: x.isdigit() and int(x) > 0
        )
        input_field = TextInput(config)
        input_field.set_value("25")
        assert input_field.validate() is True
        input_field.set_value("abc")
        assert input_field.validate() is False

    def test_text_input_to_dict(self):
        """Test to dict"""
        config = TextInputConfig(prompt="Enter name", default="John")
        input_field = TextInput(config)
        input_dict = input_field.to_dict()
        assert input_dict["prompt"] == "Enter name"
        assert input_dict["value"] == "John"


class TestSelectionList:
    """Test SelectionList component"""

    def test_selection_list_creation(self):
        """Test selection list creation"""
        config = SelectionListConfig(items=["Option 1", "Option 2", "Option 3"])
        selection = SelectionList(config)
        assert selection.current_index == 0

    def test_selection_list_select(self):
        """Test select item"""
        config = SelectionListConfig(items=["Option 1", "Option 2", "Option 3"])
        selection = SelectionList(config)
        selection.select(1)
        assert selection.current_index == 1
        assert selection.get_selected() == ["Option 2"]

    def test_selection_list_multi_select(self):
        """Test multi-select"""
        config = SelectionListConfig(
            items=["Option 1", "Option 2", "Option 3"], multi_select=True
        )
        selection = SelectionList(config)
        selection.select(0)
        selection.select(2)
        assert selection.get_selected() == ["Option 1", "Option 3"]

    def test_selection_list_move_up(self):
        """Test move up"""
        config = SelectionListConfig(items=["Option 1", "Option 2", "Option 3"])
        selection = SelectionList(config)
        selection.select(2)
        selection.move_up()
        assert selection.current_index == 1

    def test_selection_list_move_down(self):
        """Test move down"""
        config = SelectionListConfig(items=["Option 1", "Option 2", "Option 3"])
        selection = SelectionList(config)
        selection.select(0)
        selection.move_down()
        assert selection.current_index == 1

    def test_selection_list_filter(self):
        """Test filter items"""
        config = SelectionListConfig(
            items=["Apple", "Banana", "Cherry", "Date"]
        )
        selection = SelectionList(config)
        filtered = selection.filter_items("a")
        assert "Apple" in filtered
        assert "Banana" in filtered
        assert "Date" in filtered


class TestSearchComponent:
    """Test SearchComponent"""

    def test_search_component_creation(self):
        """Test search component creation"""
        config = SearchConfig(placeholder="Search...")
        search = SearchComponent(config)
        assert search.get_query() == ""

    def test_search_component_update_query(self):
        """Test update query"""
        config = SearchConfig()
        search = SearchComponent(config)
        search.update_query("test query")
        assert search.get_query() == "test query"

    def test_search_component_set_results(self):
        """Test set results"""
        config = SearchConfig()
        search = SearchComponent(config)
        results = ["Result 1", "Result 2", "Result 3"]
        search.set_results(results)
        assert search.get_results() == results

    def test_search_component_clear(self):
        """Test clear search"""
        config = SearchConfig()
        search = SearchComponent(config)
        search.update_query("test")
        search.set_results(["Result 1"])
        search.clear()
        assert search.get_query() == ""
        assert search.get_results() == []


class TestProgressBar:
    """Test ProgressBar component"""

    def test_progress_bar_creation(self):
        """Test progress bar creation"""
        config = ProgressBarConfig(total=100, label="Loading")
        progress = ProgressBar(config)
        assert progress.get_percentage() == 0.0

    def test_progress_bar_update(self):
        """Test update progress"""
        config = ProgressBarConfig(total=100)
        progress = ProgressBar(config)
        progress.update(50)
        assert progress.get_percentage() == 50.0

    def test_progress_bar_increment(self):
        """Test increment progress"""
        config = ProgressBarConfig(total=100)
        progress = ProgressBar(config)
        progress.increment(25)
        assert progress.get_percentage() == 25.0

    def test_progress_bar_complete(self):
        """Test complete progress"""
        config = ProgressBarConfig(total=100)
        progress = ProgressBar(config)
        progress.update(100)
        assert progress.is_complete() is True


class TestTable:
    """Test Table component"""

    def test_table_creation(self):
        """Test table creation"""
        config = TableConfig(
            columns=["Name", "Age"],
            rows=[["John", "25"], ["Jane", "30"]],
        )
        table = Table(config)
        assert len(table.get_rows()) == 2

    def test_table_add_row(self):
        """Test add row"""
        config = TableConfig(columns=["Name", "Age"], rows=[])
        table = Table(config)
        table.add_row(["John", "25"])
        assert len(table.get_rows()) == 1

    def test_table_remove_row(self):
        """Test remove row"""
        config = TableConfig(
            columns=["Name", "Age"],
            rows=[["John", "25"], ["Jane", "30"]],
        )
        table = Table(config)
        table.remove_row(0)
        assert len(table.get_rows()) == 1

    def test_table_get_row(self):
        """Test get row"""
        config = TableConfig(
            columns=["Name", "Age"],
            rows=[["John", "25"], ["Jane", "30"]],
        )
        table = Table(config)
        row = table.get_row(0)
        assert row == ["John", "25"]


class TestDialog:
    """Test Dialog component"""

    def test_dialog_creation(self):
        """Test dialog creation"""
        config = DialogConfig(
            title="Confirm", message="Are you sure?", buttons=["Yes", "No"]
        )
        dialog = Dialog(config)
        assert dialog.get_selected_button() == "Yes"

    def test_dialog_select_button(self):
        """Test select button"""
        config = DialogConfig(
            title="Confirm", message="Are you sure?", buttons=["Yes", "No"]
        )
        dialog = Dialog(config)
        dialog.select_button(1)
        assert dialog.get_selected_button() == "No"

    def test_dialog_move_left(self):
        """Test move left"""
        config = DialogConfig(
            title="Confirm", message="Are you sure?", buttons=["Yes", "No"]
        )
        dialog = Dialog(config)
        dialog.select_button(1)
        dialog.move_left()
        assert dialog.selected_button == 0

    def test_dialog_move_right(self):
        """Test move right"""
        config = DialogConfig(
            title="Confirm", message="Are you sure?", buttons=["Yes", "No"]
        )
        dialog = Dialog(config)
        dialog.move_right()
        assert dialog.selected_button == 1


class TestStatusBar:
    """Test StatusBar component"""

    def test_status_bar_creation(self):
        """Test status bar creation"""
        config = StatusBarConfig(left_text="Left", center_text="Center", right_text="Right")
        status = StatusBar(config)
        assert status.config.left_text == "Left"

    def test_status_bar_update(self):
        """Test update status bar"""
        config = StatusBarConfig()
        status = StatusBar(config)
        status.update_left("New Left")
        status.update_center("New Center")
        status.update_right("New Right")
        assert status.config.left_text == "New Left"
        assert status.config.center_text == "New Center"
        assert status.config.right_text == "New Right"


# ============================================================================
# TUI Screens Tests
# ============================================================================


class TestScreenContext:
    """Test ScreenContext"""

    def test_screen_context_creation(self):
        """Test screen context creation"""
        context = ScreenContext(current_screen=ScreenType.MAIN_MENU)
        assert context.current_screen == ScreenType.MAIN_MENU


class TestMainMenuScreen:
    """Test MainMenuScreen"""

    def test_main_menu_screen_creation(self):
        """Test main menu screen creation"""
        context = ScreenContext(current_screen=ScreenType.MAIN_MENU)
        screen = MainMenuScreen(context)
        assert screen.context.current_screen == ScreenType.MAIN_MENU

    def test_main_menu_screen_render(self):
        """Test render main menu"""
        context = ScreenContext(current_screen=ScreenType.MAIN_MENU)
        screen = MainMenuScreen(context)
        content = screen.render()
        assert "mini_wiki" in content
        assert "Main Menu" in content

    def test_main_menu_screen_navigation(self):
        """Test main menu navigation"""
        context = ScreenContext(current_screen=ScreenType.MAIN_MENU)
        screen = MainMenuScreen(context)
        next_screen = screen.handle_input("down")
        assert screen.selection.current_index == 1


class TestSearchScreen:
    """Test SearchScreen"""

    def test_search_screen_creation(self):
        """Test search screen creation"""
        context = ScreenContext(current_screen=ScreenType.SEARCH)
        screen = SearchScreen(context)
        assert screen.context.current_screen == ScreenType.SEARCH

    def test_search_screen_render(self):
        """Test render search screen"""
        context = ScreenContext(current_screen=ScreenType.SEARCH)
        screen = SearchScreen(context)
        content = screen.render()
        assert "Search Documents" in content


class TestResultsScreen:
    """Test ResultsScreen"""

    def test_results_screen_creation(self):
        """Test results screen creation"""
        context = ScreenContext(current_screen=ScreenType.RESULTS)
        screen = ResultsScreen(context)
        assert screen.context.current_screen == ScreenType.RESULTS

    def test_results_screen_render(self):
        """Test render results screen"""
        context = ScreenContext(current_screen=ScreenType.RESULTS)
        screen = ResultsScreen(context)
        content = screen.render()
        assert "Search Results" in content


class TestDocumentViewerScreen:
    """Test DocumentViewerScreen"""

    def test_document_viewer_screen_creation(self):
        """Test document viewer screen creation"""
        context = ScreenContext(current_screen=ScreenType.DOCUMENT_VIEWER)
        screen = DocumentViewerScreen(context)
        assert screen.context.current_screen == ScreenType.DOCUMENT_VIEWER

    def test_document_viewer_screen_render(self):
        """Test render document viewer"""
        context = ScreenContext(current_screen=ScreenType.DOCUMENT_VIEWER)
        screen = DocumentViewerScreen(context)
        content = screen.render()
        assert "Document Viewer" in content


class TestKnowledgeBaseScreen:
    """Test KnowledgeBaseScreen"""

    def test_knowledge_base_screen_creation(self):
        """Test knowledge base screen creation"""
        context = ScreenContext(current_screen=ScreenType.KNOWLEDGE_BASE)
        screen = KnowledgeBaseScreen(context)
        assert screen.context.current_screen == ScreenType.KNOWLEDGE_BASE

    def test_knowledge_base_screen_render(self):
        """Test render knowledge base"""
        context = ScreenContext(current_screen=ScreenType.KNOWLEDGE_BASE)
        screen = KnowledgeBaseScreen(context)
        content = screen.render()
        assert "Knowledge Base" in content


class TestSettingsScreen:
    """Test SettingsScreen"""

    def test_settings_screen_creation(self):
        """Test settings screen creation"""
        context = ScreenContext(current_screen=ScreenType.SETTINGS)
        screen = SettingsScreen(context)
        assert screen.context.current_screen == ScreenType.SETTINGS

    def test_settings_screen_render(self):
        """Test render settings"""
        context = ScreenContext(current_screen=ScreenType.SETTINGS)
        screen = SettingsScreen(context)
        content = screen.render()
        assert "Settings" in content


class TestHelpScreen:
    """Test HelpScreen"""

    def test_help_screen_creation(self):
        """Test help screen creation"""
        context = ScreenContext(current_screen=ScreenType.HELP)
        screen = HelpScreen(context)
        assert screen.context.current_screen == ScreenType.HELP

    def test_help_screen_render(self):
        """Test render help"""
        context = ScreenContext(current_screen=ScreenType.HELP)
        screen = HelpScreen(context)
        content = screen.render()
        assert "mini_wiki" in content


class TestScreenFactory:
    """Test ScreenFactory"""

    def test_create_main_menu_screen(self):
        """Test create main menu screen"""
        context = ScreenContext(current_screen=ScreenType.MAIN_MENU)
        screen = ScreenFactory.create_screen(ScreenType.MAIN_MENU, context)
        assert isinstance(screen, MainMenuScreen)

    def test_create_search_screen(self):
        """Test create search screen"""
        context = ScreenContext(current_screen=ScreenType.SEARCH)
        screen = ScreenFactory.create_screen(ScreenType.SEARCH, context)
        assert isinstance(screen, SearchScreen)

    def test_create_results_screen(self):
        """Test create results screen"""
        context = ScreenContext(current_screen=ScreenType.RESULTS)
        screen = ScreenFactory.create_screen(ScreenType.RESULTS, context)
        assert isinstance(screen, ResultsScreen)


# ============================================================================
# CursesTUI Application Tests
# ============================================================================


class TestCursesTUI:
    """Test CursesTUI — the real curses-based TUI"""

    def test_tui_creation_default(self):
        """Test CursesTUI creation with defaults"""
        tui = CursesTUI()
        assert tui.running is False
        assert tui.current_menu == "main"
        assert tui.system is None

    def test_tui_creation_with_system(self):
        """Test CursesTUI creation with system"""
        mock_system = MagicMock()
        mock_system.documents = []
        tui = CursesTUI(system=mock_system)
        assert tui.system is mock_system

    def test_tui_initial_state(self):
        """Test initial state"""
        tui = CursesTUI()
        assert tui.search_query == ""
        assert tui.search_results == []
        assert tui.menu_index == 0
        assert tui.theme == "dark"
        assert tui.results_per_page == 10

    def test_tui_go_to_navigation(self):
        """Test navigation history"""
        tui = CursesTUI()
        assert tui.current_menu == "main"
        assert tui.prev_menu == []

        tui._go_to("search_input")
        assert tui.current_menu == "search_input"
        assert tui.prev_menu == ["main"]

        tui._go_to("results")
        assert tui.current_menu == "results"
        assert tui.prev_menu == ["main", "search_input"]

    def test_tui_go_back_navigation(self):
        """Test back navigation"""
        tui = CursesTUI()
        tui._go_to("search_input")
        tui._go_to("results")
        assert tui.current_menu == "results"

        tui._go_back()
        assert tui.current_menu == "search_input"

        tui._go_back()
        assert tui.current_menu == "main"

    def test_tui_show_message(self):
        """Test message display"""
        tui = CursesTUI()
        tui._show_message("Test message", duration=10)
        assert tui.message == "Test message"
        assert tui.message_timer == 10

    def test_tui_do_search_no_system(self):
        """Test search without system"""
        tui = CursesTUI()
        tui.search_query = "test"
        tui._do_search()
        assert len(tui.search_results) > 0  # fallback results

    def test_tui_do_search_with_system(self):
        """Test search with mock system"""
        mock_system = MagicMock()
        mock_system.documents = [{"id": "1", "title": "Test", "content": "Test content"}]
        mock_system.search.return_value = [
            {"id": "1", "title": "Test", "content": "Test content", "relevance": 0.9}
        ]
        tui = CursesTUI(system=mock_system)
        tui.search_query = "test"
        tui._do_search()
        assert len(tui.search_results) == 1
        mock_system.search.assert_called_once()

    def test_tui_do_load_with_system(self):
        """Test load data with mock system"""
        mock_system = MagicMock()
        mock_system.load_data.return_value = True
        mock_system.documents = [{"id": "1", "title": "Test"}]
        tui = CursesTUI(system=mock_system)
        tui.load_path = "/tmp/test.csv"
        tui._do_load()
        mock_system.load_data.assert_called_once()

    def test_tui_do_export_with_system(self):
        """Test export with mock system"""
        mock_system = MagicMock()
        mock_system.export_results.return_value = True
        tui = CursesTUI(system=mock_system)
        tui.search_results = [{"id": "1", "title": "Test"}]
        tui._do_export("json")
        mock_system.export_results.assert_called_once()

    def test_tui_do_export_no_results(self):
        """Test export with no results"""
        tui = CursesTUI()
        tui.search_results = []
        tui._do_export("json")
        # Should show message, not crash

    def test_tui_main_menu_items(self):
        """Test main menu has expected items"""
        tui = CursesTUI()
        menu_items = tui.menus["main"]
        labels = [label for label, _ in menu_items]
        assert "Load Data" in labels
        assert "Search Documents" in labels
        assert "View Knowledge Base" in labels
        assert "Export Results" in labels
        assert "Settings" in labels
        assert "Help" in labels
        assert "Exit" in labels

    def test_tui_export_menu_items(self):
        """Test export menu has expected items"""
        tui = CursesTUI()
        menu_items = tui.menus["export"]
        labels = [label for label, _ in menu_items]
        assert "Export as JSON" in labels
        assert "Export as Markdown" in labels
        assert "Export as CSV" in labels

    def test_tui_settings_toggle_theme(self):
        """Test theme toggle in settings"""
        tui = CursesTUI()
        assert tui.theme == "dark"
        tui.settings_index = 0
        tui._handle_settings_input(10)  # Enter key
        assert tui.theme == "light"
        tui.settings_index = 0
        tui._handle_settings_input(10)  # Enter key again
        assert tui.theme == "dark"


class TestRunTUI:
    """Test run_tui function"""

    def test_run_tui_creates_tui(self):
        """Test run_tui creates CursesTUI instance"""
        with patch("mini_wiki.ui.tui_app.CursesTUI") as MockTUI:
            mock_instance = MagicMock()
            MockTUI.return_value = mock_instance
            run_tui()
            MockTUI.assert_called_once()
            mock_instance.start.assert_called_once()