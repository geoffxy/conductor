import pathlib
import pytest

import conductor.lib as condlib
from .conductor_runner import ConductorRunner, FIXTURE_TEMPLATES


def test_get_output_path_non_cond():
    with pytest.raises(RuntimeError):
        _ = condlib.get_output_path()


def test_get_deps_paths_non_cond():
    with pytest.raises(RuntimeError):
        _ = condlib.get_deps_paths()


def test_get_deps_paths(tmp_path: pathlib.Path):
    cond = ConductorRunner.from_template(tmp_path, FIXTURE_TEMPLATES["lib-test"])
    result = cond.run("//path:deps")
    # The deps.py script in lib-test/path/ does the correctness assertions.
    assert result.returncode == 0


def test_get_output_path(tmp_path: pathlib.Path):
    cond = ConductorRunner.from_template(tmp_path, FIXTURE_TEMPLATES["lib-test"])
    result = cond.run("//path:output_path")
    # The output_path.py script in lib-test/path/ does the correctness assertions.
    assert result.returncode == 0
