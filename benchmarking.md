# DocAgent — Local Model Benchmarking Guide

> This document explains how docstring quality is currently evaluated in DocAgent,
> what the metric landscape looks like, and a concrete step-by-step plan for running
> a proper multi-model benchmark using locally-run Ollama models.

---

## Part 1: How the Current Evaluation Works

### The Generation Pipeline

DocAgent generates docstrings using a four-agent loop:

```
Reader → Searcher → Writer → Verifier
```

- **Reader** decides if more context is needed before writing
- **Searcher** fetches internal context (dependency graph, call relationships) and optionally external context (Perplexity web search)
- **Writer** produces the docstring given the gathered context
- **Verifier** checks quality and can either accept, send back to Writer with suggestions, or send back to Reader for more context

The key insight: DocAgent generates docstrings in **dependency order** (DFS from leaf components upward), so when a class is being documented, its methods already have docstrings that the agent can read.

The LLM backend is swappable — Claude, OpenAI, Gemini, HuggingFace, and Ollama are all supported via `src/agent/llm/`.

---

### What the Current Evaluation Measures

The project currently has three evaluation dimensions:

#### 1. Completeness — `eval_completeness.py` + `src/evaluator/completeness.py`

Pure AST-based, no LLM needed. Parses each file and checks whether required sections
are present in the docstring. Required sections are determined dynamically from the
code itself, not from a fixed checklist.

For **functions/methods**, required sections depend on what the code does:
- `summary` — always required
- `description` — always required
- `args` — only if there are parameters beyond `self`
- `returns` — only if there is a meaningful `return` statement
- `raises` — only if there are uncaught `raise` statements
- `examples` — only for public functions (not prefixed with `_`)

For **classes**, similar logic:
- `summary`, `description` — always
- `attributes` — only if the class has instance/class variables
- `parameters` — only if `__init__` takes arguments beyond `self`
- `examples` — only for public classes

Score: fraction of required sections present, 0.0–1.0.

#### 2. Helpfulness — `src/evaluate_helpfulness.py` + `src/evaluator/helpfulness_evaluator.py`

Uses an LLM as a judge (originally GPT-4o). Randomly samples 50 components where
all systems under comparison have valid docstrings, then scores each on 3 aspects:

| Aspect | What the judge asks |
|---|---|
| **Summary** | Does it add context beyond restating the function signature? |
| **Description** | Does it explain motivation, usage scenarios, integration, functionality? |
| **Parameters** | Do descriptions go beyond just repeating type hints? |

Each aspect has a detailed rubric (1–5 scale) with few-shot examples. The judge
reasons first, then outputs a score in `<score>N</score>` XML tags.

The same fixed random seed (42) is used for all systems, so the same 50 components
are evaluated across all models — enabling paired comparison.

#### 3. Truthfulness — `src/evaluator/truthfulness.py`

Uses Gemini 2.0 Flash to extract code component names mentioned in a docstring,
then checks them against the dependency graph to see if they actually exist in the repo.

Metrics: `existence_ratio`, `cross_file_ratio`, `avg_mentions_per_doc`.

Currently requires a Gemini API key. **Optional for a local-only setup.**

#### 4. Statistical Significance — `src/analyze_helpfulness_significance.py`

Runs **Wilcoxon signed-rank tests** on paired helpfulness scores between specified
system pairs. Non-parametric, appropriate for ordinal 1–5 scores. Reports p-value,
whether the difference is significant (p < 0.05), and which system is better.

---

### What the Current Evaluation Is Missing

The current setup is functional but narrow. Three specific gaps matter for a
rigorous model comparison:

1. **No parameter-level factuality check** — completeness checks if an `Args:` section
   exists, but not whether the parameters listed actually match the function signature.
2. **No return-value factuality check** — same problem for `Returns:`.
3. **Helpfulness uses only 3 LLM-judged dimensions** — missing correctness/faithfulness,
   clarity, conciseness, and non-redundancy, which the research literature identifies
   as important dimensions.
