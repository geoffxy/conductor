---
title: Run
id: run
---

```bash
$ cond run [-h] [-a] [-e] [-j [JOBS]] task_identifier
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

### `-h` or `--help`

Prints a help message that provides details about how to use the `cond run`
subcommand.

## Usage Examples

```bash
# Run //experiments:benchmark.
$ cond run --again //experiments:benchmark

# Run //experiments:benchmark, regardless if it has cached results available.
$ cond run --again //experiments:benchmark

# Run //experiments:benchmark, stopping as soon as any dependent task fails.
$ cond run --stop-early //experiments:benchmark

# Run //experiments:benchmark, allowing at most 3 tasks to run in parallel at
# any time.
$ cond run -j 3 //experiments:benchmark
```
