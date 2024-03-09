---
title: Run
id: run
---

```bash
$ cond run [-h] [-a] [-c COMMIT] [--this-commit] [-e] [-j [JOBS]] task_identifier
```

Runs the task identified by `task_identifier`, along with its dependencies.
Conductor will ensure that all dependencies (and their dependencies, and so on)
complete successfully before launching the task itself.

If any tasks in `task_identifier`'s transitive closure fail, Conductor will
still attempt to run as many of the remaining tasks as possible. Any tasks that
cannot run because one of their dependencies failed is skipped. Conductor will
report which tasks failed and which were skipped.

## Positional Arguments

### `task_identifier`

**Type:** String (required)

The task identifier of the task that you want to run.

## Optional Arguments

### `-a` or `--again`

By default, Conductor will use cached results for certain tasks if they exist
(see the reference for [`run_experiment()`](task-types/run-experiment.md)).
Setting this flag will make Conductor run all the relevant tasks again,
regardless of the cache.

### `-c` or `--at-least`

Setting this flag will make Conductor run all the relevant tasks that _do not_
have a cached version that is at least as new as the specified commit (see the
reference for [`run_experiment()`](task-types/run-experiment.md) for details on
Conductor's caching semantics). You can specify a commit using a hash, branch,
or tag. The specified commit must be an ancestor of the current commit.

This flag cannot be used with `--again` (the two flags are not compatible). This
flag also cannot be used if (i) Conductor's Git integration [is disabled](/docs/configuration.md),
(ii) your project is not managed by Git, or (iii) if your repository is bare
(there are no commits).

How does this flag differ from `--again`? When you set `--again`, Conductor will
always re-run all the relevant tasks, regardless of the cache. With
`--this-commit`, Conductor will only re-run relevant tasks that do not have a
cached version that matches your repository's current commit (i.e., the value of
`HEAD`). This is useful when you need to restart dependent tasks that failed or
were aborted.

### `--this-commit`

Setting this flag is equivalent to setting `--at-least=HEAD`. This flag cannot
be used with `--again`. If you set `--this-commit`, you also cannot set
`--at-least`.

### `-e` or `--stop-early`

If set, Conductor will immediately stop executing a task if any dependent task
fails. By default, if a dependent task fails, Conductor will still try to
execute the rest of the task's dependencies that do not depend on the failed
task.

### `-j` or `--jobs`

**Usage:** `-j [JOBS]` or `--jobs [JOBS]`

The maximum number of tasks that Conductor can run in parallel. If this flag is
_not_ used, Conductor will always execute tasks sequentially. When this flag
_is_ used, Conductor may execute up to `JOBS` tasks in parallel. Conductor will
only execute `parallelizable` tasks in parallel (see the reference for
[`run_experiment()`](task-types/run-experiment.md)).

If this flag is used without specifying a value, Conductor will set `JOBS` to be
the number of virtual CPUs detected in the machine. This flag behaves
analogously to the `-j` flag in `make`.

### `--check`

When set, Conductor will parse and validate all tasks that would be executed but
it will not actually execute the tasks. This flag is useful for checking that
tasks are defined correctly in `COND` files.

### `-h` or `--help`

Prints a help message that provides details about how to use the `cond run`
subcommand.

## Usage Examples

```bash
# Run //experiments:benchmark.
$ cond run //experiments:benchmark

# Run //experiments:benchmark, regardless if it has cached results available.
$ cond run --again //experiments:benchmark

# Run //experiments:benchmark if there are no cached results at least as new as commit abc123.
$ cond run --at-least=abc123 //experiments:benchmark

# Run //experiments:benchmark if there are no cached results for the current commit.
$ cond run --this-commit //experiments:benchmark

# Run //experiments:benchmark, stopping as soon as any dependent task fails.
$ cond run --stop-early //experiments:benchmark

# Run //experiments:benchmark, allowing at most 3 tasks to run in parallel at
# any time.
$ cond run -j 3 //experiments:benchmark
```
