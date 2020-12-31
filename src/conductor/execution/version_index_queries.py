# `id` increases monotonically, which acts as a logical clock in our use case.
create_table = """
  CREATE TABLE version_index (
    task_identifier TEXT NOT NULL,
    timestamp INTEGER NOT NULL,
    git_commit TEXT NOT NULL,
    PRIMARY KEY (task_identifier, timestamp)
  )
"""

set_format_version = "PRAGMA user_version = {version:d}"

insert_new_version = """
  INSERT INTO version_index (task_identifier, timestamp, git_commit)
    VALUES (?, ?, ?)
"""

latest_task_timestamp = """
  SELECT timestamp FROM version_index
    WHERE task_identifier = ?
    ORDER BY timestamp DESC
    LIMIT 1
"""
