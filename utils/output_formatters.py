"""
utils/output_formatters.py
==========================
Multi-format output handling for SRE-RAG pipeline.

Supports:
  • IEEE 830 (default) — Traditional SRS format
  • IEEE 29148 — Modern requirements standard
  • JSON — Structured data export
  • CSV — Tabular requirements export
  • Excel — Multi-sheet workbook with all outputs

Usage
-----
    from utils.output_formatters import get_formatter
    
    formatter = get_formatter("ieee_830")
    formatter.format_srs(srs_dict)
    formatter.save(Path("outputs/SRS.txt"))
"""

import json
import textwrap
from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional

try:
    import pandas as pd
    HAS_PANDAS = True
except ImportError:
    HAS_PANDAS = False


# ─────────────────────────────────────────────────────────────────────────────
# Base OutputFormatter Class
# ─────────────────────────────────────────────────────────────────────────────

class OutputFormatter(ABC):
    """Base class for output formatters."""

    def __init__(self, project_name: str = "SRE-RAG Project", srs_version: str = "1.0"):
        """
        Initialize formatter.

        Args:
            project_name: Name of the project
            srs_version: SRS version number
        """
        self.project_name = project_name
        self.srs_version = srs_version
        self.timestamp = datetime.now().isoformat()
        self.output_data = {}

    @abstractmethod
    def format_requirements(self, requirements: Dict[str, Any]) -> str:
        """Format requirements section."""
        pass

    @abstractmethod
    def format_moscow(self, moscow: Dict[str, Any]) -> str:
        """Format MoSCoW prioritization section."""
        pass

    @abstractmethod
    def format_dfd(self, dfd: Dict[str, Any]) -> str:
        """Format DFD section."""
        pass

    @abstractmethod
    def format_cspec(self, cspec: Dict[str, Any]) -> str:
        """Format control specification section."""
        pass

    @abstractmethod
    def format_srs(self, srs: Dict[str, Any]) -> str:
        """Format complete SRS document."""
        pass

    @abstractmethod
    def save(self, output_path: Path) -> Path:
        """Save formatted output to file."""
        pass


# ─────────────────────────────────────────────────────────────────────────────
# IEEE 830 Formatter (Default)
# ─────────────────────────────────────────────────────────────────────────────

