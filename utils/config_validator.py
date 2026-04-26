"""
utils/config_validator.py
=========================
Validate dataset_config.yaml files against the expected schema.

Ensures that all required fields are present and have valid values.
"""

from pathlib import Path
from typing import Dict, Any, List, Tuple
import yaml


class ConfigValidator:
    """Validates dataset_config.yaml files."""

    # Define the expected schema
    REQUIRED_FIELDS = {
        "dataset_name": str,
        "csv_path": str,
        "column_mappings": dict,
        "llm_settings": dict,
        "output_formats": list,
    }

    COLUMN_MAPPINGS_REQUIRED = {
        "text_columns": list,
    }

    COLUMN_MAPPINGS_OPTIONAL = {
        "metadata_columns": list,
    }

    LLM_SETTINGS_REQUIRED = {
        "model": str,
        "ollama_url": str,
    }

    LLM_SETTINGS_OPTIONAL = {
        "temperature": float,
        "num_ctx": int,
        "num_predict": int,
    }

    VALID_OUTPUT_FORMATS = ["ieee_830", "ieee_29148", "json", "csv", "excel"]

    @classmethod
    def validate_file(cls, config_path: Path) -> Tuple[bool, List[str]]:
        """
        Validate a dataset_config.yaml file.

        Args:
            config_path: Path to the YAML config file

        Returns:
            Tuple of (is_valid: bool, errors: List[str])
        """
        errors = []

        # Check file exists
        if not config_path.exists():
            return False, [f"Config file not found: {config_path}"]

        # Load YAML
        try:
            with open(config_path, "r") as f:
                config = yaml.safe_load(f)
        except yaml.YAMLError as e:
            return False, [f"Invalid YAML syntax: {e}"]
        except Exception as e:
            return False, [f"Error reading config file: {e}"]

        if config is None:
            return False, ["Config file is empty"]

        # Validate required fields
        for field, expected_type in cls.REQUIRED_FIELDS.items():
            if field not in config:
                errors.append(f"Missing required field: {field}")
            elif not isinstance(config[field], expected_type):
                errors.append(
                    f"Field '{field}' must be {expected_type.__name__}, "
                    f"got {type(config[field]).__name__}"
                )

        # Validate column_mappings
        if "column_mappings" in config:
            col_map = config["column_mappings"]
            for field, expected_type in cls.COLUMN_MAPPINGS_REQUIRED.items():
                if field not in col_map:
                    errors.append(f"Missing required field in column_mappings: {field}")
                elif not isinstance(col_map[field], expected_type):
                    errors.append(
                        f"column_mappings.{field} must be {expected_type.__name__}, "
                        f"got {type(col_map[field]).__name__}"
                    )

            # Validate text_columns is non-empty
            if "text_columns" in col_map and not col_map["text_columns"]:
                errors.append("column_mappings.text_columns cannot be empty")

        # Validate llm_settings
        if "llm_settings" in config:
            llm = config["llm_settings"]
            for field, expected_type in cls.LLM_SETTINGS_REQUIRED.items():
                if field not in llm:
                    errors.append(f"Missing required field in llm_settings: {field}")
                elif not isinstance(llm[field], expected_type):
                    errors.append(
                        f"llm_settings.{field} must be {expected_type.__name__}, "
                        f"got {type(llm[field]).__name__}"
                    )

        # Validate output_formats
        if "output_formats" in config:
            formats = config["output_formats"]
            if not formats:
                errors.append("output_formats cannot be empty")
            for fmt in formats:
                if fmt not in cls.VALID_OUTPUT_FORMATS:
                    errors.append(
                        f"Invalid output format: {fmt}. "
                        f"Valid options: {', '.join(cls.VALID_OUTPUT_FORMATS)}"
                    )

        # Validate CSV path exists
        if "csv_path" in config:
            csv_path = Path(config["csv_path"])
            if not csv_path.exists():
                errors.append(f"CSV file not found: {config['csv_path']}")

        return len(errors) == 0, errors

    @classmethod
    def load_config(cls, config_path: Path) -> Dict[str, Any]:
        """
        Load and validate a config file, raising exception if invalid.

        Args:
            config_path: Path to the YAML config file

        Returns:
            Parsed config dictionary

        Raises:
            ValueError: If config is invalid
        """
        is_valid, errors = cls.validate_file(config_path)
        if not is_valid:
            raise ValueError(f"Invalid config file:\n" + "\n".join(errors))

        with open(config_path, "r") as f:
            return yaml.safe_load(f)
