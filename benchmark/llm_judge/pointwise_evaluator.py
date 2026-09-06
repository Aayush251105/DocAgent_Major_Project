#!/usr/bin/env python3
"""
pointwise_evaluator.py
----------------------
For each model, scores a random sample of its docstrings on 6 dimensions
using the leave-one-out judge pool (remaining 4 models judge each model).

Each judge scores independently; results are averaged across judges.

Output: benchmark/results/llm_judgments/pointwise/
  pointwise_results.json   — raw per-component, per-aspect, per-judge scores
  pointwise_summary.json   — per-model averages per aspect
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
from benchmark.llm_judge.prompts import POINTWISE_RUBRICS, SYSTEM_PROMPT, pointwise_prompt

ASPECTS = list(POINTWISE_RUBRICS.keys())


def load_config(config_path: str = "benchmark/config.yaml") -> Dict[str, Any]:
    with open(PROJECT_ROOT / config_path) as f:
        return yaml.safe_load(f)


def parse_score(response: str) -> Optional[int]:
    """Extract integer score from <score>N</score> tag."""
    m = re.search(r"<score>(\d)</score>", response, re.IGNORECASE)
    if m:
        val = int(m.group(1))
        if 1 <= val <= 5:
            return val
    # Fallback: find last standalone digit 1-5
    digits = re.findall(r"\b([1-5])\b", response)
    if digits:
        return int(digits[-1])
    return None


def sample_components(
    dataset: Dict[str, Any],
    model_names: List[str],
    n: int,
    seed: int,
) -> List[str]:
    """Return component keys where ALL models have a non-empty docstring."""
    random.seed(seed)
    valid = [
        k for k, v in dataset.items()
        if all(
            v["docstrings"].get(m, {}).get("docstring", "").strip()
            for m in model_names
        )
    ]
    if len(valid) < n:
        print(f"  Warning: only {len(valid)} components have docstrings for all models (requested {n})")
        return valid
    return random.sample(valid, n)


def run(config: Dict[str, Any]) -> Dict[str, Any]:
    dataset_path = PROJECT_ROOT / config["paths"]["comparison_dataset"]
    with open(dataset_path) as f:
        dataset = json.load(f)

    model_names = [m["name"] for m in config["models"]]
    ollama_cfg = config["ollama"]
    sampling = config["sampling"]
    n_samples = sampling["n_samples"]
    seed = sampling["seed"]

    component_ids = sample_components(dataset, model_names, n_samples, seed)
    print(f"Sampled {len(component_ids)} components for point-wise evaluation")

    # Build judge LLM pool: model_name -> JudgeLLM instance
    # (instantiated lazily per model)
    ollama_model_map = {m["name"]: m["ollama_model"] for m in config["models"]}

    # Raw results list
    raw_results: List[Dict[str, Any]] = []

    for model_being_judged in model_names:
        # Leave-one-out: judges are all models EXCEPT the one being judged
        judge_names = [m for m in model_names if m != model_being_judged]

        print(f"\nEvaluating: {model_being_judged}")
        print(f"  Judges: {judge_names}")

        judge_llms: Dict[str, JudgeLLM] = {
            j: JudgeLLM(ollama_model_map[j], ollama_cfg) for j in judge_names
        }

        for comp_key in component_ids:
            comp = dataset[comp_key]
            docstring = comp["docstrings"].get(model_being_judged, {}).get("docstring", "")
            if not docstring.strip():
                continue

            source_code = comp.get("source_code", "")
            comp_type = comp.get("type", "function")

            for aspect in ASPECTS:
                prompt = pointwise_prompt(aspect, source_code, docstring, comp_type)

                for judge_name, judge_llm in judge_llms.items():
                    try:
                        response = judge_llm.chat(SYSTEM_PROMPT, prompt)
                        score = parse_score(response)
                    except Exception as e:
                        print(f"    ERROR judge={judge_name} aspect={aspect}: {e}")
                        response = ""
                        score = None

                    raw_results.append({
                        "model": model_being_judged,
                        "judge": judge_name,
                        "component_id": comp_key,
                        "aspect": aspect,
                        "score": score,
                        "response": response,
                    })

                    if score is not None:
                        print(f"    [{judge_name}] {comp_key} / {aspect}: {score}")

    # Aggregate: per-model, per-aspect average across all judges and components
    summary: Dict[str, Dict[str, Any]] = {}
    for model in model_names:
        summary[model] = {}
        for aspect in ASPECTS:
            scores = [
                r["score"] for r in raw_results
                if r["model"] == model
                and r["aspect"] == aspect
                and r["score"] is not None
            ]
            summary[model][aspect] = {
                "average": round(sum(scores) / len(scores), 3) if scores else None,
                "n": len(scores),
            }

    return {"raw_results": raw_results, "summary": summary, "component_ids": component_ids}


def main():
    config = load_config()
    results = run(config)

    out_dir = PROJECT_ROOT / config["paths"]["llm_judgments"] / "pointwise"
    out_dir.mkdir(parents=True, exist_ok=True)

    with open(out_dir / "pointwise_results.json", "w") as f:
        json.dump(results["raw_results"], f, indent=2)

    with open(out_dir / "pointwise_summary.json", "w") as f:
        json.dump(results["summary"], f, indent=2)

    print(f"\nPoint-wise results saved to: {out_dir}")
    print("\nSummary (averages):")
    for model, aspects in results["summary"].items():
        avg_scores = [v["average"] for v in aspects.values() if v["average"] is not None]
        overall = round(sum(avg_scores) / len(avg_scores), 3) if avg_scores else None
        print(f"  {model}: overall={overall} | " + " | ".join(
            f"{a}={v['average']}" for a, v in aspects.items()
        ))


if __name__ == "__main__":
    main()