class IEEE830Formatter(OutputFormatter):
    """IEEE 830 Standard SRS format."""

    def format_requirements(self, requirements: Dict[str, Any]) -> str:
        """Format requirements in IEEE 830 style."""
        lines = []
        lines.append("3. REQUIREMENTS\n")

        # Functional Requirements
        lines.append("3.1 Functional Requirements\n")
        for i, req in enumerate(requirements.get("functional", []), 1):
            lines.append(f"3.1.{i} {req.get('title', 'Untitled')}")
            lines.append(f"  Description: {req.get('description', 'N/A')}")
            lines.append(f"  Priority: {req.get('priority', 'Medium')}")
            lines.append("")

        # Non-Functional Requirements
        lines.append("3.2 Non-Functional Requirements\n")
        for i, req in enumerate(requirements.get("non_functional", []), 1):
            lines.append(f"3.2.{i} {req.get('title', 'Untitled')}")
            lines.append(f"  Description: {req.get('description', 'N/A')}")
            lines.append(f"  Category: {req.get('category', 'Other')}")
            lines.append("")

        return "\n".join(lines)

    def format_moscow(self, moscow: Dict[str, Any]) -> str:
        """Format MoSCoW prioritization in IEEE 830 style."""
        lines = []
        lines.append("4. PRIORITIZATION (MoSCoW)\n")

        for category in ["must_have", "should_have", "could_have", "wont_have"]:
            cat_name = category.replace("_", " ").title()
            items = moscow.get(category, [])
            lines.append(f"4.{['must_have', 'should_have', 'could_have', 'wont_have'].index(category) + 1} {cat_name}\n")
            for item in items:
                lines.append(f"  • {item}")
            lines.append("")

        return "\n".join(lines)

    def format_dfd(self, dfd: Dict[str, Any]) -> str:
        """Format DFD in IEEE 830 style."""
        lines = []
        lines.append("5. DATA FLOW DIAGRAM (DFD) COMPONENTS\n")

        lines.append("5.1 External Entities\n")
        for entity in dfd.get("external_entities", []):
            lines.append(f"  {entity['id']}: {entity['name']}")
            lines.append(f"    Description: {entity.get('description', 'N/A')}")
        lines.append("")

        lines.append("5.2 Processes\n")
        for process in dfd.get("processes", []):
            lines.append(f"  {process['id']}: {process['name']}")
            lines.append(f"    Description: {process.get('description', 'N/A')}")
        lines.append("")

        lines.append("5.3 Data Stores\n")
        for store in dfd.get("data_stores", []):
            lines.append(f"  {store['id']}: {store['name']}")
            lines.append(f"    Description: {store.get('description', 'N/A')}")
        lines.append("")

        return "\n".join(lines)

    def format_cspec(self, cspec: Dict[str, Any]) -> str:
        """Format control specification in IEEE 830 style."""
        lines = []
        lines.append("6. CONTROL SPECIFICATION\n")

        lines.append("6.1 Activation Tables\n")
        for table in cspec.get("activation_tables", []):
            lines.append(f"  {table['process_id']}: {table['process_name']}")
            for activation in table.get("activations", []):
                lines.append(f"    • {activation.get('condition', 'N/A')} → {activation.get('trigger_type', 'N/A')}")
        lines.append("")

        lines.append("6.2 Decision Tables\n")
        for table in cspec.get("decision_tables", []):
            lines.append(f"  {table['process_id']}: {table['process_name']}")
            for rule in table.get("rules", []):
                lines.append(f"    Rule {rule.get('rule_id', 'N/A')}: {rule.get('description', 'N/A')}")
        lines.append("")

        return "\n".join(lines)

    def format_srs(self, srs: Dict[str, Any]) -> str:
        """Format complete IEEE 830 SRS document."""
        lines = []

        # Header
        lines.append("=" * 80)
        lines.append("SOFTWARE REQUIREMENTS SPECIFICATION (IEEE 830)")
        lines.append("=" * 80)
        lines.append("")

        # Title Page
        lines.append(f"Project: {self.project_name}")
        lines.append(f"Version: {self.srs_version}")
        lines.append(f"Date: {datetime.now().strftime('%Y-%m-%d')}")
        lines.append("")
        lines.append("=" * 80)
        lines.append("")

        # Table of Contents
        lines.append("TABLE OF CONTENTS\n")
        lines.append("1. Introduction")
        lines.append("2. Overall Description")
        lines.append("3. Requirements")
        lines.append("4. Prioritization (MoSCoW)")
        lines.append("5. Data Flow Diagram (DFD) Components")
        lines.append("6. Control Specification")
        lines.append("7. Appendices")
        lines.append("")
        lines.append("=" * 80)
        lines.append("")

        # Sections
        lines.append("1. INTRODUCTION\n")
        lines.append(f"This SRS document describes the requirements for {self.project_name}.")
        lines.append("")
        lines.append("=" * 80)
        lines.append("")

        lines.append("2. OVERALL DESCRIPTION\n")
        lines.append("This section provides an overview of the product.")
        lines.append("")
        lines.append("=" * 80)
        lines.append("")

        # Add formatted sections
        if "requirements" in srs:
            lines.append(self.format_requirements(srs["requirements"]))
            lines.append("=" * 80)
            lines.append("")

        if "moscow" in srs:
            lines.append(self.format_moscow(srs["moscow"]))
            lines.append("=" * 80)
            lines.append("")

        if "dfd" in srs:
            lines.append(self.format_dfd(srs["dfd"]))
            lines.append("=" * 80)
            lines.append("")

        if "cspec" in srs:
            lines.append(self.format_cspec(srs["cspec"]))
            lines.append("=" * 80)
            lines.append("")

        # Appendices
        lines.append("7. APPENDICES\n")
        lines.append("A. Document History")
        lines.append(f"  Version {self.srs_version}: {datetime.now().strftime('%Y-%m-%d')} - Initial version")
        lines.append("")

        self.output_data = "\n".join(lines)
        return self.output_data

    def save(self, output_path: Path) -> Path:
        """Save IEEE 830 SRS to text file."""
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(self.output_data, encoding="utf-8")
        return output_path


