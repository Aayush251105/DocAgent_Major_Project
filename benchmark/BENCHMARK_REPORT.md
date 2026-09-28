# DocAgent — Benchmarking Methodology and Results

> **Note on scope:** The results in this document are from a first round of evaluation
> using models available locally via **Ollama**. This is an ongoing effort — the same
> benchmark infrastructure is designed to run against any number of additional models,
> and we are actively extending the comparison set. A list of candidate models for the
> next round is included at the end of this document.

---

## 1. What We Are Benchmarking

DocAgent is a multi-agent system that generates Python docstrings. It uses a
four-agent loop — Reader, Searcher, Writer, Verifier — and processes code in
dependency order (leaf functions first, classes last) so that each component is
documented with full knowledge of its dependencies.

The LLM backend is swappable. The benchmark isolates the effect of the underlying
model by holding everything else constant: same pipeline, same configuration,
same source code, same temperature. The only variable is the model name.

The central question is: **for docstring generation, which locally-runnable model
produces the most useful output?**

---

## 2. Models Tested (Round 1 — Ollama)

All models were run locally via Ollama on the same machine with identical generation
settings (temperature 0.1, max output tokens 4096, max input tokens 8000).

| Model Label | Ollama Tag | Parameter Count |
|-------------|------------|-----------------|
| qwen2.5-coder-1.5b | `qwen2.5-coder:1.5b` | 1.5B |
| qwen2.5-coder-3b | `qwen2.5-coder:3b` | 3B |
| qwen3-4b | `qwen3:4b` | 4B |
| qwen2.5-coder-7b | `qwen2.5-coder:7b` | 7B |

These models were chosen to explore the quality-size tradeoff within the Qwen family,
comparing a general-purpose model (qwen3-4b) against code-specialised variants
(qwen2.5-coder series) at different scales.

---

## 3. How the Benchmark Works

The evaluation pipeline has three independent layers. They are designed to
complement each other — objective metrics are fast and deterministic, LLM metrics
capture quality that AST analysis cannot, and pairwise judgments provide the
cleanest ranking signal.

### 3.1 Objective Metrics (No LLM)

These are computed entirely by static analysis of the generated code using Python's
`ast` module. They are deterministic, reproducible, and free to run.

**Structural Completeness (score: 0.0 – 1.0)**

For each documented component, we inspect the code and determine which docstring
sections are *required* — not from a fixed template, but from the code itself:

| Section | Required when... |
|---------|-----------------|
| Summary | Always |
| Description | Always |
| Args | Function has parameters beyond `self` |
| Returns | Function has a non-None return statement or yield |
| Raises | Function has uncaught `raise` statements |
| Examples | Function/class is public (not prefixed with `_`) |
| Attributes | Class has instance or class variables |
| Parameters | Class `__init__` has arguments beyond `self` |

The score is the fraction of required sections that are actually present. A score
of 1.0 means every section the code demands is documented. This tells us whether
the model produces structurally complete documentation, independent of whether the
content is accurate or useful.

### 3.2 LLM-Judged Point-wise Scoring (score: 1 – 5 per dimension)

A random sample of 50 components is selected where all models produced a non-empty
docstring (same 50 components across all models, fixed seed 42). Each docstring is
scored on six dimensions by a panel of judges.

**The six dimensions:**

| Dimension | What the judge evaluates |
|-----------|--------------------------|
| **Summary** | Does the one-liner add meaningful context beyond restating the signature? |
| **Description** | Does the extended description cover motivation, usage scenarios, and integration? |
| **Parameters** | Do parameter descriptions go beyond type hints to explain purpose and constraints? |
| **Correctness** | Does the docstring accurately describe what the code actually does? Any contradictions? |
| **Clarity** | Is the docstring immediately understandable to a developer unfamiliar with this codebase? |
| **Conciseness** | Does it avoid verbosity and repetition? Does every sentence add value? |

Each dimension uses a detailed 1–5 rubric with concrete examples at each level.
The judge is instructed to reason before scoring and output its score in a
structured XML tag (`<score>N</score>`) so scores can be parsed reliably.

**Judge selection — Leave-one-out protocol:**

No model ever judges its own output. When model X is being evaluated, the judges
are all other models in the benchmark set. Their scores are averaged to produce the
final per-dimension score for model X. This eliminates self-serving bias and also
gives us inter-judge agreement data as a side effect.

### 3.3 Pairwise Preference Judgment (primary ranking signal)

For every pair of models (all C(4,2) = 6 combinations in this round), a panel of
judges directly compares two docstrings for the same component side by side and
decides which is more useful overall.

This is a stronger signal than point-wise scoring for two reasons:
- The judge must commit to a winner rather than hedging with a mid-range score.
- It directly answers the practical question: "If I had to pick one of these two
  docstrings to ship, which would I choose?"

**Position bias control:**

Each pair is judged twice — once with model A's docstring shown first (A vs B),
and once with model B's docstring shown first (B vs A). A win is only counted when
the judge picks the same model in both orderings. If the judge flips, it is recorded
as a TIE. This eliminates the tendency of LLMs to favour whichever docstring appears
in the first position.

