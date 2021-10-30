import sqlite3
import pathlib
import time
from typing import Iterable, List, Optional, Tuple

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

    FormatVersion = 1

    def __init__(self, conn: sqlite3.Connection, last_timestamp: int):
        self._conn = conn
        self._last_timestamp = last_timestamp

    @classmethod
    def create_or_load(cls, path: pathlib.Path) -> "VersionIndex":
        if path.exists():
            # Need to restore the last timestamp used
            conn = sqlite3.connect(path)
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
        cursor.execute(
            q.insert_new_version, (str(task_identifier), timestamp, "unknown")
        )
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
