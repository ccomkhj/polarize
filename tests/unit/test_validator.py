"""Tests for validator — AST check and output equivalence."""
import textwrap

from polarize.validator.validator import (
    check_syntax,
    check_imports,
    run_and_compare,
    ValidationResult,
)


def test_check_syntax_valid():
    source = textwrap.dedent("""\
        import polars as pl
        df = pl.read_csv("data.csv")
    """)
    result = check_syntax(source)
    assert result.passed is True


def test_check_syntax_invalid():
    source = "def foo(:\n    pass"
    result = check_syntax(source)
    assert result.passed is False
    assert "syntax" in result.message.lower()


def test_check_imports_polars_present():
    source = textwrap.dedent("""\
        import polars as pl
        df = pl.read_csv("data.csv")
    """)
    result = check_imports(source)
    assert result.passed is True


def test_check_imports_from_polars_present():
    source = textwrap.dedent("""\
        from polars import read_csv
        df = read_csv("data.csv")
    """)
    result = check_imports(source)
    assert result.passed is True


def test_check_imports_polars_missing():
    source = textwrap.dedent("""\
        import pandas as pd
        df = pd.read_csv("data.csv")
    """)
    result = check_imports(source)
    assert result.passed is False
    assert "polars" in result.message.lower()


def test_check_imports_invalid_syntax():
    result = check_imports("def broken(:\n    pass\n")
    assert result.passed is False
    assert "syntax error" in result.message.lower()


def test_run_and_compare_identical_output(tmp_path):
    original = tmp_path / "original.py"
    converted = tmp_path / "converted.py"
    original.write_text(textwrap.dedent("""\
        import sys
        print("a,b")
        print("1,2")
    """))
    converted.write_text(textwrap.dedent("""\
        import sys
        print("a,b")
        print("1,2")
    """))
    result = run_and_compare(str(original), str(converted), script_args=[])
    assert result.passed is True


def test_run_and_compare_different_output(tmp_path):
    original = tmp_path / "original.py"
    converted = tmp_path / "converted.py"
    original.write_text(textwrap.dedent("""\
        print("a,b")
        print("1,2")
    """))
    converted.write_text(textwrap.dedent("""\
        print("a,b")
        print("3,4")
    """))
    result = run_and_compare(str(original), str(converted), script_args=[])
    assert result.passed is False


def test_run_and_compare_with_args(tmp_path):
    original = tmp_path / "original.py"
    converted = tmp_path / "converted.py"
    original.write_text(textwrap.dedent("""\
        import sys
        print(f"hello {sys.argv[1]}")
    """))
    converted.write_text(textwrap.dedent("""\
        import sys
        print(f"hello {sys.argv[1]}")
    """))
    result = run_and_compare(str(original), str(converted), script_args=["world"])
    assert result.passed is True


def test_run_and_compare_script_error(tmp_path):
    original = tmp_path / "original.py"
    converted = tmp_path / "converted.py"
    original.write_text('print("ok")\n')
    converted.write_text("raise ValueError('broken')\n")
    result = run_and_compare(str(original), str(converted), script_args=[])
    assert result.passed is False
    assert "error" in result.message.lower()
