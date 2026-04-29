"""
TUI Application Module
Main TUI application controller and event loop

Features:
- Application initialization
- Event loop management
- Screen navigation
- Input handling
- Output rendering
- Configuration management
"""

import logging
import sys
from typing import Dict, Optional

from mini_wiki.ui.tui_screens import (
    Screen,
    ScreenContext,
    ScreenFactory,
    ScreenType,
)
from mini_wiki.ui.tui_styles import Theme, ThemeManager

logger = logging.getLogger(__name__)


class TUIApplication:
    """Main TUI application"""

    def __init__(
        self,
        title: str = "mini_wiki",
        theme_name: str = "dark",
        width: int = 80,
        height: int = 24,
    ):
        """Initialize TUI application

        Args:
            title: Application title
            theme_name: Theme name
            width: Terminal width
            height: Terminal height
        """
        self.title = title
        self.width = width
        self.height = height
        self.running = False
        self.current_screen: Optional[Screen] = None
        self.screen_history: list[ScreenType] = []

        # Load theme
        self.theme = ThemeManager.get_theme(theme_name)
        if not self.theme:
            logger.warning(f"Theme '{theme_name}' not found, using 'dark'")
            self.theme = ThemeManager.get_theme("dark")

        # Initialize context
        self.context = ScreenContext(
            current_screen=ScreenType.MAIN_MENU,
            theme=theme_name,
        )

        logger.info(f"Initialized TUI application: {title}")

    def start(self) -> None:
        """Start application"""
        self.running = True
        logger.info("Starting TUI application")

        try:
            self._initialize_screen()
            self._event_loop()
        except KeyboardInterrupt:
            logger.info("Application interrupted by user")
        except Exception as e:
            logger.error(f"Application error: {e}", exc_info=True)
        finally:
            self.stop()

    def stop(self) -> None:
        """Stop application"""
        self.running = False
        logger.info("Stopping TUI application")
        self._cleanup()

    def _initialize_screen(self) -> None:
        """Initialize current screen"""
        try:
            self.current_screen = ScreenFactory.create_screen(
                self.context.current_screen, self.context
            )
            logger.debug(f"Initialized screen: {self.context.current_screen.value}")
        except Exception as e:
            logger.error(f"Failed to initialize screen: {e}")
            raise

    def _event_loop(self) -> None:
        """Main event loop"""
        while self.running:
            try:
                # Render current screen
                self._render()

                # Get user input
                key = self._get_input()

                # Handle input
                next_screen = self._handle_input(key)

                # Navigate to next screen if needed
                if next_screen:
                    self._navigate_to(next_screen)

            except Exception as e:
                logger.error(f"Event loop error: {e}")
                break

    def _render(self) -> None:
        """Render current screen"""
        if not self.current_screen:
            return

        try:
            # Clear screen
            self._clear_screen()

            # Render screen content
            content = self.current_screen.render()
            print(content)

            # Render status bar
            status = self.current_screen.get_status_bar()
            self._render_status_bar(status)

        except Exception as e:
            logger.error(f"Render error: {e}")

    def _get_input(self) -> str:
        """Get user input

        Returns:
            Input key
        """
        try:
            # Simulate input (in real implementation, use curses or similar)
            user_input = input("\n> ").strip().lower()

            # Map input to keys
            if user_input == "q":
                return "q"
            elif user_input == "up" or user_input == "w":
                return "up"
            elif user_input == "down" or user_input == "s":
                return "down"
            elif user_input == "left" or user_input == "a":
                return "left"
            elif user_input == "right" or user_input == "d":
                return "right"
            elif user_input == "enter" or user_input == "":
                return "enter"
            elif user_input == "backspace" or user_input == "bs":
                return "backspace"
            else:
                return user_input

        except EOFError:
            return "q"

    def _handle_input(self, key: str) -> Optional[ScreenType]:
        """Handle user input

        Args:
            key: Input key

        Returns:
            Next screen type or None
        """
        if not self.current_screen:
            return None

        try:
            next_screen = self.current_screen.handle_input(key)
            if next_screen == ScreenType.EXIT:
                self.stop()
                return None
            return next_screen
        except Exception as e:
            logger.error(f"Input handling error: {e}")
            return None

    def _navigate_to(self, screen_type: ScreenType) -> None:
        """Navigate to screen

        Args:
            screen_type: Target screen type
        """
        try:
            # Update context
            self.context.previous_screen = self.context.current_screen
            self.context.current_screen = screen_type

            # Add to history
            self.screen_history.append(screen_type)

            # Create new screen
            self._initialize_screen()

            logger.debug(f"Navigated to screen: {screen_type.value}")

        except Exception as e:
            logger.error(f"Navigation error: {e}")

    def _render_status_bar(self, status) -> None:
        """Render status bar

        Args:
            status: Status bar object
        """
        try:
            status_dict = status.to_dict()
            left = status_dict.get("left", "")
            center = status_dict.get("center", "")
            right = status_dict.get("right", "")

            # Calculate spacing
            total_width = self.width
            left_width = len(left)
            right_width = len(right)
            center_width = len(center)

            # Build status bar
            if left or center or right:
                status_line = left.ljust(left_width)
                status_line += center.center(total_width - left_width - right_width)
                status_line += right.rjust(right_width)
                print(status_line)

        except Exception as e:
            logger.error(f"Status bar render error: {e}")

    def _clear_screen(self) -> None:
        """Clear terminal screen"""
        try:
            if sys.platform == "win32":
                import os

                os.system("cls")
            else:
                import os

                os.system("clear")
        except Exception as e:
            logger.warning(f"Failed to clear screen: {e}")

    def _cleanup(self) -> None:
        """Cleanup resources"""
        try:
            logger.info("Cleaning up resources")
            # Add cleanup code here
        except Exception as e:
            logger.error(f"Cleanup error: {e}")

    def get_theme(self) -> Theme:
        """Get current theme

        Returns:
            Current theme
        """
        return self.theme

    def set_theme(self, theme_name: str) -> None:
        """Set theme

        Args:
            theme_name: Theme name
        """
        theme = ThemeManager.get_theme(theme_name)
        if theme:
            self.theme = theme
            self.context.theme = theme_name
            logger.info(f"Changed theme to: {theme_name}")
        else:
            logger.warning(f"Theme '{theme_name}' not found")

    def get_screen_history(self) -> list[ScreenType]:
        """Get screen navigation history

        Returns:
            List of visited screens
        """
        return self.screen_history

    def to_dict(self) -> Dict:
        """Convert to dictionary

        Returns:
            Dictionary representation
        """
        return {
            "title": self.title,
            "width": self.width,
            "height": self.height,
            "running": self.running,
            "current_screen": self.context.current_screen.value,
            "theme": self.context.theme,
            "screen_history": [s.value for s in self.screen_history],
        }


