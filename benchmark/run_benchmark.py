#!/usr/bin/env python3
"""
run_benchmark.py
----------------
Single entry point that runs the full benchmark pipeline.

Usage:
    python benchmark/run_benchmark.py [--skip-dataset] [--skip-objective]
                                      [--skip-pointwise] [--skip-pairwise]
                                      [--skip-report]

Steps:
    1. generate_comparison_dataset  — build comparison_dataset.json
    2. objective/completeness       — AST-based completeness scores
    3. llm_judge/pointwise          — 6-dimension point-wise LLM scores
    4. llm_judge/pairwise           — head-to-head win/loss/tie judgments
    5. report_generator             — compile final_report.md

Prerequisite: For each model in benchmark/config.yaml, generate docstrings first:
    python benchmark/generate_docstrings_for_model.py --all
    (or --model <name> for a single model)

This keeps the original repo intact — each model gets its own isolated copy under
benchmark/results/raw_generations/<model_name>/
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict

import yaml

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


def load_config(config_path: str = "benchmark/config.yaml") -> Dict[str, Any]:
    with open(PROJECT_ROOT / config_path) as f:
        return yaml.safe_load(f)


def check_raw_generations(config: Dict[str, Any]) -> bool:
    """Verify that at least one model's raw_generations folder exists."""
    raw_root = PROJECT_ROOT / config["paths"]["raw_generations"]
    found = []
    for m in config["models"]:
        folder = raw_root / m["name"]
        if folder.exists():
            found.append(m["name"])
        else:
            print(f"  WARNING: raw_generations folder not found for '{m['name']}' at {folder}")
    if not found:
        print(
            "\nERROR: No raw_generations folders found.\n"
            "Run the generation step first:\n"
            "  python benchmark/generate_docstrings_for_model.py --all\n"
            "or for a single model:\n"
            "  python benchmark/generate_docstrings_for_model.py --model <name>\n"
        )
        return False
    print(f"  Found generations for: {found}")
    return True


def run_step(name: str, fn, *args, **kwargs):
    print(f"\n{'='*60}")
    print(f"STEP: {name}")
    print("=" * 60)
    try:
        result = fn(*args, **kwargs)
        print(f"✓ {name} complete")
        return result
    except Exception as e:
        print(f"✗ {name} FAILED: {e}")
        raise