4. **No pairwise preference judgment** — the current setup scores each docstring
   independently. Having a judge directly compare two docstrings for the same component
   is a stronger signal.
5. **Hardcoded system names and pairs** throughout the evaluation scripts, making it
   friction-heavy to add new models.

---

---

## Part 2: The Expanded Metric Set

This section defines the full metric set for the new benchmark. The goal is to be
comprehensive but not overwhelming — every metric here is either computable without
an LLM, or maps directly to a well-defined judge question.

### Objective Metrics (AST-based, no LLM)

These are deterministic, fast, free to run, and not subject to judge inconsistency.

| Metric | How it's computed | Existing code |
|---|---|---|
| **Structural completeness** | Fraction of required sections present | `src/evaluator/completeness.py` ✅ |
| **Parameter coverage** | # params in signature ÷ # params documented in docstring | Needs to be written |
| **Parameter factuality** | Are all documented params actual params in the signature? | Needs to be written |
| **Return-value coverage** | Does a `Returns:` section exist when the function returns a value? | Partially in completeness.py ✅ |
| **Return-value factuality** | Does the return type in the docstring match the type annotation? | Needs to be written |
| **Default-value correctness** | If a default value is mentioned in the docstring, does it match the code? | Needs to be written |
| **Hallucinated entities** | Do component names mentioned in the docstring exist in the dependency graph? | `src/evaluator/truthfulness.py` ✅ (needs Gemini swap) |

**Coverage vs. factuality distinction:**
- *Coverage* = did you mention it at all?
- *Factuality* = is what you said correct/matching the actual code?

Both matter. A docstring that documents 5 non-existent parameters is worse than one
that accurately documents 3 out of 5 real parameters.

---

### LLM-Judged Metrics (multi-judge, 1–5 scale)

These require a capable judge model. Run on a sampled subset (50–100 components).
Each dimension gets its own prompt with a rubric and few-shot examples.

| Metric | What the judge asks | Existing code |
|---|---|---|
| **Correctness / Faithfulness** | Does it accurately describe what the code actually does? | Needs to be written |
| **Completeness** | Does it cover all important information about the code? | Needs to be written |
| **Helpfulness** | Is it genuinely useful to a developer reading it? | `src/evaluator/helpfulness_evaluator.py` ✅ |
| **Clarity** | Is it clear and understandable without extra effort? | Needs to be written |
| **Conciseness** | Does it avoid unnecessary verbosity and repetition? | Needs to be written |
| **Non-redundancy** | Does it provide information beyond what's obvious from the signature? | Partially in summary evaluator ✅ |
| **Overall preference** | Between docstring A and B for the same function, which is better? | Needs to be written (pairwise) |

**Why pairwise preference matters:** Point-wise scoring (scoring each docstring
independently) is noisier than directly comparing two docstrings. The judge can
hedge on a point-wise score but is forced to make a decision in a head-to-head
comparison. Use it as a tiebreaker and as a consistency check.

---

### How Objective and LLM Metrics Complement Each Other

They will often agree, but when they don't, that's the interesting result:

- A model that scores high on structural completeness but low on faithfulness →
  it generates plausible-looking but inaccurate docstrings
- A model that scores low on completeness but high on helpfulness →
  it writes useful summaries but skips boilerplate sections
- A model where objective and LLM metrics diverge significantly →
  worth investigating manually

Always preserve raw outputs so you can do this kind of analysis after the fact.

---

---

## Part 3: The New Benchmark Architecture

The core principle: **do not modify DocAgent's generation pipeline**. Treat generation
as a black box that produces datasets. Build evaluation as a completely separate layer.

### Proposed Directory Structure

