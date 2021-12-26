create_table = """
  CREATE TABLE version_index (
    task_identifier TEXT NOT NULL,
    timestamp INTEGER NOT NULL,
    git_commit_hash TEXT,
    has_uncommitted_changes INTEGER NOT NULL,
    PRIMARY KEY (task_identifier, timestamp)
  )
"""

set_format_version = "PRAGMA user_version = {version:d}"

get_format_version = "PRAGMA user_version"

get_max_timestamp = "SELECT MAX(timestamp) FROM version_index"

insert_new_version = """
  INSERT INTO version_index (
    task_identifier,
    timestamp,
    git_commit_hash,
    has_uncommitted_changes
  )
  VALUES (?, ?, ?, ?)
"""

latest_task_version = """
  SELECT
    timestamp,
    git_commit_hash,
    has_uncommitted_changes
  FROM
    version_index
  WHERE task_identifier = ?
    ORDER BY timestamp DESC
    LIMIT 1
"""

all_entries = """
  SELECT
    task_identifier,
    timestamp,
    git_commit_hash,
    has_uncommitted_changes
  FROM
    version_index
"""

all_entries_latest = """
  WITH latest_entries AS (
    SELECT task_identifier, MAX(timestamp) AS timestamp
    FROM version_index GROUP BY task_identifier
  )
  SELECT
    c.task_identifier,
    c.timestamp,
    c.git_commit_hash,
    c.has_uncommitted_changes
  FROM
    version_index AS c
  INNER JOIN
    latest_entries AS l
  ON
    c.task_identifier = l.task_identifier
    AND c.timestamp = l.timestamp
"""

all_entries_for_task = """
  SELECT
    task_identifier,
    timestamp,
    git_commit_hash,
    has_uncommitted_changes
  FROM
    version_index
  WHERE
    task_identifier = ?
"""

latest_entry_for_task = """
  SELECT
    task_identifier,
    timestamp,
    git_commit_hash,
    has_uncommitted_changes
  FROM
    version_index
  WHERE
    task_identifier = ?
  ORDER BY timestamp DESC
  LIMIT 1
"""

all_versions = """
  SELECT
    task_identifier,
    timestamp,
    git_commit_hash,
    has_uncommitted_changes
  FROM
    version_index
"""


# Queries used in format 1 (retained for testing purposes)

v1_create_table = """
  CREATE TABLE version_index (
    task_identifier TEXT NOT NULL,
    timestamp INTEGER NOT NULL,
    git_commit TEXT NOT NULL,
    PRIMARY KEY (task_identifier, timestamp)
  )
"""

v1_insert_new_version = """
  INSERT INTO version_index (task_identifier, timestamp, git_commit)
    VALUES (?, ?, ?)
"""


# Queries used for migrating from format 1 to format 2
# - Remove the "NOT NULL" constraint from `version_index.git_commit`
# - Add a `has_uncommitted_changes BOOL` column to `version_index`

v1_to_v2_create_tmp_table = create_table.replace("version_index", "version_index_new")

v1_to_v2_migrate_tmp_table = """
  INSERT INTO version_index_new
    SELECT task_identifier, timestamp, NULL, 0 FROM version_index
"""

v1_to_v2_drop_old_table = "DROP TABLE version_index"

v1_to_v2_rename_new_table = "ALTER TABLE version_index_new RENAME TO version_index"
