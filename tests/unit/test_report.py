"""Tests for structured JSON report generation."""
import json

from polarize.discovery.analyzer import ReadCall
from polarize.discovery.scorer import ScoredOperation
from polarize.reporter.report import build_discover_report


def test_report_structure():
    ops = [
        ScoredOperation(
            operation="groupby", line=10, code='df.groupby("col").sum()',
            in_loop=False, compute_weight="high", raw_score=30,
        ),
    ]
    reads = [ReadCall(method="read_csv", line=5, code='pd.read_csv("data.csv")')]
    report = build_discover_report("test.py", ops, reads)
    assert report["file"] == "test.py"
    assert len(report["operations"]) == 1
    assert report["operations"][0]["operation"] == "groupby"
    assert report["operations"][0]["line"] == 10
    assert report["operations"][0]["compute_weight"] == "high"
    assert report["summary"]["total_ops"] == 1
    assert report["summary"]["compute_heavy_ops"] == 1
    assert report["summary"]["suggested_conversion_order"] == [10]
    assert len(report["data_sources"]) == 1


def test_report_is_valid_json():
    ops = [ScoredOperation(operation="merge", line=20, code='df.merge(other, on="id")', in_loop=False, compute_weight="high", raw_score=30)]
    report = build_discover_report("pipeline.py", ops, [])
    serialized = json.dumps(report)
    parsed = json.loads(serialized)
    assert parsed["file"] == "pipeline.py"


def test_report_filters_by_threshold():
    ops = [
        ScoredOperation(operation="groupby", line=10, code="df.groupby()", in_loop=False, compute_weight="high", raw_score=30),
        ScoredOperation(operation="fillna", line=20, code="df.fillna(0)", in_loop=False, compute_weight="medium", raw_score=15),
        ScoredOperation(operation="head", line=30, code="df.head()", in_loop=False, compute_weight="low", raw_score=5),
    ]
    assert len(build_discover_report("f.py", ops, [], threshold="high")["operations"]) == 1
    assert len(build_discover_report("f.py", ops, [], threshold="medium")["operations"]) == 2
    assert len(build_discover_report("f.py", ops, [], threshold="low")["operations"]) == 3


def test_report_conversion_order_matches_score_order():
    ops = [
        ScoredOperation(operation="groupby", line=50, code="df.groupby()", in_loop=False, compute_weight="high", raw_score=30),
        ScoredOperation(operation="sort_values", line=10, code="df.sort_values()", in_loop=False, compute_weight="high", raw_score=25),
    ]
    report = build_discover_report("f.py", ops, [])
    assert report["summary"]["suggested_conversion_order"] == [50, 10]


def test_report_empty_file():
    report = build_discover_report("empty.py", [], [])
    assert report["operations"] == []
    assert report["summary"]["total_ops"] == 0
    assert report["summary"]["compute_heavy_ops"] == 0
