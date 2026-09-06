#!/usr/bin/env python3
"""
generate_docstrings_for_model.py
---------------------------------
Generates docstrings for ONE model from benchmark/config.yaml and stores
the result in a dedicated folder, leaving the original repo completely
untouched.

What it does:
  1. Reads benchmark/config.yaml to find the model entry
  2. Writes a temporary per-model DocAgent config (in benchmark/configs/)
  3. Copies the original repo to benchmark/results/raw_generations/<model_name>/
  4. Runs generate_docstrings.py against that copy
  5. Original repo is never modified

Usage:
    # Generate for one specific model (by name from config.yaml)
    python benchmark/generate_docstrings_for_model.py --model model_a

    # Generate for ALL models sequentially
    python benchmark/generate_docstrings_for_model.py --all

    # Specify a different source repo (default: data/raw_test_repo)
    python benchmark/generate_docstrings_for_model.py --model model_a --repo data/my_repo

    # Force re-generation even if output folder already exists
    python benchmark/generate_docstrings_for_model.py --model model_a --overwrite
"""

import argparse
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

PROJECT_ROOT = Path(__file__).parent.parent


def load_config(config_path: str = "benchmark/config.yaml") -> Dict[str, Any]:
    with open(PROJECT_ROOT / config_path) as f:
        return yaml.safe_load(f)


def write_model_config(model_entry: Dict[str, Any], ollama_cfg: Dict[str, Any], out_path: Path) -> None:
    """
    Write a complete DocAgent-compatible config yaml for a single model.
    All generation settings (temperature, tokens, flow_control) are kept
    identical across models — only the model name changes.
    """
    config = {
        "llm": {
            "type": "ollama",
            "model": model_entry["ollama_model"],
            "api_base": ollama_cfg.get("api_base", "http://localhost:11434/v1"),
            "api_key": ollama_cfg.get("api_key", "ollama"),
            "temperature": ollama_cfg.get("temperature", 0.1),
            "max_output_tokens": 4096,
            "max_input_tokens": 8000,
        },
        "flow_control": {
            "max_reader_search_attempts": 2,
            "max_verifier_rejections": 1,
            "status_sleep_time": 0,
        },
        "docstring_options": {
            "overwrite_docstrings": True,
        },
    }

    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w") as f:
        yaml.dump(config, f, default_flow_style=False)

    print(f"  Wrote model config: {out_path}")


def copy_repo(source: Path, dest: Path, overwrite: bool) -> bool:
    """
    Copy source repo to dest. Returns False if dest already exists and
    overwrite is False.
    """
    if dest.exists():
        if not overwrite:
            print(f"  Output folder already exists: {dest}")
            print(f"  Use --overwrite to re-generate. Skipping.")
            return False
        print(f"  Removing existing output folder: {dest}")
        shutil.rmtree(dest)

    print(f"  Copying repo: {source} → {dest}")
    shutil.copytree(source, dest)
    return True


def run_generation(model_name: str, repo_copy: Path, config_path: Path) -> bool:
    """
    Invoke generate_docstrings.py as a subprocess against the repo copy.
    Returns True on success.
    """
    cmd = [
        sys.executable,
        str(PROJECT_ROOT / "generate_docstrings.py"),
        "--repo-path", str(repo_copy),
        "--config-path", str(config_path),
        "--overwrite-docstrings",
    ]

    print(f"\n  Running DocAgent for '{model_name}'...")
    print(f"  Command: {' '.join(cmd)}\n")

    result = subprocess.run(cmd, cwd=str(PROJECT_ROOT))
    return result.returncode == 0


def generate_for_model(
    model_name: str,
    config: Dict[str, Any],
    source_repo: Path,
    overwrite: bool,
) -> bool:
    """Full pipeline for one model. Returns True on success."""
    # Find the model entry
    model_entry = next(
        (m for m in config["models"] if m["name"] == model_name), None
    )
    if model_entry is None:
        print(f"ERROR: Model '{model_name}' not found in benchmark/config.yaml")
        print(f"  Available models: {[m['name'] for m in config['models']]}")
        return False

    ollama_cfg = config["ollama"]
    raw_gen_root = PROJECT_ROOT / config["paths"]["raw_generations"]

    print(f"\n{'='*60}")
    print(f"Model: {model_name}  ({model_entry['ollama_model']})")
    print("=" * 60)

    # 1. Write per-model DocAgent config
    model_config_path = PROJECT_ROOT / "benchmark" / "configs" / f"{model_name}.yaml"
    write_model_config(model_entry, ollama_cfg, model_config_path)

    # 2. Copy original repo to output folder
    dest = raw_gen_root / model_name
    copied = copy_repo(source_repo, dest, overwrite)
    if not copied:
        return True  # Already exists, not an error

    # 3. Run generation
    success = run_generation(model_name, dest, model_config_path)

    if success:
        print(f"\n✓  '{model_name}' done — output at: {dest}")
    else:
        print(f"\n✗  '{model_name}' generation FAILED. Check output above.")
        # Remove the partial output so a re-run starts clean
        if dest.exists():
            shutil.rmtree(dest)
            print(f"  Removed incomplete output folder: {dest}")

    return success


def main():
    parser = argparse.ArgumentParser(
        description="Generate docstrings for benchmark models, one isolated copy per model."
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "--model",
        type=str,
        help="Name of the model to generate for (must match a name in benchmark/config.yaml)",
    )
    group.add_argument(
        "--all",
        action="store_true",
        help="Generate for all models defined in benchmark/config.yaml sequentially",
    )
    parser.add_argument(
        "--repo",
        type=str,
        default=None,
        help="Path to the source repo to document (default: taken from benchmark/config.yaml or data/raw_test_repo)",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Re-generate even if the output folder already exists",
    )
    args = parser.parse_args()

    config = load_config()

    # Resolve source repo: CLI flag > config.yaml > hardcoded default
    if args.repo:
        source_repo = Path(args.repo)
        if not source_repo.is_absolute():
            source_repo = PROJECT_ROOT / source_repo
    else:
        config_repo = config.get("paths", {}).get("source_repo")
        source_repo = PROJECT_ROOT / (config_repo if config_repo else "data/raw_test_repo")

    if not source_repo.exists():
        print(f"ERROR: Source repo not found: {source_repo}")
        sys.exit(1)

    print(f"Source repo: {source_repo}")
    print(f"Output root: {PROJECT_ROOT / config['paths']['raw_generations']}")

    if args.all:
        model_names = [m["name"] for m in config["models"]]
        print(f"\nGenerating for all models: {model_names}")
        results = {}
        for name in model_names:
            results[name] = generate_for_model(name, config, source_repo, args.overwrite)

        print(f"\n{'='*60}")
        print("GENERATION SUMMARY")
        print("=" * 60)
        for name, ok in results.items():
            status = "✓ done" if ok else "✗ failed"
            print(f"  {name:<20} {status}")

        if not all(results.values()):
            sys.exit(1)
    else:
        ok = generate_for_model(args.model, config, source_repo, args.overwrite)
        sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
