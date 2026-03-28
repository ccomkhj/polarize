import pathlib

import pytest

FIXTURES_DIR = pathlib.Path(__file__).parent / "fixtures"


@pytest.fixture
def fixtures_dir():
    return FIXTURES_DIR


@pytest.fixture
def groupby_agg_dir(fixtures_dir):
    return fixtures_dir / "groupby_agg"


@pytest.fixture
def merge_join_dir(fixtures_dir):
    return fixtures_dir / "merge_join"


@pytest.fixture
def sort_values_dir(fixtures_dir):
    return fixtures_dir / "sort_values"


@pytest.fixture
def apply_func_dir(fixtures_dir):
    return fixtures_dir / "apply_func"


@pytest.fixture
def chained_ops_dir(fixtures_dir):
    return fixtures_dir / "chained_ops"


@pytest.fixture
def loop_groupby_dir(fixtures_dir):
    return fixtures_dir / "loop_groupby"
