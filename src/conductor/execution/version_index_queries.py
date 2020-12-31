# `id` increases monotonically, which acts as a logical clock in our use case.
create_table = """
  CREATE TABLE version_index (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    task_identifier TEXT NOT NULL,
    timestamp INTEGER NOT NULL,
    git_commit TEXT NOT NULL
  )
"""

set_format_version = "PRAGMA user_version = {version:d}"

create_index = """
  CREATE INDEX task_by_id ON version_index(task_identifier, id)
"""

insert_new_version = """
  INSERT INTO version_index (id, task_identifier, timestamp, git_commit)
    VALUES (NULL, ?, CURRENT_TIMESTAMP, ?)
"""

latest_id_for_task = """
  SELECT id FROM version_index
    WHERE task_identifier = ?
    ORDER BY id DESC
    LIMIT 1
"""
