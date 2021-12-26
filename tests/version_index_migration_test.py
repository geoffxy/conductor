import pathlib
import sqlite3
from typing import Iterable
import conductor.execution.version_index_queries as q
from conductor.config import VERSION_INDEX_BACKUP_NAME_TEMPLATE, VERSION_INDEX_NAME
from conductor.execution.version_index import VersionIndex

# pylint: disable=no-member
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


def create_v1_version_index(filepath: pathlib.Path, entries: Iterable[Iterable]):
    conn = sqlite3.connect(filepath)
    conn.execute(q.v1_create_table)
    conn.execute(q.set_format_version.format(version=1))
    conn.executemany(q.v1_insert_new_version, entries)
    conn.commit()
