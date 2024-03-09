---
title: run_experiment()
id: run-experiment
---

```python
run_experiment(name, run, parallelizable=False, args=[], options={}, deps=[])
```

A `run_experiment()` task runs the command specified in the `run` argument. The
task's output files are [versioned](#versioning-and-caching-semantics) and
[archivable](cli/archive.md).

All files that this task produces should be written to the path given in the
`COND_OUT` environment variable. This ensures that (i) your experiment results
can be versioned and archived correctly, and (ii) that other tasks that depend
on this task can find this task's produced files.

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

### `args`

**Type:** List of primitive types (default: `[]`)

A list of ordered arguments that should be passed to the command string
specified in `run`. The arguments will be passed to the command in the order
they are listed in `args`. The primitive types supported in `args` are strings,
Booleans, integers, and floating point numbers.

#### Example

```python
run_experiment(
  name="example",
  run="./run.sh",
  args=["arg1", "arg2", 123, True, 0.3],
)
```

Conductor will execute the task shown above by running `./run.sh arg1 arg2 123
true 0.3` in `bash`.

### `options`

**Type:** Dictionary mapping string keys to primitive values (default: `{}`)

A map of string keys to primitive values that should be passed to the command
string specified in `run`. Conductor treats these options as command line
"flags" and will pass them to the `run` command using `--key=value` syntax. Like
`args`, the primitive types supported in `options` are strings, Booleans,
integers, and floating point numbers. When `args` and `options` are both
non-empty, `args` are always passed first before `options`.

#### Example

```python
run_experiment(
  name="example",
  run="./run.sh",
  args=["arg1"],
  options={
    "foo": 3,
    "bar": True,
  },
)
```

Conductor will execute the task shown above by running `./run.sh arg1 --foo=3
--bar=true` in `bash`.

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

## Reserved File Names

Conductor records additional metadata about `run_experiment()` tasks in special
files under the path given by `$COND_OUT`. Your executable should not produce
files with the same names because they will be overwritten.

| File Name         | Description  |
| :---------------- | :----------- |
| `args.json`       | The arguments passed to the `run` command using `args`, serialized to JSON. |
| `options.json`    | The options passed to the `run` command using `options`, serialized to JSON. |
| `stderr.log`      | A log of the `run` command's output to standard error. |
| `stdout.log`      | A log of the `run` command's output to standard out. |

## Versioning and Caching Semantics

Conductor versions `run_experiment()` tasks' outputs. When running a
`run_experiment()` task, Conductor will check to see if a previous compatible
output version exists. If so, it will use the cached results of the "most
compatible" version instead of running the task again (unless otherwise
specified, see [`cond run`](cli/run.md)). This section describes the semantics
of output version "compatibility."

### Projects Using Git

Whenever a `run_experiment()` task executes, Conductor records the repository's
current commit hash and associates it with the outputs. Conductor then
determines a task output's compatibility based on the task output's commit hash
and the repository's current commit (i.e., the value of `HEAD`).

The most compatible version is the version whose commit is both (i) an ancestor
of the current commit (i.e., an ancestor of `HEAD`), and (ii) "closest" to the
current commit. Conductor defines closeness as the number of commits separating
the repository's current commit (`HEAD`) and the task version's commit. If there
are multiple closest task versions, Conductor selects the most recent one as
determined by execution timestamp. If there are no "compatible" outputs,
Conductor will execute the task.

### Projects Without Git

If your project is not managed using Git (or has Conductor's Git integration
explicitly disabled), Conductor will always select the most _recent_ version of
the task's outputs. Recency is determined by when the task was executed (i.e., a
timestamp). If there are no outputs available, Conductor will execute the task.

## Usage Example

```python title="COND"
run_experiment(
  name="benchmark",
  run="./run_benchmark.sh",
  parallelizable=False,
  args=["my_dataset.csv"],
  options={
    "threads": 3,
  },
  deps=[
    ":compile",
  ],
)
```
