---
title: run_command()
id: run-command
---

```python
run_command(name, run, parallelizable=False, deps=[])
```

A `run_command()` task runs the command specified in the `run` argument. The
difference between this task type and
[`run_experiment()`](task-types/run-experiment.md) is that the outputs from this
task are not versioned (nor are they archivable). A `run_command()` task is
usually well-suited for orchestrating the environment setup and data
transformation steps of your research computing pipeline (e.g., compiling
executables or generating figures from benchmark results).

All files that this task produces should be written to the path given in the
`COND_OUT` environment variable. This ensures that other tasks that depend on
this task can find this task's produced files.

## Arguments

### `name`

**Type:** String (required)

The task's name. This name must be unique within the task's `COND` file. A task
name can only contain letters, numbers, hyphens (`-`), and underscores (`_`).

### `run`

**Type:** String (required)

The command to execute when running this task. This command will be executed
using `bash`, with the location of the task's `COND` file as the shell's working
directory. In other words, any relative paths in the command will be interpreted
as relative to the directory containing the task's `COND` file.

Conductor uses the exit code of the command to determine whether it succeeded or
failed. If the command succeeds, it should exit with an exit code of `0`.
Conductor interprets any non-zero exit code as a failure. If a task fails, it
prevents any other tasks that depend on it from executing (see the reference for
[`cond run`](cli/run.md)).

### `parallelizable`

**Type:** Boolean (default: `False`)

If set to `True`, Conductor may launch this task while other `parallelizable`
tasks are running. You should set this argument to `True` if it is okay for this
task to execute while other tasks are also running.

By default, tasks are not `parallelizable`, and so Conductor will not launch a
new task until the previously launched task has completed (or failed).

### `deps`

**Type:** List of task identifiers (default: `[]`)

A list of task identifiers that this task should depend on. Conductor will
ensure that all dependencies execute successfully before launching this task.

When depending on tasks defined in the same `COND` file, you can just specify
the task's name prefixed by a colon (e.g., `:compile` would refer to a task
named `compile` defined in the same file). If you need to depend on a task
defined in a different `COND` file, you must specify the fully qualified task
identifier (e.g., `//experiments:benchmark` would refer to a task named
`benchmark` defined in the `COND` file in the `experiments` directory).

## Usage Example

```python title="COND"
run_command(
  name="figures",
  run="python make_figures.py",
  parallelizable=True,
  deps=[
    ":benchmark",
  ],
)
```
