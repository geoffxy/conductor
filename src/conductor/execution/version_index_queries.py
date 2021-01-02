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

get_max_timestamp = "SELECT MAX(timestamp) FROM version_index"

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

all_entries = "SELECT task_identifier, timestamp, git_commit FROM version_index"

all_entries_latest = """
  WITH latest_entries AS (
    SELECT task_identifier, MAX(timestamp) AS timestamp
    FROM version_index GROUP BY task_identifier
  )
  SELECT c.task_identifier, c.timestamp, c.git_commit
    FROM version_index AS c INNER JOIN latest_entries AS l
    ON c.task_identifier = l.task_identifier AND c.timestamp = l.timestamp
"""

all_entries_for_task = """
  SELECT task_identifier, timestamp, git_commit FROM version_index
    WHERE task_identifier = ?
"""

latest_entry_for_task = """
  SELECT task_identifier, timestamp, git_commit FROM version_index
    WHERE task_identifier = ?
    ORDER BY timestamp DESC
    LIMIT 1
"""

all_versions = "SELECT task_identifier, timestamp FROM version_index"
