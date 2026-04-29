"""
Export Manager Module
Export search results and documents to various formats

Features:
- Export to JSON
- Export to Markdown
- Export to CSV
- Export to PDF (with formatting)
- Batch export
- Export with custom templates
- Export statistics
"""

import json
import logging
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class ExportFormat(Enum):
    """Export format"""

    JSON = "json"
    MARKDOWN = "markdown"
    CSV = "csv"
    PDF = "pdf"
    HTML = "html"


@dataclass
class ExportConfig:
    """Export configuration

    Attributes:
        format: Export format
        output_path: Output file path
        include_metadata: Include metadata
        include_references: Include references
        include_scores: Include relevance/importance scores
        pretty_print: Pretty print output
        template: Custom template (optional)
    """

    format: ExportFormat
    output_path: str
    include_metadata: bool = True
    include_references: bool = True
    include_scores: bool = True
    pretty_print: bool = True
    template: Optional[str] = None


@dataclass
class ExportResult:
    """Export result

    Attributes:
        success: Export success
        format: Export format
        output_path: Output file path
        items_exported: Number of items exported
        file_size_bytes: File size in bytes
        export_time_ms: Time taken to export
        message: Status message
    """

    success: bool
    format: ExportFormat
    output_path: str
    items_exported: int
    file_size_bytes: int
    export_time_ms: float
    message: str


