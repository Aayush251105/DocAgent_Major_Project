# DocAgent — Model Benchmark Report
_Generated: 2026-10-11 20:52_

## Models Evaluated

- **qwen2.5-coder-7b** (`qwen2.5-coder:7b`) — generation time: —
- **qwen3-8b** (`qwen3:8b`) — generation time: 32m 30s
- **llama3.1-8b** (`llama3.1:8b`) — generation time: 12m 58s
- **mistral-7b** (`mistral:7b`) — generation time: 10m 04s
- **deepseek-coder-6.7b** (`deepseek-coder:6.7b`) — generation time: 28m 50s
- **codegemma-7b** (`codegemma:7b`) — generation time: 8m 57s
- **codellama-7b** (`codellama:7b`) — generation time: 17m 50s
- **yi-coder-9b** (`yi-coder:9b`) — generation time: 14m 18s

> **Judge protocol:** Leave-one-out. When model X is evaluated, judges are all other models.

---

## 1. Pairwise Win Rate Ranking

Primary metric. Each matchup is judged by the 3 remaining models.
Position bias is controlled by running each pair in both orderings;
a win is only counted when the judge agrees across both orderings.

| Rank | Model | Win Rate | W | L | T | Total Decisions |
| ---- | ----- | -------- | - | - | - | --------------- |
| 1 | codellama-7b | **42.3%** | 497 | 110 | 569 | 1176 |
| 2 | yi-coder-9b | **40.7%** | 479 | 56 | 641 | 1176 |
| 3 | deepseek-coder-6.7b | **19.2%** | 226 | 233 | 717 | 1176 |
| 4 | qwen2.5-coder-7b | **18.0%** | 212 | 243 | 721 | 1176 |
| 5 | mistral-7b | **17.7%** | 208 | 259 | 709 | 1176 |
| 6 | qwen3-8b | **11.7%** | 137 | 335 | 704 | 1176 |
| 7 | llama3.1-8b | **9.6%** | 113 | 355 | 708 | 1176 |
| 8 | codegemma-7b | **8.7%** | 102 | 383 | 691 | 1176 |

---

## 2. Docstring Generation Time

Wall-clock time for DocAgent to generate docstrings across the entire test repository with each model. Measured end-to-end including reader, searcher, writer, and verifier passes.

| Model | Ollama Tag | Generation Time |
| ----- | ---------- | --------------- |
| qwen2.5-coder-7b | `qwen2.5-coder:7b` | — |
| qwen3-8b | `qwen3:8b` | 32m 30s |
| llama3.1-8b | `llama3.1:8b` | 12m 58s |
| mistral-7b | `mistral:7b` | 10m 04s |
| deepseek-coder-6.7b | `deepseek-coder:6.7b` | 28m 50s |
| codegemma-7b | `codegemma:7b` | 8m 57s |
| codellama-7b | `codellama:7b` | 17m 50s |
| yi-coder-9b | `yi-coder:9b` | 14m 18s |

---

## 3. Pairwise Head-to-Head Results

Each cell shows `W / L / T` (wins, losses, ties) for the **row model** against the **column model**.

| Model | qwen2.5-coder-7b | qwen3-8b | llama3.1-8b | mistral-7b | deepseek-coder-6.7b | codegemma-7b | codellama-7b | yi-coder-9b |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| **qwen2.5-coder-7b** | — | 43/9/116 | 40/13/115 | 35/26/107 | 25/35/108 | 45/11/112 | 19/74/75 | 5/75/88 |
| **qwen3-8b** | 9/43/116 | — | 24/32/112 | 15/38/115 | 30/43/95 | 27/26/115 | 22/80/66 | 10/73/85 |
| **llama3.1-8b** | 13/40/115 | 32/24/112 | — | 10/53/105 | 17/50/101 | 26/18/124 | 13/86/69 | 2/84/82 |
| **mistral-7b** | 26/35/107 | 38/15/115 | 53/10/105 | — | 23/31/114 | 46/10/112 | 18/78/72 | 4/80/84 |
| **deepseek-coder-6.7b** | 35/25/108 | 43/30/95 | 50/17/101 | 31/23/114 | — | 51/22/95 | 9/61/98 | 7/55/106 |
| **codegemma-7b** | 11/45/112 | 26/27/115 | 18/26/124 | 10/46/112 | 22/51/95 | — | 10/95/63 | 5/93/70 |
| **codellama-7b** | 74/19/75 | 80/22/66 | 86/13/69 | 78/18/72 | 61/9/98 | 95/10/63 | — | 23/19/126 |
| **yi-coder-9b** | 75/5/88 | 73/10/85 | 84/2/82 | 80/4/84 | 55/7/106 | 93/5/70 | 19/23/126 | — |

