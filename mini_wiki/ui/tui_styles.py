"""
TUI Styles Module
Defines colors, themes, and styling for the TUI interface

Features:
- Color definitions
- Theme management
- Style presets
- Dark and light themes
- Custom theme creation
"""

import logging
from dataclasses import dataclass
from enum import Enum
from typing import Dict, Optional

logger = logging.getLogger(__name__)


class Color(Enum):
    """Color definitions"""

    # Basic colors
    BLACK = "black"
    WHITE = "white"
    RED = "red"
    GREEN = "green"
    YELLOW = "yellow"
    BLUE = "blue"
    MAGENTA = "magenta"
    CYAN = "cyan"

    # Bright colors
    BRIGHT_BLACK = "bright_black"
    BRIGHT_RED = "bright_red"
    BRIGHT_GREEN = "bright_green"
    BRIGHT_YELLOW = "bright_yellow"
    BRIGHT_BLUE = "bright_blue"
    BRIGHT_MAGENTA = "bright_magenta"
    BRIGHT_CYAN = "bright_cyan"
    BRIGHT_WHITE = "bright_white"


@dataclass
class ColorScheme:
    """Color scheme definition

    Attributes:
        primary: Primary color
        secondary: Secondary color
        accent: Accent color
        success: Success color
        warning: Warning color
        error: Error color
        info: Info color
        background: Background color
        foreground: Foreground color
    """

    primary: str
    secondary: str
    accent: str
    success: str
    warning: str
    error: str
    info: str
    background: str
    foreground: str


@dataclass
class TextStyle:
    """Text style definition

    Attributes:
        color: Text color
        background: Background color
        bold: Bold text
        italic: Italic text
        underline: Underline text
        reverse: Reverse video
    """

    color: Optional[str] = None
    background: Optional[str] = None
    bold: bool = False
    italic: bool = False
    underline: bool = False
    reverse: bool = False

    def to_dict(self) -> Dict:
        """Convert to dictionary

        Returns:
            Dictionary representation
        """
        return {
            "color": self.color,
            "background": self.background,
            "bold": self.bold,
            "italic": self.italic,
            "underline": self.underline,
            "reverse": self.reverse,
        }


class Theme:
    """Theme definition"""

    def __init__(
        self,
        name: str,
        color_scheme: ColorScheme,
        styles: Optional[Dict[str, TextStyle]] = None,
    ):
        """Initialize theme

        Args:
            name: Theme name
            color_scheme: Color scheme
            styles: Dictionary of named styles
        """
        self.name = name
        self.color_scheme = color_scheme
        self.styles = styles or {}

    def get_style(self, name: str) -> Optional[TextStyle]:
        """Get style by name

        Args:
            name: Style name

        Returns:
            TextStyle or None if not found
        """
        return self.styles.get(name)

    def to_dict(self) -> Dict:
        """Convert to dictionary

        Returns:
            Dictionary representation
        """
        return {
            "name": self.name,
            "color_scheme": {
                "primary": self.color_scheme.primary,
                "secondary": self.color_scheme.secondary,
                "accent": self.color_scheme.accent,
                "success": self.color_scheme.success,
                "warning": self.color_scheme.warning,
                "error": self.color_scheme.error,
                "info": self.color_scheme.info,
                "background": self.color_scheme.background,
                "foreground": self.color_scheme.foreground,
            },
            "styles": {
                name: style.to_dict() for name, style in self.styles.items()
            },
        }


