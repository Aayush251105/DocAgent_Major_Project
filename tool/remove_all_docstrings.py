#!/usr/bin/env python3
"""Recursively remove Python docstrings from a file or project directory.

The script removes module, class, function, async-function, and method
docstrings.  It intentionally leaves ordinary string literals untouched.
"""

from __future__ import annotations

import argparse
import ast
import shutil
import sys
from pathlib import Path
from typing import Iterable

SKIPPED_DIRECTORIES = {".git", ".hg", ".svn", ".venv", "venv", "__pycache__"}


def is_docstring(statement: ast.stmt) -> bool:
    """Return whether *statement* is a standalone string literal."""
    return (
        isinstance(statement, ast.Expr)
        and isinstance(statement.value, ast.Constant)
        and isinstance(statement.value.value, str)
    )


class DocstringRemover(ast.NodeTransformer):
    """Remove only the leading docstring expression from AST bodies."""

    def __init__(self) -> None:
        self.removed = 0

    def _remove_from_body(self, node: ast.AST, require_statement: bool = False) -> ast.AST:
        body = node.body  # type: ignore[attr-defined]
        if body and is_docstring(body[0]):
            node.body = body[1:]  # type: ignore[attr-defined]
            self.removed += 1
        if require_statement and not node.body:  # type: ignore[attr-defined]
            node.body = [ast.Pass()]  # type: ignore[attr-defined]
        return node

    def visit_Module(self, node: ast.Module) -> ast.AST:
        self.generic_visit(node)
        return self._remove_from_body(node)

    def visit_ClassDef(self, node: ast.ClassDef) -> ast.AST:
        self.generic_visit(node)
        return self._remove_from_body(node, require_statement=True)

    def visit_FunctionDef(self, node: ast.FunctionDef) -> ast.AST:
        self.generic_visit(node)
        return self._remove_from_body(node, require_statement=True)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> ast.AST:
        self.generic_visit(node)
        return self._remove_from_body(node, require_statement=True)


def python_files(target: Path) -> Iterable[Path]:
    """Yield Python files under *target*, skipping VCS and virtualenv folders."""
    if target.is_file():
        if target.suffix == ".py":
            yield target
        return

    for path in target.rglob("*.py"):
        if not any(parent.name in SKIPPED_DIRECTORIES for parent in path.parents):
            yield path


def remove_docstrings(path: Path, dry_run: bool, backup: bool) -> bool:
    """Strip docstrings from one Python file and return whether it changed."""
    source = path.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(path))
    transformer = DocstringRemover()
    updated = ast.fix_missing_locations(transformer.visit(tree))
    if not transformer.removed:
        return False
    if hasattr(ast, "unparse"):
        output = ast.unparse(updated) + "\n"
    else:  # Python 3.8 compatibility for the project's declared support.
        try:
            import astor
        except ImportError as exc:  # pragma: no cover - Python-version dependent
            raise RuntimeError("Python 3.8 requires the 'astor' package") from exc
        output = astor.to_source(updated)

    if not dry_run:
        if backup:
            shutil.copy2(path, path.with_suffix(path.suffix + ".bak"))
        path.write_text(output, encoding="utf-8")
    return True


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Remove all Python docstrings from a file or project directory."
    )
    parser.add_argument("path", type=Path, help="Python file or project directory to process")
    parser.add_argument("--dry-run", action="store_true", help="Report changes without writing files")
    parser.add_argument("--backup", action="store_true", help="Save each changed file as <name>.py.bak")
    args = parser.parse_args()

    target = args.path.expanduser().resolve()
    if not target.exists():
        parser.error(f"Path does not exist: {target}")
    if target.is_file() and target.suffix != ".py":
        parser.error("A file target must have a .py extension")

    files = list(python_files(target))
    changed = 0
    failed = 0
    for path in files:
        try:
            if remove_docstrings(path, args.dry_run, args.backup):
                changed += 1
                action = "Would update" if args.dry_run else "Updated"
                print(f"{action}: {path}")
        except (OSError, SyntaxError, UnicodeDecodeError) as error:
            failed += 1
            print(f"Error: {path}: {error}", file=sys.stderr)

    verb = "would change" if args.dry_run else "changed"
    print(f"Scanned {len(files)} Python file(s); {verb} {changed}; errors: {failed}.")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