# ─────────────────────────────────────────────────────────────────────────────
# IEEE 29148 Formatter (Modern Standard)
# ─────────────────────────────────────────────────────────────────────────────

class IEEE29148Formatter(IEEE830Formatter):
    """IEEE 29148 Standard (modern requirements standard)."""

    def format_srs(self, srs: Dict[str, Any]) -> str:
        """Format complete IEEE 29148 SRS document."""
        lines = []

        # Header
        lines.append("=" * 80)
        lines.append("SYSTEM AND SOFTWARE REQUIREMENTS SPECIFICATION (IEEE 29148)")
        lines.append("=" * 80)
        lines.append("")

        # Title Page
        lines.append(f"Project: {self.project_name}")
        lines.append(f"Version: {self.srs_version}")
        lines.append(f"Date: {datetime.now().strftime('%Y-%m-%d')}")
        lines.append("")
        lines.append("=" * 80)
        lines.append("")

        # Table of Contents
        lines.append("TABLE OF CONTENTS\n")
        lines.append("1. Scope")
        lines.append("2. Normative References")
        lines.append("3. Terms, Definitions, and Abbreviated Terms")
        lines.append("4. System Overview")
        lines.append("5. System Requirements")
        lines.append("6. Traceability")
        lines.append("7. Appendices")
        lines.append("")
        lines.append("=" * 80)
        lines.append("")

        # Sections
        lines.append("1. SCOPE\n")
        lines.append(f"This specification defines the requirements for {self.project_name}.")
        lines.append("")
        lines.append("=" * 80)
        lines.append("")

        lines.append("2. NORMATIVE REFERENCES\n")
        lines.append("IEEE 29148:2018 - Systems and software engineering - Life cycle processes - Requirements engineering")
        lines.append("")
        lines.append("=" * 80)
        lines.append("")

        lines.append("3. TERMS, DEFINITIONS, AND ABBREVIATED TERMS\n")
        lines.append("See Section 7 (Appendices) for glossary.")
        lines.append("")
        lines.append("=" * 80)
        lines.append("")

        lines.append("4. SYSTEM OVERVIEW\n")
        lines.append(f"The {self.project_name} system provides the following capabilities:")
        lines.append("")
        lines.append("=" * 80)
        lines.append("")

        lines.append("5. SYSTEM REQUIREMENTS\n")
        if "requirements" in srs:
            lines.append(self.format_requirements(srs["requirements"]))
        lines.append("")
        lines.append("=" * 80)
        lines.append("")

        lines.append("6. TRACEABILITY\n")
        lines.append("Traceability matrix mapping requirements to design and test cases.")
        lines.append("")
        lines.append("=" * 80)
        lines.append("")

        # Appendices
        lines.append("7. APPENDICES\n")
        lines.append("A. Glossary")
        lines.append("B. Document History")
        lines.append(f"  Version {self.srs_version}: {datetime.now().strftime('%Y-%m-%d')} - Initial version")
        lines.append("")

        self.output_data = "\n".join(lines)
        return self.output_data


# ─────────────────────────────────────────────────────────────────────────────
# JSON Formatter
# ─────────────────────────────────────────────────────────────────────────────

class JSONFormatter(OutputFormatter):
    """JSON structured output format."""

    def format_requirements(self, requirements: Dict[str, Any]) -> str:
        """Return requirements as JSON string."""
        return json.dumps(requirements, indent=2, ensure_ascii=False)

    def format_moscow(self, moscow: Dict[str, Any]) -> str:
        """Return MoSCoW as JSON string."""
        return json.dumps(moscow, indent=2, ensure_ascii=False)

    def format_dfd(self, dfd: Dict[str, Any]) -> str:
        """Return DFD as JSON string."""
        return json.dumps(dfd, indent=2, ensure_ascii=False)

    def format_cspec(self, cspec: Dict[str, Any]) -> str:
        """Return CSPEC as JSON string."""
        return json.dumps(cspec, indent=2, ensure_ascii=False)

    def format_srs(self, srs: Dict[str, Any]) -> str:
        """Format complete SRS as JSON."""
        output = {
            "metadata": {
                "project_name": self.project_name,
                "srs_version": self.srs_version,
                "timestamp": self.timestamp,
            },
            "content": srs,
        }
        self.output_data = json.dumps(output, indent=2, ensure_ascii=False)
        return self.output_data

    def save(self, output_path: Path) -> Path:
        """Save JSON to file."""
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(self.output_data, encoding="utf-8")
        return output_path


