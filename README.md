# Ruppert

**Ruppert** is a local, read-only research assistant for Markdown knowledge bases. It combines deterministic document retrieval with a small LLM running through Ollama. Its longer-term goal is to investigate source-code repositories and produce concise, evidence-backed reports.

**Status:** Documentation RAG v0.2 (46 passing tests, verified on 2026-11-02). Repository/code indexing is **not implemented yet**.

## What works today

- Recursively discovers `.md` and `.markdown` documents within a local knowledge directory.
- Splits Markdown into sections using heading hierarchy, retaining original source line ranges.
- Builds a SQLite FTS5 index and searches with BM25 ranking.
- Retrieves matching sections and optional descendant sections with a bounded context size.
- Uses a local Ollama model to answer questions from retrieved documentation.
- Separates context text from the trusted source manifest and checks generated citations against that manifest.
- Warns about missing, invented, or otherwise unrecognized citations.
- Provides a CLI for free-form chat, indexing, keyword search, and document-grounded research.

**Limits:** Retrieval is lexical, not semantic; the index is rebuilt rather than updated incrementally; citation validation is *structural*, not proof that a cited passage supports a claim. `ruppert ask` is ungrounded chat and can hallucinate. Source-code scanning, symbol indexing, call graphs, and multi-repository investigation are roadmap items.

### Project structure

```text
ruppert/
├── README.md
├── .gitignore
├── pyproject.toml
├── src/ruppert/
│   ├── cli.py                 # ask, index, search, research
│   ├── models.py              # Document, Section, SearchHit, ContextResult
│   ├── markdown_loader.py     # heading-aware Markdown parsing
│   ├── knowledge_scanner.py   # local document discovery
│   ├── knowledge_index.py     # SQLite FTS5 / BM25
│   ├── context_builder.py     # bounded context + trusted source manifest
│   ├── citation_validator.py  # structural citation verification
│   ├── llm.py                 # Ollama client
│   └── rag.py                 # retrieval-augmented answers
├── tests/                     # pytest suite
├── knowledge/                 # PRIVATE, gitignored; user-supplied Markdown
└── data/                      # PRIVATE, gitignored; generated SQLite indexes
```

## Installation

Requires Python 3.12+ and, for `ask` / `research`, a running local Ollama server with the model configured in `src/ruppert/llm.py` (`qwen3.5:4b-q4_K_M` in v0.2).

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e .
ruppert --help
```

Install the development dependencies when working on the codebase (for example, via the project's `dev` extra if available).

Run Ollama locally in another terminal (the executable location depends on your installation):

```bash
OLLAMA_NO_CLOUD=1 \
OLLAMA_HOST=127.0.0.1:11434 \
OLLAMA_MAX_LOADED_MODELS=1 \
OLLAMA_NUM_PARALLEL=1 \
OLLAMA_CONTEXT_LENGTH=8192 \
OLLAMA_KEEP_ALIVE=1m \
ollama serve
```

Some hardware requires additional GPU-specific configuration. `index` and `search` work **without** a running LLM.

## Quick start

Create your own Markdown files inside `knowledge/` (this entire directory is excluded from Git), then index them:

```bash
ruppert index --knowledge knowledge --db data/knowledge.db
```

Re-run `index` after editing the documents. The index is currently rebuilt in full.

## Casual commands

Use these for everyday exploration:

```bash
# Direct LLM conversation: no retrieval, no grounded citations
ruppert ask "Explain the difference between unit and integration tests."

# Find documentation without invoking the LLM
ruppert search "testing strategy"

# Ask a question using indexed documents
ruppert research "How should we approach a bug report?"

# Request extended model reasoning (optional, potentially slower)
ruppert research "What evidence is needed before implementing a fix?" --think
```

## Targeted commands

Use these to control exactly what Ruppert retrieves and how much it sends to the model:

```bash
# Inspect search results first
ruppert search "regression tests" --limit 5
ruppert search "regression tests" --limit 3 --full
ruppert search "regression tests" --limit 2 --expand

# Keep the user question distinct from the FTS search terms
ruppert research \
  "Which test layers should we prioritize?" \
  --query "testing strategy" \
  --limit 1

# Constrain section expansion and context budget
ruppert research \
  "What should we verify before proposing a fix?" \
  --query "hypotheses evidence" \
  --limit 2 \
  --descendants 2 \
  --max-chars 6000

# Use an alternate, separately indexed knowledge base
ruppert index --knowledge /path/to/private/docs --db data/other.db
ruppert search "testing" --db data/other.db
ruppert research "How do we test changes?" --db data/other.db
```

| Command | Local LLM | Indexed documents | Options |
|---|---|---|---|
| `ruppert ask "..."` | Yes | No | `--think` |
| `ruppert index` | No | Creates/rebuilds | `--knowledge`, `--db` |
| `ruppert search "..."` | No | Yes | `--db`, `--limit`, `--full`, `--expand` |
| `ruppert research "..."` | Yes | Yes | `--db`, `--query`, `--limit`, `--descendants`, `--max-chars`, `--think` |

Defaults: knowledge root `knowledge/`, index `data/knowledge.db`; `research` uses `--limit 3`, `--descendants 3`, and `--max-chars 8000`. Use `<command> --help` for current CLI details.

## Citations and evidence

Retrieved excerpts are labeled with original file and line ranges, such as `guide.md:L10-20`. A separate trusted manifest records **only the sections actually included in context**. The citation validator accepts a model citation only when its reference exactly matches this manifest. It supports common Markdown reference formats but may miss others.

If the model creates a narrower or different line range, Ruppert reports an **unverified citation** rather than silently treating it as valid. A structurally valid citation is **not** a semantic verification of the claim. Check the original material before acting on an important conclusion.

## Tests and quality checks

```bash
python -m pytest -q
ruff check src/ tests/
ruff format --check src/ tests/
git diff --check
```

Verified baseline for Documentation RAG v0.2: **46 passing tests**. Tests use mocked LLM calls and do not require Ollama.

## Roadmap

1. **Done:** Local Ollama and quantized model integration.
2. **Done:** Markdown scanner, parser, SQLite FTS5 / BM25.
3. **Done:** Documentation RAG v0.2 and trusted citation manifest.
4. **Next:** Read-only repository scanner, starting with Rust files.
5. **Planned:** Symbol index, cross-file references, structural code retrieval.
6. **Planned:** Evidence-backed code investigation reports, facts vs. hypotheses.
7. **Planned:** Incremental updates, hybrid/semantic retrieval, multiple repositories, additional hardware profiles.

**Usage rule:** `ask` for ungrounded chat, `search` to locate evidence, and `research` for document-grounded answers. The source files—not the LLM response—remain the authority.