class ThemeManager:
    """Manage TUI themes"""

    # Dark theme
    DARK_SCHEME = ColorScheme(
        primary="bright_blue",
        secondary="bright_cyan",
        accent="bright_yellow",
        success="bright_green",
        warning="bright_yellow",
        error="bright_red",
        info="bright_blue",
        background="black",
        foreground="bright_white",
    )

    DARK_THEME = Theme(
        name="dark",
        color_scheme=DARK_SCHEME,
        styles={
            "title": TextStyle(color="bright_blue", bold=True),
            "subtitle": TextStyle(color="bright_cyan", bold=True),
            "header": TextStyle(color="bright_white", bold=True),
            "success": TextStyle(color="bright_green"),
            "warning": TextStyle(color="bright_yellow"),
            "error": TextStyle(color="bright_red"),
            "info": TextStyle(color="bright_blue"),
            "muted": TextStyle(color="bright_black"),
            "highlight": TextStyle(color="bright_yellow", reverse=True),
            "selected": TextStyle(color="black", background="bright_cyan"),
            "border": TextStyle(color="bright_cyan"),
            "code": TextStyle(color="bright_green"),
        },
    )

    # Light theme
    LIGHT_SCHEME = ColorScheme(
        primary="blue",
        secondary="cyan",
        accent="yellow",
        success="green",
        warning="yellow",
        error="red",
        info="blue",
        background="white",
        foreground="black",
    )

    LIGHT_THEME = Theme(
        name="light",
        color_scheme=LIGHT_SCHEME,
        styles={
            "title": TextStyle(color="blue", bold=True),
            "subtitle": TextStyle(color="cyan", bold=True),
            "header": TextStyle(color="black", bold=True),
            "success": TextStyle(color="green"),
            "warning": TextStyle(color="yellow"),
            "error": TextStyle(color="red"),
            "info": TextStyle(color="blue"),
            "muted": TextStyle(color="bright_black"),
            "highlight": TextStyle(color="yellow", reverse=True),
            "selected": TextStyle(color="white", background="blue"),
            "border": TextStyle(color="cyan"),
            "code": TextStyle(color="green"),
        },
    )

    # Monokai theme
    MONOKAI_SCHEME = ColorScheme(
        primary="bright_cyan",
        secondary="bright_magenta",
        accent="bright_yellow",
        success="bright_green",
        warning="bright_yellow",
        error="bright_red",
        info="bright_blue",
        background="black",
        foreground="bright_white",
    )

    MONOKAI_THEME = Theme(
        name="monokai",
        color_scheme=MONOKAI_SCHEME,
        styles={
            "title": TextStyle(color="bright_cyan", bold=True),
            "subtitle": TextStyle(color="bright_magenta", bold=True),
            "header": TextStyle(color="bright_white", bold=True),
            "success": TextStyle(color="bright_green"),
            "warning": TextStyle(color="bright_yellow"),
            "error": TextStyle(color="bright_red"),
            "info": TextStyle(color="bright_blue"),
            "muted": TextStyle(color="bright_black"),
            "highlight": TextStyle(color="black", background="bright_yellow"),
            "selected": TextStyle(color="black", background="bright_cyan"),
            "border": TextStyle(color="bright_magenta"),
            "code": TextStyle(color="bright_green"),
        },
    )

    # Built-in themes
    THEMES = {
        "dark": DARK_THEME,
        "light": LIGHT_THEME,
        "monokai": MONOKAI_THEME,
    }

    @classmethod
    def get_theme(cls, name: str) -> Optional[Theme]:
        """Get theme by name

        Args:
            name: Theme name

        Returns:
            Theme or None if not found
        """
        return cls.THEMES.get(name.lower())

    @classmethod
    def list_themes(cls) -> Dict[str, str]:
        """List all available themes

        Returns:
            Dictionary of theme names and descriptions
        """
        return {
            "dark": "Dark theme with bright colors",
            "light": "Light theme with standard colors",
            "monokai": "Monokai theme inspired by popular editor theme",
        }

    @classmethod
    def create_custom_theme(
        cls,
        name: str,
        color_scheme: ColorScheme,
        styles: Optional[Dict[str, TextStyle]] = None,
    ) -> Theme:
        """Create custom theme

        Args:
            name: Theme name
            color_scheme: Color scheme
            styles: Dictionary of styles (optional)

        Returns:
            Custom Theme
        """
        theme = Theme(name, color_scheme, styles)
        logger.info(f"Created custom theme: {name}")
        return theme


# Convenience functions
def get_dark_theme() -> Theme:
    """Get dark theme"""
    return ThemeManager.DARK_THEME


def get_light_theme() -> Theme:
    """Get light theme"""
    return ThemeManager.LIGHT_THEME


def get_monokai_theme() -> Theme:
    """Get monokai theme"""
    return ThemeManager.MONOKAI_THEME
