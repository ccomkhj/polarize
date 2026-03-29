"""Shared application logic for the CLI and public Python API."""
from __future__ import annotations

from pathlib import Path
from typing import Any

from polarize.discovery.analyzer import analyze_file
from polarize.discovery.scorer import score_operations
from polarize.reporter.report import build_discover_report
from polarize.validator.validator import (
    ValidationResult,
    check_imports,
    check_syntax,
    run_and_compare,
)


def discover_path(
    path: str,
    threshold: str = "medium",
    recursive: bool = False,
) -> dict[str, Any]:
    """Discover pandas operations for a file or directory."""
    path_obj = Path(path)
    if not path_obj.exists():
        raise FileNotFoundError(path)

    if path_obj.is_file():
        return _discover_file(path, threshold)

    reports: list[dict[str, Any]] = []
    for file_path in _iter_python_files(path_obj, recursive):
        report = _discover_file(str(file_path), threshold)
        if report["operations"] or report["data_sources"]:
            reports.append(report)

    return {"path": path, "reports": reports}


def validate_conversion(
    original: str,
    converted: str,
    script_args: list[str] | None = None,
) -> dict[str, Any]:
    """Run all validation checks and return structured output."""
    converted_source = Path(converted).read_text()
    syntax_result = check_syntax(converted_source)

    checks = [syntax_result]
    if syntax_result.passed:
        checks.append(check_imports(converted_source))
        checks.append(run_and_compare(original, converted, script_args or []))
    else:
        checks.extend(
            [
                ValidationResult(
                    check="imports",
                    passed=False,
                    message="Skipped import check because converted file has invalid syntax",
                ),
                ValidationResult(
                    check="equivalence",
                    passed=False,
                    message="Skipped equivalence check because converted file has invalid syntax",
                ),
            ]
        )

    return _validation_output(checks)


def _discover_file(file_path: str, threshold: str) -> dict[str, Any]:
    analysis = analyze_file(file_path)
    scored = score_operations(analysis.operations)
    return build_discover_report(
        file_path,
        scored,
        analysis.read_calls,
        threshold=threshold,
    )


def _iter_python_files(path: Path, recursive: bool) -> list[Path]:
    if recursive:
        return sorted(path.rglob("*.py"))
    return sorted(path.glob("*.py"))


def _validation_output(checks: list[ValidationResult]) -> dict[str, Any]:
    all_passed = all(check.passed for check in checks)
    return {
        "status": "pass" if all_passed else "fail",
        "checks": [
            {
                "check": check.check,
                "passed": check.passed,
                "message": check.message,
            }
            for check in checks
        ],
    }