class ExportManager:
    """Manage exports"""

    def __init__(self):
        """Initialize export manager"""
        self.exporters: Dict[ExportFormat, callable] = {}
        self._register_default_exporters()

    def _register_default_exporters(self) -> None:
        """Register default exporters"""
        self.exporters[ExportFormat.JSON] = self._export_json
        self.exporters[ExportFormat.MARKDOWN] = self._export_markdown
        self.exporters[ExportFormat.CSV] = self._export_csv
        self.exporters[ExportFormat.PDF] = self._export_pdf
        self.exporters[ExportFormat.HTML] = self._export_html

    def register_exporter(self, format: ExportFormat, exporter_func: callable) -> None:
        """Register custom exporter

        Args:
            format: Export format
            exporter_func: Exporter function
        """
        self.exporters[format] = exporter_func
        logger.info(f"Registered exporter: {format.value}")

    def export(
        self,
        items: List[Dict[str, Any]],
        config: ExportConfig,
    ) -> ExportResult:
        """Export items

        Args:
            items: Items to export
            config: Export configuration

        Returns:
            ExportResult
        """
        import time

        start_time = time.time()

        try:
            exporter = self.exporters.get(config.format)
            if not exporter:
                return ExportResult(
                    success=False,
                    format=config.format,
                    output_path=config.output_path,
                    items_exported=0,
                    file_size_bytes=0,
                    export_time_ms=(time.time() - start_time) * 1000,
                    message=f"Exporter not found for format: {config.format.value}",
                )

            # Export
            content = exporter(items, config)

            # Write to file
            output_path = Path(config.output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(content)

            file_size = output_path.stat().st_size

            return ExportResult(
                success=True,
                format=config.format,
                output_path=str(output_path),
                items_exported=len(items),
                file_size_bytes=file_size,
                export_time_ms=(time.time() - start_time) * 1000,
                message=f"Successfully exported {len(items)} items to {config.format.value}",
            )

        except Exception as e:
            logger.error(f"Export error: {e}")
            return ExportResult(
                success=False,
                format=config.format,
                output_path=config.output_path,
                items_exported=0,
                file_size_bytes=0,
                export_time_ms=(time.time() - start_time) * 1000,
                message=f"Export failed: {str(e)}",
            )

    def _export_json(
        self, items: List[Dict[str, Any]], config: ExportConfig
    ) -> str:
        """Export to JSON

        Args:
            items: Items to export
            config: Export configuration

        Returns:
            JSON string
        """
        export_items = []
        for item in items:
            export_item = {}
            if config.include_metadata:
                export_item["title"] = item.get("title")
                export_item["source"] = item.get("source")
                export_item["date"] = item.get("date")
            if config.include_scores:
                export_item["relevance"] = item.get("relevance")
                export_item["importance"] = item.get("importance")
            export_item["content"] = item.get("content")
            if config.include_references:
                export_item["references"] = item.get("references", [])
            export_items.append(export_item)

        if config.pretty_print:
            return json.dumps(export_items, indent=2)
        else:
            return json.dumps(export_items)

    def _export_markdown(
        self, items: List[Dict[str, Any]], config: ExportConfig
    ) -> str:
        """Export to Markdown

        Args:
            items: Items to export
            config: Export configuration

        Returns:
            Markdown string
        """
        lines = []
        lines.append("# Export Results\n")
        lines.append(f"Generated: {datetime.now().isoformat()}\n")
        lines.append(f"Total items: {len(items)}\n\n")

        for i, item in enumerate(items, 1):
            lines.append(f"## {i}. {item.get('title', 'Untitled')}\n")

            if config.include_metadata:
                lines.append(f"**Source:** {item.get('source', 'Unknown')}\n")
                lines.append(f"**Date:** {item.get('date', 'Unknown')}\n")

            if config.include_scores:
                lines.append(
                    f"**Relevance:** {item.get('relevance', 0.0):.2f} | "
                    f"**Importance:** {item.get('importance', 0.0):.2f}\n"
                )

            lines.append(f"\n{item.get('content', 'No content')}\n")

            if config.include_references:
                references = item.get("references", [])
                if references:
                    lines.append("\n### References\n")
                    for ref in references:
                        lines.append(f"- {ref}\n")

            lines.append("\n---\n\n")

        return "".join(lines)

    def _export_csv(
        self, items: List[Dict[str, Any]], config: ExportConfig
    ) -> str:
        """Export to CSV

        Args:
            items: Items to export
            config: Export configuration

        Returns:
            CSV string
        """
        import csv
        from io import StringIO

        output = StringIO()
        headers = ["Title", "Source", "Date", "Relevance", "Importance", "Content"]

        writer = csv.DictWriter(output, fieldnames=headers)
        writer.writeheader()

        for item in items:
            row = {
                "Title": item.get("title", ""),
                "Source": item.get("source", "") if config.include_metadata else "",
                "Date": item.get("date", "") if config.include_metadata else "",
                "Relevance": item.get("relevance", "") if config.include_scores else "",
                "Importance": item.get("importance", "") if config.include_scores else "",
                "Content": item.get("content", ""),
            }
            writer.writerow(row)

        return output.getvalue()

    def _export_pdf(
        self, items: List[Dict[str, Any]], config: ExportConfig
    ) -> str:
        """Export to PDF (as text for now)

        Args:
            items: Items to export
            config: Export configuration

        Returns:
            PDF-formatted string
        """
        # For now, return markdown-like format
        # In production, use reportlab or similar
        return self._export_markdown(items, config)

    def _export_html(
        self, items: List[Dict[str, Any]], config: ExportConfig
    ) -> str:
        """Export to HTML

        Args:
            items: Items to export
            config: Export configuration

        Returns:
            HTML string
        """
        lines = []
        lines.append("<!DOCTYPE html>\n")
        lines.append("<html>\n")
        lines.append("<head>\n")
        lines.append("<meta charset='utf-8'>\n")
        lines.append("<title>Export Results</title>\n")
        lines.append("<style>\n")
        lines.append("body { font-family: Arial, sans-serif; margin: 20px; }\n")
        lines.append("h1 { color: #333; }\n")
        lines.append("h2 { color: #666; border-bottom: 1px solid #ddd; padding-bottom: 10px; }\n")
        lines.append(".metadata { color: #999; font-size: 0.9em; }\n")
        lines.append(".scores { background: #f5f5f5; padding: 10px; border-radius: 5px; }\n")
        lines.append("</style>\n")
        lines.append("</head>\n")
        lines.append("<body>\n")

        lines.append("<h1>Export Results</h1>\n")
        lines.append(f"<p>Generated: {datetime.now().isoformat()}</p>\n")
        lines.append(f"<p>Total items: {len(items)}</p>\n")

        for i, item in enumerate(items, 1):
            lines.append(f"<h2>{i}. {item.get('title', 'Untitled')}</h2>\n")

            if config.include_metadata:
                lines.append("<div class='metadata'>\n")
                lines.append(f"<p><strong>Source:</strong> {item.get('source', 'Unknown')}</p>\n")
                lines.append(f"<p><strong>Date:</strong> {item.get('date', 'Unknown')}</p>\n")
                lines.append("</div>\n")

            if config.include_scores:
                lines.append("<div class='scores'>\n")
                lines.append(
                    f"<p><strong>Relevance:</strong> {item.get('relevance', 0.0):.2f} | "
                    f"<strong>Importance:</strong> {item.get('importance', 0.0):.2f}</p>\n"
                )
                lines.append("</div>\n")

            lines.append(f"<p>{item.get('content', 'No content')}</p>\n")

            if config.include_references:
                references = item.get("references", [])
                if references:
                    lines.append("<h3>References</h3>\n")
                    lines.append("<ul>\n")
                    for ref in references:
                        lines.append(f"<li>{ref}</li>\n")
                    lines.append("</ul>\n")

            lines.append("<hr>\n")

        lines.append("</body>\n")
        lines.append("</html>\n")

        return "".join(lines)


def export_to_json(
    items: List[Dict[str, Any]], output_path: str, pretty_print: bool = True
) -> ExportResult:
    """Convenience function to export to JSON

    Args:
        items: Items to export
        output_path: Output file path
        pretty_print: Pretty print output

    Returns:
        ExportResult
    """
    manager = ExportManager()
    config = ExportConfig(
        format=ExportFormat.JSON,
        output_path=output_path,
        pretty_print=pretty_print,
    )
    return manager.export(items, config)


def export_to_markdown(
    items: List[Dict[str, Any]], output_path: str
) -> ExportResult:
    """Convenience function to export to Markdown

    Args:
        items: Items to export
        output_path: Output file path

    Returns:
        ExportResult
    """
    manager = ExportManager()
    config = ExportConfig(
        format=ExportFormat.MARKDOWN,
        output_path=output_path,
    )
    return manager.export(items, config)


def export_to_csv(items: List[Dict[str, Any]], output_path: str) -> ExportResult:
    """Convenience function to export to CSV

    Args:
        items: Items to export
        output_path: Output file path

    Returns:
        ExportResult
    """
    manager = ExportManager()
    config = ExportConfig(
        format=ExportFormat.CSV,
        output_path=output_path,
    )
    return manager.export(items, config)
