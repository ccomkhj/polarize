"""Polarize — agent-native pandas-to-Polars conversion toolkit."""
from __future__ import annotations

from typing import Optional

__version__ = "0.1.0"


def discover(path: str, threshold: str = "medium", recursive: bool = False) -> dict:
    from polarize.discovery.analyzer import analyze_file
    from polarize.discovery.scorer import score_operations
    from polarize.reporter.report import build_discover_report

    analysis = analyze_file(path)
    scored = score_operations(analysis.operations)
    return build_discover_report(path, scored, analysis.read_calls, threshold=threshold)


def validate(
    original: str,
    converted: str,
    script_args: Optional[list[str]] = None,
) -> dict:
    from polarize.validator.validator import check_syntax, check_imports, run_and_compare

    with open(converted) as f:
        converted_source = f.read()

    checks = [
        check_syntax(converted_source),
        check_imports(converted_source),
        run_and_compare(original, converted, script_args or []),
    ]

    all_passed = all(c.passed for c in checks)
    return {
        "status": "pass" if all_passed else "fail",
        "checks": [
            {"check": c.check, "passed": c.passed, "message": c.message}
            for c in checks
        ],
    }


def profile(
    original: str,
    converted: str,
    runs: int = 5,
    script_args: Optional[list[str]] = None,
) -> dict:
    from polarize.profiler.profiler import profile_scripts

    result = profile_scripts(original, converted, script_args or [], runs=runs)
    return result.to_dict()
