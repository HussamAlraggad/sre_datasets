"""
04_generate_srs.py
==================
Pipeline Stage 4 — Orchestrator

Ties together all pipeline stages:
  1. Load FAISS retriever (02_retriever.py)
  2. Retrieve top-k reviews for the query
  3. Run all 5 LangChain chains (03_chains.py)
  4. Write output files to outputs/

Output files produced
---------------------
  outputs/requirements.json    — FR + NFR list
  outputs/moscow.json          — MoSCoW prioritization table
  outputs/dfd_components.json  — DFD entities, processes, stores, flows
  outputs/cspec_tables.json    — Activation + Decision tables (raw JSON)
  outputs/cspec_tables.md      — CSPEC tables formatted as Markdown
  outputs/SRS.md               — Full IEEE 830 SRS document

Usage
-----
    python 04_generate_srs.py
    python 04_generate_srs.py --query "What salary features do users want?"
    python 04_generate_srs.py --k 30 --query "remote work and flexibility features"
    python 04_generate_srs.py --skip-retrieval  # re-run chains on existing reviews.json
"""

import argparse
import json
import sys
import textwrap
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from config import (
    DEFAULT_QUERY,
    RETRIEVER_K,
    OUTPUTS_DIR,
    SRS_PROJECT_NAME,
    SRS_VERSION,
)


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def _save_json(data: dict | list, filename: str):
    OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)
    path = OUTPUTS_DIR / filename
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"  [SAVED] {path}")
    return path


def _save_text(text: str, filename: str):
    OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)
    path = OUTPUTS_DIR / filename
    path.write_text(text, encoding="utf-8")
    print(f"  [SAVED] {path}")
    return path


def _cspec_to_markdown(cspec: dict) -> str:
    """Render the CSPEC JSON into human-readable Markdown tables."""
    lines = ["# CSPEC — Control Specification\n"]

    # ── Activation Tables ─────────────────────────────────────────────────────
    lines.append("## Activation Tables\n")
    for at in cspec.get("activation_tables", []):
        lines.append(f"### {at['process_id']}: {at['process_name']}\n")
        lines.append("| Condition | Trigger Type | Description |")
        lines.append("|---|---|---|")
        for a in at.get("activations", []):
            cond    = a.get("condition", "").replace("|", "\\|")
            ttype   = a.get("trigger_type", "").replace("|", "\\|")
            desc    = a.get("description", "").replace("|", "\\|")
            lines.append(f"| {cond} | {ttype} | {desc} |")
        lines.append("")

    # ── Decision Tables ───────────────────────────────────────────────────────
    lines.append("## Decision Tables\n")
    for dt in cspec.get("decision_tables", []):
        lines.append(f"### {dt['process_id']}: {dt['process_name']}\n")
        conditions = dt.get("conditions", [])
        actions    = dt.get("actions",    [])
        rules      = dt.get("rules",      [])

        if not rules:
            lines.append("_No rules defined._\n")
            continue

        rule_ids = [r["rule_id"] for r in rules]

        # Header row: empty label col + one col per rule
        header  = "| |" + "|".join(rule_ids) + "|"
        divider = "|---|" + "|".join(["---"] * len(rule_ids)) + "|"
        lines.append(header)
        lines.append(divider)

        # Condition rows
        for i, cond in enumerate(conditions):
            vals = [r["condition_values"][i] if i < len(r["condition_values"]) else "-"
                    for r in rules]
            lines.append(f"| **{cond}** |" + "|".join(vals) + "|")

        # Separator between conditions and actions
        lines.append("|" + "---|" * (len(rule_ids) + 1))

        # Action rows
        for j, action in enumerate(actions):
            vals = [r["action_values"][j] if j < len(r["action_values"]) else "-"
                    for r in rules]
            lines.append(f"| _{action}_ |" + "|".join(vals) + "|")

        lines.append("")

    return "\n".join(lines)


