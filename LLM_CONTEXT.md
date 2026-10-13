# DocAgent — LLM Context Document

This document gives a complete technical picture of the DocAgent codebase for use as LLM context. Read it before generating code, answering questions, or making modifications.

---

## What This Project Does

DocAgent automatically generates high-quality Python docstrings for an entire repository. It uses a multi-agent pipeline where specialized LLM-backed agents collaborate to read, search, write, and verify docstrings. The processing order is determined by static dependency analysis: components with no dependencies are documented first, building a documented foundation before tackling more complex code.

**Research paper:** [DocAgent: A Multi-Agent System for Automated Code Documentation Generation](https://arxiv.org/abs/2504.08725) (Yang et al., 2025)

---

## Repository Layout

```
DocAgent_Major_Project/
├── generate_docstrings.py        # Main CLI entrypoint
├── run_web_ui.py                 # Launch Flask web UI for generation
├── eval_completeness.py          # Run completeness evaluation
├── setup.py                      # Package definition and dependencies
├── config/
│   └── example_config.yaml       # Template config — copy to agent_config.yaml
├── src/
│   ├── agent/                    # Core multi-agent framework
│   │   ├── orchestrator.py       # Coordinates all agents (main logic)
│   │   ├── reader.py             # Decides if more context is needed
│   │   ├── searcher.py           # Retrieves internal/external context
│   │   ├── writer.py             # Generates the docstring via LLM
│   │   ├── verifier.py           # QA-checks the generated docstring
│   │   ├── base.py               # Shared BaseAgent (LLM init, memory)
│   │   ├── workflow.py           # generate_docstring() entry-point function
│   │   ├── llm/                  # LLMFactory and provider wrappers
│   │   └── tool/                 # ASTNodeAnalyzer, PerplexityAPI
│   ├── dependency_analyzer/
│   │   ├── ast_parser.py         # Parses repo → CodeComponent objects + dependency graph
│   │   └── topo_sort.py          # Topological sort / DFS traversal of the graph
│   ├── evaluator/
│   │   ├── completeness.py       # Checks param/return/exception coverage
│   │   ├── helpfulness_evaluator.py  # LLM-based helpfulness scoring
│   │   └── truthfulness.py       # Truthfulness checks
│   ├── visualizer/
│   │   ├── progress.py           # Terminal progress visualization
│   │   ├── status.py             # Per-agent status display
│   │   └── web_bridge.py         # Patches visualizers for web UI
│   ├── web/                      # Flask app for generation UI
│   └── web_eval/                 # Flask app for evaluation UI
├── benchmark/                    # Benchmarking pipeline
│   ├── run_benchmark.py
│   ├── generate_docstrings_for_model.py
│   ├── llm_judge/                # Pairwise and pointwise LLM judges
│   └── objective/                # Completeness metric
├── data/
│   ├── raw_test_repo/            # Test repository (vending machine domain)
│   └── raw_test_repo_simple/     # Simpler test repository
├── output/
│   └── dependency_graphs/        # JSON dependency graphs saved per run
└── tool/
    ├── remove_docstrings.py      # Strip all docstrings from a repo
    └── serve_local_llm.sh        # Shell script to start Ollama
```

---

## Key Data Structures

### `CodeComponent` (`src/dependency_analyzer/ast_parser.py`)

The central data object representing one documentable unit (function, method, or class).

```python
@dataclass
class CodeComponent:
    id: str               # Unique dotted path, e.g. "inventory.manager.InventoryManager.add_item"
    node: ast.AST         # The AST node (not serialized to JSON)
    component_type: str   # "function" | "class" | "method"
    file_path: str        # Absolute path to the containing file
    relative_path: str    # Relative path within the repo root
    depends_on: Set[str]  # IDs of components this one depends on
    source_code: str      # Raw source text of the component
    start_line: int
    end_line: int
    has_docstring: bool
    docstring: str        # Existing docstring content, or ""
```

Component IDs follow the pattern `<module_path>.<ClassName>.<method_name>`. For top-level functions, it is `<module_path>.<function_name>`. Module paths use dots, derived from the file path relative to the repo root.

### Dependency Graph

A `Dict[str, Set[str]]` where each key is a component ID and the value is the set of component IDs it **depends on** (i.e., an edge A → B means "A uses B"). This natural dependency direction is used throughout the codebase.

---

## Pipeline: How Docstrings Are Generated

### Step 1 — Parse the Repository

`DependencyParser.parse_repository()` performs three AST passes over all `.py` files:

1. **Collect components** — finds all `FunctionDef`, `AsyncFunctionDef`, `ClassDef` nodes (top-level functions and class methods only; nested functions are skipped).
2. **Resolve dependencies** — for each component, walks its AST subtree to find `Name` and `Attribute` references, resolving them against known imports and modules.
3. **Add class→method edges** — each class is made to depend on its own methods (except `__init__`), so methods are documented before their parent class.

The resulting component dictionary and dependency graph are saved to `output/dependency_graphs/<repo_name>_dependency_graph.json`.

### Step 2 — Order Components

`dependency_first_dfs(graph)` performs a DFS from root nodes (nodes with no incoming edges). Because edges mean "depends on", processing a node after all its dependencies guarantees each component's dependencies are already documented when it is processed.

Cycle handling: Tarjan's algorithm detects strongly connected components; cycles are broken by removing an edge.

Alternative ordering modes (controlled by `--order-mode`):
- `topo` (default) — dependency-ordered DFS
- `random_node` — shuffle all components randomly
- `random_file` — shuffle files randomly, preserve intra-file order

### Step 3 — Multi-Agent Loop (per component)

For each component, `generate_docstring_for_component()` calls `Orchestrator.process()`. The orchestrator runs this loop:

```
while True:
    Reader.process(focal_component, accumulated_context)
    if needs_info and attempts < max_reader_search_attempts:
        Searcher.process(reader_response, ast_node, ast_tree, dep_graph)
        → update accumulated context
        → refresh Reader memory
        continue

    while True:  # writer-verifier refinement cycle
        Writer.process(focal_component, context)  → docstring
        Verifier.process(focal_component, docstring, context)  → XML verdict

        if accepted or max_rejections reached:
            return docstring

        if needs_context:
            break  # back to outer reader-searcher loop

        else:
            writer.add_to_memory(improvement_suggestion)
            # continue inner loop (writer revises)
```

Flow control parameters (from `config/agent_config.yaml`):
- `max_reader_search_attempts` (default: 4) — how many times Reader can request more context
- `max_verifier_rejections` (default: 3) — how many revision cycles before accepting
- `status_sleep_time` (default: 3) — seconds between status updates

### Step 4 — Write Back to File

`set_docstring_in_file()` re-parses the target file with `ast.parse`, locates the component node, inserts or replaces the first `ast.Expr` string constant (the docstring), then unparses the tree back with `ast.unparse` (Python ≥ 3.9) or `astor` as fallback.

---

## Agent Details

### BaseAgent (`src/agent/base.py`)
Provides:
- `__init__(agent_name)` — loads config, initializes LLM via `LLMFactory`
- `add_to_memory(role, content)` — appends to `self.memory` (conversation history)
- `clear_memory()` / `refresh_memory(messages)` — memory management
- `generate_response(messages)` — calls the LLM with the given message list

### Reader
- Receives: `(focal_component: str, context: str)`
- Returns: XML response with `<INFO_NEED>true/false</INFO_NEED>` and structured search requests if needed
- Memory is preserved across iterations within one component so the Reader can accumulate understanding

### Searcher
- Receives: Reader's XML request, `ast_node`, `ast_tree`, `dependency_graph`, `focal_node_dependency_path`
- Uses `ASTNodeAnalyzer` for internal context (callers, callees, class/function definitions)
- Uses `PerplexityAPI` for external web search
- Returns: dict with `internal` and `external` keys (see `Orchestrator._update_context`)

### Writer
- Receives: `(focal_component: str, context: str)`
- Uses tailored prompts for classes vs. functions/methods (Google docstring style)
- Output is wrapped in `<DOCSTRING>...</DOCSTRING>` tags; the orchestrator extracts the content

### Verifier
- Receives: `(focal_component: str, docstring: str, context: str)`
- Returns XML:
  ```xml
  <NEED_REVISION>true/false</NEED_REVISION>
  <MORE_CONTEXT>true/false</MORE_CONTEXT>
  <SUGGESTION>...</SUGGESTION>              <!-- if no more context needed -->
  <SUGGESTION_CONTEXT>...</SUGGESTION_CONTEXT>  <!-- if more context needed -->
  ```

### Orchestrator
- Owns all agents and the accumulated `self.context` string
- Context is structured XML:
  ```xml
  <CONTEXT>
    <INTERNAL_INFO>
      <CLASS>...</CLASS>
      <FUNCTION>...</FUNCTION>
      <METHOD>...</METHOD>
      <CALL_BY>...</CALL_BY>
    </INTERNAL_INFO>
    <EXTERNAL_RETRIEVAL_INFO>...</EXTERNAL_RETRIEVAL_INFO>
  </CONTEXT>
  ```
- Token budgeting: `_constrain_context_length()` uses tiktoken to truncate the largest XML section when total tokens (context + focal component) exceed `max_input_tokens`
- Context is reset to `""` at the start of each new component

---

## LLM Provider Support

Configured under the `llm` key in `config/agent_config.yaml`:

| `type`          | Notes |
|-----------------|-------|
| `ollama`        | Default. OpenAI-compatible endpoint at `http://localhost:11434/v1/`. Model must be pulled first. |
| `openai`        | Requires `api_key`. Models: gpt-4o, gpt-4-turbo, gpt-3.5-turbo, etc. |
| `gemini`        | Requires `api_key`. Model: gemini-1.5-pro, etc. |
| `huggingface`   | Local or remote HuggingFace inference. Needs `device` (cuda/cpu) and `torch_dtype`. |

Rate limits per provider are defined under `rate_limits` in the config. Cost tracking is built into the rate limiter and reported at the end of a run.

---

## Configuration Reference (`config/agent_config.yaml`)

```yaml
llm:
  type: "ollama"            # ollama | openai | gemini | huggingface
  api_key: "ollama"
  api_base: "http://localhost:11434/v1/"
  model: "qwen2.5-coder:7b"
  temperature: 0.1
  max_output_tokens: 4096
  max_input_tokens: 100000  # Per-call token budget for context

rate_limits:
  ollama:
    requests_per_minute: 30
    input_tokens_per_minute: 100000
    output_tokens_per_minute: 30000
    input_token_price_per_million: 0.0
    output_token_price_per_million: 0.0

flow_control:
  max_reader_search_attempts: 2
  max_verifier_rejections: 1
  status_sleep_time: 1

docstring_options:
  overwrite_docstrings: false  # Skip components that already have docstrings

perplexity:
  api_key: "your-key"     # Only needed for external web search
  model: "sonar"
  temperature: 0.1
  max_output_tokens: 250
```

---

## CLI Usage

```bash
# Standard run
python generate_docstrings.py --repo-path /path/to/repo

# With explicit config
python generate_docstrings.py --repo-path /path/to/repo --config-path config/agent_config.yaml

# Overwrite existing docstrings
python generate_docstrings.py --repo-path /path/to/repo --overwrite-docstrings

# Test mode: generates placeholder docstrings, no LLM calls
python generate_docstrings.py --repo-path /path/to/repo --test-mode placeholder

# Test mode: prints context before every Writer call (useful for debugging prompts)
python generate_docstrings.py --repo-path /path/to/repo --test-mode context_print

# Random ordering (for ablation experiments)
python generate_docstrings.py --repo-path /path/to/repo --order-mode random_node

# Enable web UI integration
python generate_docstrings.py --repo-path /path/to/repo --enable-web

# Web UI (runs on http://localhost:5000)
python run_web_ui.py --host 0.0.0.0 --port 5000

# Evaluation web UI (runs on http://localhost:5001)
python src/web_eval/app.py --host 0.0.0.0 --port 5001
```

---

## Installation

```bash
git clone <repo_url>
cd DocAgent_Major_Project
python -m venv venv && source venv/bin/activate
pip install -e .

# Optional extras
pip install -e ".[visualization]"   # matplotlib, pygraphviz, networkx
pip install -e ".[cuda]"            # torch + accelerate for GPU
pip install -e ".[dev]"             # pytest, black, flake8

# Copy and edit config
cp config/example_config.yaml config/agent_config.yaml
```

Python version requirement: **≥ 3.8**. Python 3.9+ is recommended because `ast.unparse` is used to rewrite files; `astor` is used as a fallback on older versions.

---

## Benchmarking

The `benchmark/` directory contains a full evaluation pipeline:

1. **`generate_docstrings_for_model.py`** — runs DocAgent (or a baseline) against a test repo using a specific model config from `benchmark/configs/`.
2. **`generate_comparison_dataset.py`** — assembles outputs from multiple models into a comparison dataset (`results/comparison_dataset.json`).
3. **`llm_judge/`** — two evaluation modes:
   - `pointwise_evaluator.py` — scores each docstring on absolute quality
   - `pairwise_evaluator.py` — head-to-head comparison between models
4. **`objective/completeness.py`** — static metric: checks that all parameters, return values, and exceptions mentioned in the code are covered by the docstring.
5. **`report_generator.py`** — collates all results into a markdown report.

Model configs tested: `qwen2.5-coder-1.5b`, `qwen2.5-coder-3b`, `qwen2.5-coder-7b`, `qwen3-4b`.

---

## Evaluator Modules (`src/evaluator/`)

The evaluator is separate from the generation pipeline and is used post-hoc:

- **`completeness.py`** — AST-based: extracts all parameters, return annotations, and raised exceptions from a function and checks whether the docstring mentions each one.
- **`helpfulness_evaluator.py`** — LLM-based: scores docstrings across multiple helpfulness dimensions (description, parameters, returns, examples, clarity).
- **`helpfulness_evaluator_ablation.py`** — Variant for ablation study.
- **`truthfulness.py`** — Checks that docstring claims are consistent with the actual code.
- **`segment.py`** — Parses a docstring into sections (description, args, returns, raises, examples).

---

## Important Implementation Notes

1. **`__init__` methods are always skipped** — the generation loop checks `component_id.endswith(".__init__")` and marks them completed without generating.

2. **Token cap on focal component** — if the focal component exceeds 10,000 tokens it is truncated before being passed to the orchestrator.

3. **File re-parsing after each write** — since inserting a docstring changes line numbers, the parser re-scans the file for any remaining components from the same file.

4. **Docstring skip logic** — by default, a component with an existing docstring of more than 10 words is skipped. Use `--overwrite-docstrings` or set `docstring_options.overwrite_docstrings: true` in config to override.

5. **`clean_generated_docstring()`** — strips surrounding triple-quote wrappers if a model returns them, preventing double-quoting in the output file.

6. **Memory isolation** — each component starts with a clean orchestrator context (`self.context = ""`). Agent memories (conversation history) are also cleared or refreshed at defined points in the loop to avoid cross-component contamination.

7. **Dependency graph edge direction** — edges are **A → B meaning "A depends on B"**. Root nodes (no outgoing dependencies) are processed first. This is the opposite of a traditional topological sort "dependents-last" output, so the DFS result is **not reversed**.

---

## Common Entry Points for Code Modifications

| Task | File(s) to edit |
|------|----------------|
| Change agent prompts | `src/agent/reader.py`, `writer.py`, `verifier.py` |
| Add a new LLM provider | `src/agent/llm/` (add a new class, register in `LLMFactory`) |
| Change dependency resolution logic | `src/dependency_analyzer/ast_parser.py` |
| Change traversal order | `src/dependency_analyzer/topo_sort.py` |
| Change docstring insertion / AST rewrite | `generate_docstrings.py` (`set_docstring_in_file`, `set_node_docstring`) |
| Add a new evaluation metric | `src/evaluator/` |
| Extend the web UI | `src/web/app.py`, `src/web/templates/` |
| Add benchmark models | `benchmark/configs/` (add a new `.yaml`) |
