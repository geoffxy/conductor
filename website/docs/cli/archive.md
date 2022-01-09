---
title: Archive
id: archive
---

```bash
cond archive [-h] [-o OUTPUT] [-l] [task_identifier]
```

Conductor's archive functionality provides a convenient way to back up the task
outputs of "archivable" tasks
([`run_experiment()`](task-types/run-experiment.md) and
[`run_experiment_group()`](task-types/run-experiment-group.md)). Conductor
packages task outputs into a single `.tar.gz` file, which can then be backed up
or transferred. The `cond archive` command helps you create these archive files.
Conductor also provides a way to restore the task outputs in an archive through
[`cond restore`](cli/restore.md).

## Positional Arguments

### `task_identifier`

**Type:** String (optional)

The task identifier of the task you want to archive. By design, Conductor only
archives experiment-based tasks (`run_experiment()` and
`run_experiment_group()`). Thus, during the archive process, Conductor will only
archive the experiment-based tasks in the transitive closure of
`task_identifier` (i.e., only its dependencies which are experiments). The idea
is that you should be able to regenerate all other task outputs as long as you
have the original experiment results.

The `task_identifier` argument is optional. If you do not specify a task,
Conductor will archive _all_ archivable task outputs.

## Optional Arguments

### `-o` or `--output`

**Usage:** `-o OUTPUT` or `--output OUTPUT`

The path (and optionally file name) where the output archive should be saved.
The path must exist. This argument is optional. If unspecified, Conductor will
save the archive in its output directory (`cond-out`).

### `-l` or `--latest`

If set, Conductor will only archive the latest (most recent) output version of
the requested tasks. By default, Conductor will archive all output versions of
the archivable tasks.

### `-h` or `--help`

Prints a help message that provides details about how to use the `cond archive`
subcommand.

## Usage Examples

```bash
# Create an archive of all existing archivable task outputs.
$ cond archive

# Archive all experiment task outputs of //experiments:run_benchmark and its
# dependencies.
$ cond archive //experiments:run_benchmark

# Create an archive of only the latest versions of each archivable task output.
$ cond archive --latest

# Create an archive of all existing archivable task outputs and save it as
# "my_archive.tar.gz".
$ cond archive --output my_archive.tar.gz
```