# ─────────────────────────────────────────────────────────────────────────────
# CSV Formatter
# ─────────────────────────────────────────────────────────────────────────────

class CSVFormatter(OutputFormatter):
    """CSV tabular output format."""

    def format_requirements(self, requirements: Dict[str, Any]) -> str:
        """Format requirements as CSV."""
        if not HAS_PANDAS:
            return "ERROR: pandas not installed. Install with: pip install pandas"

        rows = []
        for req_type, reqs in requirements.items():
            for req in reqs:
                rows.append({
                    "Type": req_type.replace("_", " ").title(),
                    "Title": req.get("title", ""),
                    "Description": req.get("description", ""),
                    "Priority": req.get("priority", ""),
                    "Category": req.get("category", ""),
                })

        df = pd.DataFrame(rows)
        return df.to_csv(index=False)

    def format_moscow(self, moscow: Dict[str, Any]) -> str:
        """Format MoSCoW as CSV."""
        if not HAS_PANDAS:
            return "ERROR: pandas not installed"

        rows = []
        for category, items in moscow.items():
            for item in items:
                rows.append({
                    "Category": category.replace("_", " ").title(),
                    "Requirement": item,
                })

        df = pd.DataFrame(rows)
        return df.to_csv(index=False)

    def format_dfd(self, dfd: Dict[str, Any]) -> str:
        """Format DFD as CSV."""
        if not HAS_PANDAS:
            return "ERROR: pandas not installed"

        rows = []
        for entity in dfd.get("external_entities", []):
            rows.append({
                "Type": "External Entity",
                "ID": entity.get("id", ""),
                "Name": entity.get("name", ""),
                "Description": entity.get("description", ""),
            })

        for process in dfd.get("processes", []):
            rows.append({
                "Type": "Process",
                "ID": process.get("id", ""),
                "Name": process.get("name", ""),
                "Description": process.get("description", ""),
            })

        df = pd.DataFrame(rows)
        return df.to_csv(index=False)

    def format_cspec(self, cspec: Dict[str, Any]) -> str:
        """Format CSPEC as CSV."""
        if not HAS_PANDAS:
            return "ERROR: pandas not installed"

        rows = []
        for table in cspec.get("activation_tables", []):
            for activation in table.get("activations", []):
                rows.append({
                    "Type": "Activation",
                    "Process": table.get("process_id", ""),
                    "Condition": activation.get("condition", ""),
                    "Trigger": activation.get("trigger_type", ""),
                })

        df = pd.DataFrame(rows)
        return df.to_csv(index=False)

    def format_srs(self, srs: Dict[str, Any]) -> str:
        """Format complete SRS as CSV (requirements only)."""
        if "requirements" in srs:
            return self.format_requirements(srs["requirements"])
        return "No requirements found"

    def save(self, output_path: Path) -> Path:
        """Save CSV to file."""
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(self.output_data, encoding="utf-8")
        return output_path


# ─────────────────────────────────────────────────────────────────────────────
# Excel Formatter
# ─────────────────────────────────────────────────────────────────────────────

