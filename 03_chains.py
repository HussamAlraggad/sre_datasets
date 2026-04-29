"""
03_chains.py
============
Pipeline Stage 3 — LangChain Chains

Defines five sequential LangChain chains, each backed by a dedicated
prompt template and the Ollama LLM (llama3:8b).

Chains
------
1. fr_nfr_chain       — Extract Functional & Non-Functional Requirements from reviews
2. moscow_chain       — Apply MoSCoW prioritization to the extracted requirements
3. dfd_chain          — Identify DFD Level-1 components (entities, processes, stores, flows)
4. cspec_chain        — Build Activation Tables + Decision Tables (CSPEC)
5. srs_chain          — Format everything into an IEEE 830 SRS document

Each chain is a plain function that accepts string inputs and returns a string.
Chains 2–5 receive the JSON output of the previous chain as input, forming a
linear processing pipeline.

All prompt templates are loaded via PromptLoader from Jinja2 templates in
prompts/templates/. Templates are parameterized with custom categories,
domain descriptions, and project names from dataset_config.yaml.

Dependencies
------------
    pip install langchain langchain-ollama langchain-community tqdm
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from config import (
    OLLAMA_MODEL,
    OLLAMA_BASE_URL,
    LLM_TEMPERATURE,
    LLM_NUM_CTX,
    LLM_NUM_PREDICT,
    PROMPTS_DIR,
    SRS_PROJECT_NAME,
    SRS_VERSION,
    SRS_STANDARD,
)
from utils import PromptLoader, ConfigValidator


# ─────────────────────────────────────────────────────────────────────────────
# Lazy imports
# ─────────────────────────────────────────────────────────────────────────────

def _get_llm():
    """Return a configured ChatOllama instance."""
    try:
        from langchain_ollama import ChatOllama
    except ImportError:
        try:
            from langchain_community.chat_models import ChatOllama
        except ImportError:
            print("[ERROR] langchain-ollama / langchain-community not installed.")
            print("  Run:  pip install langchain-ollama langchain-community")
            sys.exit(1)

    return ChatOllama(
        model=OLLAMA_MODEL,
        base_url=OLLAMA_BASE_URL,
        temperature=LLM_TEMPERATURE,
        num_ctx=LLM_NUM_CTX,
        num_predict=LLM_NUM_PREDICT,
    )


# ─────────────────────────────────────────────────────────────────────────────
# Prompt loader initialization
# ─────────────────────────────────────────────────────────────────────────────

def _load_config() -> dict:
    """Load dataset_config.yaml or use defaults."""
    config_path = Path("dataset_config.yaml")
    if config_path.exists():
        try:
            return ConfigValidator.load_config(config_path)
        except Exception as e:
            print(f"[WARN] Failed to load config: {e}")
            return {}
    return {}


# Initialize PromptLoader and load config
_prompt_loader = PromptLoader()
_config = _load_config()

# Get configuration parameters for template rendering
_domain_description = _config.get("srs_metadata", {}).get("domain_description", "")
_project_name = _config.get("srs_metadata", {}).get("project_name", SRS_PROJECT_NAME)
_categories_enabled = _config.get("categories", {}).get("enabled", False)
_fr_categories = _config.get("categories", {}).get("functional_requirements", [])
_nfr_categories = _config.get("categories", {}).get("non_functional_requirements", [])


# ─────────────────────────────────────────────────────────────────────────────
# JSON safety helper
# ─────────────────────────────────────────────────────────────────────────────

def _safe_json(raw: str, chain_name: str) -> dict:
    """
    Try to parse `raw` as JSON.
    Handles three common LLM output patterns:
      1. JSON wrapped in ```json ... ``` markdown fences
      2. Natural-language preamble before the JSON object/array
      3. Extra text / a second JSON block appended after the first object
         (json.JSONDecoder.raw_decode stops after the first complete value)
    Returns the parsed dict/list, or a dict with an 'error' key on failure.
    """
    text = raw.strip()

    # Strip ```json ... ``` or ``` ... ``` wrappers
    if text.startswith("```"):
        lines = text.splitlines()
        # drop first line (```json or ```) and last line (```)
        text = "\n".join(lines[1:-1]).strip()

    # Find the first JSON object { or array [
    first_brace = min(
        (text.find("{") if text.find("{") != -1 else len(text)),
        (text.find("[") if text.find("[") != -1 else len(text)),
    )
    text = text[first_brace:]

    try:
        # raw_decode stops after the first complete JSON value, ignoring
        # any trailing text or a second JSON block the LLM may have appended
        obj, _ = json.JSONDecoder().raw_decode(text)
        return obj
    except json.JSONDecodeError as exc:
        print(f"[WARN] {chain_name} returned non-JSON output: {exc}")
        return {"error": str(exc), "raw_output": raw}


# ─────────────────────────────────────────────────────────────────────────────
# Chain 1 — FR / NFR Extraction
# ─────────────────────────────────────────────────────────────────────────────

def run_fr_nfr_chain(reviews: list[str], llm=None) -> dict:
    """
    Input : list of raw review strings (from FAISS retrieval)
    Output: dict with keys 'functional_requirements' and
            'non_functional_requirements'
    """
    if llm is None:
        llm = _get_llm()

    reviews_text = "\n\n---\n\n".join(
        f"[Review {i+1}]\n{r}" for i, r in enumerate(reviews)
    )
    
    # Render template with configuration parameters
    prompt = _prompt_loader.render(
        "fr_nfr_extraction",
        reviews=reviews_text,
        domain_description=_domain_description,
        project_name=_project_name,
        categories_enabled=_categories_enabled,
        fr_categories=_fr_categories,
        nfr_categories=_nfr_categories,
    )

    print("[Chain 1/5] FR/NFR extraction …", flush=True)
    response = llm.invoke(prompt)
    raw      = response.content if hasattr(response, "content") else str(response)
    result   = _safe_json(raw, "FR/NFR chain")

    n_fr  = len(result.get("functional_requirements", []))
    n_nfr = len(result.get("non_functional_requirements", []))
    print(f"            → {n_fr} FRs, {n_nfr} NFRs extracted.")
    return result


# ─────────────────────────────────────────────────────────────────────────────
# Chain 2 — MoSCoW Prioritization
# ─────────────────────────────────────────────────────────────────────────────

def run_moscow_chain(requirements: dict, llm=None) -> dict:
    """
    Input : dict from run_fr_nfr_chain
    Output: dict with key 'moscow_prioritization' and 'summary'
    """
    if llm is None:
        llm = _get_llm()

    requirements_json = json.dumps(requirements, indent=2, ensure_ascii=False)
    
    # Render template with configuration parameters
    prompt = _prompt_loader.render(
        "moscow_prioritization",
        requirements_json=requirements_json,
        project_name=_project_name,
    )

    print("[Chain 2/5] MoSCoW prioritization …", flush=True)
    response = llm.invoke(prompt)
    raw      = response.content if hasattr(response, "content") else str(response)
    result   = _safe_json(raw, "MoSCoW chain")

    summary = result.get("summary", {})
    print(
        f"            → MUST:{summary.get('must_count','?')}  "
        f"SHOULD:{summary.get('should_count','?')}  "
        f"COULD:{summary.get('could_count','?')}  "
        f"WON'T:{summary.get('wont_count','?')}"
    )
    return result


# ─────────────────────────────────────────────────────────────────────────────
# Chain 3 — DFD Component Identification
# ─────────────────────────────────────────────────────────────────────────────

def run_dfd_chain(requirements: dict, llm=None) -> dict:
    """
    Input : dict from run_fr_nfr_chain
    Output: dict with keys 'external_entities', 'processes',
            'data_stores', 'data_flows'
    """
    if llm is None:
        llm = _get_llm()

    requirements_json = json.dumps(requirements, indent=2, ensure_ascii=False)
    
    # Render template with configuration parameters
    prompt = _prompt_loader.render(
        "dfd_components",
        requirements_json=requirements_json,
        project_name=_project_name,
    )

    print("[Chain 3/5] DFD component identification …", flush=True)
    response = llm.invoke(prompt)
    raw      = response.content if hasattr(response, "content") else str(response)
    result   = _safe_json(raw, "DFD chain")

    print(
        f"            → "
        f"{len(result.get('external_entities', []))} entities, "
        f"{len(result.get('processes', []))} processes, "
        f"{len(result.get('data_stores', []))} stores, "
        f"{len(result.get('data_flows', []))} flows."
    )
    return result


# ─────────────────────────────────────────────────────────────────────────────
# Chain 4 — CSPEC Logic (Activation + Decision Tables)
# ─────────────────────────────────────────────────────────────────────────────

def run_cspec_chain(dfd: dict, llm=None) -> dict:
    """
    Input : dict from run_dfd_chain
    Output: dict with keys 'activation_tables' and 'decision_tables'
    """
    if llm is None:
        llm = _get_llm()

    dfd_json = json.dumps(dfd, indent=2, ensure_ascii=False)
    
    # Render template with configuration parameters
    prompt = _prompt_loader.render(
        "cspec_logic",
        dfd_json=dfd_json,
        project_name=_project_name,
    )

    print("[Chain 4/5] CSPEC logic extraction …", flush=True)
    response = llm.invoke(prompt)
    raw      = response.content if hasattr(response, "content") else str(response)
    result   = _safe_json(raw, "CSPEC chain")

    print(
        f"            → "
        f"{len(result.get('activation_tables', []))} activation tables, "
        f"{len(result.get('decision_tables', []))} decision tables."
    )
    return result


# ─────────────────────────────────────────────────────────────────────────────
# Chain 5 — SRS Formatter (IEEE 830)
# ─────────────────────────────────────────────────────────────────────────────

def run_srs_chain(
    requirements: dict,
    moscow: dict,
    dfd: dict,
    llm=None,
) -> str:
    """
    Input : all previous chain outputs
    Output: full SRS document as a Markdown string
    """
    from datetime import date as _date

    if llm is None:
        llm = _get_llm()

    # Render template with configuration parameters
    prompt = _prompt_loader.render(
        "srs_formatter",
        requirements_json=json.dumps(requirements, indent=2, ensure_ascii=False),
        moscow_json=json.dumps(moscow, indent=2, ensure_ascii=False),
        dfd_json=json.dumps(dfd, indent=2, ensure_ascii=False),
        project_name=_project_name,
        srs_version=SRS_VERSION,
        date=_date.today().isoformat(),
    )

    print("[Chain 5/5] SRS document formatting …", flush=True)
    response = llm.invoke(prompt)
    raw      = response.content if hasattr(response, "content") else str(response)

    # Strip any conversational preamble before the first Markdown heading
    heading_pos = raw.find("#")
    if heading_pos > 0:
        raw = raw[heading_pos:]

    print(f"            → SRS document: {len(raw):,} characters.")
    return raw


# ─────────────────────────────────────────────────────────────────────────────
# Convenience: run all chains in sequence, sharing one LLM instance
# ─────────────────────────────────────────────────────────────────────────────

def run_all_chains(reviews: list[str]) -> dict:
    """
    Runs chains 1–5 in order, sharing one LLM instance.

    Returns:
        {
            "requirements": dict,   # FR + NFR
            "moscow":       dict,   # MoSCoW table
            "dfd":          dict,   # DFD components
            "cspec":        dict,   # Activation + Decision tables
            "srs_markdown": str,    # Full IEEE 830 SRS document
        }
    """
    llm = _get_llm()

    requirements = run_fr_nfr_chain(reviews,                  llm=llm)
    moscow       = run_moscow_chain(requirements,              llm=llm)
    dfd          = run_dfd_chain(requirements,                 llm=llm)
    cspec        = run_cspec_chain(dfd,                        llm=llm)
    srs_markdown = run_srs_chain(requirements, moscow, dfd,    llm=llm)

    return {
        "requirements": requirements,
        "moscow":       moscow,
        "dfd":          dfd,
        "cspec":        cspec,
        "srs_markdown": srs_markdown,
    }
