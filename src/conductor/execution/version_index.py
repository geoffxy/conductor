import sqlite3
import pathlib
import shutil
import time
from typing import Any, Iterable, List, Optional, Tuple, Sequence

from conductor.config import VERSION_INDEX_BACKUP_NAME_TEMPLATE
from conductor.errors import UnsupportedVersionIndexFormat
from conductor.task_identifier import TaskIdentifier
from conductor.utils.git import Git
import conductor.execution.version_index_queries as q


class Version:
    def __init__(
        self, timestamp: int, commit_hash: Optional[str], has_uncommitted_changes: bool
    ):
        self._timestamp = timestamp
        self._commit_hash = commit_hash
        self._has_uncommitted_changes = has_uncommitted_changes

    @property
    def timestamp(self) -> int:
        return self._timestamp

    @property
    def commit_hash(self) -> Optional[str]:
        return self._commit_hash

    @property
    def has_uncommitted_changes(self) -> bool:
        return self._has_uncommitted_changes

    def __repr__(self) -> str:
        return (
            "Version(timestamp={}, commit_hash={}, has_uncommitted_changes={})".format(
                self._timestamp,
                str(self._commit_hash),
                str(self._has_uncommitted_changes),
            )
        )

    def __str__(self) -> str:
        # The timestamp uniquely identifies the version.
        return str(self._timestamp)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Version):
            return NotImplemented
        return (
            self.timestamp == other.timestamp
            and self.commit_hash == other.commit_hash
            and self.has_uncommitted_changes == other.has_uncommitted_changes
        )

    def __hash__(self) -> int:
        return hash((self._timestamp, self._commit_hash, self._has_uncommitted_changes))


class VersionIndex:
    """
    The `VersionIndex` is a persistent data structure that keeps track of all
    output versions of "archivable" task executions.
    """

    # v0.4.0 and older: FormatVersion = 1
    FormatVersion = 2

    def __init__(
        self,
        conn: sqlite3.Connection,
        last_timestamp: int,
        underlying_db_path: pathlib.Path,
    ):
        self._conn = conn
        self._last_timestamp = last_timestamp
        self._underlying_db_path = underlying_db_path

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
                last_timestamp=(
                    result[0] if result is not None and result[0] is not None else 0
                ),
                underlying_db_path=path,
            )

        # Need to create the DB
        path.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(path)
        conn.execute(q.set_format_version.format(version=cls.FormatVersion))
        conn.execute(q.create_table)
        conn.commit()
        return VersionIndex(conn, 0, path)

    def clone(self) -> "VersionIndex":
        """
        Clone this `VersionIndex` instance. This is helpful for creating a
        instance associated with the same thread (for the SQLite connection,
        needed in Conductor's explorer API).
        """
        conn = sqlite3.connect(self._underlying_db_path)
        return VersionIndex(
            conn=conn,
            last_timestamp=self._last_timestamp,
            underlying_db_path=self._underlying_db_path,
        )

    def get_latest_output_version(
        self, task_identifier: TaskIdentifier
    ) -> Optional[Version]:
        cursor = self._conn.cursor()
        cursor.execute(q.latest_task_version, (str(task_identifier),))
        row = cursor.fetchone()
        if row is None:
            return None
        return self._version_from_row(row)

    def get_all_versions_for_task(
        self, task_identifier: TaskIdentifier
    ) -> List[Version]:
        cursor = self._conn.cursor()
        cursor.execute(q.all_entries_for_task, (str(task_identifier),))
        results = []
        for row in cursor:
            results.append(self._version_from_row(row[1:]))
        return results

    def generate_new_output_version(self, commit: Optional[Git.Commit]) -> Version:
        timestamp = int(time.time())
        if timestamp == self._last_timestamp:
            timestamp += 1
        elif timestamp < self._last_timestamp:
            timestamp = self._last_timestamp + 1
        self._last_timestamp = timestamp

        commit_hash: Optional[str] = None
        if commit is not None:
            commit_hash = commit.hash

        return Version(
            timestamp, commit_hash, commit.has_changes if commit is not None else False
        )

    def insert_output_version(
        self, task_identifier: TaskIdentifier, version: Version, unchecked: bool = False
    ) -> int:
        """
        Insert a versioned task into the index and return the number of rows
        inserted. This will return 0 rows inserted if the task version is
        already in the index.
        """
        if unchecked:
            query = q.insert_new_version_unchecked
        else:
            query = q.insert_new_version
        cursor = self._conn.cursor()
        has_uncommitted_changes = 1 if version.has_uncommitted_changes else 0
        cursor.execute(
            query,
            (
                str(task_identifier),
                version.timestamp,
                version.commit_hash,
                has_uncommitted_changes,
            ),
        )
        return cursor.rowcount

    def get_all_versions(self) -> List[Tuple[TaskIdentifier, Version]]:
        cursor = self._conn.cursor()
        cursor.execute(q.all_versions)
        return [
            (TaskIdentifier.from_str(row[0]), self._version_from_row(row[1:]))
            for row in cursor
        ]

    def get_all_unversioned(self) -> List[TaskIdentifier]:
        try:
            cursor = self._conn.cursor()
            cursor.execute(q.get_unversioned_tasks)
            return [TaskIdentifier.from_str(row[0]) for row in cursor]
        except sqlite3.OperationalError:
            # The unversioned table does not exist, so there are no unversioned tasks.
            # We create the unversioned table only when we add unversioned tasks.
            return []

    def get_versioned_tasks(
        self, tasks: Optional[List[TaskIdentifier]], latest_only: bool
    ) -> List[Tuple[TaskIdentifier, Version]]:
        cursor = self._conn.cursor()
        if tasks is None:
            if latest_only:
                cursor.execute(q.all_entries_latest)
            else:
                cursor.execute(q.all_entries)
            return [
                (TaskIdentifier.from_str(row[0]), self._version_from_row(row[1:]))
                for row in cursor
            ]

        else:
            results = []
            for task_id in tasks:
                if latest_only:
                    cursor.execute(q.latest_entry_for_task, (str(task_id),))
                else:
                    cursor.execute(q.all_entries_for_task, (str(task_id),))
                for row in cursor:
                    results.append(
                        (
                            TaskIdentifier.from_str(row[0]),
                            self._version_from_row(row[1:]),
                        )
                    )
            return results

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

    @staticmethod
    def copy_specific_entries_to(
        dest: "VersionIndex", entries: List[Tuple[TaskIdentifier, Version]]
    ) -> int:
        values = []
        for task_id, version in entries:
            values.append(
                (
                    str(task_id),
                    version.timestamp,
                    version.commit_hash,
                    1 if version.has_uncommitted_changes else 0,
                )
            )
        return dest.bulk_load(values)

    def bulk_load(self, rows: Iterable) -> int:
        """
        Load the rows into the index and return the number loaded
        """
        cursor = self._conn.cursor()
        cursor.executemany(q.insert_new_version, rows)
        return cursor.rowcount

    def bulk_load_unversioned(self, task_ids: Iterable[TaskIdentifier]) -> int:
        """
        Load the unversioned task IDs into the index and return the number loaded.
        """
        cursor = self._conn.cursor()
        cursor.execute(q.create_unversioned_table)
        rows = [(str(task_id),) for task_id in task_ids]
        cursor.executemany(q.add_unversioned_task, rows)
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
        # `has_uncommitted_changes` columns are set to `NULL` and `0`
        # respectively.
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
            raise

    def _version_from_row(self, row: Sequence[Any]) -> Version:
        return Version(
            timestamp=row[0],
            commit_hash=row[1],
            has_uncommitted_changes=(False if row[2] == 0 else True),
        )
