"""Tests for profiler — benchmarks original vs converted."""
import textwrap

from polarize.profiler.profiler import profile_scripts, ProfileResult


def test_profile_returns_valid_result(tmp_path):
    fast = tmp_path / "fast.py"
    slow = tmp_path / "slow.py"
    fast.write_text(textwrap.dedent("""\
        total = sum(range(100))
        print(total)
    """))
    slow.write_text(textwrap.dedent("""\
        total = sum(range(100))
        print(total)
    """))
    result = profile_scripts(str(slow), str(fast), script_args=[], runs=3)
    assert isinstance(result, ProfileResult)
    assert result.original_time_s > 0
    assert result.converted_time_s > 0
    assert result.original_peak_memory_mb >= 0
    assert result.converted_peak_memory_mb >= 0


def test_profile_with_script_args(tmp_path):
    script = tmp_path / "script.py"
    script.write_text(textwrap.dedent("""\
        import sys
        n = int(sys.argv[1])
        print(sum(range(n)))
    """))
    result = profile_scripts(str(script), str(script), script_args=["1000"], runs=2)
    assert result.original_time_s > 0
    assert result.converted_time_s > 0


def test_profile_reports_improvement_pct(tmp_path):
    script = tmp_path / "script.py"
    script.write_text('print("hello")\n')
    result = profile_scripts(str(script), str(script), script_args=[], runs=3)
    assert isinstance(result.time_improvement_pct, float)
    assert isinstance(result.memory_improvement_pct, float)


def test_profile_to_dict(tmp_path):
    script = tmp_path / "script.py"
    script.write_text('print("ok")\n')
    result = profile_scripts(str(script), str(script), script_args=[], runs=2)
    d = result.to_dict()
    assert "original_time_s" in d
    assert "converted_time_s" in d
    assert "time_improvement_pct" in d
    assert "memory_improvement_pct" in d
    assert "runs" in d


def test_profile_script_error(tmp_path):
    good = tmp_path / "good.py"
    bad = tmp_path / "bad.py"
    good.write_text('print("ok")\n')
    bad.write_text("raise ValueError('fail')\n")
    result = profile_scripts(str(good), str(bad), script_args=[], runs=2)
    assert result.error is not None