def main():
    parser = argparse.ArgumentParser(description="Run the full DocAgent model benchmark")
    parser.add_argument("--skip-dataset", action="store_true", help="Skip dataset generation (use existing)")
    parser.add_argument("--skip-objective", action="store_true", help="Skip objective completeness scoring")
    parser.add_argument("--skip-pointwise", action="store_true", help="Skip point-wise LLM evaluation")
    parser.add_argument("--skip-pairwise", action="store_true", help="Skip pairwise LLM evaluation")
    parser.add_argument("--skip-report", action="store_true", help="Skip report generation")
    args = parser.parse_args()

    config = load_config()
    model_names = [m["name"] for m in config["models"]]
    print(f"Models configured: {model_names}")

    # ── Check prerequisites ──────────────────────────────────────────────────
    if not args.skip_dataset:
        print("\nChecking raw_generations directories...")
        if not check_raw_generations(config):
            sys.exit(1)

    # ── Step 1: Build comparison dataset ────────────────────────────────────
    if not args.skip_dataset:
        from benchmark.generate_comparison_dataset import build_comparison_dataset
        import json as _json

        def _build_dataset():
            dataset = build_comparison_dataset(config)
            out = PROJECT_ROOT / config["paths"]["comparison_dataset"]
            out.parent.mkdir(parents=True, exist_ok=True)
            with open(out, "w") as f:
                _json.dump(dataset, f, indent=2)
            print(f"  Saved {len(dataset)} components to {out}")

        run_step("Build Comparison Dataset", _build_dataset)
    else:
        print("\nSkipping dataset generation (--skip-dataset)")

    # ── Step 2: Objective completeness ──────────────────────────────────────
    completeness_summary = {}
    if not args.skip_objective:
        from benchmark.objective.completeness import run as run_completeness

        def _run_completeness():
            result = run_completeness(config)
            out_dir = PROJECT_ROOT / config["paths"]["objective_output"]
            out_dir.mkdir(parents=True, exist_ok=True)
            with open(out_dir / "completeness.json", "w") as f:
                json.dump(result, f, indent=2)
            return result["summary"]

        completeness_summary = run_step("Objective Completeness", _run_completeness)
        print("\n  Completeness averages:")
        for m, s in completeness_summary.items():
            print(f"    {m}: {s['average_score']:.3f}")
    else:
        print("\nSkipping objective completeness (--skip-objective)")
        # Try to load existing
        comp_path = PROJECT_ROOT / config["paths"]["objective_output"] / "completeness.json"
        if comp_path.exists():
            with open(comp_path) as f:
                completeness_summary = json.load(f)["summary"]

    # ── Step 3: Point-wise LLM evaluation ───────────────────────────────────
    pointwise_summary = {}
    if not args.skip_pointwise:
        from benchmark.llm_judge.pointwise_evaluator import run as run_pointwise

        def _run_pointwise():
            result = run_pointwise(config)
            out_dir = PROJECT_ROOT / config["paths"]["llm_judgments"] / "pointwise"
            out_dir.mkdir(parents=True, exist_ok=True)
            with open(out_dir / "pointwise_results.json", "w") as f:
                json.dump(result["raw_results"], f, indent=2)
            with open(out_dir / "pointwise_summary.json", "w") as f:
                json.dump(result["summary"], f, indent=2)
            return result["summary"]

        pointwise_summary = run_step("Point-wise LLM Evaluation", _run_pointwise)
    else:
        print("\nSkipping point-wise evaluation (--skip-pointwise)")
        pw_path = PROJECT_ROOT / config["paths"]["llm_judgments"] / "pointwise" / "pointwise_summary.json"
        if pw_path.exists():
            with open(pw_path) as f:
                pointwise_summary = json.load(f)

    # ── Step 4: Pairwise LLM evaluation ─────────────────────────────────────
    win_rate_ranking = []
    pair_summary = {}
    if not args.skip_pairwise:
        from benchmark.llm_judge.pairwise_evaluator import run as run_pairwise

        def _run_pairwise():
            result = run_pairwise(config)
            out_dir = PROJECT_ROOT / config["paths"]["llm_judgments"] / "pairwise"
            out_dir.mkdir(parents=True, exist_ok=True)
            with open(out_dir / "pairwise_results.json", "w") as f:
                json.dump(result["raw_results"], f, indent=2)
            with open(out_dir / "pairwise_summary.json", "w") as f:
                json.dump(result["pair_summary"], f, indent=2)
            with open(out_dir / "win_rate_ranking.json", "w") as f:
                json.dump(result["win_rate_ranking"], f, indent=2)
            return result

        pairwise_result = run_step("Pairwise LLM Evaluation", _run_pairwise)
        win_rate_ranking = pairwise_result["win_rate_ranking"]
        pair_summary = pairwise_result["pair_summary"]

        print("\n  Win Rate Ranking:")
        for rank, entry in enumerate(win_rate_ranking, 1):
            print(
                f"    {rank}. {entry['model']:<20} "
                f"{entry['win_rate']:.1%}  "
                f"W={entry['wins']} L={entry['losses']} T={entry['ties']}"
            )
    else:
        print("\nSkipping pairwise evaluation (--skip-pairwise)")
        ranking_path = PROJECT_ROOT / config["paths"]["llm_judgments"] / "pairwise" / "win_rate_ranking.json"
        pair_path = PROJECT_ROOT / config["paths"]["llm_judgments"] / "pairwise" / "pairwise_summary.json"
        if ranking_path.exists():
            with open(ranking_path) as f:
                win_rate_ranking = json.load(f)
        if pair_path.exists():
            with open(pair_path) as f:
                pair_summary = json.load(f)

    # ── Step 5: Generate report ──────────────────────────────────────────────
    if not args.skip_report:
        from benchmark.report_generator import generate_report

        def _generate_report():
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
            print(f"  Report: {out_path}")

        run_step("Generate Final Report", _generate_report)
    else:
        print("\nSkipping report generation (--skip-report)")

    print("\n" + "=" * 60)
    print("BENCHMARK COMPLETE")
    print("=" * 60)
    print(f"Final report: {PROJECT_ROOT / config['paths']['final_report']}")


if __name__ == "__main__":
    main()
