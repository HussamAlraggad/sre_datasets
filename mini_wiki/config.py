"""
Configuration management for mini_wiki
"""

import os
from pathlib import Path
from typing import Any, Dict, Optional

import yaml
from pydantic import BaseSettings, validator


class MiniWikiConfig(BaseSettings):
    """Configuration for mini_wiki"""

    # App settings
    app_name: str = "mini_wiki"
    app_version: str = "1.0.0"
    debug: bool = False
    log_level: str = "INFO"

    # Paths
    data_dir: Path = Path("./data")
    cache_dir: Path = Path("./cache")
    log_dir: Path = Path("./logs")
    config_dir: Path = Path("./config")

    # Dataset settings
    max_dataset_size_mb: int = 1000

    # Embeddings settings
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    embedding_dimension: int = 384
    embedding_batch_size: int = 32
    embedding_device: str = "cpu"

    # Ranking settings
    relevance_weight: float = 0.6
    importance_weight: float = 0.4

    # UI settings
    ui_theme: str = "dark"
    table_width: int = 120
    results_per_page: int = 20

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

    @validator("data_dir", "cache_dir", "log_dir", "config_dir", pre=True)
    def create_directories(cls, v):
        """Create directories if they don't exist"""
        path = Path(v)
        path.mkdir(parents=True, exist_ok=True)
        return path


class ConfigManager:
    """Manage mini_wiki configuration"""

    def __init__(self, config_path: Optional[str] = None):
        """Initialize configuration manager

        Args:
            config_path: Path to configuration file
        """
        self.config_path = config_path or self._find_config()
        self.config = self._load_config()

    def _find_config(self) -> str:
        """Find configuration file in standard locations"""
        locations = [
            "./mini_wiki_config.yaml",
            "~/.mini_wiki/config.yaml",
            "/etc/mini_wiki/config.yaml",
        ]

        for location in locations:
            path = Path(location).expanduser()
            if path.exists():
                return str(path)

        # Return default location
        return "./mini_wiki_config.yaml"

    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from file"""
        if not Path(self.config_path).exists():
            return self._get_default_config()

        with open(self.config_path, "r") as f:
            return yaml.safe_load(f) or {}

    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration"""
        return {
            "app": {
                "name": "mini_wiki",
                "version": "1.0.0",
                "debug": False,
                "log_level": "INFO",
            },
            "dataset": {
                "storage_dir": "./data",
                "cache_dir": "./cache",
                "max_size_mb": 1000,
            },
            "embeddings": {
                "model": "sentence-transformers/all-MiniLM-L6-v2",
                "dimension": 384,
                "batch_size": 32,
                "device": "cpu",
            },
            "ranking": {
                "weights": {"relevance": 0.6, "importance": 0.4},
            },
            "ui": {
                "theme": "dark",
                "table_width": 120,
                "results_per_page": 20,
            },
        }

    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value by key (supports dot notation)

        Args:
            key: Configuration key (e.g., "app.name", "embeddings.model")
            default: Default value if key not found

        Returns:
            Configuration value
        """
        keys = key.split(".")
        value = self.config

        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
                if value is None:
                    return default
            else:
                return default

        return value

    def set(self, key: str, value: Any) -> None:
        """Set configuration value by key (supports dot notation)

        Args:
            key: Configuration key (e.g., "app.name")
            value: Configuration value
        """
        keys = key.split(".")
        config = self.config

        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]

        config[keys[-1]] = value

    def save(self, path: Optional[str] = None) -> None:
        """Save configuration to file

        Args:
            path: Path to save configuration (defaults to config_path)
        """
        path = path or self.config_path
        Path(path).parent.mkdir(parents=True, exist_ok=True)

        with open(path, "w") as f:
            yaml.dump(self.config, f, default_flow_style=False, sort_keys=False)

    def to_dict(self) -> Dict[str, Any]:
        """Get configuration as dictionary"""
        return self.config.copy()


# Global configuration instance
_config_manager: Optional[ConfigManager] = None


def get_config(config_path: Optional[str] = None) -> ConfigManager:
    """Get global configuration manager instance

    Args:
        config_path: Path to configuration file

    Returns:
        ConfigManager instance
    """
    global _config_manager

    if _config_manager is None:
        _config_manager = ConfigManager(config_path)

    return _config_manager
