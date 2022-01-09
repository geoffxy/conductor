---
title: group()
id: group
---

```python
group(name, deps=[])
```

The purpose of a `group()` task is to "assign" a task identifier to a _group_ of
other tasks. A `group()` task allows you to tell Conductor to run multiple tasks
while only referring to a single task identifier.

One use case for a `group()` task is when you have a list of tasks that are
usually run together (e.g., a series of tasks that comprise a benchmark suite).
In this scenario, you can use a `group()` task to make it more convenient to run
all of the tasks in the suite.

The difference between `group()` and [`combine()`](task-types/combine.md) is
that `combine()` takes the additional step of copying its dependencies' outputs
into a single output directory (a `group()` task does not do this step).

## Arguments

### `name`

**Type:** String (required)

The task's name. This name must be unique within the task's `COND` file. A task
name can only contain letters, numbers, hyphens (`-`), and underscores (`_`).

### `deps`

**Type:** List of task identifiers (default: `[]`)

A list of task identifiers that should be executed when this task is requested
to be executed (i.e., the tasks that should be part of this "group").

When listing tasks defined in the same `COND` file, you can just specify the
task's name prefixed by a colon (e.g., `:compile` would refer to a task named
`compile` defined in the same file). If you need to list a task defined in a
different `COND` file, you must specify the fully qualified task identifier
(e.g., `//experiments:benchmark` would refer to a task named `benchmark` defined
in the `COND` file in the `experiments` directory).

## Usage Example

```python title="COND"
group(
  name="run_all_benchmarks",
  deps=[
    ":benchmark_a",
    ":benchmark_b",
  ],
)
```
