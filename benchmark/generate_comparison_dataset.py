#!/usr/bin/env python3
"""
generate_comparison_dataset.py
--------------------------------
Walks the raw_generations folders for all configured models, extracts
docstrings via AST, runs structural completeness scoring, and merges
everything into a single JSON keyed by component path.

Output: benchmark/results/comparison_dataset.json

Run after you have generated docstrings for all models:
    python benchmark/generate_comparison_dataset.py
"""

import ast
import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

# ── project root on path so src.evaluator imports work ──────────────────────
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from evaluator.completeness import (
    ClassCompletenessEvaluator,
    FunctionCompletenessEvaluator,
)

# ── helpers ──────────────────────────────────────────────────────────────────

def load_config(config_path: str = "benchmark/config.yaml") -> Dict[str, Any]:
    with open(PROJECT_ROOT / config_path) as f:
        return yaml.safe_load(f)


def get_docstring(node: ast.AST) -> Optional[str]:
    return ast.get_docstring(node)


def get_function_signature(node: ast.FunctionDef) -> str:
    """Return a compact signature string, e.g. foo(a: int, b: str) -> bool"""
    args_parts = []
    args = node.args
    # positional args
    for arg in args.args:
        part = arg.arg
        if arg.annotation:
            part += f": {ast.unparse(arg.annotation)}"
        args_parts.append(part)
    # *args
    if args.vararg:
        part = f"*{args.vararg.arg}"
        if args.vararg.annotation:
            part += f": {ast.unparse(args.vararg.annotation)}"
        args_parts.append(part)
    # keyword-only
    for arg in args.kwonlyargs:
        part = arg.arg
        if arg.annotation:
            part += f": {ast.unparse(arg.annotation)}"
        args_parts.append(part)
    # **kwargs
    if args.kwarg:
        part = f"**{args.kwarg.arg}"
        if args.kwarg.annotation:
            part += f": {ast.unparse(args.kwarg.annotation)}"
        args_parts.append(part)

    ret = ""
    if node.returns:
        ret = f" -> {ast.unparse(node.returns)}"

    return f"{node.name}({', '.join(args_parts)}){ret}"


def extract_actual_params(node: ast.FunctionDef) -> List[str]:
    """Return list of parameter names, excluding 'self' and 'cls'."""
    skip = {"self", "cls"}
    params = [a.arg for a in node.args.args if a.arg not in skip]
    params += [a.arg for a in node.args.kwonlyargs]
    if node.args.vararg:
        params.append(node.args.vararg.arg)
    if node.args.kwarg:
        params.append(node.args.kwarg.arg)
    return params


def has_raise(node: ast.FunctionDef) -> bool:
    for child in ast.walk(node):
        if isinstance(child, ast.Raise):
            return True
    return False


def has_return(node: ast.FunctionDef) -> bool:
    for child in ast.walk(node):
        if isinstance(child, ast.Return) and child.value is not None:
            if not (isinstance(child.value, ast.Constant) and child.value.value is None):
                return True
        if isinstance(child, (ast.Yield, ast.YieldFrom)):
            return True
    return False


def get_return_annotation(node: ast.FunctionDef) -> Optional[str]:
    if node.returns:
        return ast.unparse(node.returns)
    return None


def completeness_scores(
    node: ast.AST, docstring: Optional[str]
) -> Dict[str, bool]:
    """Run completeness evaluation and return element_scores dict."""
    if isinstance(node, ast.ClassDef):
        ev = ClassCompletenessEvaluator()
        ev.evaluate(node)
    elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
        ev = FunctionCompletenessEvaluator()
        ev.evaluate(node)
    else:
        return {}
    return dict(ev.element_scores)


def walk_python_files(root: Path):
    for path in sorted(root.rglob("*.py")):
        yield path


# ── per-file extractor ────────────────────────────────────────────────────────

