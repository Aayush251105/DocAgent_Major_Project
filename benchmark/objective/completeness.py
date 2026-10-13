#!/usr/bin/env python3
"""
objective/completeness.py
--------------------------
Reads the comparison dataset and computes structural completeness scores
for every model on every component.

Output: benchmark/results/objective/completeness.json

Schema:
{
  "per_component": {
    "<component_key>": {
      "<model_name>": {
        "score": 0.83,
        "element_scores": { "summary": true, "description": true, ... },
        "element_required": { "summary": true, ... }
      }
    }
  },
  "summary": {
    "<model_name>": {
      "average_score": 0.81,
      "n": 42
    }
  }
}
"""

import ast
import json
import sys
from pathlib import Path
from typing import Any, Dict

import yaml

PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from evaluator.completeness import (
    ClassCompletenessEvaluator,
    FunctionCompletenessEvaluator,
)


def load_config(config_path: str = "benchmark/config.yaml") -> Dict[str, Any]:
    with open(PROJECT_ROOT / config_path) as f:
        return yaml.safe_load(f)


def score_docstring(comp_type: str, source_code: str, docstring: str) -> Dict[str, Any]:
    """
    Run completeness evaluation given the component type, source code, and docstring.
    Returns {"score": float, "element_scores": {...}, "element_required": {...}}
    """
    try:
        tree = ast.parse(source_code)
    except SyntaxError:
        return {"score": 0.0, "element_scores": {}, "element_required": {}}

    # Grab the first top-level node that matches the type
    node = None
    for n in ast.walk(tree):
        if comp_type == "class" and isinstance(n, ast.ClassDef):
            node = n
            break
        elif comp_type in ("function", "method") and isinstance(
            n, (ast.FunctionDef, ast.AsyncFunctionDef)
        ):
            node = n
            break

    if node is None:
        return {"score": 0.0, "element_scores": {}, "element_required": {}}

    # Inject the docstring so the evaluator sees it
    if docstring:
        docstring_node = ast.Expr(value=ast.Constant(value=docstring))
        if node.body and isinstance(node.body[0], ast.Expr) and isinstance(
            node.body[0].value, ast.Constant
        ):
            node.body[0] = docstring_node
        else:
            node.body.insert(0, docstring_node)

    if comp_type == "class":
        ev = ClassCompletenessEvaluator()
    else:
        ev = FunctionCompletenessEvaluator()

    score = ev.evaluate(node)
    return {
        "score": score,
        "element_scores": dict(ev.element_scores),
        "element_required": dict(ev.element_required),
    }


def run(config: Dict[str, Any]) -> Dict[str, Any]:
    dataset_path = PROJECT_ROOT / config["paths"]["comparison_dataset"]
    with open(dataset_path) as f:
        dataset = json.load(f)

    model_names = [m["name"] for m in config["models"]]

    per_component: Dict[str, Any] = {}
    all_scores: Dict[str, list] = {m: [] for m in model_names}

    for comp_key, comp_data in dataset.items():
        per_component[comp_key] = {}
        comp_type = comp_data["type"]
        source_code = comp_data.get("source_code", "")

        for model in model_names:
            docstring = comp_data["docstrings"].get(model, {}).get("docstring", "")
            result = score_docstring(comp_type, source_code, docstring)
            per_component[comp_key][model] = result
            all_scores[model].append(result["score"])

    summary = {}
    for model in model_names:
        scores = all_scores[model]
        summary[model] = {
            "average_score": sum(scores) / len(scores) if scores else 0.0,
            "n": len(scores),
        }

    return {"per_component": per_component, "summary": summary}


def main():
    config = load_config()
    result = run(config)

    out_dir = PROJECT_ROOT / config["paths"]["objective_output"]
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "completeness.json"

    with open(out_path, "w") as f:
        json.dump(result, f, indent=2)

    print(f"Completeness scores saved to: {out_path}")
    print("\nSummary:")
    for model, stats in result["summary"].items():
        print(f"  {model}: {stats['average_score']:.3f} (n={stats['n']})")


if __name__ == "__main__":
    main()