---

## 4. Full Metrics Summary

Completeness is AST-based (0–1). All other scores are LLM-judged (1–5, averaged across leave-one-out judges).

| Model | Gen. Time | Complete. | Summary | Desc. | Params | Correct. | Clarity | Concise. | LLM Avg | Win Rate |
| ----- | --------- | --------- | ------- | ----- | ------ | -------- | ------- | -------- | ------- | -------- |
| codellama-7b | 17m 50s | 0.892 | 2.926 | 4.321 | 3.590 | 4.022 | 4.021 | 3.156 | 3.673 | **42.3%** |
| yi-coder-9b | 14m 18s | 0.964 | 2.989 | 4.397 | 3.806 | 4.390 | 4.122 | 3.544 | 3.875 | **40.7%** |
| deepseek-coder-6.7b | 28m 50s | 0.763 | 3.323 | 4.095 | 3.647 | 3.984 | 3.937 | 3.396 | 3.730 | **19.2%** |
| qwen2.5-coder-7b | — | 0.821 | 3.059 | 4.144 | 3.610 | 4.301 | 4.204 | 3.684 | 3.834 | **18.0%** |
| mistral-7b | 10m 04s | 0.790 | 2.765 | 3.842 | 3.309 | 4.026 | 4.058 | 3.738 | 3.623 | **17.7%** |
| qwen3-8b | 32m 30s | 0.573 | 3.082 | 3.286 | 3.087 | 3.663 | 3.510 | 3.821 | 3.408 | **11.7%** |
| llama3.1-8b | 12m 58s | 0.768 | 2.926 | 3.428 | 3.086 | 3.947 | 3.828 | 3.885 | 3.517 | **9.6%** |
| codegemma-7b | 8m 57s | 0.755 | 2.770 | 3.562 | 3.080 | 4.163 | 4.047 | 3.789 | 3.569 | **8.7%** |

---

## 5. Structural Completeness (AST-based)

Score = fraction of required docstring sections present (0–1). Required sections are determined from the code itself (e.g. `Args` only if the function has parameters, `Raises` only if there are raise statements).

| Model | Average Completeness |
| ----- | -------------------- |
| codellama-7b | 0.892 |
| yi-coder-9b | 0.964 |
| deepseek-coder-6.7b | 0.763 |
| qwen2.5-coder-7b | 0.821 |
| mistral-7b | 0.790 |
| qwen3-8b | 0.573 |
| llama3.1-8b | 0.768 |
| codegemma-7b | 0.755 |

---

## 6. Point-wise LLM Judge Scores

Each score is 1–5, averaged across all leave-one-out judges and sampled components.

| Model | Summary | Description | Parameters | Correctness | Clarity | Conciseness |
| ----- | ------- | ----------- | ---------- | ----------- | ------- | ----------- |
| codellama-7b | 2.926 | 4.321 | 3.590 | 4.022 | 4.021 | 3.156 |
| yi-coder-9b | 2.989 | 4.397 | 3.806 | 4.390 | 4.122 | 3.544 |
| deepseek-coder-6.7b | 3.323 | 4.095 | 3.647 | 3.984 | 3.937 | 3.396 |
| qwen2.5-coder-7b | 3.059 | 4.144 | 3.610 | 4.301 | 4.204 | 3.684 |
| mistral-7b | 2.765 | 3.842 | 3.309 | 4.026 | 4.058 | 3.738 |
| qwen3-8b | 3.082 | 3.286 | 3.087 | 3.663 | 3.510 | 3.821 |
| llama3.1-8b | 2.926 | 3.428 | 3.086 | 3.947 | 3.828 | 3.885 |
| codegemma-7b | 2.770 | 3.562 | 3.080 | 4.163 | 4.047 | 3.789 |

---

## 7. Methodology

- **Components sampled per evaluation:** 50
- **Random seed:** 42
- **Judging:** Leave-one-out. For model X, judges are the other N−1 models.
- **Pairwise position bias control:** Each pair run twice with A/B positions swapped. Final winner requires agreement across both orderings; disagreement → TIE.
- **Objective completeness:** Pure AST parsing, no LLM involved.
- **Point-wise scoring:** 6 dimensions (summary, description, parameters, correctness, clarity, conciseness), score 1–5 per judge.
