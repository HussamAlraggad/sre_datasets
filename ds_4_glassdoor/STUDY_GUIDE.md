# Study Guide
## Glassdoor RAG — Software Requirements Engineering

> This document covers every theoretical concept used in this project.
> Read it alongside your coursework. Sections are ordered to match the
> pipeline stages.

---

## Table of Contents

1. [What is a RAG System?](#1-what-is-a-rag-system)
2. [Embeddings and Vector Search](#2-embeddings-and-vector-search)
3. [FAISS — Fast Similarity Search](#3-faiss--fast-similarity-search)
4. [LangChain Concepts](#4-langchain-concepts)
5. [Functional Requirements (FR)](#5-functional-requirements-fr)
6. [Non-Functional Requirements (NFR)](#6-non-functional-requirements-nfr)
7. [MoSCoW Prioritization](#7-moscow-prioritization)
8. [Data Flow Diagrams (DFD)](#8-data-flow-diagrams-dfd)
9. [CSPEC — Control Specification](#9-cspec--control-specification)
10. [IEEE 830 / IEEE 29148 SRS Standard](#10-ieee-830--ieee-29148-srs-standard)
11. [How This Project Maps to the Course](#11-how-this-project-maps-to-the-course)
12. [Key Terms Glossary](#12-key-terms-glossary)
13. [Changelog](#13-changelog)

---

## 1. What is a RAG System?

**RAG = Retrieval-Augmented Generation**

A RAG system combines two AI components:

```
 USER QUERY
     │
     ▼
 ┌──────────┐     similarity search    ┌──────────────┐
 │ Embedder │  ──────────────────────► │ Vector Store │
 └──────────┘                          └──────┬───────┘
                                              │ top-k documents
                                              ▼
                                       ┌──────────────┐
                                       │    LLM       │  ◄── prompt template
                                       └──────┬───────┘
                                              │
                                              ▼
                                        GENERATED ANSWER
```

### Why RAG instead of just an LLM?

| Problem with pure LLM | RAG solution |
|---|---|
| Knowledge cut-off date | Retrieves live/custom documents |
| Hallucination (invents facts) | Grounds answers in real text |
| Can't process 3.5 GB of data | Stores data in vector index, retrieves what's relevant |
| Generic answers | Answers come from YOUR data |

### In this project

- **Documents** = 16.9 million Glassdoor reviews
- **Retriever** = FAISS index queried with L2 distance
- **Generator** = Ollama `llama3:8b` running locally
- **Task** = Extract software requirements from what real employees wrote

---

## 2. Embeddings and Vector Search

### What is a text embedding?

An embedding converts text into a fixed-length numeric vector. Similar texts
produce vectors that are close together in high-dimensional space.

```
"good salary and benefits"        → [0.12, -0.34, 0.88, ...]  ← 384 numbers
"competitive compensation package" → [0.14, -0.31, 0.85, ...]  ← very close!
"poor management communication"   → [-0.42, 0.67, -0.11, ...]  ← far away
```

### The model used: `all-MiniLM-L6-v2`

- Architecture: MiniLM (distilled BERT)
- Output dimension: 384
- Trained on: 1B+ sentence pairs
- Speed: ~14 000 sentences/second on GPU
- Quality: excellent for semantic similarity tasks

### Why GPU for embedding?

The embedding model is a neural network. The GPU parallelises the matrix
multiplications across all texts in a batch simultaneously. A batch of 256
texts takes roughly the same GPU time as a single text would on CPU.

### Similarity metric: L2 distance

FAISS uses **L2 (Euclidean) distance** by default with `IndexFlatL2`:

```
distance(a, b) = sqrt( sum_i (a_i - b_i)² )
```

Lower distance = more similar. When `normalize_embeddings=True` is set
(as in this project), L2 distance and cosine similarity become equivalent.

---

## 3. FAISS — Fast Similarity Search

**FAISS** (Facebook AI Similarity Search) is a library for efficient nearest
neighbour search in dense vector spaces.

### Why FAISS?

| Property | Value for this project |
|---|---|
| Index size | ~16.9M × 384 × 4 bytes ≈ **26 GB** (all-MiniLM) |
| Query time | < 1 second for k=20 on `IndexFlatL2` |
| Exact search | `IndexFlatL2` gives exact results (no approximation) |
| No server needed | Runs in-process, stored as a single file |

### Shard strategy (used in 01_ingest.py)

Because the full index is too large to build in memory all at once:

1. Embed 50 000 rows → write `shard_00000.index`
2. Embed next 50 000 rows → write `shard_00001.index`
3. …repeat ~340 times…
4. Read all shards → merge into `merged.index`

Each shard holds 50 000 vectors × 384 dims × 4 bytes ≈ **73 MB**.
The merged index is ~26 GB.

### Progress / resume

`faiss_index/progress.json` tracks which shards are done. If the script is
killed, re-running it reads this file and skips completed shards.

---

## 4. LangChain Concepts

LangChain is a framework for building LLM-powered applications.

### Key components used in this project

| Component | Role in this project |
|---|---|
| `HuggingFaceEmbeddings` | Wraps sentence-transformers model for embedding |
| `ChatOllama` | Wraps local Ollama LLM for generation |
| `PromptTemplate` | Defines the structure of each LLM call |
| Chain (manual) | Passes outputs from one LLM call as input to the next |

### Chain pipeline in this project

```
reviews (list of strings from FAISS)
    │
    ▼ Chain 1
FR/NFR Extraction  ──► requirements.json
    │
    ▼ Chain 2
MoSCoW Prioritization ──► moscow.json
    │
    ▼ Chain 3 (parallel to chain 2, same input as chain 1)
DFD Components ──► dfd_components.json
    │
    ▼ Chain 4
CSPEC Logic ──► cspec_tables.json / .md
    │
    ▼ Chain 5 (all previous outputs combined)
SRS Formatter ──► SRS.md
```

### Prompt engineering principles used

1. **Role definition** — "You are a Senior Requirements Engineer …"
2. **Structured output** — ask for JSON with a specific schema
3. **Few-shot guidance** — show the expected field names in the schema
4. **Low temperature** — `0.1` keeps output deterministic and structured
5. **JSON fence stripping** — `_safe_json()` handles LLM wrapping output in ```json

---

## 5. Functional Requirements (FR)

### Definition

A **Functional Requirement** describes **what a system must do** — a
capability, behaviour, or function.

> "The system shall allow users to submit a company review including a rating,
> title, pros, cons, and optional advice for management."

### Characteristics of a good FR

- Starts with "The system shall …"
- One requirement = one capability (no "and" joining two things)
- Verifiable: you can write a test for it
- Unambiguous: only one interpretation

### FR categories used in this project

| Category | Examples |
|---|---|
| Authentication | Login, registration, password reset |
| Profile | User profile, job history |
| Review | Submit review, edit review, flag review |
| Search | Search companies, filter by industry |
| Analytics | Rating trends, sentiment analysis |
| Notification | Email alerts, in-app notifications |
| Admin | Moderate reviews, manage users |
| Moderation | Report abuse, content filtering |
| Integration | LinkedIn import, salary data APIs |

---

## 6. Non-Functional Requirements (NFR)

### Definition

A **Non-Functional Requirement** describes **how well a system must perform**
a function — the quality attributes of the system.

> "The system shall return search results within 2 seconds for 95% of queries
> under normal load conditions."

### NFR categories (ISO/IEC 25010 quality model)

| Category | Question it answers |
|---|---|
| Performance | How fast? How many users simultaneously? |
| Security | Who can access what? How is data protected? |
| Usability | How easy is it for users to learn and use? |
| Reliability | How often does it fail? How long to recover? |
| Scalability | Can it grow with more users/data? |
| Maintainability | How easy is it to update and fix? |
| Accessibility | Can users with disabilities use it? (WCAG) |
| Privacy | How is personal data handled? (GDPR) |

### FR vs NFR — quick test

Ask: "Is this about WHAT the system does or HOW WELL it does it?"
- WHAT → FR
- HOW WELL → NFR

---

## 7. MoSCoW Prioritization

### Definition

MoSCoW is a prioritization technique that categorises requirements into four
buckets based on their business value and urgency.

| Category | Meaning | Rule of thumb |
|---|---|---|
| **M**ust have | Non-negotiable. System fails without it. | Core MVP features |
| **S**hould have | Important but not vital. Defer if needed. | High-value features |
| **C**ould have | Nice to have. Low impact if omitted. | Polish / extras |
| **W**on't have | Out of scope for this version. | Backlog / future |

### How prioritization decisions are made

Four factors are weighed:

1. **Frequency** — How many reviews mentioned this theme?
2. **Impact** — How much does this affect the core user goal?
3. **Risk** — Does omitting it cause legal/security/trust issues?
4. **Feasibility** — Can this be built given the project constraints?

### MoSCoW in practice

For a v1.0 Glassdoor-style app:
- **Must**: User registration, submit review, view reviews, basic search
- **Should**: Rating analytics, email notifications, company profiles
- **Could**: AI-powered sentiment analysis, salary benchmarking charts
- **Won't**: Mobile native app, API marketplace, employer response dashboard

---

## 8. Data Flow Diagrams (DFD)

### What is a DFD?

A DFD (Data Flow Diagram) is a graphical model showing how data moves through
a system. It does **not** show control flow, timing, or hardware.

### The four components

| Symbol | Name | Description | Example |
|---|---|---|---|
| Rectangle | **External Entity** | Actor outside the system boundary | Employee, Job Seeker, Admin |
| Circle/Bubble | **Process** | Transformation of data | P1: Validate Review |
| Arrow | **Data Flow** | Named data moving between components | "Review Data", "Search Query" |
| Open rectangle | **Data Store** | Persistent storage | D1: Reviews Database |

### DFD levels

| Level | Scope |
|---|---|
| Level 0 (Context Diagram) | Single bubble = the whole system; only external entities shown |
| Level 1 | Major processes decomposed; data stores introduced |
| Level 2+ | Individual processes decomposed further |

This project generates **Level 1** components.

### DFD rules (Yourdon/DeMarco notation)

1. Every process must have at least one input AND one output flow.
2. Data flows must be named (not "data" — use "Review Submission", etc.).
3. Data stores are only accessed by processes (never by external entities directly).
4. External entities are sources or sinks — they don't transform data.
5. No flow from one data store directly to another (must go through a process).

### How to draw the DFD from the output

Use `outputs/dfd_components.md` or `outputs/dfd_components.json`.

1. Draw each **External Entity** as a labeled rectangle.
2. Draw each **Process** as a labeled circle, numbered (P1, P2, …).
3. Draw each **Data Store** as a labeled open rectangle (D1, D2, …).
4. For each **Data Flow**, draw a named arrow from source → destination.
5. Check all DFD rules are satisfied.

Tools: draw.io, Lucidchart, Microsoft Visio, or pen and paper.

---

## 9. CSPEC — Control Specification

### What is CSPEC?

CSPEC (Control Specification) is a Structured Analysis artefact that
describes the **control logic** inside a DFD process — when a process
activates and how it makes decisions.

It consists of two tables:

### A. Activation Table

Lists the conditions (events or inputs) that cause a process to start.

| Process | Condition | Trigger Type |
|---|---|---|
| P1: Validate Review | Review submission received | data-arrival |
| P2: Authenticate User | Login request received | user-action |
| P3: Send Notification | Review approved | event |

### B. Decision Table

Defines the branching logic inside a process.
Each column is one combination of conditions → set of actions.

```
                        │ R1 │ R2 │ R3 │ R4 │
────────────────────────┼────┼────┼────┼────┤
CONDITION                                   │
  User authenticated?   │ Y  │ Y  │ N  │ N  │
  Content passes filter?│ Y  │ N  │ Y  │ N  │
────────────────────────┼────┼────┼────┼────┤
ACTION                                      │
  Save review           │ X  │ -  │ -  │ -  │
  Show error: content   │ -  │ X  │ -  │ -  │
  Redirect to login     │ -  │ -  │ X  │ X  │
```

### Why CSPEC matters for this project

- It bridges the DFD (WHAT data flows) with the process logic (HOW decisions
  are made inside each bubble).
- In an SRS, CSPEC tables go into Section 4 alongside the DFD.
- They directly inform the development of use cases and unit tests.

---

## 10. IEEE 830 / IEEE 29148 SRS Standard

### What is an SRS?

An **SRS (Software Requirements Specification)** is a document that completely
describes all the functions and constraints of a software system to be
developed.

### IEEE 830 vs IEEE 29148

| Standard | Year | Notes |
|---|---|---|
| IEEE 830-1998 | 1998 | Classic SRS structure; most taught in universities |
| IEEE 29148-2018 | 2018 | Updated, replaces 830; more modern terminology |

Both share the same core structure. This project uses IEEE 830 as the primary
template because it is more commonly referenced in coursework.

### IEEE 830 Document Structure

```
1. Introduction
   1.1 Purpose
   1.2 Scope
   1.3 Definitions, Acronyms, Abbreviations
   1.4 References
   1.5 Overview

2. Overall Description
   2.1 Product Perspective
   2.2 Product Functions
   2.3 User Characteristics
   2.4 Constraints
   2.5 Assumptions and Dependencies

3. Specific Requirements
   3.1 Functional Requirements   ← FR-001, FR-002 …
   3.2 Non-Functional Requirements ← NFR-001, NFR-002 …

4. System Models
   4.1 DFD Level-1
   4.2 CSPEC

5. Appendices
   5.1 MoSCoW Summary
   5.2 Traceability Matrix
```

### Traceability Matrix

A traceability matrix links requirements to other artefacts:

| FR/NFR ID | Requirement | DFD Process | MoSCoW |
|---|---|---|---|
| FR-001 | The system shall allow … | P1, P3 | MUST |
| NFR-002 | The system shall respond … | P2 | SHOULD |

This matrix ensures every requirement is covered by at least one process, and
every process implements at least one requirement.

---

## 11. How This Project Maps to the Course

| Course Topic | Where it appears in this project |
|---|---|
| Requirements Elicitation | `01_ingest.py` + `03_chains.py` Chain 1 — mining reviews as a stakeholder source |
| FR Classification | `prompts/fr_nfr_extraction.txt` + `requirements.json` |
| NFR Classification | Same as above (ISO/IEC 25010 categories) |
| Prioritization (MoSCoW) | `prompts/moscow_prioritization.txt` + `moscow.json` |
| Flow Model / DFD | `prompts/dfd_components.txt` + `dfd_components.md` |
| Control Specification | `prompts/cspec_logic.txt` + `cspec_tables.md` |
| SRS Document (IEEE 830) | `prompts/srs_formatter.txt` + `outputs/SRS.md` |
| Validation & Verification | The retrieval step grounds all outputs in real user data |

### The RAG advantage for requirements engineering

Traditional requirements elicitation relies on:
- Interviews, workshops, surveys (expensive, slow)
- Reading competitor app reviews manually (tedious at scale)

This RAG system automates the analysis of **16.9 million real employee
reviews**, extracting patterns that no human analyst could process manually.
The LLM then applies domain expertise (requirements engineering knowledge
baked into the prompt) to structure the findings into a formal SRS.

---

## 12. Key Terms Glossary

| Term | Definition |
|---|---|
| **RAG** | Retrieval-Augmented Generation — combines semantic search with LLM generation |
| **Embedding** | A dense vector representation of text, where semantic similarity = geometric closeness |
| **FAISS** | Facebook AI Similarity Search — library for fast nearest-neighbour search in vector spaces |
| **LLM** | Large Language Model — neural network trained to generate text (e.g. llama3:8b) |
| **Ollama** | Local LLM runtime — runs LLMs on your own hardware without an API key |
| **LangChain** | Python framework for building LLM-powered pipelines and agents |
| **FR** | Functional Requirement — what the system must do |
| **NFR** | Non-Functional Requirement — how well the system must do it |
| **MoSCoW** | Must / Should / Could / Won't — requirement prioritization framework |
| **DFD** | Data Flow Diagram — graphical model of data movement through a system |
| **CSPEC** | Control Specification — tables describing process activation logic and decisions |
| **SRS** | Software Requirements Specification — formal document describing all system requirements |
| **IEEE 830** | IEEE standard defining the structure and content of an SRS document |
| **Traceability Matrix** | Table linking requirements to design/test artefacts |
| **L2 distance** | Euclidean distance metric used by FAISS for similarity search |
| **Cosine similarity** | Alternative similarity metric (equivalent to L2 on normalised vectors) |
| **Shard** | A partial FAISS index covering a subset of the data, merged later |
| **Temperature** | LLM parameter controlling randomness: 0.0 = deterministic, 1.0 = creative |

---

## 13. Changelog

| Date | Version | Changes |
|---|---|---|
| 2026-03-13 | v1.0 | Initial study guide. All theoretical concepts covered. |

---

*This document is kept up to date as the project evolves.*