**Leave-one-out judging for pairs:**

When comparing model A vs model B, the judges are all remaining models (C, D, ...).
This means no model involved in a matchup influences the verdict on that matchup.

The final ranking is determined by **win rate** — the fraction of all individual
judgment decisions that a model won across all its matchups.

---

## 4. Results (Round 1)

### 4.1 Pairwise Win Rate — Primary Ranking

| Rank | Model | Win Rate | Wins | Losses | Ties | Total Decisions |
|------|-------|----------|------|--------|------|-----------------|
| 1 | **qwen2.5-coder-7b** | **17.9%** | 30 | 6 | 132 | 168 |
| 2 | qwen3-4b | 16.1% | 27 | 51 | 90 | 168 |
| 3 | qwen2.5-coder-1.5b | 13.7% | 23 | 36 | 109 | 168 |
| 4 | qwen2.5-coder-3b | 12.5% | 21 | 8 | 139 | 168 |

**Reading the win rates:** The absolute win rate percentages are low because the
majority of decisions are ties. A tie occurs when the judge either genuinely cannot
distinguish quality, or flips its answer between the two orderings (position bias
catch). The ranking signal comes from the *relative* win rates and especially the
win/loss ratio.

**Notable observation:** qwen2.5-coder-7b leads on win rate (30 wins, only 6 losses —
a 5:1 ratio) while qwen2.5-coder-3b, despite its similar completeness score, wins
21 but loses only 8 — suggesting the 3b model is rarely clearly worse but also rarely
clearly better, making it a cautious middle-ground performer.

### 4.2 Head-to-Head Matrix

Each cell shows `W / L / T` (wins / losses / ties) for the **row model** against the
**column model**.

| | qwen2.5-coder-1.5b | qwen3-4b | qwen2.5-coder-3b | qwen2.5-coder-7b |
|---|---|---|---|---|
| **qwen2.5-coder-1.5b** | — | 15/21/20 | 3/2/51 | 5/13/38 |
| **qwen3-4b** | 21/15/20 | — | 5/19/32 | 1/17/38 |
| **qwen2.5-coder-7b** | 13/5/38 | 17/1/38 | 0/0/56 | — |
| **qwen2.5-coder-3b** | 2/3/51 | 19/5/32 | — | 0/0/56 |

Key observations:
- **qwen2.5-coder-7b vs qwen3-4b:** 17 wins, only 1 loss — the clearest head-to-head result in the dataset, strongly favouring the code-specialised 7b model over the general-purpose 4b model.
- **qwen2.5-coder-7b vs qwen2.5-coder-3b:** 56 ties, 0 wins, 0 losses — judges could not reliably distinguish these two models when directly compared, suggesting the 3b model gets very close to the 7b model's output quality in many cases.
- **qwen3-4b vs qwen2.5-coder-3b:** qwen3-4b loses this matchup (5 wins, 19 losses), despite being a larger general model — code specialisation at 3B beats general capability at 4B for this task.

### 4.3 Structural Completeness

| Model | Average Completeness |
|-------|---------------------|
| qwen2.5-coder-7b | **0.821** |
| qwen2.5-coder-3b | 0.805 |
| qwen2.5-coder-1.5b | 0.754 |
| qwen3-4b | 0.549 |

qwen3-4b drops sharply here. A completeness score of 0.549 means the model is
leaving roughly half of required sections undocumented on average — it tends to
write good prose when it does write, but frequently omits entire sections.

### 4.4 Point-wise LLM Judge Scores (1–5)

| Model | Summary | Desc. | Params | Correct. | Clarity | Concise. | Overall Avg |
|-------|---------|-------|--------|----------|---------|----------|-------------|
| qwen2.5-coder-7b | 3.875 | 3.804 | 3.456 | 3.947 | 3.839 | 4.018 | **3.823** |
| qwen2.5-coder-1.5b | 3.089 | **4.672** | 3.466 | **4.930** | **4.397** | 3.357 | 3.985 |
| qwen2.5-coder-3b | 2.750 | 4.143 | 3.310 | 4.404 | 4.143 | 3.625 | 3.729 |
| qwen3-4b | 3.049 | 2.762 | 2.795 | 3.440 | 3.393 | **3.905** | 3.224 |

### 4.5 Interpreting the Divergence Between Point-wise and Pairwise

The most interesting result here is **qwen2.5-coder-1.5b**. It scores highest on
three point-wise dimensions (description, correctness, clarity) and has the highest
LLM average (3.985), yet it ranks **3rd on win rate**. How?

Point-wise scores and pairwise preferences measure related but different things:
- Point-wise scoring rates each docstring *in isolation* against a rubric.
- Pairwise judgment compares two docstrings for the *same function* — the judge
  sees both and decides which it would rather have.

The 1.5b model likely writes longer, descriptive docstrings that score well when
read alone (hence high description and correctness scores) but lose head-to-head
when a judge compares them against a more focused alternative from the 7b model.
This is consistent with its **lower conciseness score (3.357)** — it writes more,
which reads well in isolation, but judges prefer the tighter output of the 7b model
when given a direct choice.