def _dfd_to_markdown(dfd: dict) -> str:
    """Render DFD JSON as a readable Markdown summary."""
    lines = ["# DFD Level-1 Components\n"]

    lines.append("## External Entities\n")
    lines.append("| ID | Name | Description | Sends | Receives |")
    lines.append("|---|---|---|---|---|")
    for e in dfd.get("external_entities", []):
        sends    = ", ".join(e.get("sends", []))
        receives = ", ".join(e.get("receives", []))
        lines.append(f"| {e['id']} | {e['name']} | {e.get('description','')} | {sends} | {receives} |")
    lines.append("")

    lines.append("## Processes\n")
    lines.append("| ID | Name | Description | Inputs | Outputs |")
    lines.append("|---|---|---|---|---|")
    for p in dfd.get("processes", []):
        ins  = ", ".join(p.get("inputs", []))
        outs = ", ".join(p.get("outputs", []))
        lines.append(f"| {p['id']} | {p['name']} | {p.get('description','')} | {ins} | {outs} |")
    lines.append("")

    lines.append("## Data Stores\n")
    lines.append("| ID | Name | Description | Read By | Written By |")
    lines.append("|---|---|---|---|---|")
    for d in dfd.get("data_stores", []):
        rb = ", ".join(d.get("read_by",    []))
        wb = ", ".join(d.get("written_by", []))
        lines.append(f"| {d['id']} | {d['name']} | {d.get('description','')} | {rb} | {wb} |")
    lines.append("")

    lines.append("## Data Flows\n")
    lines.append("| Name | From | To | Description |")
    lines.append("|---|---|---|---|")
    for f in dfd.get("data_flows", []):
        lines.append(
            f"| {f['name']} | {f['from']} | {f['to']} | {f.get('description','')} |"
        )
    lines.append("")

    return "\n".join(lines)