```
benchmark/
├── generate_comparison_dataset.py   ← collects all 5 models' outputs into one JSON
│
├── objective/
│   ├── completeness.py              ← wraps existing src/evaluator/completeness.py
│   ├── parameter_coverage.py        ← NEW: coverage + factuality for args
│   ├── factuality.py                ← NEW: return type, default value checks
│   └── hallucination.py             ← wraps/replaces src/evaluator/truthfulness.py
│
├── llm_judge/
│   ├── pairwise_evaluator.py        ← NEW: head-to-head preference judgments
│   ├── pointwise_evaluator.py       ← extends existing helpfulness evaluator
│   ├── prompts.py                   ← all judge prompts in one place
│   └── aggregate.py                 ← computes per-system averages, agreement stats
│
├── statistics/
│   ├── pairwise_ranking.py          ← NEW: ranks models by win rate from pairwise
│   ├── wilcoxon.py                  ← wraps existing analyze_significance.py logic
│   └── agreement.py                 ← NEW: inter-judge agreement (if using multiple judges)
│
└── results/
    ├── raw_generations/             ← one subfolder per model, copy of generated repo
    ├── objective/                   ← JSON outputs from objective metrics
    ├── llm_judgments/               ← JSON with every individual judge decision
    └── final_results/               ← summary tables, significance tests, final report
```

### What maps to existing code

| New file | Maps from existing code |
|---|---|
| `benchmark/objective/completeness.py` | `eval_completeness.py` + `src/evaluator/completeness.py` |
| `benchmark/llm_judge/pointwise_evaluator.py` | `src/evaluator/helpfulness_evaluator.py` |
| `benchmark/llm_judge/prompts.py` | `src/evaluator/helpfulness_summary/description/parameters.py` |
| `benchmark/statistics/wilcoxon.py` | `src/analyze_helpfulness_significance.py` |
| `benchmark/objective/hallucination.py` | `src/evaluator/truthfulness.py` (minus Gemini dependency) |

Everything else in the `benchmark/` directory is new.

---

---

## Part 4: Step-by-Step Execution Plan

### Prerequisites

- Ollama installed and running: `ollama serve`
- 6 models pulled — 5 generators + 1 judge
- DocAgent dependencies installed (see `INSTALL.md`)
- A target Python repository with no existing docstrings (or use `--overwrite-docstrings`)

---

### Step 1: Decide Your Models

Pick 5 generator models and 1 judge model. Example lineup:

```
Generator A:  qwen2.5-coder:7b
Generator B:  llama3.1:8b
Generator C:  deepseek-coder:6.7b
Generator D:  codestral:7b
Generator E:  starcoder2:7b

Judge:        qwen2.5-coder:14b   (or any capable model you trust to follow instructions)
```

**On judge model selection:** The judge needs to reliably follow structured prompts
and output `<score>N</score>` XML tags. Before committing to a judge, send it one
sample prompt and verify it responds in the expected format. A 14B+ model is
strongly preferred over a 7B model for judging.

---

### Step 2: Create One Config Per Generator Model

Copy `config/example_config.yaml` five times. **Change only the `model:` field.**
Everything else — `temperature`, `max_input_tokens`, `flow_control` — must be
identical across all five configs. Different settings would confound the comparison.

```
config/bench_model_A.yaml   →  model: "qwen2.5-coder:7b"
config/bench_model_B.yaml   →  model: "llama3.1:8b"
config/bench_model_C.yaml   →  model: "deepseek-coder:6.7b"
config/bench_model_D.yaml   →  model: "codestral:7b"
config/bench_model_E.yaml   →  model: "starcoder2:7b"
```

Template for each config:
```yaml
llm:
  type: "ollama"
  model: "<model-name-here>"
  api_base: "http://localhost:11434/v1"
  api_key: "ollama"
  temperature: 0.1
  max_output_tokens: 4096
  max_input_tokens: 8000

flow_control:
  max_reader_search_attempts: 2
  max_verifier_rejections: 1
  status_sleep_time: 0

docstring_options:
  overwrite_docstrings: true
```

---

### Step 3: Keep a Clean Copy of the Target Repo

```bash
cp -r data/raw_test_repo data/raw_test_repo_ORIGINAL
```

You will restore from this before every generation run.

---

### Step 4: Generate Docstrings with Each Model (5 runs)

Run the following cycle for each model. This is the only step that touches DocAgent's
generation code — everything after this is pure evaluation.

