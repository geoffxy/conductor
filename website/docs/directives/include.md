---
title: include()
id: include
---

```python
include(path)
```

The `include()` directive allows you to "include" a separate file in a `COND`
file. The primary use case for `include()` is when you want to share common
configuration values among multiple `COND` files (for use across multiple task
definitions). You can define the configuration values in a single file, and then
`include()` that file in every relevant `COND` file.

When encountering an `include()` directive, Conductor will interpret the
included file as a Python program. Any symbols (e.g., variables, functions)
defined in the included file will be usable inside the `COND` file. A `COND`
file can `include()` as many other files as needed. Note that `include()`
directives are processed in the order they are written in the `COND` file (i.e.,
from top to bottom).

Included files are meant to be used to share configuration values. As a result,
included files cannot `include()` other files (i.e., nested `include()`s are not
supported). An included file also cannot define any tasks. Included files must
also be *deterministic* (i.e., they must always produce the same results each
time they are evaluated). These restrictions are meant to keep `include()`
directives simple to reason about.


## Arguments

### `path`

**Type:** String (required)

The path to the file to include, which will be interpreted as a Python program.
To distinguish Conductor includes from regular Python programs, all included
files must have a `.cond` extension.

Paths can be specified either (i) relative to the `COND` file's location, or
(ii) relative to the project root. To specify a path relative to the project
root, use `//` to indicate the project root (see the usage example below).


## Usage Example

In the example below, we define two `run_experiment()` tasks in separate `COND`
files. However, both tasks share configuration values that are defined in
`common.cond`.

```python title=experiments/common.cond
# Common configuration values.
REPETITIONS = 3
THREADS = 2 * 8
```

```python title=experiments/baseline/COND
# Include `common.cond` using a relative path.
include("../common.cond")

run_experiment(
  name="baseline",
  run="./evaluate_baseline.sh",
  options={
    "repetitions": REPETITIONS,
    "threads": THREADS,
  },
)
```

```python title=experiments/new_system/COND
# Include `common.cond` using a path relative to the project root.
include("//experiments/common.cond")

run_experiment(
  name="new_system",
  run="./evaluate_new_system.sh",
  options={
    "repetitions": REPETITIONS,
    "threads": THREADS,
  },
)
```
