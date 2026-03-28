"""Compute-weight scoring for pandas operations."""
from __future__ import annotations

import dataclasses

from polarize.discovery.analyzer import PandasOperation


@dataclasses.dataclass
class ScoredOperation:
    """A pandas operation with a compute-weight score."""
    operation: str
    line: int
    code: str
    in_loop: bool
    compute_weight: str  # "high", "medium", "low"
    raw_score: int


# Base scores for operations
BASE_SCORES: dict[str, int] = {
    # High
    "groupby": 30,
    "merge": 30,
    "join": 30,
    "apply": 30,
    "pivot_table": 30,
    "melt": 30,
    "sort_values": 25,
    "sort_index": 25,
    "concat": 25,
    # Medium
    "fillna": 15,
    "drop_duplicates": 15,
    "value_counts": 15,
    "agg": 15,
    # Low
    "head": 5,
    "tail": 5,
    "rename": 5,
}

LOOP_MULTIPLIER = 2

# Thresholds
HIGH_THRESHOLD = 20
MEDIUM_THRESHOLD = 10


def _weight_label(score: int) -> str:
    if score >= HIGH_THRESHOLD:
        return "high"
    if score >= MEDIUM_THRESHOLD:
        return "medium"
    return "low"


def score_operations(operations: list[PandasOperation]) -> list[ScoredOperation]:
    """Score and rank pandas operations by compute weight."""
    scored = []
    for op in operations:
        base = BASE_SCORES.get(op.operation, 10)
        raw = base * LOOP_MULTIPLIER if op.in_loop else base
        scored.append(ScoredOperation(
            operation=op.operation,
            line=op.line,
            code=op.code,
            in_loop=op.in_loop,
            compute_weight=_weight_label(raw),
            raw_score=raw,
        ))
    scored.sort(key=lambda s: s.raw_score, reverse=True)
    return scored
