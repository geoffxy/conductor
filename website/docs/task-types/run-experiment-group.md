---
title: run_experiment_group()
id: run-experiment-group
---

```python
run_experiment_group(name, run, experiments=[], chain_experiments=False, deps=[])
```

A `run_experiment_group()` task lets you specify a list of experiments that
share the same `run` command and dependencies. In other words, a
`run_experiment_group()` task is a concise way of defining a list of
[`run_experiment()`](task-types/run-experiment.md) tasks that all have the same
`run` command and `deps` but differ in their `args` and `options`. The
individual experiments are all versioned and archivable, just as if they were
`run_experiment()` tasks. After the experiments execute successfully, their
outputs are copied into a single output directory (using the same semantics as
[`combine()`](task-types/combine.md)).

The `run_experiment_group()` task type is actually just syntactic sugar.
Conductor implements this task type by transforming its experiments list into
`run_experiment()` tasks and a single `combine()` task (see the [usage
example](#usage-example)).

A common use case for this task type is running experiments where you need to
"sweep" over one or more parameters.

## Arguments

### `name`

**Type:** String (required)

The task's name. This name must be unique within the task's `COND` file. A task
name can only contain letters, numbers, hyphens (`-`), and underscores (`_`).

### `run`

**Type:** String (required)

The command to execute when running the experiments in this task. This command
will be executed using `bash`, with the location of the task's `COND` file as
the shell's working directory. In other words, any relative paths in the command
will be interpreted as relative to the directory containing the task's `COND`
file.

Conductor uses the exit code of the command to determine whether it succeeded or
failed. If the command succeeds, it should exit with an exit code of `0`.
Conductor interprets any non-zero exit code as a failure. If a task fails, it
prevents any other tasks that depend on it from executing (see the reference for
[`cond run`](cli/run.md)).

### `experiments`

**Type:** List of `ExperimentInstance`s (default: `[]`)

```python
ExperimentInstance(name, args=[], options={}, parallelizable=False)
```

The arguments that `ExperimentInstance()` takes have the same semantics as the
arguments listed in the [`run_experiment()` reference](task-types/run-experiment.md).

:::note

The `name` used for each `ExperimentInstance` must be unique in the `COND` file.
Each `ExperimentInstance` `name` must also be different from the `name` used for
the experiment's enclosing `run_experiment_group()`.

:::

### `chain_experiments`

**Type:** Boolean (optional)

If set to `True`, Conductor will add dependency constraints between the
experiment instances listed in `experiments`. Conductor adds the dependencies in
the order the experiment instances are defined, creating a "dependency chain."
See the usage example at the bottom of this page for an example of what this
argument does.

This argument is useful when you want to run different experiment _groups_
concurrently, but do not want the experiments within one group to run
concurrently.

### `deps`

**Type:** List of task identifiers (default: `[]`)

A list of task identifiers that all experiments in this task should depend on.
Conductor will ensure that all dependencies execute successfully before
launching this task.

When depending on tasks defined in the same `COND` file, you can just specify
the task's name prefixed by a colon (e.g., `:compile` would refer to a task
named `compile` defined in the same file). If you need to depend on a task
defined in a different `COND` file, you must specify the fully qualified task
identifier (e.g., `//experiments:benchmark` would refer to a task named
`benchmark` defined in the `COND` file in the `experiments` directory).

## Usage Example

In this example, we define a `run_experiment_group()` task that runs
`./run_benchmark.sh` with `--threads` set to 1 and 2. Since `COND` files are
interpreted as Python code, you can use Python's language features to help you
define your tasks.

```python title="COND"
run_experiment_group(
  name="sweep",
  run="./run_benchmark.sh",
  experiments=[
    ExperimentInstance(
      name="sweep-{}".format(threads),
      options={
        "threads": threads,
      },
      parallelizable=False,
    )
    # COND files are interpreted as Python code. So, you can use list
    # comprehension when defining your experiments.
    for threads in range(1, 3)
  ],
  chain_experiments=True,
  deps=[
    ":compile",
  ],
)
```

Internally, Conductor translates the above task definition into

```python
run_experiment(
  name="sweep-1",
  run="./run_benchmark.sh",
  options={
    "threads": 1,
  },
  parallelizable=False,
  deps=[
    ":compile",
  ],
)

run_experiment(
  name="sweep-2",
  run="./run_benchmark.sh",
  options={
    "threads": 2,
  },
  parallelizable=False,
  deps=[
    ":compile",
    ":sweep-1",
  ],
)

combine(
  name="sweep",
  deps=[
    ":sweep-1",
    ":sweep-2",
  ],
)
```