```bash
# --- Model A ---
cp -r data/raw_test_repo_ORIGINAL data/raw_test_repo

python generate_docstrings.py \
  --repo-path data/raw_test_repo \
  --config-path config/bench_model_A.yaml \
  --overwrite-docstrings

cp -r data/raw_test_repo benchmark/results/raw_generations/qwen2.5-coder-7b

# --- Repeat for B, C, D, E ---
```

After all 5 runs:
```
benchmark/results/raw_generations/
    qwen2.5-coder-7b/
    llama3.1-8b/
    deepseek-coder-6.7b/
    codestral-7b/
    starcoder2-7b/
```

---

### Step 5: Build the Comparison Dataset (NEW SCRIPT)

This is the central step. Write `benchmark/generate_comparison_dataset.py`.

It walks all 5 generated repo copies, extracts docstrings via AST, runs completeness
scoring, and merges everything into a single JSON keyed by component path and system name.

**Input:** the 5 directories from Step 4 + original repo for source code ground truth
**Output:** `benchmark/results/comparison_dataset.json`

Expected structure:
```json
{
  "raw_test_repo/vending_machine.VendingMachine.add_product": {
    "type": "method",
    "source_code": "def add_product(self, product_id: str, price: float) -> bool:\n    ...",
    "signature": "add_product(self, product_id: str, price: float) -> bool",
    "actual_params": ["product_id", "price"],
    "actual_return_type": "bool",
    "has_raise": true,
    "docstrings": {
      "qwen2.5-coder-7b": {
        "docstring": "Adds a product to the vending machine...",
        "element_scores": {
          "summary": true,
          "description": true,
          "args": true,
          "returns": true,
          "raises": false,
          "examples": false
        }
      },
      "llama3.1-8b": {
        "docstring": "...",
        "element_scores": { ... }
      }
    }
  }
}
```

Including `actual_params`, `actual_return_type`, and `has_raise` in the dataset
means the objective factuality checks can run directly against this JSON without
re-parsing source files.

---

### Step 6: Run Objective Metrics

#### 6a. Structural Completeness

Already works. Can be run on each raw generation folder directly:

```bash
python eval_completeness.py benchmark/results/raw_generations/qwen2.5-coder-7b
```

Or write `benchmark/objective/completeness.py` to read from the comparison dataset
JSON and produce a structured output to `benchmark/results/objective/completeness.json`.

#### 6b. Parameter Coverage and Factuality (NEW)

Write `benchmark/objective/parameter_coverage.py`:

- **Coverage:** for each component, count `actual_params` vs how many appear in the
  docstring's `Args:` section. Coverage = documented / total.
- **Factuality:** check the inverse — are any names in the `Args:` section that do
  not appear in `actual_params`? Those are hallucinated parameter names.

Both are pure string matching against the AST data already in the comparison dataset.

#### 6c. Return-Value and Default-Value Factuality (NEW)

Write `benchmark/objective/factuality.py`:

- **Return factuality:** if `actual_return_type` is annotated in the signature, does
  the `Returns:` section mention a compatible type?
- **Default-value correctness:** if the docstring mentions a default value for a
  parameter (e.g., "defaults to 0"), does it match the actual default in the
  function signature from the AST?

#### 6d. Hallucinated Entities

`src/evaluator/truthfulness.py` currently uses Gemini. For a local-only setup,
write `benchmark/objective/hallucination.py` that uses your judge Ollama model instead
of Gemini to extract mentioned component names, then checks them against the
dependency graph JSON at `output/dependency_graphs/`.

---

### Step 7: Run LLM-Judged Metrics

#### 7a. Configure the Judge

The existing `src/evaluator/helpfulness_evaluator.py` uses OpenAI. Two changes needed:

**Change 1 — swap the LLM backend** in `src/evaluator/helpfulness_evaluator.py`:

