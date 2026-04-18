#!/usr/bin/env python3
import ast
import subprocess
import sys


def get_staged_py_files() -> list[str]:
    result = subprocess.run(
        ["git", "diff", "--cached", "--name-only", "--diff-filter=ACM"],
        capture_output=True, text=True,
    )
    return [f for f in result.stdout.splitlines() if f.endswith(".py")]


def _parse_file(filepath: str):
    try:
        with open(filepath, encoding="utf-8") as f:
            return ast.parse(f.read()), None
    except SyntaxError as e:
        return None, f"[SyntaxError] {e}"
    except OSError as e:
        return None, f"[OSError] {e}"


def _is_docstring(node) -> bool:
    return (
        isinstance(node, ast.Expr)
        and isinstance(node.value, ast.Constant)
        and isinstance(node.value.value, str)
    )


def _check_docstrings(tree: ast.AST, filepath: str) -> list[str]:
    errors = []
    targets = (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)
    for node in ast.walk(tree):
        if isinstance(node, targets) and node.body and _is_docstring(node.body[0]):
            name = getattr(node, "name", "<module>")
            line = node.body[0].lineno
            errors.append(f"  {filepath}:{line}  [docstring] {name}")
    return errors


def _check_line_limits(tree: ast.AST, filepath: str) -> list[str]:
    errors = []
    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        length = node.end_lineno - node.lineno + 1
        if length > 20:
            errors.append(
                f"  {filepath}:{node.lineno}  [20lines] '{node.name}' {length}lines"
            )
    return errors


def check_file(filepath: str) -> list[str]:
    tree, err = _parse_file(filepath)
    if err:
        return [f"  {filepath}: {err}"]
    return _check_docstrings(tree, filepath) + _check_line_limits(tree, filepath)


def main() -> None:
    files = get_staged_py_files()
    if not files:
        sys.exit(0)

    all_errors: list[str] = []
    for filepath in files:
        all_errors.extend(check_file(filepath))

    if all_errors:
        print("[FAIL] CLAUDE.md rules violated:\n")
        for err in all_errors:
            print(err)
        print("\nCommit cancelled. Fix violations and try again.")
        sys.exit(1)

    print(f"[OK] CLAUDE.md rules passed ({len(files)} files checked)")


if __name__ == "__main__":
    main()