This is exactly why pairwise judgment is the primary metric: it better reflects
the real-world developer experience of choosing one docstring over another.

---

## 5. Summary Findings

1. **qwen2.5-coder-7b is the best overall performer** in this round — highest win
   rate, highest completeness, and well-balanced scores across all six quality
   dimensions. Its win/loss ratio (30:6) is the most decisive in the dataset.

2. **Code specialisation matters more than size** — qwen2.5-coder-3b (3B, code
   specialised) outperforms qwen3-4b (4B, general purpose) in pairwise matchups,
   even though it's smaller. For docstring generation specifically, domain-specific
   training is more valuable than extra parameters.

3. **Completeness and quality diverge for small models** — qwen2.5-coder-1.5b achieves
   competitive point-wise scores but leaves more sections incomplete (0.754 vs 0.821
   for the 7b model) and loses on conciseness, causing it to drop in pairwise preference.

4. **qwen3-4b is the weakest performer despite its size** — the general-purpose model
   under-indexes on structural completeness (0.549) and loses most of its direct
   matchups against the code-specialised models. General reasoning ability does not
   compensate for lack of code documentation training at this scale.

5. **The high tie rate is expected and healthy** — a large fraction of TIE results
   means the models are broadly competitive. The benchmark correctly avoids inflating
   differences through position bias.

---

## 6. Planned Next Round — Additional Models

The benchmark infrastructure is model-agnostic. Any model available via Ollama
(or any OpenAI-compatible endpoint) can be added by updating `benchmark/config.yaml`.
The following models are strong candidates for the next evaluation round:

### Code-Specialised Models

| Model | Ollama Tag | Notes |
|-------|------------|-------|
| DeepSeek Coder V2 Lite | `deepseek-coder-v2:16b` | Strong code model, MoE architecture |
| DeepSeek Coder 6.7B | `deepseek-coder:6.7b` | Direct competitor to qwen2.5-coder-7b |
| CodeLlama 7B | `codellama:7b` | Meta's code-specific model, well-established baseline |
| CodeLlama 13B | `codellama:13b` | Larger variant, good for judge role |
| Starcoder2 7B | `starcoder2:7b` | BigCode project, trained on 600+ languages |
| Codestral 7B | `codestral:7b` | Mistral's code model |
| Granite Code 8B | `granite-code:8b` | IBM's code model, Apache 2.0 licence |

### General-Purpose Models (for comparison)

| Model | Ollama Tag | Notes |
|-------|------------|-------|
| Llama 3.1 8B | `llama3.1:8b` | Meta's general model, strong instruction following |
| Mistral 7B | `mistral:7b` | Strong general baseline, good context handling |
| Gemma 2 9B | `gemma2:9b` | Google's open model, competitive at 9B scale |
| Phi-3.5 Mini | `phi3.5:3.8b` | Microsoft, surprisingly capable at small size |
| Qwen2.5 7B | `qwen2.5:7b` | General variant — compare directly against coder variant |

### Larger Models (for judge role or upper-bound comparison)

| Model | Ollama Tag | Notes |
|-------|------------|-------|
| Qwen2.5-Coder 14B | `qwen2.5-coder:14b` | Larger coder model, strong judge candidate |
| Llama 3.1 70B (Q4) | `llama3.1:70b` | Requires ~40GB RAM, high-quality judge |
| DeepSeek Coder 33B | `deepseek-coder:33b` | Requires significant VRAM |

> **Recommendation for next round:** Add `deepseek-coder:6.7b`, `codellama:7b`,
> `starcoder2:7b`, `llama3.1:8b`, and `mistral:7b` as the five generator models.
> Use `qwen2.5-coder:14b` or `codellama:13b` as an external judge (outside the
> leave-one-out pool) for a cross-validation check on the judging quality.

---

## 7. Limitations of This Round

- **Small model pool:** Four models from one family (Qwen) limits generalisability.
  The next round will introduce architectural diversity.
- **Small test repo:** The benchmark was run on `data/raw_test_repo`, a synthetic
  test repository. Results may differ on a larger, real-world codebase.
- **No external judge cross-validation:** All judges in Round 1 are also generators.
  Adding a dedicated external judge (not in the generator pool) would let us
  validate the leave-one-out judgments independently.
- **No statistical significance testing:** With 168 total decisions per model, some
  differences (especially between ranks 2–4) may not be statistically significant.
  Wilcoxon signed-rank tests on the point-wise paired scores are planned for the
  next round.

---

## 8. Reproducibility

All results are fully reproducible:

- Fixed random seed (42) used for all sampling
- All raw judge responses are stored in `benchmark/results/llm_judgments/`
- Per-model configs are stored in `benchmark/configs/`
- Generation is isolated — each model's output is in its own folder under
  `benchmark/results/raw_generations/`, the original repo is never modified

To reproduce this run:
```bash
# 1. Set models in benchmark/config.yaml
# 2. Generate docstrings (one isolated copy per model)
python benchmark/generate_docstrings_for_model.py --all

# 3. Run full evaluation
python benchmark/run_benchmark.py
```
