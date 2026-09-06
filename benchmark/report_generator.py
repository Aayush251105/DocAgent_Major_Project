#!/usr/bin/env python3
"""
report_generator.py
-------------------
Reads all results from benchmark/results/ and writes
benchmark/results/final_report.md.

Can be run standalone after run_benchmark.py, or called directly
by run_benchmark.py at the end of a full run.
"""

import json
import sys
from datetime import datetime
from itertools import combinations
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from benchmark.llm_judge.aggregate import build_summary


def load_config(config_path: str = "benchmark/config.yaml") -> Dict[str, Any]:
    with open(PROJECT_ROOT / config_path) as f:
        return yaml.safe_load(f)


def _fmt(val: Optional[float], decimals: int = 3) -> str:
    if val is None:
        return "—"
    return f"{val:.{decimals}f}"


def _pct(val: Optional[float]) -> str:
    if val is None:
        return "—"
    return f"{val:.1%}"


def generate_report(
    model_names: List[str],
    completeness_summary: Dict[str, Any],
    pointwise_summary: Dict[str, Any],
    win_rate_ranking: List[Dict[str, Any]],
    pair_summary: Dict[str, Any],
    config: Dict[str, Any],
) -> str:
    summary_rows = build_summary(
        model_names,
        completeness_summary,
        pointwise_summary,
        win_rate_ranking,
    )

    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    lines = []

    # ── Header ──────────────────────────────────────────────────────────────
    lines += [
        "# DocAgent — Model Benchmark Report",
        f"_Generated: {now}_",
        "",
        "## Models Evaluated",
        "",
    ]
    ollama_map = {m["name"]: m["ollama_model"] for m in config["models"]}
    for m in model_names:
        lines.append(f"- **{m}** (`{ollama_map.get(m, m)}`)")
    lines += [
        "",
        "> **Judge protocol:** Leave-one-out. "
        "When model X is evaluated, judges are all other models.",
        "",
        "---",
        "",
    ]

    # ── 1. Win Rate Ranking ──────────────────────────────────────────────────
    lines += [
        "## 1. Pairwise Win Rate Ranking",
        "",
        "Primary metric. Each matchup is judged by the 3 remaining models.",
        "Position bias is controlled by running each pair in both orderings;",
        "a win is only counted when the judge agrees across both orderings.",
        "",
        "| Rank | Model | Win Rate | W | L | T | Total Decisions |",
        "| ---- | ----- | -------- | - | - | - | --------------- |",
    ]
    for rank, row in enumerate(summary_rows, 1):
        lines.append(
            f"| {rank} | {row['model']} | **{_pct(row['win_rate'])}** "
            f"| {row['wins']} | {row['losses']} | {row['ties']} "
            f"| {row['total_decisions']} |"
        )
    lines += ["", "---", ""]

    # ── 2. Pairwise Head-to-Head Matrix ─────────────────────────────────────
    lines += [
        "## 2. Pairwise Head-to-Head Results",
        "",
        "Each cell shows `W / L / T` (wins, losses, ties) for the **row model** against the **column model**.",
        "",
    ]
    # Build header
    header = "| Model |" + "".join(f" {m} |" for m in model_names)
    sep = "| --- |" + " --- |" * len(model_names)
    lines += [header, sep]

    for row_model in model_names:
        cells = [f"**{row_model}**"]
        for col_model in model_names:
            if row_model == col_model:
                cells.append("—")
            else:
                # find pair entry
                key1 = f"{row_model} vs {col_model}"
                key2 = f"{col_model} vs {row_model}"
                if key1 in pair_summary:
                    ps = pair_summary[key1]
                    w, l, t = ps["A_wins"], ps["B_wins"], ps["ties"]
                elif key2 in pair_summary:
                    ps = pair_summary[key2]
                    w, l, t = ps["B_wins"], ps["A_wins"], ps["ties"]
                else:
                    w, l, t = 0, 0, 0
                cells.append(f"{w}/{l}/{t}")
        lines.append("| " + " | ".join(cells) + " |")

    lines += ["", "---", ""]

    # ── 3. Overall Summary Table ─────────────────────────────────────────────
    lines += [
        "## 3. Full Metrics Summary",
        "",
        "Completeness is AST-based (0–1). All other scores are LLM-judged (1–5, averaged across leave-one-out judges).",
        "",
        "| Model | Complete. | Summary | Desc. | Params | Correct. | Clarity | Concise. | LLM Avg | Win Rate |",
        "| ----- | --------- | ------- | ----- | ------ | -------- | ------- | -------- | ------- | -------- |",
    ]
    for row in summary_rows:
        lines.append(
            f"| {row['model']} "
            f"| {_fmt(row['completeness'])} "
            f"| {_fmt(row['summary_score'])} "
            f"| {_fmt(row['description_score'])} "
            f"| {_fmt(row['parameters_score'])} "
            f"| {_fmt(row['correctness_score'])} "
            f"| {_fmt(row['clarity_score'])} "
            f"| {_fmt(row['conciseness_score'])} "
            f"| {_fmt(row['llm_overall'])} "
            f"| **{_pct(row['win_rate'])}** |"
        )
    lines += ["", "---", ""]

    # ── 4. Objective Completeness Detail ────────────────────────────────────
    lines += [
        "## 4. Structural Completeness (AST-based)",
        "",
        "Score = fraction of required docstring sections present (0–1). "
        "Required sections are determined from the code itself (e.g. `Args` only "
        "if the function has parameters, `Raises` only if there are raise statements).",
        "",
        "| Model | Average Completeness |",
        "| ----- | -------------------- |",
    ]
    for row in summary_rows:
        lines.append(f"| {row['model']} | {_fmt(row['completeness'])} |")
    lines += ["", "---", ""]

    # ── 5. Point-wise LLM Scores Detail ─────────────────────────────────────
    lines += [
        "## 5. Point-wise LLM Judge Scores",
        "",
        "Each score is 1–5, averaged across all leave-one-out judges and sampled components.",
        "",
        "| Model | Summary | Description | Parameters | Correctness | Clarity | Conciseness |",
        "| ----- | ------- | ----------- | ---------- | ----------- | ------- | ----------- |",
    ]
    for row in summary_rows:
        lines.append(
            f"| {row['model']} "
            f"| {_fmt(row['summary_score'])} "
            f"| {_fmt(row['description_score'])} "
            f"| {_fmt(row['parameters_score'])} "
            f"| {_fmt(row['correctness_score'])} "
            f"| {_fmt(row['clarity_score'])} "
            f"| {_fmt(row['conciseness_score'])} |"
        )
    lines += ["", "---", ""]

    # ── 6. Methodology ───────────────────────────────────────────────────────
    sampling = config["sampling"]
    lines += [
        "## 6. Methodology",
        "",
        f"- **Components sampled per evaluation:** {sampling['n_samples']}",
        f"- **Random seed:** {sampling['seed']}",
        "- **Judging:** Leave-one-out. For model X, judges are the other N−1 models.",
        "- **Pairwise position bias control:** Each pair run twice with A/B positions "
        "swapped. Final winner requires agreement across both orderings; disagreement → TIE.",
        "- **Objective completeness:** Pure AST parsing, no LLM involved.",
        "- **Point-wise scoring:** 6 dimensions (summary, description, parameters, "
        "correctness, clarity, conciseness), score 1–5 per judge.",
        "",
    ]

    return "\n".join(lines)


