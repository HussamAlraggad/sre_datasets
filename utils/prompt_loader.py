"""
utils/prompt_loader.py
======================
Load and render Jinja2 prompt templates with configuration parameters.

The PromptLoader handles:
  1. Loading Jinja2 templates from prompts/templates/
  2. Rendering templates with configuration parameters
  3. Providing default values for optional parameters
  4. Validating template parameters
"""

from pathlib import Path
from typing import Dict, Any, Optional
from jinja2 import Environment, FileSystemLoader, TemplateNotFound, TemplateSyntaxError


class PromptLoader:
    """Load and render Jinja2 prompt templates."""

    # Template names and their required parameters
    TEMPLATES = {
        "fr_nfr_extraction": {
            "required": ["reviews"],
            "optional": ["domain_description", "project_name", "categories_enabled", "fr_categories", "nfr_categories"],
        },
        "moscow_prioritization": {
            "required": ["requirements_json"],
            "optional": ["project_name", "project_description"],
        },
        "dfd_components": {
            "required": ["requirements_json"],
            "optional": ["project_name"],
        },
        "cspec_logic": {
            "required": ["dfd_json"],
            "optional": ["project_name"],
        },
        "srs_formatter": {
            "required": ["requirements_json", "moscow_json", "dfd_json"],
            "optional": ["project_name", "srs_version", "date"],
        },
    }

    def __init__(self, templates_dir: Optional[Path] = None):
        """
        Initialize the prompt loader.

        Args:
            templates_dir: Path to templates directory (default: prompts/templates/)
        """
        if templates_dir is None:
            templates_dir = Path(__file__).parent.parent / "prompts" / "templates"

        self.templates_dir = Path(templates_dir)
        if not self.templates_dir.exists():
            raise FileNotFoundError(f"Templates directory not found: {self.templates_dir}")

        # Initialize Jinja2 environment
        self.env = Environment(
            loader=FileSystemLoader(str(self.templates_dir)),
            trim_blocks=True,
            lstrip_blocks=True,
        )

    def render(self, template_name: str, **kwargs) -> str:
        """
        Render a template with the given parameters.

        Args:
            template_name: Name of the template (without .jinja2 extension)
            **kwargs: Template parameters

        Returns:
            Rendered template string

        Raises:
            ValueError: If required parameters are missing
            TemplateNotFound: If template doesn't exist
            TemplateSyntaxError: If template has syntax errors
        """
        # Validate template name
        if template_name not in self.TEMPLATES:
            raise ValueError(f"Unknown template: {template_name}. Valid options: {list(self.TEMPLATES.keys())}")

        # Validate required parameters
        template_spec = self.TEMPLATES[template_name]
        missing = set(template_spec["required"]) - set(kwargs.keys())
        if missing:
            raise ValueError(
                f"Missing required parameters for '{template_name}': {missing}. "
                f"Required: {template_spec['required']}"
            )

        # Add default values for optional parameters
        defaults = self._get_defaults(template_name)
        for key, value in defaults.items():
            if key not in kwargs:
                kwargs[key] = value

        # Load and render template
        try:
            template = self.env.get_template(f"{template_name}.jinja2")
            return template.render(**kwargs)
        except TemplateNotFound:
            raise TemplateNotFound(f"Template not found: {template_name}.jinja2")
        except TemplateSyntaxError as e:
            raise TemplateSyntaxError(f"Syntax error in template '{template_name}': {e}", e.lineno)

    def _get_defaults(self, template_name: str) -> Dict[str, Any]:
        """
        Get default values for optional parameters.

        Args:
            template_name: Name of the template

        Returns:
            Dictionary of default parameter values
        """
        defaults = {
            "domain_description": "a workplace review and rating web application",
            "project_name": "Software System",
            "project_description": "A system designed to help users share experiences and make informed decisions.",
            "categories_enabled": False,
            "fr_categories": [],
            "nfr_categories": [],
            "srs_version": "1.0",
            "date": "2026-04-27",
        }
        return defaults

    def get_available_templates(self) -> Dict[str, Dict[str, Any]]:
        """
        Get information about all available templates.

        Returns:
            Dictionary mapping template names to their specifications
        """
        return self.TEMPLATES.copy()

    def validate_config(self, config: Dict[str, Any]) -> tuple[bool, list[str]]:
        """
        Validate that a configuration has all required parameters for all templates.

        Args:
            config: Configuration dictionary (typically from dataset_config.yaml)

        Returns:
            Tuple of (is_valid: bool, errors: List[str])
        """
        errors = []

        # Check for required config sections
        required_sections = ["dataset_name", "llm_settings"]
        for section in required_sections:
            if section not in config:
                errors.append(f"Missing required config section: {section}")

        # Check for categories if enabled
        if config.get("categories", {}).get("enabled", False):
            categories = config.get("categories", {})
            if not categories.get("functional_requirements"):
                errors.append("Categories enabled but no functional_requirements defined")
            if not categories.get("non_functional_requirements"):
                errors.append("Categories enabled but no non_functional_requirements defined")

        return len(errors) == 0, errors

    def render_from_config(self, template_name: str, config: Dict[str, Any], **overrides) -> str:
        """
        Render a template using configuration from dataset_config.yaml.

        Args:
            template_name: Name of the template
            config: Configuration dictionary from dataset_config.yaml
            **overrides: Override specific parameters

        Returns:
            Rendered template string

        Raises:
            ValueError: If config is invalid or missing required parameters
        """
        # Validate config
        is_valid, errors = self.validate_config(config)
        if not is_valid:
            raise ValueError(f"Invalid configuration:\n" + "\n".join(errors))

        # Build parameters from config
        params = {
            "project_name": config.get("dataset_name", "Software System"),
            "srs_version": config.get("srs_metadata", {}).get("version", "1.0"),
            "date": config.get("srs_metadata", {}).get("date", "2026-04-27"),
        }

        # Add category information if enabled
        if config.get("categories", {}).get("enabled", False):
            categories = config.get("categories", {})
            params["categories_enabled"] = True
            params["fr_categories"] = categories.get("functional_requirements", [])
            params["nfr_categories"] = categories.get("non_functional_requirements", [])
        else:
            params["categories_enabled"] = False
            params["fr_categories"] = []
            params["nfr_categories"] = []

        # Apply overrides
        params.update(overrides)

        # Render template
        return self.render(template_name, **params)