```python
# Remove:
from src.agent.llm.openai_llm import OpenAILLM
self.llm = OpenAILLM(api_key=api_key, model=model)

# Add:
from src.agent.llm.ollama_llm import OllamaLLM
self.llm = OllamaLLM(model="qwen2.5-coder:14b", api_base="http://localhost:11434/v1")
```

**Change 2 — update the SYSTEMS list** in the same file:

```python
SYSTEMS = [
    "qwen2.5-coder-7b",
    "llama3.1-8b",
    "deepseek-coder-6.7b",
    "codestral-7b",
    "starcoder2-7b",
]
```

Names must exactly match the keys used in the comparison dataset JSON.

#### 7b. Extend the Point-wise Judge (NEW dimensions)

The existing `helpfulness_evaluator.py` covers summary, description, and parameters.
Write or extend it in `benchmark/llm_judge/pointwise_evaluator.py` to add:

| New dimension | What the judge is asked |
|---|---|
| **Correctness / Faithfulness** | "Does this docstring accurately describe what the code does? Are there any statements that contradict the implementation?" |
| **Clarity** | "Is this docstring clear and understandable to a developer unfamiliar with this codebase?" |
| **Conciseness** | "Does this docstring avoid unnecessary verbosity? Does it repeat information that is already obvious?" |
| **Non-redundancy** | "Does this docstring provide meaningful information beyond what can already be inferred from the function name and signature?" |

Each dimension gets a rubric (1–5) and at least one good/poor example in the prompt.
All prompts should live in `benchmark/llm_judge/prompts.py` so they can be updated
without touching the evaluation logic.

#### 7c. Add Pairwise Preference Judgment (NEW)

Write `benchmark/llm_judge/pairwise_evaluator.py`.

For a sampled subset of components, present the judge with two docstrings side by side
and ask: which is better overall, and why?

```
Component: VendingMachine.add_product
Code: [source code here]

Docstring A:
[qwen2.5-coder-7b output]

Docstring B:
[llama3.1-8b output]

Which docstring is more useful to a developer? Answer A, B, or TIE.
Briefly explain your reasoning.
```

Run this for all C(5,2) = 10 model pairs across the sampled components.
Results go into `benchmark/results/llm_judgments/pairwise/`.

**Important:** randomize which model appears as A vs B to detect position bias.
Run each pair twice with positions swapped, and flag cases where the judge changes
its answer.

#### 7d. Run Point-wise Eval

```bash
python src/evaluate_helpfulness.py \
  --data-path benchmark/results/comparison_dataset.json \
  --output-dir benchmark/results/llm_judgments/pointwise \
  --n-samples 50 \
  --seed 42
```

All raw individual judge decisions must be saved — not just averages.

---

### Step 8: Run Statistical Analysis

#### 8a. Wilcoxon Tests (existing, needs config update)

Update `src/analyze_helpfulness_significance.py` to use all C(5,2) = 10 model pairs:

```python
system_pairs = [
    ("qwen2.5-coder-7b", "llama3.1-8b"),
    ("qwen2.5-coder-7b", "deepseek-coder-6.7b"),
    ("qwen2.5-coder-7b", "codestral-7b"),
    ("qwen2.5-coder-7b", "starcoder2-7b"),
    ("llama3.1-8b", "deepseek-coder-6.7b"),
    ("llama3.1-8b", "codestral-7b"),
    ("llama3.1-8b", "starcoder2-7b"),
    ("deepseek-coder-6.7b", "codestral-7b"),
    ("deepseek-coder-6.7b", "starcoder2-7b"),
    ("codestral-7b", "starcoder2-7b"),
]
```

Run per-metric and overall.

#### 8b. Pairwise Win Rate Ranking (NEW)

Write `benchmark/statistics/pairwise_ranking.py` that reads the pairwise judgments
and computes a win/loss/tie table across all model pairs, then ranks models by
win rate. This is a more interpretable final ranking than averaging scores.

```
Final Ranking (by pairwise win rate):
1. codestral-7b        — 68% win rate
2. qwen2.5-coder-7b   — 61% win rate
3. llama3.1-8b         — 52% win rate
...
```

