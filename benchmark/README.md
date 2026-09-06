# Benchmark — DocAgent Multi-Model Evaluation

This directory contains a self-contained benchmarking system for comparing
docstring quality across multiple LLM models. It is completely separate from
DocAgent's generation pipeline — generation is treated as a black box, and
everything here is pure evaluation.

---

## Design Principles

- **Original repo is never modified.** Each model gets its own isolated copy.
- **Leave-one-out judging.** When model X is evaluated, the judges are all other models. No model ever judges its own output.
- **Position bias control.** Each pairwise matchup is run twice with A/B positions swapped. A win only counts when the judge agrees across both orderings — otherwise it's a TIE.
- **Win rate is the primary metric.** Point-wise scores (1–5) and structural completeness are secondary signals.
- **Fully configurable.** One file (`config.yaml`) controls everything — models, Ollama endpoint, sampling size, paths.

---

## Directory Structure

```
benchmark/
│
├── README.md                         ← this file
├── config.yaml                       ← single config: models, paths, sampling settings
│
├── generate_docstrings_for_model.py  ← Step 1: generate + store per-model output safely
├── generate_comparison_dataset.py    ← Step 2: merge all outputs into one JSON
├── run_benchmark.py                  ← Step 3: run full evaluation pipeline
├── report_generator.py               ← Step 5: compile final_report.md (also called by run_benchmark)
│
├── configs/                          ← auto-generated per-model DocAgent configs (do not edit)
│
├── objective/
│   ├── __init__.py
│   └── completeness.py               ← AST-based structural completeness (no LLM)
│
├── llm_judge/
│   ├── __init__.py
│   ├── judge_llm.py                  ← thin LLM wrapper (Ollama-compatible)
│   ├── prompts.py                    ← all judge prompts in one place
│   ├── pointwise_evaluator.py        ← 6-dimension point-wise scoring
│   ├── pairwise_evaluator.py         ← head-to-head win/loss/tie judgments
│   └── aggregate.py                  ← combines all metrics into summary structure
│
└── results/                          ← all outputs land here (git-ignored)
    ├── raw_generations/
    │   ├── model_a/                  ← copy of repo documented by model_a
    │   ├── model_b/
    │   └── ...
    ├── comparison_dataset.json       ← merged docstrings + metadata for all models
    ├── objective/
    │   └── completeness.json
    ├── llm_judgments/
    │   ├── pointwise/
    │   │   ├── pointwise_results.json
    │   │   └── pointwise_summary.json
    │   └── pairwise/
    │       ├── pairwise_results.json
    │       ├── pairwise_summary.json
    │       └── win_rate_ranking.json
    └── final_report.md               ← the human-readable result document
```

---

## Configuration — `config.yaml`

Everything is controlled from this one file. Open it and set:

```yaml
models:
  - name: "model_a"              # label used in reports and folder names
    ollama_model: "qwen2.5-coder:7b"   # Ollama model tag (must be pulled)

  - name: "model_b"
    ollama_model: "llama3.1:8b"

  # ... up to 5 models

ollama:
  api_base: "http://localhost:11434/v1"
  temperature: 0.1
  max_tokens: 1024

sampling:
  n_samples: 50    # components evaluated per model in LLM judging
  seed: 42

paths:
  source_repo: "data/raw_test_repo"   # repo to document — NEVER modified
  raw_generations: "benchmark/results/raw_generations"
  # ... other output paths
```

**Rules:**
- `name` values must be unique and valid folder names (no spaces).
- `ollama_model` must match what `ollama list` shows on your machine.
- All generation settings (temperature, flow_control) are kept identical across all models — only the model name changes. This is enforced automatically.

---

## What Each File Does

### `generate_docstrings_for_model.py`
Safely generates docstrings for one or all models without touching the original repo.

For each model it:
1. Writes a temporary DocAgent config to `benchmark/configs/<model_name>.yaml`
2. Copies the original repo to `benchmark/results/raw_generations/<model_name>/`
3. Runs `generate_docstrings.py` against that copy
4. If generation fails, the partial output folder is deleted so a retry is clean

### `generate_comparison_dataset.py`
Walks all per-model output folders, extracts docstrings via AST, runs structural
completeness scoring, and merges everything into `comparison_dataset.json`.

This is the central data file that all evaluation steps read from. Schema per component:

```json
{
  "module.ClassName.method_name": {
    "type": "method",
    "source_code": "...",
    "signature": "method_name(a: int, b: str) -> bool",
    "actual_params": ["a", "b"],
    "return_annotation": "bool",
    "has_raise": true,
    "has_return": true,
    "docstrings": {
      "model_a": {
        "docstring": "...",
        "element_scores": { "summary": true, "args": true, ... }
      },
      "model_b": { ... }
    }
  }
}
```

### `objective/completeness.py`
Pure AST evaluation — no LLM needed. Checks which required docstring sections are
present for each component. Required sections are determined from the code itself
(e.g. `Args` only if the function has parameters, `Raises` only if there are
uncaught raise statements). Score is 0.0–1.0.

### `llm_judge/prompts.py`
All judge prompts live here. Edit this file if you want to tune rubrics without
touching evaluation logic. Contains:
- 6 point-wise rubrics: `summary`, `description`, `parameters`, `correctness`, `clarity`, `conciseness`
- 1 pairwise preference prompt

