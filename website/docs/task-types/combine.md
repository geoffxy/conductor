---
title: combine()
id: combine
---

```python
combine(name, deps=[])
```

A `combine()` task copies the output files of its dependencies into a single
directory (the `combine()` task's output directory). The task's output directory
will contain one subdirectory for each of its dependencies, each containing the
dependency's output files.

A common use case for this task is to "combine" the outputs of multiple related
tasks. For example, if you use different scripts to generate a collection of
figures, you can use a `combine()` task to copy the generated figures into a
single directory.

## Arguments

### `name`

**Type:** String (required)

The task's name. This name must be unique within the task's `COND` file. A task
name can only contain letters, numbers, hyphens (`-`), and underscores (`_`).

### `deps`

**Type:** List of task identifiers (default: `[]`)

A list of task identifiers that this task should depend on. Conductor will
ensure that all dependencies execute successfully before launching this task.

:::info

The dependencies listed in a `combine()` task must have unique _names_. This is
because a `combine()` task creates a subdirectory for each dependency using the
dependency's name.

For example, the task identifiers `//foo:build` and `//bar:build` are distinct,
but they share the same name and thus cannot both be listed as a dependency in a
`combine()` task.

:::

When depending on tasks defined in the same `COND` file, you can just specify
the task's name prefixed by a colon (e.g., `:compile` would refer to a task
named `compile` defined in the same file). If you need to depend on a task
defined in a different `COND` file, you must specify the fully qualified task
identifier (e.g., `//experiments:benchmark` would refer to a task named
`benchmark` defined in the `COND` file in the `experiments` directory).

## Usage Example

```python title="COND"
combine(
  name="make_figures",
  deps=[
    ":make_figure1",
    ":make_figure2",
  ],
)
```

This task's output directory will contain two subdirectories: `make_figure1` and
`make_figure2`. The subdirectories will contain the outputs from the
`:make_figure1` and `:make_figure2` tasks respectively.
