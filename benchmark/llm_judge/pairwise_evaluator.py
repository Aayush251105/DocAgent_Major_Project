#!/usr/bin/env python3
"""
pairwise_evaluator.py
---------------------
Head-to-head preference judgments for all C(5,2) = 10 model pairs.

Leave-one-out judging: when comparing model_A vs model_B, the judges are
the remaining 3 models from your 5.

Each pair is also run with positions SWAPPED to detect position bias.
A win is only counted if the judge picks the same model in both orderings.
If the judge flips, the result is recorded as a TIE.

Output: benchmark/results/llm_judgments/pairwise/
  pairwise_results.json   — every individual judgment
  pairwise_summary.json   — win/loss/tie counts per pair
  win_rate_ranking.json   — per-model win rate across all pairs
"""

import json
import random
import re
import sys
from itertools import combinations
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import yaml

PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from benchmark.llm_judge.judge_llm import JudgeLLM
from benchmark.llm_judge.prompts import SYSTEM_PROMPT, pairwise_prompt


def load_config(config_path: str = "benchmark/config.yaml") -> Dict[str, Any]:
    with open(PROJECT_ROOT / config_path) as f:
        return yaml.safe_load(f)


def parse_winner(response: str) -> Optional[str]:
    """Extract A / B / TIE from <winner>...</winner> tag."""
    m = re.search(r"<winner>(A|B|TIE)</winner>", response, re.IGNORECASE)
    if m:
        return m.group(1).upper()
    # Fallback: scan for explicit keywords
    upper = response.upper()
    if "DOCSTRING A" in upper and "DOCSTRING B" not in upper:
        return "A"
    if "DOCSTRING B" in upper and "DOCSTRING A" not in upper:
        return "B"
    return "TIE"


def sample_components(
    dataset: Dict[str, Any],
    model_a: str,
    model_b: str,
    n: int,
    seed: int,
) -> List[str]:
    """Components where both models have a non-empty docstring."""
    random.seed(seed)
    valid = [
        k for k, v in dataset.items()
        if v["docstrings"].get(model_a, {}).get("docstring", "").strip()
        and v["docstrings"].get(model_b, {}).get("docstring", "").strip()
    ]
    if len(valid) < n:
        return valid
    return random.sample(valid, n)


def judge_pair(
    judge_llm: JudgeLLM,
    source_code: str,
    doc_a: str,
    doc_b: str,
    comp_type: str,
) -> Tuple[str, str, str, str]:
    """
    Run both orderings (A vs B, then B vs A).
    Returns (winner_forward, response_forward, winner_reverse, response_reverse).
    """
    prompt_fwd = pairwise_prompt(source_code, doc_a, doc_b, comp_type)
    resp_fwd = judge_llm.chat(SYSTEM_PROMPT, prompt_fwd)
    winner_fwd = parse_winner(resp_fwd)  # A or B

    prompt_rev = pairwise_prompt(source_code, doc_b, doc_a, comp_type)
    resp_rev = judge_llm.chat(SYSTEM_PROMPT, prompt_rev)
    winner_rev_raw = parse_winner(resp_rev)  # A or B, but in reversed positions
    # Map back: if reversed prompt winner is A, that's actually doc_b (model_b)
    if winner_rev_raw == "A":
        winner_rev = "B"
    elif winner_rev_raw == "B":
        winner_rev = "A"
    else:
        winner_rev = "TIE"

    return winner_fwd, resp_fwd, winner_rev, resp_rev


def resolve_winner(winner_fwd: Optional[str], winner_rev: Optional[str]) -> str:
    """
    Combine forward and reverse orderings.
    Both agree on A → A wins.
    Both agree on B → B wins.
    Disagreement or either is TIE → TIE.
    """
    if winner_fwd == winner_rev and winner_fwd in ("A", "B"):
        return winner_fwd
    return "TIE"


