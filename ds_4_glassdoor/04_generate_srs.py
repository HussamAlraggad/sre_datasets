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

    # SRS document (already Markdown from chain 5)
    srs_text = results["srs_markdown"]
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
