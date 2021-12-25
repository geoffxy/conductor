import sqlite3
import pathlib
import shutil
import time
from typing import Iterable, List, Optional, Tuple

from conductor.config import VERSION_INDEX_BACKUP_NAME_TEMPLATE
from conductor.errors import UnsupportedVersionIndexFormat
from conductor.task_identifier import TaskIdentifier
import conductor.execution.version_index_queries as q


class Version:
    def __init__(self, ident: int):
        self._id = ident

    def __repr__(self) -> str:
        return "Version(id={})".format(self._id)

    def __str__(self) -> str:
        return str(self._id)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Version):
            return NotImplemented
        return self._id == other._id


class VersionIndex:
    """
    The `VersionIndex` is a persistent data structure that keeps track of all
    output versions of "archivable" task executions.
    """

    # pylint: disable=no-member

    FormatVersion = 2

    def __init__(self, conn: sqlite3.Connection, last_timestamp: int):
        self._conn = conn
        self._last_timestamp = last_timestamp

    @classmethod
    def create_or_load(cls, path: pathlib.Path) -> "VersionIndex":
        if path.exists():
            conn = sqlite3.connect(path)
            format_version = conn.execute(q.get_format_version).fetchone()[0]
            if format_version == 1:
                # Upgrade the version index to format 2.
                cls._run_v1_to_v2_migration(conn, path)
            elif format_version != cls.FormatVersion:
                raise UnsupportedVersionIndexFormat(version=format_version)

            # Need to restore the last timestamp used.
            result = conn.execute(q.get_max_timestamp).fetchone()
            return VersionIndex(
                conn=conn,
                last_timestamp=result[0]
                if result is not None and result[0] is not None
                else 0,
            )

        # Need to create the DB
        path.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(path)
        conn.execute(q.set_format_version.format(version=cls.FormatVersion))
        conn.execute(q.create_table)
        conn.commit()
        return VersionIndex(conn, 0)

    def get_latest_output_version(
        self, task_identifier: TaskIdentifier
    ) -> Optional[Version]:
        cursor = self._conn.cursor()
        cursor.execute(q.latest_task_timestamp, (str(task_identifier),))
        row = cursor.fetchone()
        if row is None:
            return None
        return Version(row[0])

    def generate_new_output_version(self, task_identifier: TaskIdentifier) -> Version:
        timestamp = int(time.time())
        if timestamp == self._last_timestamp:
            timestamp += 1
        elif timestamp < self._last_timestamp:
            timestamp = self._last_timestamp + 1
        self._last_timestamp = timestamp

        cursor = self._conn.cursor()
        cursor.execute(q.insert_new_version, (str(task_identifier), timestamp))
        return Version(timestamp)

    def get_all_versions(self) -> List[Tuple[TaskIdentifier, Version]]:
        cursor = self._conn.cursor()
        cursor.execute(q.all_versions)
        return [(TaskIdentifier.from_str(row[0]), Version(row[1])) for row in cursor]

    def copy_entries_to(
        self,
        dest: "VersionIndex",
        tasks: Optional[List[TaskIdentifier]],
        latest_only: bool,
    ) -> int:
        cursor = self._conn.cursor()
        if tasks is None:
            if latest_only:
                cursor.execute(q.all_entries_latest)
            else:
                cursor.execute(q.all_entries)
            return dest.bulk_load(cursor)

        insert_count = 0
        for task_id in tasks:
            if latest_only:
                cursor.execute(q.latest_entry_for_task, (str(task_id),))
            else:
                cursor.execute(q.all_entries_for_task, (str(task_id),))
            insert_count += dest.bulk_load(cursor)
        return insert_count

    def bulk_load(self, rows: Iterable) -> int:
        """
        Load the rows into the index and return the number loaded
        """
        cursor = self._conn.cursor()
        cursor.executemany(q.insert_new_version, rows)
        return cursor.rowcount

    def commit_changes(self):
        if not self._conn.in_transaction:
            return
        self._conn.commit()

    def rollback_changes(self):
        if not self._conn.in_transaction:
            return
        self._conn.rollback()

    @staticmethod
    def _run_v1_to_v2_migration(conn: sqlite3.Connection, path: pathlib.Path):
        # Upgrades the version index's persistent format from version 1 to 2.
        # For all existing entries, the `git_commit_hash` and
        # `commit_has_changes` columns are set to `NULL` and `0` respectively.
        backup_copy_path = path.with_name(
            VERSION_INDEX_BACKUP_NAME_TEMPLATE.format(vfrom=1, vto=2)
        )
        if not backup_copy_path.exists():
            # Back up the version index file first.
            shutil.copy2(src=path, dst=backup_copy_path)

        # Run the migration.
        try:
            conn.execute(q.v1_to_v2_create_tmp_table)
            conn.execute(q.v1_to_v2_migrate_tmp_table)
            conn.execute(q.v1_to_v2_drop_old_table)
            conn.execute(q.v1_to_v2_rename_new_table)
            conn.execute(q.set_format_version.format(version=2))
            conn.commit()
        except RuntimeError:
            conn.rollback()
