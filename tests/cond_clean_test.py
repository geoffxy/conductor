import pathlib
from .conductor_runner import ConductorRunner, EXAMPLE_TEMPLATES


def test_cond_clean(tmp_path: pathlib.Path):
    cond = ConductorRunner.from_template(tmp_path, EXAMPLE_TEMPLATES["hello_world"])
    result = cond.run("//:hello_world")
    assert result.returncode == 0
    assert cond.output_path.exists()

    result = cond.clean()
    assert result.returncode == 0
    assert not cond.output_path.exists()
