"""CLI entry point — four commands for agent interaction."""
from __future__ import annotations

import json
import os
import sys
from typing import Any

import click

from polarize.app import discover_path, validate_conversion
from polarize.discovery.scorer import BASE_SCORES, HIGH_THRESHOLD, MEDIUM_THRESHOLD
from polarize.profiler.profiler import profile_scripts


def _weight_label(score: int) -> str:
    if score >= HIGH_THRESHOLD:
        return "high"
    if score >= MEDIUM_THRESHOLD:
        return "medium"
    return "low"


@click.group()
def cli():
    """Polarize — agent-native pandas-to-Polars conversion toolkit."""
    pass


@cli.command()
@click.argument("path")
@click.option("--threshold", type=click.Choice(["high", "medium", "low"]), default="medium")
@click.option("--recursive", is_flag=True, default=False)
@click.option("--format", "output_format", type=click.Choice(["json", "text"]), default="json")
def discover(path: str, threshold: str, recursive: bool, output_format: str):
    """Discover compute-heavy pandas operations in a file or directory."""
    if not os.path.exists(path):
        click.echo(json.dumps({"error": f"Path not found: {path}"}), err=True)
        sys.exit(2)

    report = discover_path(path, threshold=threshold, recursive=recursive)

    if output_format == "json":
        click.echo(json.dumps(report, indent=2))
        return

    _echo_discover_text(report)


@cli.command()
@click.option("--original", required=True, type=click.Path(exists=True))
@click.option("--converted", required=True, type=click.Path(exists=True))
@click.argument("script_args", nargs=-1, type=click.UNPROCESSED)
def validate(original: str, converted: str, script_args: tuple):
    """Validate that converted script produces equivalent output."""
    output = validate_conversion(original, converted, list(script_args))
    click.echo(json.dumps(output, indent=2))
    sys.exit(0 if output["status"] == "pass" else 1)


@cli.command()
@click.option("--original", required=True, type=click.Path(exists=True))
@click.option("--converted", required=True, type=click.Path(exists=True))
@click.option("--runs", default=5, type=int)
@click.argument("script_args", nargs=-1, type=click.UNPROCESSED)
def profile(original: str, converted: str, runs: int, script_args: tuple):
    """Benchmark original vs converted script performance."""
    result = profile_scripts(original, converted, list(script_args), runs=runs)
    click.echo(json.dumps(result.to_dict(), indent=2))
    if result.error:
        sys.exit(1)


@cli.command()
@click.option("--threshold", type=click.Choice(["high", "medium", "low"]), default="low")
def ops(threshold: str):
    """List supported pandas operations and their compute weights."""
    weight_rank = {"high": 3, "medium": 2, "low": 1}
    min_rank = weight_rank[threshold]
    operations = []
    for name, base_score in sorted(BASE_SCORES.items(), key=lambda x: x[1], reverse=True):
        weight = _weight_label(base_score)
        if weight_rank[weight] >= min_rank:
            operations.append({"name": name, "compute_weight": weight, "base_score": base_score})
    click.echo(json.dumps({"operations": operations}, indent=2))


def _echo_discover_text(report: dict[str, Any]) -> None:
    reports = _discover_reports(report)
    if not reports:
        click.echo("No pandas operations found.")
        return

    for index, item in enumerate(reports):
        if index > 0:
            click.echo("")
        click.echo(f"File: {item['file']}")
        click.echo(
            f"Total ops: {item['summary']['total_ops']}, "
            f"Compute-heavy: {item['summary']['compute_heavy_ops']}"
        )
        click.echo(f"Conversion order: {item['summary']['suggested_conversion_order']}")
        click.echo("")
        for op in item["operations"]:
            ctx = f" ({op['context']})" if "context" in op else ""
            click.echo(
                f"  L{op['line']} [{op['compute_weight']}] "
                f"{op['operation']}: {op['code']}{ctx}"
            )


def _discover_reports(report: dict[str, Any]) -> list[dict[str, Any]]:
    if "file" in report:
        return [report]
    return report["reports"]
