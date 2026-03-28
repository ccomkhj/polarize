"""Structured JSON report generation."""
from __future__ import annotations

from polarize.discovery.analyzer import ReadCall
from polarize.discovery.scorer import ScoredOperation

WEIGHT_RANK = {"high": 3, "medium": 2, "low": 1}


def build_discover_report(
    file_path: str,
    scored_ops: list[ScoredOperation],
    read_calls: list[ReadCall],
    threshold: str = "low",
) -> dict:
    min_rank = WEIGHT_RANK.get(threshold, 1)
    filtered = [op for op in scored_ops if WEIGHT_RANK[op.compute_weight] >= min_rank]

    operations = []
    for op in filtered:
        entry = {"line": op.line, "code": op.code, "operation": op.operation, "compute_weight": op.compute_weight}
        if op.in_loop:
            entry["context"] = "called inside a loop"
        operations.append(entry)

    compute_heavy = [op for op in filtered if op.compute_weight == "high"]
    data_sources = [{"method": rc.method, "line": rc.line, "code": rc.code} for rc in read_calls]

    return {
        "file": file_path,
        "operations": operations,
        "data_sources": data_sources,
        "summary": {
            "total_ops": len(filtered),
            "compute_heavy_ops": len(compute_heavy),
            "suggested_conversion_order": [op.line for op in filtered],
        },
    }