def _patch_srs(srs_text: str, requirements: dict, moscow: dict, dfd: dict) -> str:
    """
    Post-process the LLM-generated SRS to fix predictable quality issues:

    1. Strip any trailing LLM commentary after the last '|' table row.
    2. Remove spurious extra sections the LLM tends to hallucinate
       (5.2 Glossary, 5.3 Acronyms, 5.4 References, standalone "None" lines).
    3. If Section 5.2 Traceability Matrix is absent, append it deterministically
       from the requirements, moscow, and dfd JSON data.
    4. Ensure Section 1.3 has actual terms, not just "None".
    """
    import re

    lines = srs_text.splitlines()

    # ── 1. Strip trailing commentary after the last table row ─────────────────
    last_table_line = max(
        (i for i, ln in enumerate(lines) if ln.strip().startswith("|") and ln.strip().endswith("|")),
        default=len(lines) - 1,
    )
    lines = lines[:last_table_line + 1]

    # ── 2. Remove spurious extra sections the LLM hallucinates ────────────────
    spurious_headings = re.compile(
        r"^###\s+(5\.[3-9]|Glossary|Acronyms?|Abbreviations?|References?)",
        re.IGNORECASE,
    )
    filtered: list[str] = []
    skip_until_heading = False
    for ln in lines:
        if spurious_headings.match(ln):
            skip_until_heading = True
            continue
        if skip_until_heading:
            if ln.startswith("#"):
                skip_until_heading = False
            else:
                continue
        filtered.append(ln)
    lines = filtered

    # ── 3. Fix Section 1.3 if it only says "None" ─────────────────────────────
    result: list[str] = []
    i = 0
    while i < len(lines):
        result.append(lines[i])
        if lines[i].strip() == "### 1.3 Definitions, Acronyms, and Abbreviations":
            # Check if next non-empty line is just "None"
            j = i + 1
            while j < len(lines) and lines[j].strip() == "":
                j += 1
            if j < len(lines) and lines[j].strip().lower() == "none":
                # Replace with a proper definitions table
                result.append("")
                result.append("| Term | Definition |")
                result.append("|---|---|")
                result.append("| **FR** | Functional Requirement — what the system must do |")
                result.append("| **NFR** | Non-Functional Requirement — how well the system must do it |")
                result.append("| **MoSCoW** | Must / Should / Could / Won't — requirement prioritization framework |")
                result.append("| **DFD** | Data Flow Diagram — graphical model of data movement |")
                result.append("| **CSPEC** | Control Specification — process activation and decision logic |")
                result.append("| **SRS** | Software Requirements Specification |")
                result.append("| **IEEE 830** | IEEE standard for SRS document structure |")
                i = j + 1  # skip the "None" line
                continue
        i += 1
    lines = result

    srs_text = "\n".join(lines)

    # ── 4. Replace Section 3 with a deterministic render from JSON ────────────
    # Build MoSCoW lookup: id → {moscow, justification}
    _moscow_detail: dict = {}
    for item in moscow.get("moscow_prioritization", []):
        _moscow_detail[item["id"]] = {
            "moscow":        item.get("moscow", "—"),
            "justification": item.get("justification", ""),
        }

    # Build Section 3 text
    sec3_lines = [
        "## 3. Specific Requirements",
        "### 3.1 Functional Requirements",
    ]
    for req in requirements.get("functional_requirements", []):
        rid  = req["id"]
        cat  = req.get("category", rid)
        stmt = req.get("statement", "")
        src  = req.get("source", "")
        rat  = req.get("rationale", "")
        mos  = _moscow_detail.get(rid, {})
        prio = mos.get("moscow", "—")
        just = mos.get("justification", "")
        sec3_lines += [
            f"#### {rid}: {cat}",
            stmt,
            "",
            f"* MoSCoW Priority: {prio}",
            f"* Justification: {just}",
            f"* Source: {src}",
            f"* Rationale: {rat}",
            "",
        ]

    sec3_lines.append("### 3.2 Non-Functional Requirements")
    for req in requirements.get("non_functional_requirements", []):
        rid  = req["id"]
        cat  = req.get("category", rid)
        stmt = req.get("statement", "")
        src  = req.get("source", "")
        rat  = req.get("rationale", "")
        mos  = _moscow_detail.get(rid, {})
        prio = mos.get("moscow", "—")
        just = mos.get("justification", "")
        sec3_lines += [
            f"#### {rid}: {cat}",
            stmt,
            "",
            f"* MoSCoW Priority: {prio}",
            f"* Justification: {just}",
            f"* Source: {src}",
            f"* Rationale: {rat}",
            "",
        ]

    new_section_3 = "\n".join(sec3_lines)

    # Strip whatever Section 3 the LLM wrote and replace with ours
    srs_text = re.sub(
        r"## 3\. Specific Requirements.*?(## 4\.)",
        new_section_3 + "\n\n" + r"\1",
        srs_text,
        count=1,
        flags=re.DOTALL,
    )

    # ── 5. Replace Section 5.1 MoSCoW Summary Table deterministically ───────────
    _moscow_summary_rows = []
    for req in requirements.get("functional_requirements", []) + requirements.get("non_functional_requirements", []):
        rid  = req["id"]
        stmt = req.get("statement", "")
        mos  = _moscow_detail.get(rid, {})
        prio = mos.get("moscow", "—")
        just = mos.get("justification", "")
        _moscow_summary_rows.append(f"| {rid} | {stmt} | {prio} | {just} |")

    new_51 = (
        "### 5.1 MoSCoW Summary Table\n\n"
        "| ID | Statement | MoSCoW Priority | Justification |\n"
        "|---|---|---|---|\n"
    ) + "\n".join(_moscow_summary_rows)

    srs_text = re.sub(
        r"### 5\.1 MoSCoW Summary Table.*?(### 5\.2)",
        new_51 + "\n\n" + r"\1",
        srs_text,
        count=1,
        flags=re.DOTALL,
    )

    # ── 6. Append Traceability Matrix if missing ──────────────────────────────
    has_traceability = bool(re.search(r"###\s+5\.2\s+Traceability", srs_text, re.IGNORECASE))
    if not has_traceability:
        # Build a lookup: id → moscow priority
        moscow_map: dict[str, str] = {}
        for item in moscow.get("moscow_prioritization", []):
            moscow_map[item["id"]] = item.get("moscow", "—")

        # Build a lookup: requirement_id → statement (first 60 chars)
        req_map: dict[str, str] = {}
        for req in requirements.get("functional_requirements", []) + requirements.get("non_functional_requirements", []):
            stmt = req.get("statement", "")
            req_map[req["id"]] = stmt[:60] + ("…" if len(stmt) > 60 else "")

        # Build a simple process-to-requirement mapping from DFD
        # Map each FR/NFR to processes based on keyword overlap
        processes = dfd.get("processes", [])
        process_ids = [p["id"] for p in processes]

        def _map_req_to_processes(req_id: str) -> str:
            """Heuristic: assign processes based on FR category."""
            category_map = {
                "Authentication": ["P1"],
                "Profile":        ["P1", "P2"],
                "Review":         ["P2"],
                "Search":         ["P3"],
                "Analytics":      ["P4"],
                "Notification":   ["P5"],
                "Admin":          ["P6", "P7"],
                "Moderation":     ["P6"],
                "Integration":    ["P7"],
                "Reliability":    process_ids[:3],
                "Performance":    process_ids[:3],
                "Security":       process_ids[:3],
                "Usability":      process_ids[:3],
                "Scalability":    process_ids[:3],
                "Privacy":        process_ids[:2],
            }
            # Look up category from requirements JSON
            for req in requirements.get("functional_requirements", []) + requirements.get("non_functional_requirements", []):
                if req["id"] == req_id:
                    cat = req.get("category", "")
                    mapped = category_map.get(cat, process_ids[:2] if process_ids else ["P1"])
                    # Filter to only IDs that actually exist in this run's DFD
                    valid = [pid for pid in mapped if pid in process_ids]
                    return ", ".join(valid) if valid else (process_ids[0] if process_ids else "P1")
            return process_ids[0] if process_ids else "P1"

        rows = []
        all_reqs = (
            requirements.get("functional_requirements", []) +
            requirements.get("non_functional_requirements", [])
        )
        for req in all_reqs:
            rid   = req["id"]
            stmt  = req_map.get(rid, "")
            procs = _map_req_to_processes(rid)
            prio  = moscow_map.get(rid, "—")
            rows.append(f"| {rid} | {stmt} | {procs} | {prio} |")

        traceability_section = (
            "\n\n### 5.2 Traceability Matrix\n\n"
            "| FR/NFR ID | Statement (truncated) | DFD Process IDs | MoSCoW |\n"
            "|---|---|---|---|\n"
        ) + "\n".join(rows)

        srs_text += traceability_section

    return srs_text


