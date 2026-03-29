"""Polarize — agent-native pandas-to-Polars conversion toolkit."""
from __future__ import annotations

from typing import Optional

from polarize.app import discover_path, validate_conversion

__version__ = "0.1.0"


def discover(path: str, threshold: str = "medium", recursive: bool = False) -> dict:
    return discover_path(path, threshold=threshold, recursive=recursive)


def validate(
    original: str,
    converted: str,
    script_args: Optional[list[str]] = None,
) -> dict:
    return validate_conversion(original, converted, script_args)


def profile(
    original: str,
    converted: str,
    runs: int = 5,
    script_args: Optional[list[str]] = None,
) -> dict:
    from polarize.profiler.profiler import profile_scripts

    result = profile_scripts(original, converted, script_args or [], runs=runs)
    return result.to_dict()
