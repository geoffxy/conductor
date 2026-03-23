import pathlib
import sqlite3
from typing import Iterable, Tuple, Optional
import conductor.execution.version_index_queries as q
from conductor.config import VERSION_INDEX_BACKUP_NAME_TEMPLATE, VERSION_INDEX_NAME
from conductor.execution.version_index import VersionIndex
from conductor.errors import CorruptedVersionIndex
from conductor.task_identifier import TaskIdentifier
import pytest

# pylint: disable=protected-access


def test_v1_to_v2_upgrade(tmp_path: pathlib.Path):
    test_versions = [
        ("//:test1", 1, "unknown"),
        ("//:test2", 2, "unknown"),
        ("//:test3", 3, "unknown"),
    ]
    version_index_path = tmp_path / VERSION_INDEX_NAME

    # Create an existing version index (format 1).
    create_v1_version_index(version_index_path, test_versions)

    # Run the upgrade.
    conn = sqlite3.connect(version_index_path)
    VersionIndex._run_v1_to_v2_migration(conn, version_index_path)

    # The backup version index should still exist.
    assert (
        tmp_path / VERSION_INDEX_BACKUP_NAME_TEMPLATE.format(vfrom=1, vto=2)
    ).is_file()

    # The version number should have changed to 2.
    conn.close()
    conn = sqlite3.connect(version_index_path)
    assert conn.execute(q.get_format_version).fetchone()[0] == 2

    # The existing versions should be readable.
    for i, row in enumerate(conn.execute(q.all_entries)):
        assert row[0] == test_versions[i][0]
        assert row[1] == test_versions[i][1]

    conn.close()


def test_v1_to_v2_upgrade_e2e(tmp_path: pathlib.Path):
    test_versions = [
        ("//:test1", 1, "unknown"),
        ("//:test2", 2, "unknown"),
        ("//:test3", 3, "unknown"),
    ]
    version_index_path = tmp_path / VERSION_INDEX_NAME

    # Create an existing version index (format 1).
    create_v1_version_index(version_index_path, test_versions)

    # Migration should automatically run.
    vindex = VersionIndex.create_or_load(version_index_path)

    # The backup version index should still exist.
    assert (
        tmp_path / VERSION_INDEX_BACKUP_NAME_TEMPLATE.format(vfrom=1, vto=2)
    ).is_file()

    # Should be able to read all the versions from the upgraded index.
    all_versions = vindex.get_all_versions()
    assert len(test_versions) == len(all_versions)
    for expected, actual in zip(test_versions, all_versions):
        assert expected[0] == str(actual[0])
        assert expected[1] == actual[1].timestamp


def test_v2_to_v3_upgrade(tmp_path: pathlib.Path):
    test_versions = [
        ("//:test1", 1, "abc123", 0),
        ("//:test2", 2, "def456", 1),
        ("//:test3", 3, None, 0),
    ]
    version_index_path = tmp_path / VERSION_INDEX_NAME

    # Create an existing version index (format 2).
    create_v2_version_index(version_index_path, test_versions)

    # Run the upgrade.
    conn = sqlite3.connect(version_index_path)
    VersionIndex._run_v2_to_v3_migration(conn, version_index_path)

    # The backup version index should still exist.
    assert (
        tmp_path / VERSION_INDEX_BACKUP_NAME_TEMPLATE.format(vfrom=2, vto=3)
    ).is_file()

    # The version number should have changed to 3.
    conn.close()
    conn = sqlite3.connect(version_index_path)
    assert conn.execute(q.get_format_version).fetchone()[0] == 3

    # The existing versions should still be readable.
    for i, row in enumerate(conn.execute(q.all_entries)):
        assert row[0] == test_versions[i][0]
        assert row[1] == test_versions[i][1]
        assert row[2] == test_versions[i][2]
        assert row[3] == test_versions[i][3]

    # The new overrides table should exist and be writable.
    conn.execute(q.upsert_version_override, ("//:test1", 1234))
    row = conn.execute(q.get_version_override, ("//:test1",)).fetchone()
    assert row is not None
    assert row[0] == 1234
    conn.close()


def test_v2_to_v3_upgrade_e2e(tmp_path: pathlib.Path):
    test_versions = [
        ("//:test1", 100, None, 0),
        ("//:test1", 200, "def456", 1),
        ("//:test2", 300, "abc123", 0),
    ]
    version_index_path = tmp_path / VERSION_INDEX_NAME

    # Create an existing version index (format 2).
    create_v2_version_index(version_index_path, test_versions)

    # Migration should automatically run.
    vindex = VersionIndex.create_or_load(version_index_path)

    # The backup version index should still exist.
    assert (
        tmp_path / VERSION_INDEX_BACKUP_NAME_TEMPLATE.format(vfrom=2, vto=3)
    ).is_file()

    # Should be able to read all the versions from the upgraded index.
    all_versions = vindex.get_all_versions()
    assert len(test_versions) == len(all_versions)
    for expected, actual in zip(test_versions, all_versions):
        assert expected[0] == str(actual[0])
        assert expected[1] == actual[1].timestamp

    # Should be able to insert and read version overrides.
    task_id = TaskIdentifier.from_str("//:test1")
    assert vindex.get_version_override(task_id) is None
    vindex.set_version_override(task_id, 100)
    override = vindex.get_version_override(task_id)
    assert override is not None
    assert override.timestamp == 100
    assert override.commit_hash is None
    assert override.has_uncommitted_changes is False

    vindex.set_version_override(task_id, 200)
    override = vindex.get_version_override(task_id)
    assert override is not None
    assert override.timestamp == 200
    assert override.commit_hash == "def456"
    assert override.has_uncommitted_changes is True

    vindex.clear_version_override(task_id)
    assert vindex.get_version_override(task_id) is None


def test_get_version_override_raises_for_corrupt_reference(tmp_path: pathlib.Path):
    test_versions = [
        ("//:test1", 1, "abc123", 0),
    ]
    version_index_path = tmp_path / VERSION_INDEX_NAME

    create_v2_version_index(version_index_path, test_versions)
    vindex = VersionIndex.create_or_load(version_index_path)

    task_id = TaskIdentifier.from_str("//:test1")
    # Override points to a timestamp that has no corresponding version row.
    vindex.set_version_override(task_id, 999)
    with pytest.raises(CorruptedVersionIndex):
        vindex.get_version_override(task_id)


def create_v1_version_index(
    filepath: pathlib.Path, entries: Iterable[Tuple[str, int, str]]
):
    conn = sqlite3.connect(filepath)
    conn.execute(q.v1_create_table)
    conn.execute(q.set_format_version.format(version=1))
    conn.executemany(q.v1_insert_new_version, entries)
    conn.commit()


def create_v2_version_index(
    filepath: pathlib.Path, entries: Iterable[Tuple[str, int, Optional[str], int]]
):
    conn = sqlite3.connect(filepath)
    conn.execute(q.create_table)
    conn.execute(q.set_format_version.format(version=2))
    conn.executemany(q.insert_new_version, entries)
    conn.commit()
