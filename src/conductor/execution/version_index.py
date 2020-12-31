import sqlite3
import pathlib
from typing import Optional

from conductor.task_identifier import TaskIdentifier
import conductor.execution.version_index_queries as q


class Version:
    def __init__(self, id: int):
        self._id = id

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

    FormatVersion = 1

    def __init__(self, conn: sqlite3.Connection):
        self._conn = conn

    @classmethod
    def create_or_load(cls, path: pathlib.Path) -> "VersionIndex":
        if path.exists():
            return VersionIndex(sqlite3.connect(path))

        # Need to create the DB
        path.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(path)
        conn.execute(q.set_format_version.format(version=cls.FormatVersion))
        conn.execute(q.create_table)
        conn.execute(q.create_index)
        conn.commit()
        return VersionIndex(conn)

    def get_latest_output_version(
        self, task_identifier: TaskIdentifier
    ) -> Optional[Version]:
        cursor = self._conn.cursor()
        cursor.execute(q.latest_id_for_task, (str(task_identifier),))
        row = cursor.fetchone()
        if row is None:
            return None
        return Version(row[0])

    def generate_new_output_version(self, task_identifier: TaskIdentifier) -> Version:
        cursor = self._conn.cursor()
        cursor.execute(q.insert_new_version, (str(task_identifier), "unknown"))
        return Version(cursor.lastrowid)

    def commit_changes(self):
        if not self._conn.in_transaction:
            return
        self._conn.commit()

    def rollback_changes(self):
        if not self._conn.in_transaction:
            return
        self._conn.rollback()