def _print_banner(title: str):
    width = 70
    print("\n" + "=" * width)
    print(f"  {title}")
    print("=" * width + "\n")


# ─────────────────────────────────────────────────────────────────────────────
# Main orchestrator
# ─────────────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Glassdoor RAG — SRS Generator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=textwrap.dedent("""
            Examples:
              python 04_generate_srs.py
              python 04_generate_srs.py --query "salary transparency features"
              python 04_generate_srs.py --k 30
              python 04_generate_srs.py --skip-retrieval
        """),
    )
    parser.add_argument(
        "--query", "-q",
        default=DEFAULT_QUERY,
        help="Search query for FAISS retrieval (default: from config.py)",
    )
    parser.add_argument(
        "--k", "-k",
        type=int,
        default=RETRIEVER_K,
        help=f"Number of reviews to retrieve (default: {RETRIEVER_K})",
    )
    parser.add_argument(
        "--skip-retrieval",
        action="store_true",
        help="Skip retrieval; reuse outputs/retrieved_reviews.json if it exists",
    )
    args = parser.parse_args()

    start_time = datetime.now()
    _print_banner(f"Glassdoor RAG — SRS Generator  |  {start_time.strftime('%Y-%m-%d %H:%M')}")

    # ── Step 1: Retrieve reviews ──────────────────────────────────────────────
    retrieved_path = OUTPUTS_DIR / "retrieved_reviews.json"

    if args.skip_retrieval and retrieved_path.exists():
        print(f"[SKIP] Using cached reviews from {retrieved_path}")
        with open(retrieved_path) as f:
            reviews = json.load(f)
        print(f"       Loaded {len(reviews)} reviews.")
    else:
        print(f"[STEP 1/5] Retrieving top-{args.k} reviews for query:")
        print(f"           \"{args.query}\"\n")

        import sys as _sys
        FAISSRetriever = _sys.modules["retriever_module"].FAISSRetriever
        retriever = FAISSRetriever(k=args.k)
        reviews   = retriever.retrieve_texts(args.query)

        _save_json(reviews, "retrieved_reviews.json")
        print(f"       Retrieved {len(reviews)} reviews.\n")

    # ── Step 2–6: Run all 5 chains ────────────────────────────────────────────
    print("[STEP 2/5] Running LangChain chains against Ollama …\n")

    import sys as _sys
    run_all_chains = _sys.modules["chains_module"].run_all_chains
    results = run_all_chains(reviews)

    # ── Step 3: Save all outputs ──────────────────────────────────────────────
    _print_banner("Saving output files")

    _save_json(results["requirements"], "requirements.json")
    _save_json(results["moscow"],       "moscow.json")
    _save_json(results["dfd"],          "dfd_components.json")
    _save_json(results["cspec"],        "cspec_tables.json")

    # Render human-readable Markdown artefacts
    cspec_md = _cspec_to_markdown(results["cspec"])
    _save_text(cspec_md, "cspec_tables.md")

    dfd_md = _dfd_to_markdown(results["dfd"])
    _save_text(dfd_md, "dfd_components.md")

    # SRS document (already Markdown from chain 5) — apply post-processing
    srs_text = results["srs_markdown"]
    srs_text = _patch_srs(srs_text, results["requirements"], results["moscow"], results["dfd"])
    _save_text(srs_text, "SRS.md")

    # ── Done ──────────────────────────────────────────────────────────────────
    elapsed = (datetime.now() - start_time).total_seconds()
    _print_banner(f"All done!  Total time: {elapsed:.1f}s")

    print("Output files:")
    for fname in [
        "retrieved_reviews.json",
        "requirements.json",
        "moscow.json",
        "dfd_components.json",
        "dfd_components.md",
        "cspec_tables.json",
        "cspec_tables.md",
        "SRS.md",
    ]:
        p = OUTPUTS_DIR / fname
        size = p.stat().st_size if p.exists() else 0
        print(f"  {p}  ({size:,} bytes)")

    print(f"\nSRS document: {OUTPUTS_DIR / 'SRS.md'}\n")


# ─────────────────────────────────────────────────────────────────────────────
# Fix dynamic import — simpler approach
# ─────────────────────────────────────────────────────────────────────────────

def _load_module(name: str, file_path: Path):
    import importlib.util
    import types
    spec = importlib.util.spec_from_file_location(name, file_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load module from {file_path}")
    mod = types.ModuleType(name)
    mod.__file__ = str(file_path)
    spec.loader.exec_module(mod)
    return mod


if __name__ == "__main__":
    # Patch the dynamic imports to use file-relative loading
    _base = Path(__file__).parent

    _retriever_mod = _load_module("retriever_module", _base / "02_retriever.py")
    _chains_mod    = _load_module("chains_module",    _base / "03_chains.py")

    # Inject into namespace so main() can find them
    import builtins as _builtins
    _builtins.__dict__["FAISSRetriever"] = _retriever_mod.FAISSRetriever
    _builtins.__dict__["run_all_chains"] = _chains_mod.run_all_chains

    # Monkey-patch main's local import to use pre-loaded modules
    import sys as _sys
    _sys.modules["retriever_module"] = _retriever_mod
    _sys.modules["chains_module"]    = _chains_mod

    main()
