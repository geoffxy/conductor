# The name of the file where tasks are defined.
COND_FILE_NAME = "COND"

# The name of the Conductor configuration file (it marks the project root).
CONFIG_FILE_NAME = "cond_config.toml"

# The output directory name. All Conductor outputs are stored in this
# directory.
OUTPUT_DIR = "cond-out"

# The suffix to use when creating an output directory for a task. We append
# this suffix to the task's name to ensure uniqueness.
TASK_OUTPUT_DIR_SUFFIX = ".task"

# The file name of the on-disk version index.
VERSION_INDEX_NAME = "version_index.sqlite"

# A template for the version index backup when performing a version migration.
VERSION_INDEX_BACKUP_NAME_TEMPLATE = "version_index_backup-v{vfrom}-v{vto}.sqlite"

# The environment variable that stores the absolute path to the task's output
# directory. Tasks are supposed to use this variable to determine where to
# write their output files.
OUTPUT_ENV_VARIABLE_NAME = "COND_OUT"

# The environment variable that stores the path(s) to the outputs of the task's
# dependencies. There may be multiple paths, in which case they are separated
# by `DEPS_ENV_PATH_SEPARATOR`. Tasks can use this variable to find any files
# that were generated by its direct dependencies.
DEPS_ENV_VARIABLE_NAME = "COND_DEPS"

# The separator used to separate multiple paths in the `DEPS_ENV_VARIABLE_NAME`
# environment variable.
DEPS_ENV_PATH_SEPARATOR = ":"

# The environment variable that stores the name of the task being executed.
TASK_NAME_ENV_VARIABLE_NAME = "COND_NAME"

# The environment variable that stores the "slot" number of the task being
# executed. This variable is only set when the task may be running in parallel
# with other tasks.
SLOT_ENV_VARIABLE_NAME = "COND_SLOT"

# A template for the default name of a Conductor archive.
ARCHIVE_FILE_NAME_TEMPLATE = "cond-archive+{timestamp}.tar.gz"

# The file name of the version index used in a Conductor archive.
ARCHIVE_VERSION_INDEX = "version_index_archive.sqlite"

# The name of the staging directory where archived files are temporarily extracted.
ARCHIVE_STAGING = "archive-tmp"

# The names of the files that store copies of a task's standard output and error.
STDOUT_LOG_FILE = "stdout.log"
STDERR_LOG_FILE = "stderr.log"

# The format of an experiment option when used as a command line option.
EXP_OPTION_CMD_FORMAT = "--{key}={value}"

# The name of the experiment options serialized JSON file.
EXP_OPTION_JSON_FILE_NAME = "options.json"

# The name of the experiment arguments serialized JSON file.
EXP_ARGS_JSON_FILE_NAME = "args.json"