#### 8c. Judge Agreement Check (NEW, optional but recommended)

If you run the helpfulness eval with multiple judge models (e.g., both qwen:14b and
llama3.1:70b), write `benchmark/statistics/agreement.py` to compute inter-judge
agreement using Cohen's Kappa or Spearman correlation. Low agreement means the
metric is noisy and results should be interpreted carefully.

---

### Step 9: Produce Final Report

Aggregate all outputs into a single results document:

```
benchmark/results/final_results/
    summary_table.md           ← one row per model, one column per metric
    objective_breakdown.json   ← per-component objective scores
    llm_breakdown.json         ← per-component LLM scores
    pairwise_matrix.md         ← win/loss table for all pairs
    significance_tests.md      ← Wilcoxon results
```

The summary table should look something like:

| Model | Completeness | Param Coverage | Param Factuality | Faithfulness | Helpfulness | Clarity | Win Rate |
|---|---|---|---|---|---|---|---|
| qwen2.5-coder-7b | 0.82 | 0.76 | 0.91 | 3.8 | 3.6 | 4.1 | 61% |
| llama3.1-8b | 0.74 | 0.68 | 0.88 | 3.5 | 3.9 | 3.7 | 52% |
| ... | | | | | | | |

---

---

## Part 5: What Needs to Be Built

### Must-have (pipeline doesn't work without these)

| Task | File | Notes |
|---|---|---|
| Comparison dataset builder | `benchmark/generate_comparison_dataset.py` | Central new script |
| Swap judge LLM to Ollama | `src/evaluator/helpfulness_evaluator.py` | ~5 line change |
| Update SYSTEMS list | `src/evaluator/helpfulness_evaluator.py` | ~5 line change |
| Update system pairs | `src/analyze_helpfulness_significance.py` | Update list |

### Should-have (significantly improves rigor)

| Task | File | Notes |
|---|---|---|
| Parameter coverage + factuality | `benchmark/objective/parameter_coverage.py` | AST-based, no LLM |
| Return/default factuality | `benchmark/objective/factuality.py` | AST-based, no LLM |
| Faithfulness judge prompt + evaluator | `benchmark/llm_judge/pointwise_evaluator.py` | New dimension |
| Clarity, conciseness, non-redundancy prompts | `benchmark/llm_judge/prompts.py` | New dimensions |
| Pairwise preference evaluator | `benchmark/llm_judge/pairwise_evaluator.py` | Strongest signal |
| Pairwise win rate ranking | `benchmark/statistics/pairwise_ranking.py` | Clean final ranking |

### Nice-to-have (polish)

| Task | File | Notes |
|---|---|---|
| Hallucination eval without Gemini | `benchmark/objective/hallucination.py` | Swap Gemini → Ollama judge |
| Inter-judge agreement | `benchmark/statistics/agreement.py` | Needs 2+ judges |
| Final report generator | `benchmark/results/final_results/` | Aggregates all outputs |

---

## Part 6: Key Principles to Follow

**Preserve all raw outputs.**
Never save only averages. Every individual judge decision, every per-component score,
every raw docstring — keep all of it. This is what lets you later answer "why did
Model A beat Model B on faithfulness?" or "did the objective and LLM metrics agree?"

**Separate generation from evaluation.**
Don't modify DocAgent's generation pipeline for this experiment. Treat `generate_docstrings.py`
as a black box. All the new work lives in `benchmark/`.

**Keep configs identical across models.**
Temperature, max tokens, flow control — identical for all 5 generators. The only
variable should be the model name.

**Use a fixed random seed.**
Seed 42 is already used in the existing helpfulness evaluator. Keep it consistent
everywhere so results are reproducible.

**Document your judge model.**
The judge model is itself a variable in the experiment. Always record which model
was used as the judge alongside the results, so future runs with a different judge
can be compared.

**Run pairwise first, point-wise second.**
If you're short on time or compute, pairwise preference judgments give you a ranking
faster and with less noise than averaging point-wise scores across 7 dimensions.