def main():
    config = load_config()
    model_names = [m["name"] for m in config["models"]]

    base = PROJECT_ROOT / "benchmark" / "results"

    # Load objective completeness
    comp_path = base / "objective" / "completeness.json"
    if not comp_path.exists():
        print(f"ERROR: {comp_path} not found. Run objective/completeness.py first.")
        sys.exit(1)
    with open(comp_path) as f:
        completeness_data = json.load(f)
    completeness_summary = completeness_data.get("summary", {})

    # Load pointwise summary
    pw_path = base / "llm_judgments" / "pointwise" / "pointwise_summary.json"
    if not pw_path.exists():
        print(f"ERROR: {pw_path} not found. Run llm_judge/pointwise_evaluator.py first.")
        sys.exit(1)
    with open(pw_path) as f:
        pointwise_summary = json.load(f)

    # Load pairwise ranking and summary
    ranking_path = base / "llm_judgments" / "pairwise" / "win_rate_ranking.json"
    pair_path = base / "llm_judgments" / "pairwise" / "pairwise_summary.json"
    if not ranking_path.exists() or not pair_path.exists():
        print(f"ERROR: pairwise results not found. Run llm_judge/pairwise_evaluator.py first.")
        sys.exit(1)
    with open(ranking_path) as f:
        win_rate_ranking = json.load(f)
    with open(pair_path) as f:
        pair_summary = json.load(f)

    report = generate_report(
        model_names,
        completeness_summary,
        pointwise_summary,
        win_rate_ranking,
        pair_summary,
        config,
    )

    out_path = PROJECT_ROOT / config["paths"]["final_report"]
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(report, encoding="utf-8")
    print(f"\nFinal report written to: {out_path}")


if __name__ == "__main__":
    main()
