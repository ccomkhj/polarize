"""Validation — AST syntax check, import check, and output equivalence."""
from __future__ import annotations

import ast
import dataclasses
import subprocess
import sys


@dataclasses.dataclass
class ValidationResult:
    """Result of a single validation check."""
    check: str
    passed: bool
    message: str


def check_syntax(source: str) -> ValidationResult:
    try:
        ast.parse(source)
        return ValidationResult(check="syntax", passed=True, message="Valid Python syntax")
    except SyntaxError as e:
        return ValidationResult(check="syntax", passed=False, message=f"Syntax error at line {e.lineno}: {e.msg}")


def check_imports(source: str) -> ValidationResult:
    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name == "polars":
                    return ValidationResult(check="imports", passed=True, message="Polars import found")
    return ValidationResult(check="imports", passed=False, message="Polars import not found in converted file")


def run_and_compare(
    original_path: str,
    converted_path: str,
    script_args: list[str],
    timeout: int = 60,
) -> ValidationResult:
    try:
        original_result = subprocess.run(
            [sys.executable, original_path, *script_args],
            capture_output=True, text=True, timeout=timeout,
        )
    except subprocess.TimeoutExpired:
        return ValidationResult(check="equivalence", passed=False, message="Original script timed out")

    if original_result.returncode != 0:
        return ValidationResult(check="equivalence", passed=False, message=f"Original script error: {original_result.stderr.strip()}")

    try:
        converted_result = subprocess.run(
            [sys.executable, converted_path, *script_args],
            capture_output=True, text=True, timeout=timeout,
        )
    except subprocess.TimeoutExpired:
        return ValidationResult(check="equivalence", passed=False, message="Converted script timed out")

    if converted_result.returncode != 0:
        return ValidationResult(check="equivalence", passed=False, message=f"Converted script error: {converted_result.stderr.strip()}")

    original_out = original_result.stdout.strip()
    converted_out = converted_result.stdout.strip()

    if original_out == converted_out:
        return ValidationResult(check="equivalence", passed=True, message="Outputs match")

    return ValidationResult(
        check="equivalence", passed=False,
        message=f"Output mismatch.\nOriginal:\n{original_out[:500]}\nConverted:\n{converted_out[:500]}",
    )
