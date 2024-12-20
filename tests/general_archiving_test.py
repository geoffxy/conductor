import pathlib
from conductor.config import VERSION_INDEX_NAME
from conductor.context import Context
from conductor.execution.version_index import VersionIndex
from conductor.task_identifier import TaskIdentifier
from conductor.utils.output_archiving import create_archive, restore_archive
from .conductor_runner import ConductorRunner, EXAMPLE_TEMPLATES


def test_overall_archiving(tmp_path: pathlib.Path):
    cond = ConductorRunner.from_template(tmp_path, EXAMPLE_TEMPLATES["dependencies"])
    result = cond.run("//figures:graph")
    assert result.returncode == 0

    run_benchmark_id = TaskIdentifier.from_str("//experiments:run_benchmark")
    figures_id = TaskIdentifier.from_str("//figures:graph")
    version_index = VersionIndex.create_or_load(cond.output_path / VERSION_INDEX_NAME)
    versions = version_index.get_all_versions_for_task(run_benchmark_id)
    assert len(versions) == 1

    ctx = Context(cond.project_root)
    ctx.task_index.load_transitive_closure(figures_id)
    to_archive = [
        (run_benchmark_id, versions[0]),
        (figures_id, None),
    ]
    archive_output_path = cond.project_root / "test_archive.tar.gz"
    assert not archive_output_path.exists()
    create_archive(ctx, to_archive, archive_output_path)
    assert archive_output_path.exists()

    # Clear the output directory and recreate the Context to clear out cached
    # state.
    result = cond.clean()
    ctx = Context(cond.project_root)
    assert result.returncode == 0

    # Restore the archive.
    restore_archive(ctx, archive_output_path)

    # Check that the output directories for the relevant tasks were restored.
    expt_out_dir = cond.find_task_output_dir(str(run_benchmark_id), is_experiment=True)
    assert expt_out_dir is not None
    assert expt_out_dir.exists()
    assert expt_out_dir.is_dir()
    assert (expt_out_dir / "results.csv").exists()

    figures_out_dir = cond.find_task_output_dir(str(figures_id), is_experiment=False)
    assert figures_out_dir is not None
    assert figures_out_dir.exists()
    assert figures_out_dir.is_dir()
    assert (figures_out_dir / "graph.csv").exists()