def extract_components_from_file(
    file_path: Path,
    repo_root: Path,
) -> Dict[str, Dict[str, Any]]:
    """
    Parse one .py file and return a dict of component_key -> metadata.
    component_key is relative to repo_root, e.g.:
        'vending_machine.VendingMachine.add_product'
    """
    source = file_path.read_text(encoding="utf-8")
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return {}

    rel = file_path.relative_to(repo_root)
    # Use dot-separated module path as prefix, stripping .py
    module_prefix = str(rel).replace(os.sep, ".").removesuffix(".py")

    components: Dict[str, Dict[str, Any]] = {}

    for node in ast.iter_child_nodes(tree):
        # ── top-level function ────────────────────────────────────────────
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if node.name == "__init__":
                continue
            key = f"{module_prefix}.{node.name}"
            docstring = get_docstring(node)
            components[key] = {
                "type": "function",
                "source_code": ast.unparse(node),
                "signature": get_function_signature(node),
                "actual_params": extract_actual_params(node),
                "return_annotation": get_return_annotation(node),
                "has_raise": has_raise(node),
                "has_return": has_return(node),
                # docstrings filled in per-model below
                "docstrings": {},
            }

        # ── class ─────────────────────────────────────────────────────────
        elif isinstance(node, ast.ClassDef):
            class_key = f"{module_prefix}.{node.name}"
            class_docstring = get_docstring(node)
            components[class_key] = {
                "type": "class",
                "source_code": ast.unparse(node),
                "signature": node.name,
                "actual_params": [],
                "return_annotation": None,
                "has_raise": False,
                "has_return": False,
                "docstrings": {},
            }

            # ── methods inside the class ──────────────────────────────────
            for item in ast.iter_child_nodes(node):
                if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    if item.name == "__init__":
                        continue
                    method_key = f"{module_prefix}.{node.name}.{item.name}"
                    components[method_key] = {
                        "type": "method",
                        "source_code": ast.unparse(item),
                        "signature": get_function_signature(item),
                        "actual_params": extract_actual_params(item),
                        "return_annotation": get_return_annotation(item),
                        "has_raise": has_raise(item),
                        "has_return": has_return(item),
                        "docstrings": {},
                    }

    return components


# ── main builder ─────────────────────────────────────────────────────────────

def build_comparison_dataset(config: Dict[str, Any]) -> Dict[str, Any]:
    raw_gen_root = PROJECT_ROOT / config["paths"]["raw_generations"]
    model_names = [m["name"] for m in config["models"]]

    # Step 1: build the skeleton from the FIRST model's generated repo
    # (all models should produce the same components — same source files)
    first_model_root = raw_gen_root / model_names[0]
    if not first_model_root.exists():
        raise FileNotFoundError(
            f"Raw generations folder not found: {first_model_root}\n"
            f"Run DocAgent for each model first and copy results into "
            f"benchmark/results/raw_generations/<model_name>/"
        )

    print(f"Building component skeleton from: {first_model_root}")
    dataset: Dict[str, Any] = {}

    for py_file in walk_python_files(first_model_root):
        comps = extract_components_from_file(py_file, first_model_root)
        dataset.update(comps)

    print(f"  Found {len(dataset)} components")

    # Step 2: for each model, extract docstrings and completeness scores
    for model_name in model_names:
        model_root = raw_gen_root / model_name
        if not model_root.exists():
            print(f"  WARNING: folder not found for model '{model_name}', skipping")
            continue

        print(f"Extracting docstrings from: {model_root}")
        model_count = 0

        for py_file in walk_python_files(model_root):
            source = py_file.read_text(encoding="utf-8")
            try:
                tree = ast.parse(source)
            except SyntaxError:
                continue

            rel = py_file.relative_to(model_root)
            module_prefix = str(rel).replace(os.sep, ".").removesuffix(".py")

            for node in ast.iter_child_nodes(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    if node.name == "__init__":
                        continue
                    key = f"{module_prefix}.{node.name}"
                    _record_docstring(dataset, key, node, model_name)
                    model_count += 1

                elif isinstance(node, ast.ClassDef):
                    class_key = f"{module_prefix}.{node.name}"
                    _record_docstring(dataset, class_key, node, model_name)
                    model_count += 1

                    for item in ast.iter_child_nodes(node):
                        if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                            if item.name == "__init__":
                                continue
                            method_key = f"{module_prefix}.{node.name}.{item.name}"
                            _record_docstring(dataset, method_key, item, model_name)
                            model_count += 1

        print(f"  Recorded {model_count} docstrings for '{model_name}'")

    return dataset


def _record_docstring(
    dataset: Dict[str, Any],
    key: str,
    node: ast.AST,
    model_name: str,
) -> None:
    if key not in dataset:
        return  # component not in skeleton — skip

    docstring = get_docstring(node)
    element_scores = completeness_scores(node, docstring)

    dataset[key]["docstrings"][model_name] = {
        "docstring": docstring or "",
        "element_scores": element_scores,
    }


# ── entry point ───────────────────────────────────────────────────────────────

def main():
    config = load_config()
    dataset = build_comparison_dataset(config)

    output_path = PROJECT_ROOT / config["paths"]["comparison_dataset"]
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(dataset, f, indent=2)

    print(f"\nComparison dataset saved to: {output_path}")
    print(f"Total components: {len(dataset)}")

    # Quick coverage summary
    model_names = [m["name"] for m in config["models"]]
    print("\nDocstring coverage per model:")
    for model in model_names:
        covered = sum(
            1 for v in dataset.values()
            if v["docstrings"].get(model, {}).get("docstring", "")
        )
        print(f"  {model}: {covered}/{len(dataset)}")


if __name__ == "__main__":
    main()