class ExcelFormatter(OutputFormatter):
    """Excel multi-sheet workbook format."""

    def format_requirements(self, requirements: Dict[str, Any]) -> str:
        """Format requirements (for Excel, we'll handle in save())."""
        return json.dumps(requirements, indent=2, ensure_ascii=False)

    def format_moscow(self, moscow: Dict[str, Any]) -> str:
        """Format MoSCoW (for Excel, we'll handle in save())."""
        return json.dumps(moscow, indent=2, ensure_ascii=False)

    def format_dfd(self, dfd: Dict[str, Any]) -> str:
        """Format DFD (for Excel, we'll handle in save())."""
        return json.dumps(dfd, indent=2, ensure_ascii=False)

    def format_cspec(self, cspec: Dict[str, Any]) -> str:
        """Format CSPEC (for Excel, we'll handle in save())."""
        return json.dumps(cspec, indent=2, ensure_ascii=False)

    def format_srs(self, srs: Dict[str, Any]) -> str:
        """Format complete SRS (store for Excel export)."""
        self.output_data = srs
        return json.dumps(srs, indent=2, ensure_ascii=False)

    def save(self, output_path: Path) -> Path:
        """Save multi-sheet Excel workbook."""
        if not HAS_PANDAS:
            raise ImportError("pandas is required for Excel export. Install with: pip install pandas openpyxl")

        output_path.parent.mkdir(parents=True, exist_ok=True)

        with pd.ExcelWriter(output_path, engine="openpyxl") as writer:
            # Requirements sheet
            if isinstance(self.output_data, dict) and "requirements" in self.output_data:
                reqs = self.output_data["requirements"]
                rows = []
                for req_type, req_list in reqs.items():
                    for req in req_list:
                        rows.append({
                            "Type": req_type.replace("_", " ").title(),
                            "Title": req.get("title", ""),
                            "Description": req.get("description", ""),
                            "Priority": req.get("priority", ""),
                        })
                if rows:
                    pd.DataFrame(rows).to_excel(writer, sheet_name="Requirements", index=False)

            # MoSCoW sheet
            if isinstance(self.output_data, dict) and "moscow" in self.output_data:
                moscow = self.output_data["moscow"]
                rows = []
                for category, items in moscow.items():
                    for item in items:
                        rows.append({
                            "Category": category.replace("_", " ").title(),
                            "Requirement": item,
                        })
                if rows:
                    pd.DataFrame(rows).to_excel(writer, sheet_name="MoSCoW", index=False)

            # DFD sheet
            if isinstance(self.output_data, dict) and "dfd" in self.output_data:
                dfd = self.output_data["dfd"]
                rows = []
                for entity in dfd.get("external_entities", []):
                    rows.append({
                        "Type": "Entity",
                        "ID": entity.get("id", ""),
                        "Name": entity.get("name", ""),
                    })
                for process in dfd.get("processes", []):
                    rows.append({
                        "Type": "Process",
                        "ID": process.get("id", ""),
                        "Name": process.get("name", ""),
                    })
                if rows:
                    pd.DataFrame(rows).to_excel(writer, sheet_name="DFD", index=False)

            # Summary sheet
            summary_rows = [
                {"Field": "Project Name", "Value": self.project_name},
                {"Field": "SRS Version", "Value": self.srs_version},
                {"Field": "Generated", "Value": datetime.now().strftime("%Y-%m-%d %H:%M:%S")},
            ]
            pd.DataFrame(summary_rows).to_excel(writer, sheet_name="Summary", index=False)

        return output_path


# ─────────────────────────────────────────────────────────────────────────────
# Helper Functions
# ─────────────────────────────────────────────────────────────────────────────

def get_formatter(format_name: str, project_name: str = "SRE-RAG Project", srs_version: str = "1.0") -> OutputFormatter:
    """
    Get formatter instance by name.

    Args:
        format_name: Format name (ieee_830, ieee_29148, json, csv, excel)
        project_name: Project name for SRS header
        srs_version: SRS version number

    Returns:
        OutputFormatter instance

    Raises:
        ValueError: If format_name is not recognized
    """
    formatters = {
        "ieee_830": IEEE830Formatter,
        "ieee_29148": IEEE29148Formatter,
        "json": JSONFormatter,
        "csv": CSVFormatter,
        "excel": ExcelFormatter,
    }

    if format_name not in formatters:
        raise ValueError(f"Unknown format: {format_name}. Available: {list(formatters.keys())}")

    return formatters[format_name](project_name=project_name, srs_version=srs_version)


def list_formats() -> List[str]:
    """List available output formats."""
    return ["ieee_830", "ieee_29148", "json", "csv", "excel"]
