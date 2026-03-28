"""Profiler — benchmarks original vs converted scripts."""
from __future__ import annotations

import dataclasses
import subprocess
import sys
import time
from typing import Optional


@dataclasses.dataclass
class ProfileResult:
    """Result of profiling original vs converted script."""
    original_time_s: float
    converted_time_s: float
    original_peak_memory_mb: float
    converted_peak_memory_mb: float
    time_improvement_pct: float
    memory_improvement_pct: float
    runs: int
    error: Optional[str] = None

    def to_dict(self) -> dict:
        return dataclasses.asdict(self)


def _run_timed(script_path: str, script_args: list[str], runs: int) -> tuple[float, float, Optional[str]]:
    # First, check script runs without error
    check = subprocess.run(
        [sys.executable, script_path, *script_args],
        capture_output=True, text=True, timeout=120,
    )
    if check.returncode != 0:
        return 0.0, 0.0, f"Script error: {check.stderr.strip()}"

    # Measure memory with a wrapper on first run
    memory_wrapper = (
        "import tracemalloc, runpy, sys; "
        "tracemalloc.start(); "
        f"sys.argv = {[script_path, *script_args]!r}; "
        f"runpy.run_path({script_path!r}, run_name='__main__'); "
        "peak = tracemalloc.get_traced_memory()[1]; "
        "tracemalloc.stop(); "
        f"print(peak, file=sys.stderr)"
    )
    mem_result = subprocess.run(
        [sys.executable, "-c", memory_wrapper],
        capture_output=True, text=True, timeout=120,
    )
    peak_memory_mb = 0.0
    if mem_result.returncode == 0 and mem_result.stderr.strip():
        try:
            peak_bytes = int(mem_result.stderr.strip().split('\n')[-1])
            peak_memory_mb = peak_bytes / (1024 * 1024)
        except (ValueError, IndexError):
            pass

    # Measure time over multiple runs
    times = []
    for _ in range(runs):
        start = time.perf_counter()
        subprocess.run(
            [sys.executable, script_path, *script_args],
            capture_output=True, timeout=120,
        )
        elapsed = time.perf_counter() - start
        times.append(elapsed)

    avg_time = sum(times) / len(times)
    return avg_time, peak_memory_mb, None


def profile_scripts(
    original_path: str,
    converted_path: str,
    script_args: list[str],
    runs: int = 5,
) -> ProfileResult:
    orig_time, orig_mem, orig_err = _run_timed(original_path, script_args, runs)
    if orig_err:
        return ProfileResult(
            original_time_s=0, converted_time_s=0,
            original_peak_memory_mb=0, converted_peak_memory_mb=0,
            time_improvement_pct=0, memory_improvement_pct=0,
            runs=runs, error=f"Original: {orig_err}",
        )

    conv_time, conv_mem, conv_err = _run_timed(converted_path, script_args, runs)
    if conv_err:
        return ProfileResult(
            original_time_s=orig_time, converted_time_s=0,
            original_peak_memory_mb=orig_mem, converted_peak_memory_mb=0,
            time_improvement_pct=0, memory_improvement_pct=0,
            runs=runs, error=f"Converted: {conv_err}",
        )

    time_pct = ((orig_time - conv_time) / orig_time * 100) if orig_time > 0 else 0.0
    mem_pct = ((orig_mem - conv_mem) / orig_mem * 100) if orig_mem > 0 else 0.0

    return ProfileResult(
        original_time_s=round(orig_time, 6),
        converted_time_s=round(conv_time, 6),
        original_peak_memory_mb=round(orig_mem, 3),
        converted_peak_memory_mb=round(conv_mem, 3),
        time_improvement_pct=round(time_pct, 2),
        memory_improvement_pct=round(mem_pct, 2),
        runs=runs,
    )