def run(config: Dict[str, Any]) -> Dict[str, Any]:
    dataset_path = PROJECT_ROOT / config["paths"]["comparison_dataset"]
    with open(dataset_path) as f:
        dataset = json.load(f)

    model_names = [m["name"] for m in config["models"]]
    ollama_cfg = config["ollama"]
    sampling = config["sampling"]
    n_samples = sampling["n_samples"]
    seed = sampling["seed"]

    ollama_model_map = {m["name"]: m["ollama_model"] for m in config["models"]}

    raw_results: List[Dict[str, Any]] = []

    pairs = list(combinations(model_names, 2))
    print(f"Running pairwise evaluation for {len(pairs)} pairs")

    for model_a, model_b in pairs:
        # Leave-one-out judges: everyone except model_a and model_b
        judge_names = [m for m in model_names if m not in (model_a, model_b)]
        print(f"\n  {model_a} vs {model_b}  (judges: {judge_names})")

        judge_llms: Dict[str, JudgeLLM] = {
            j: JudgeLLM(ollama_model_map[j], ollama_cfg) for j in judge_names
        }

        component_ids = sample_components(dataset, model_a, model_b, n_samples, seed)
        print(f"  Sampled {len(component_ids)} components")

        for comp_key in component_ids:
            comp = dataset[comp_key]
            doc_a = comp["docstrings"].get(model_a, {}).get("docstring", "")
            doc_b = comp["docstrings"].get(model_b, {}).get("docstring", "")
            source_code = comp.get("source_code", "")
            comp_type = comp.get("type", "function")

            for judge_name, judge_llm in judge_llms.items():
                try:
                    wf, rf, wr, rr = judge_pair(
                        judge_llm, source_code, doc_a, doc_b, comp_type
                    )
                    final_winner = resolve_winner(wf, wr)
                except Exception as e:
                    print(f"    ERROR judge={judge_name}: {e}")
                    wf, rf, wr, rr, final_winner = None, "", None, "", "TIE"

                raw_results.append({
                    "model_a": model_a,
                    "model_b": model_b,
                    "judge": judge_name,
                    "component_id": comp_key,
                    "winner_forward": wf,
                    "winner_reverse": wr,
                    "final_winner": final_winner,  # A, B, or TIE (resolved)
                    "response_forward": rf,
                    "response_reverse": rr,
                })

                print(f"    [{judge_name}] {comp_key}: {model_a} vs {model_b} → {final_winner}")

    # ── Aggregate pairwise summary ─────────────────────────────────────────
    pair_summary: Dict[str, Dict[str, int]] = {}
    for model_a, model_b in pairs:
        pair_key = f"{model_a} vs {model_b}"
        pair_summary[pair_key] = {"A_wins": 0, "B_wins": 0, "ties": 0, "total": 0}

        for r in raw_results:
            if r["model_a"] == model_a and r["model_b"] == model_b:
                fw = r["final_winner"]
                pair_summary[pair_key]["total"] += 1
                if fw == "A":
                    pair_summary[pair_key]["A_wins"] += 1
                elif fw == "B":
                    pair_summary[pair_key]["B_wins"] += 1
                else:
                    pair_summary[pair_key]["ties"] += 1

    # ── Win rate ranking ───────────────────────────────────────────────────
    wins: Dict[str, int] = {m: 0 for m in model_names}
    losses: Dict[str, int] = {m: 0 for m in model_names}
    ties: Dict[str, int] = {m: 0 for m in model_names}
    total_decisions: Dict[str, int] = {m: 0 for m in model_names}

    for r in raw_results:
        ma, mb, fw = r["model_a"], r["model_b"], r["final_winner"]
        total_decisions[ma] += 1
        total_decisions[mb] += 1
        if fw == "A":
            wins[ma] += 1
            losses[mb] += 1
        elif fw == "B":
            wins[mb] += 1
            losses[ma] += 1
        else:
            ties[ma] += 1
            ties[mb] += 1

    ranking = []
    for model in model_names:
        n = total_decisions[model]
        win_rate = wins[model] / n if n > 0 else 0.0
        ranking.append({
            "model": model,
            "wins": wins[model],
            "losses": losses[model],
            "ties": ties[model],
            "total": n,
            "win_rate": round(win_rate, 4),
        })
    ranking.sort(key=lambda x: x["win_rate"], reverse=True)

    return {
        "raw_results": raw_results,
        "pair_summary": pair_summary,
        "win_rate_ranking": ranking,
    }


def main():
    config = load_config()
    results = run(config)

    out_dir = PROJECT_ROOT / config["paths"]["llm_judgments"] / "pairwise"
    out_dir.mkdir(parents=True, exist_ok=True)

    with open(out_dir / "pairwise_results.json", "w") as f:
        json.dump(results["raw_results"], f, indent=2)

    with open(out_dir / "pairwise_summary.json", "w") as f:
        json.dump(results["pair_summary"], f, indent=2)

    with open(out_dir / "win_rate_ranking.json", "w") as f:
        json.dump(results["win_rate_ranking"], f, indent=2)

    print(f"\nPairwise results saved to: {out_dir}")
    print("\nWin Rate Ranking:")
    for rank, entry in enumerate(results["win_rate_ranking"], 1):
        print(
            f"  {rank}. {entry['model']:<20} "
            f"win_rate={entry['win_rate']:.1%}  "
            f"W={entry['wins']} L={entry['losses']} T={entry['ties']}"
        )


if __name__ == "__main__":
    main()
