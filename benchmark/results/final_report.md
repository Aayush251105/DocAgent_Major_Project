# DocAgent — Model Benchmark Report
_Generated: 2026-09-08 13:40_

## Models Evaluated

- **qwen2.5-coder-1.5b** (`qwen2.5-coder:1.5b`)
- **qwen3-4b** (`qwen3:4b`)
- **qwen2.5-coder-3b** (`qwen2.5-coder:3b`)
- **qwen2.5-coder-7b** (`qwen2.5-coder:7b`)

> **Judge protocol:** Leave-one-out. When model X is evaluated, judges are all other models.

---

## 1. Pairwise Win Rate Ranking

Primary metric. Each matchup is judged by the 3 remaining models.
Position bias is controlled by running each pair in both orderings;
a win is only counted when the judge agrees across both orderings.

| Rank | Model | Win Rate | W | L | T | Total Decisions |
| ---- | ----- | -------- | - | - | - | --------------- |
| 1 | qwen2.5-coder-7b | **17.9%** | 30 | 6 | 132 | 168 |
| 2 | qwen3-4b | **16.1%** | 27 | 51 | 90 | 168 |
| 3 | qwen2.5-coder-1.5b | **13.7%** | 23 | 36 | 109 | 168 |
| 4 | qwen2.5-coder-3b | **12.5%** | 21 | 8 | 139 | 168 |

---

## 2. Pairwise Head-to-Head Results

Each cell shows `W / L / T` (wins, losses, ties) for the **row model** against the **column model**.

| Model | qwen2.5-coder-1.5b | qwen3-4b | qwen2.5-coder-3b | qwen2.5-coder-7b |
| --- | --- | --- | --- | --- |
| **qwen2.5-coder-1.5b** | — | 15/21/20 | 3/2/51 | 5/13/38 |
| **qwen3-4b** | 21/15/20 | — | 5/19/32 | 1/17/38 |
| **qwen2.5-coder-3b** | 2/3/51 | 19/5/32 | — | 0/0/56 |
| **qwen2.5-coder-7b** | 13/5/38 | 17/1/38 | 0/0/56 | — |

---

## 3. Full Metrics Summary

Completeness is AST-based (0–1). All other scores are LLM-judged (1–5, averaged across leave-one-out judges).

| Model | Complete. | Summary | Desc. | Params | Correct. | Clarity | Concise. | LLM Avg | Win Rate |
| ----- | --------- | ------- | ----- | ------ | -------- | ------- | -------- | ------- | -------- |
| qwen2.5-coder-7b | 0.821 | 3.875 | 3.804 | 3.456 | 3.947 | 3.839 | 4.018 | 3.823 | **17.9%** |
| qwen3-4b | 0.549 | 3.049 | 2.762 | 2.795 | 3.440 | 3.393 | 3.905 | 3.224 | **16.1%** |
| qwen2.5-coder-1.5b | 0.754 | 3.089 | 4.672 | 3.466 | 4.930 | 4.397 | 3.357 | 3.985 | **13.7%** |
| qwen2.5-coder-3b | 0.805 | 2.750 | 4.143 | 3.310 | 4.404 | 4.143 | 3.625 | 3.729 | **12.5%** |

---

## 4. Structural Completeness (AST-based)

Score = fraction of required docstring sections present (0–1). Required sections are determined from the code itself (e.g. `Args` only if the function has parameters, `Raises` only if there are raise statements).

| Model | Average Completeness |
| ----- | -------------------- |
| qwen2.5-coder-7b | 0.821 |
| qwen3-4b | 0.549 |
| qwen2.5-coder-1.5b | 0.754 |
| qwen2.5-coder-3b | 0.805 |

---

## 5. Point-wise LLM Judge Scores

Each score is 1–5, averaged across all leave-one-out judges and sampled components.

| Model | Summary | Description | Parameters | Correctness | Clarity | Conciseness |
| ----- | ------- | ----------- | ---------- | ----------- | ------- | ----------- |
| qwen2.5-coder-7b | 3.875 | 3.804 | 3.456 | 3.947 | 3.839 | 4.018 |
| qwen3-4b | 3.049 | 2.762 | 2.795 | 3.440 | 3.393 | 3.905 |
| qwen2.5-coder-1.5b | 3.089 | 4.672 | 3.466 | 4.930 | 4.397 | 3.357 |
| qwen2.5-coder-3b | 2.750 | 4.143 | 3.310 | 4.404 | 4.143 | 3.625 |

---

## 6. Methodology

- **Components sampled per evaluation:** 50
- **Random seed:** 42
- **Judging:** Leave-one-out. For model X, judges are the other N−1 models.
- **Pairwise position bias control:** Each pair run twice with A/B positions swapped. Final winner requires agreement across both orderings; disagreement → TIE.
- **Objective completeness:** Pure AST parsing, no LLM involved.
- **Point-wise scoring:** 6 dimensions (summary, description, parameters, correctness, clarity, conciseness), score 1–5 per judge.