### `llm_judge/judge_llm.py`
Thin wrapper over the project's existing `OpenAILLM` client pointed at Ollama.
Handles all judge LLM calls.

### `llm_judge/pointwise_evaluator.py`
For each model, scores a sampled set of its docstrings on 6 dimensions (1–5).

**Leave-one-out:** model X is judged by all other N−1 models. Scores are averaged
across all judges and all sampled components.

### `llm_judge/pairwise_evaluator.py`
Runs all C(5,2) = 10 head-to-head matchups.

**Leave-one-out:** pair A vs B is judged by the remaining 3 models.

**Position bias control:** each pair runs twice with A/B swapped. The final winner
requires the judge to pick the same model in both orderings. Disagreement → TIE.

Outputs a win/loss/tie table and a final win-rate ranking per model.

### `llm_judge/aggregate.py`
Utility that combines completeness, pointwise scores, and pairwise win rates into
a single list of model rows. Used by the report generator.

### `report_generator.py`
Reads all result JSONs and writes `final_report.md`. Can be run standalone to
regenerate the report without re-running evaluations.

### `run_benchmark.py`
Master entry point. Runs all steps in sequence. Each step can be skipped
independently with `--skip-*` flags, which is useful for resuming after a failure
or re-running just the report.

---

## How to Run — Step by Step

### Prerequisites

```bash
# Ollama must be running
ollama serve

# Pull the models you've listed in config.yaml
ollama pull qwen2.5-coder:7b
ollama pull llama3.1:8b
# ... etc

# DocAgent dependencies must be installed
pip install -e .
```

### Step 1 — Generate docstrings for all models

```bash
python benchmark/generate_docstrings_for_model.py --all
```

This is the only step that calls the LLM generation pipeline. It will take a
while (one full DocAgent run per model). Your original repo under `data/` is
never touched.

To generate for a single model only:
```bash
python benchmark/generate_docstrings_for_model.py --model model_a
```

To use a different source repo than the one in `config.yaml`:
```bash
python benchmark/generate_docstrings_for_model.py --all --repo path/to/my_repo
```

To force re-generation if output already exists:
```bash
python benchmark/generate_docstrings_for_model.py --model model_a --overwrite
```

After this step, `benchmark/results/raw_generations/` will contain one subfolder
per model with the fully documented repo inside.

### Step 2 — Run the full evaluation

```bash
python benchmark/run_benchmark.py
```

This runs all remaining steps in order:
1. Builds `comparison_dataset.json` from the generated repos
2. Computes AST-based completeness scores
3. Runs point-wise LLM judging (6 dimensions, leave-one-out)
4. Runs pairwise LLM judging (all 10 pairs, leave-one-out)
5. Writes `benchmark/results/final_report.md`

### Skipping steps (for resuming or re-running)

```bash
# Skip generation (raw_generations already exist) and jump straight to evaluation
python benchmark/run_benchmark.py --skip-dataset

# Re-run only the report from existing results
python benchmark/run_benchmark.py --skip-dataset --skip-objective --skip-pointwise --skip-pairwise

# Equivalent: just run the report generator directly
python benchmark/report_generator.py
```

Available flags: `--skip-dataset`, `--skip-objective`, `--skip-pointwise`,
`--skip-pairwise`, `--skip-report`

---

## Output — `final_report.md`

The report contains five sections:

1. **Pairwise Win Rate Ranking** — primary result. Models ranked by win rate across
   all head-to-head matchups.

2. **Head-to-Head Matrix** — W/L/T for every model pair.

3. **Full Metrics Summary** — one row per model, one column per metric (completeness,
   all 6 LLM dimensions, win rate).

4. **Structural Completeness** — AST-based scores detail.

5. **Point-wise LLM Scores** — per-dimension averages (1–5).

---

## Metrics Reference

| Metric | Type | Range | Notes |
|--------|------|--------|-------|
| Structural Completeness | AST-based | 0–1 | No LLM; checks required sections are present |
| Summary | LLM-judged | 1–5 | Does it add context beyond the signature? |
| Description | LLM-judged | 1–5 | Covers motivation, usage, integration? |
| Parameters | LLM-judged | 1–5 | Goes beyond repeating type hints? |
| Correctness | LLM-judged | 1–5 | Does it accurately describe what the code does? |
| Clarity | LLM-judged | 1–5 | Understandable to an unfamiliar developer? |
| Conciseness | LLM-judged | 1–5 | No verbosity or unnecessary repetition? |
| **Win Rate** | Pairwise | 0–1 | **Primary metric.** Fraction of head-to-head judgments won |

---

## Raw Data

All raw outputs are preserved:
- `pointwise_results.json` — every individual judge score with the judge's full response
- `pairwise_results.json` — every individual judgment with both orderings and the resolved winner

This lets you investigate specific cases: "Why did model_a win on correctness but lose on conciseness?" or "Which components caused the most disagreement between judges?"

---

## Changes Made to the Existing Codebase

Nothing in `src/` or the root-level scripts was modified. The benchmark is a
completely additive layer. The only connection to existing code is:

- `benchmark/objective/completeness.py` imports `src/evaluator/completeness.py`
- `benchmark/llm_judge/judge_llm.py` imports `src/agent/llm/openai_llm.py`
- `benchmark/generate_docstrings_for_model.py` calls `generate_docstrings.py` as a subprocess

The generation pipeline itself (`generate_docstrings.py`, `src/agent/`) is unchanged.