class TUIApplicationBuilder:
    """Builder for TUI application"""

    def __init__(self):
        """Initialize builder"""
        self.title = "mini_wiki"
        self.theme_name = "dark"
        self.width = 80
        self.height = 24

    def with_title(self, title: str) -> "TUIApplicationBuilder":
        """Set application title

        Args:
            title: Application title

        Returns:
            Builder instance
        """
        self.title = title
        return self

    def with_theme(self, theme_name: str) -> "TUIApplicationBuilder":
        """Set theme

        Args:
            theme_name: Theme name

        Returns:
            Builder instance
        """
        self.theme_name = theme_name
        return self

    def with_dimensions(self, width: int, height: int) -> "TUIApplicationBuilder":
        """Set terminal dimensions

        Args:
            width: Terminal width
            height: Terminal height

        Returns:
            Builder instance
        """
        self.width = width
        self.height = height
        return self

    def build(self) -> TUIApplication:
        """Build application

        Returns:
            TUIApplication instance
        """
        return TUIApplication(
            title=self.title,
            theme_name=self.theme_name,
            width=self.width,
            height=self.height,
        )


def create_app(
    title: str = "mini_wiki",
    theme: str = "dark",
    width: int = 80,
    height: int = 24,
) -> TUIApplication:
    """Create TUI application

    Args:
        title: Application title
        theme: Theme name
        width: Terminal width
        height: Terminal height

    Returns:
        TUIApplication instance
    """
    return TUIApplicationBuilder().with_title(title).with_theme(theme).with_dimensions(
        width, height
    ).build()
