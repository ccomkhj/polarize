"""CLI entry point — four commands for agent interaction."""
from __future__ import annotations

import json
import os
import sys

import click

from polarize.discovery.analyzer import analyze_file
from polarize.discovery.scorer import score_operations, BASE_SCORES, HIGH_THRESHOLD, MEDIUM_THRESHOLD
from polarize.reporter.report import build_discover_report
from polarize.validator.validator import check_syntax, check_imports, run_and_compare
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

    files = []
    if os.path.isfile(path):
        files = [path]
    elif os.path.isdir(path) and recursive:
        for root, _, filenames in os.walk(path):
            for f in filenames:
                if f.endswith(".py"):
                    files.append(os.path.join(root, f))
    elif os.path.isdir(path):
        files = [os.path.join(path, f) for f in os.listdir(path) if f.endswith(".py")]

    for file_path in files:
        analysis = analyze_file(file_path)
        if analysis.pandas_alias is None:
            continue
        scored = score_operations(analysis.operations)
        report = build_discover_report(file_path, scored, analysis.read_calls, threshold=threshold)

        if output_format == "json":
            click.echo(json.dumps(report, indent=2))
        else:
            click.echo(f"File: {report['file']}")
            click.echo(f"Total ops: {report['summary']['total_ops']}, "
                       f"Compute-heavy: {report['summary']['compute_heavy_ops']}")
            click.echo(f"Conversion order: {report['summary']['suggested_conversion_order']}")
            click.echo("")
            for op in report["operations"]:
                ctx = f" ({op['context']})" if "context" in op else ""
                click.echo(f"  L{op['line']} [{op['compute_weight']}] {op['operation']}: {op['code']}{ctx}")


@cli.command()
@click.option("--original", required=True, type=click.Path(exists=True))
@click.option("--converted", required=True, type=click.Path(exists=True))
@click.argument("script_args", nargs=-1, type=click.UNPROCESSED)
def validate(original: str, converted: str, script_args: tuple):
    """Validate that converted script produces equivalent output."""
    with open(converted) as f:
        converted_source = f.read()
    checks = []
    syntax_result = check_syntax(converted_source)
    checks.append(syntax_result)
    import_result = check_imports(converted_source)
    checks.append(import_result)
    equiv_result = run_and_compare(original, converted, list(script_args))
    checks.append(equiv_result)
    all_passed = all(c.passed for c in checks)
    output = {
        "status": "pass" if all_passed else "fail",
        "checks": [{"check": c.check, "passed": c.passed, "message": c.message} for c in checks],
    }
    click.echo(json.dumps(output, indent=2))
    sys.exit(0 if all_passed else 1)


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
