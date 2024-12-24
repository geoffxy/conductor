import pathlib
import shutil

from .conductor_runner import (
    ConductorRunner,
    count_task_outputs,
    EXAMPLE_TEMPLATES,
    FIXTURE_TEMPLATES,
)
from conductor.utils.output_archiving import platform_archive_type


def test_archive_restore(tmp_path: pathlib.Path):
    cond = ConductorRunner.from_template(tmp_path, EXAMPLE_TEMPLATES["dependencies"])
    result = cond.archive("//figures:graph", output_path=None, latest=False)
    # We didn't run the task yet, so archiving it will not work
    assert result.returncode != 0

    result = cond.run("//figures:graph")
    assert result.returncode == 0

    result = cond.archive("//figures:graph", output_path=None, latest=False)
    assert result.returncode == 0

    expected_archive_type = platform_archive_type()

    # Make sure we found the archive
    found_archive = False
    archive_name = None
    orig_archive_path = None
    for file in cond.output_path.iterdir():
        if file.name.endswith(f".tar.{expected_archive_type.extension()}"):
            found_archive = True
            archive_name = file.name
            orig_archive_path = file
            shutil.copy2(file, cond.project_root)
            assert (cond.project_root / archive_name).exists()
            break
    assert found_archive and archive_name is not None and orig_archive_path is not None

    # Restoring the archive into an output directory that already contains the results
    # should fail
    result = cond.restore(orig_archive_path, strict=True)
    assert result.returncode != 0

    # Remove the output directory and then try restoring
    shutil.rmtree(cond.output_path)
    result = cond.restore(cond.project_root / archive_name, strict=True)
    assert result.returncode == 0

    # Only the run_experiment() task output should be restored
    restored_experiment_dir = cond.output_path / "experiments"
    assert restored_experiment_dir.is_dir()
    assert count_task_outputs(restored_experiment_dir) == 1


def test_restore_invalid(tmp_path: pathlib.Path):
    cond = ConductorRunner.from_template(tmp_path, EXAMPLE_TEMPLATES["hello_world"])
    result = cond.restore(cond.output_path / "non_existent.tar.zst", strict=True)
    assert result.returncode != 0


def test_archive_output(tmp_path: pathlib.Path):
    cond = ConductorRunner.from_template(tmp_path, EXAMPLE_TEMPLATES["hello_world"])
    result = cond.run("//:hello_world")
    assert result.returncode == 0

    expected_archive_type = platform_archive_type()
    expected_extension = expected_archive_type.extension()
    output_archive = cond.project_root / f"custom.tar.{expected_extension}"
    assert not output_archive.exists()
    result = cond.archive("//:hello_world", output_path=output_archive, latest=False)
    assert result.returncode == 0
    assert output_archive.exists() and output_archive.is_file()


def test_archive_output_dir(tmp_path: pathlib.Path):
    cond = ConductorRunner.from_template(tmp_path, EXAMPLE_TEMPLATES["hello_world"])
    result = cond.run("//:hello_world")
    assert result.returncode == 0

    # Provide an output directory only
    result = cond.archive("//:hello_world", output_path=cond.project_root, latest=False)
    assert result.returncode == 0

    expected_archive_type = platform_archive_type()
    expected_extension = expected_archive_type.extension()

    # Ensure the archive was saved in the correct output directory with a
    # Conductor-provided name
    archive_found = False
    for file in cond.project_root.iterdir():
        if file.name.startswith("cond-archive") and file.name.endswith(
            f".tar.{expected_extension}"
        ):
            archive_found = True
            break
    assert archive_found


def test_archive_overwrite(tmp_path: pathlib.Path):
    cond = ConductorRunner.from_template(tmp_path, EXAMPLE_TEMPLATES["hello_world"])
    result = cond.run("//:hello_world")
    assert result.returncode == 0

    existing_file = cond.project_root / "test.txt"
    existing_file.touch()
    assert existing_file.is_file()

    # Conductor should not overwrite existing files
    result = cond.archive("//:hello_world", output_path=existing_file, latest=False)
    assert result.returncode != 0


def test_archive_restore_latest(tmp_path: pathlib.Path):
    cond = ConductorRunner.from_template(tmp_path, EXAMPLE_TEMPLATES["hello_world"])
    result = cond.run("//:hello_world")
    assert result.returncode == 0
    assert count_task_outputs(cond.output_path) == 1

    # Generate a newer output
    result = cond.run("//:hello_world", again=True)
    assert result.returncode == 0
    assert count_task_outputs(cond.output_path) == 2

    expected_archive_type = platform_archive_type()
    expected_extension = expected_archive_type.extension()

    # Archive the latest only
    output_archive = cond.project_root / f"latest.tar.{expected_extension}"
    assert not output_archive.exists()
    result = cond.archive("//:hello_world", output_path=output_archive, latest=True)
    assert result.returncode == 0
    assert output_archive.exists() and output_archive.is_file()

    # Restoring into an existing experiment output directory should fail
    result = cond.restore(output_archive, strict=True)
    assert result.returncode != 0

    # Restore into an empty output path. Only one of the experiment outputs
    # should have been archived (and thus restored).
    shutil.rmtree(cond.output_path)
    result = cond.restore(output_archive, strict=True)
    assert result.returncode == 0
    assert count_task_outputs(cond.output_path) == 1


def test_partial_archive_restore(tmp_path: pathlib.Path):
    cond = ConductorRunner.from_template(tmp_path, FIXTURE_TEMPLATES["experiments"])
    result = cond.run("//sweep:threads-args-1")
    assert result.returncode == 0

    # Make an archive with just this first result.
    expected_archive_type = platform_archive_type()
    expected_extension = expected_archive_type.extension()
    output_archive1 = cond.project_root / f"partial1.tar.{expected_extension}"
    assert not output_archive1.exists()
    result = cond.archive(
        "//sweep:threads-args", output_path=output_archive1, latest=False
    )
    assert result.returncode == 0
    assert output_archive1.exists() and output_archive1.is_file()

    # Run the second experiment.
    result = cond.run("//sweep:threads-args-2")
    assert result.returncode == 0

    # Make an archive with both results.
    output_archive2 = cond.project_root / f"partial2.tar.{expected_extension}"
    assert not output_archive2.exists()
    result = cond.archive(
        "//sweep:threads-args", output_path=output_archive2, latest=False
    )
    assert result.returncode == 0
    assert output_archive2.exists() and output_archive2.is_file()

    shutil.rmtree(cond.output_path)
    expected_task_out = cond.output_path / "sweep"

    # Restore the first archive - it should succeed.
    result = cond.restore(output_archive1, strict=False)
    assert result.returncode == 0
    assert count_task_outputs(expected_task_out) == 1

    # Restore the second archive - on strict mode it should fail.
    result = cond.restore(output_archive2, strict=True)
    assert result.returncode != 0
    assert count_task_outputs(expected_task_out) == 1

    # Restore on non-strict mode.
    result = cond.restore(output_archive2, strict=False)
    if result.returncode != 0:
        print(result.stdout.decode("utf-8"))
        print(result.stderr.decode("utf-8"))
    assert result.returncode == 0
    assert count_task_outputs(expected_task_out) == 2
