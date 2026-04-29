"""
Main entry point for mini_wiki
"""

import logging
from pathlib import Path
from typing import List, Optional

import click

from .config import get_config
from .core.data_models import Dataset, RankingResult
from .utils.logger import setup_logging


class MiniWiki:
    """Main mini_wiki application class"""

    def __init__(self, config_path: Optional[str] = None):
        """Initialize mini_wiki

        Args:
            config_path: Path to configuration file
        """
        self.config = get_config(config_path)
        self.logger = logging.getLogger(__name__)
        setup_logging(self.config.get("app.log_level", "INFO"))

        self.dataset: Optional[Dataset] = None
        self.results: Optional[RankingResult] = None

    def load_dataset(self, path: str, format: Optional[str] = None) -> Dataset:
        """Load dataset from file

        Args:
            path: Path to dataset file
            format: File format (auto-detected if not specified)

        Returns:
            Loaded dataset
        """
        self.logger.info(f"Loading dataset from {path}")
        # TODO: Implement dataset loading
        raise NotImplementedError("Dataset loading not yet implemented")

    def set_topic(self, topic: str) -> None:
        """Set research topic

        Args:
            topic: Research topic/query
        """
        self.logger.info(f"Setting research topic: {topic}")
        # TODO: Implement topic setting

    def rank(self, limit: int = 20) -> RankingResult:
        """Rank dataset content

        Args:
            limit: Maximum number of results to return

        Returns:
            Ranking results
        """
        self.logger.info(f"Ranking dataset (limit={limit})")
        # TODO: Implement ranking
        raise NotImplementedError("Ranking not yet implemented")

    def export(
        self, format: str = "csv", path: Optional[str] = None, include_reference: bool = True
    ) -> str:
        """Export results

        Args:
            format: Export format (csv, json, yaml, markdown)
            path: Output file path
            include_reference: Include AI reference in export

        Returns:
            Path to exported file
        """
        self.logger.info(f"Exporting results to {path} (format={format})")
        # TODO: Implement export
        raise NotImplementedError("Export not yet implemented")

    def run_tui(self) -> None:
        """Run interactive TUI"""
        self.logger.info("Starting TUI interface")
        # TODO: Implement TUI
        raise NotImplementedError("TUI not yet implemented")


@click.group()
@click.version_option()
def cli():
    """mini_wiki - Universal Research Assistant"""
    pass


@cli.command()
@click.argument("path", type=click.Path(exists=True))
@click.option("--format", type=str, help="File format (auto-detected if not specified)")
@click.option("--config", type=click.Path(exists=True), help="Configuration file path")
def load(path: str, format: Optional[str], config: Optional[str]):
    """Load dataset from file"""
    wiki = MiniWiki(config_path=config)
    dataset = wiki.load_dataset(path, format=format)
    click.echo(f"Loaded dataset: {dataset.name} ({len(dataset.records)} records)")


@cli.command()
@click.argument("query", type=str)
@click.option("--config", type=click.Path(exists=True), help="Configuration file path")
def topic(query: str, config: Optional[str]):
    """Set research topic"""
    wiki = MiniWiki(config_path=config)
    wiki.set_topic(query)
    click.echo(f"Research topic set to: {query}")


@cli.command()
@click.option("--limit", type=int, default=20, help="Maximum number of results")
@click.option("--format", type=str, default="table", help="Output format (table, json, yaml)")
@click.option("--config", type=click.Path(exists=True), help="Configuration file path")
def rank(limit: int, format: str, config: Optional[str]):
    """Rank dataset content"""
    wiki = MiniWiki(config_path=config)
    results = wiki.rank(limit=limit)
    click.echo(f"Ranked {len(results.results)} results")


@cli.command()
@click.argument("format", type=str)
@click.argument("output", type=click.Path())
@click.option("--include-reference", is_flag=True, help="Include AI reference")
@click.option("--config", type=click.Path(exists=True), help="Configuration file path")
def export(format: str, output: str, include_reference: bool, config: Optional[str]):
    """Export results"""
    wiki = MiniWiki(config_path=config)
    path = wiki.export(format=format, path=output, include_reference=include_reference)
    click.echo(f"Exported to: {path}")


@cli.command()
@click.option("--config", type=click.Path(exists=True), help="Configuration file path")
def tui(config: Optional[str]):
    """Run interactive TUI"""
    wiki = MiniWiki(config_path=config)
    wiki.run_tui()


if __name__ == "__main__":
    cli()
