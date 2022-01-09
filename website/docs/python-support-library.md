---
title: Python Support Library
id: python-support-library
---

Conductor includes a Python library that provides utilities for tasks that are
implemented as Python scripts. For example, you might use a Python script to
process experiment results, transform data, or create figures. As long as you
have installed Conductor, you can access the Python library by importing
`conductor.lib`.

```python
import conductor.lib as cond
```

:::note

The functions in this library are meant to be called in scripts that are
launched by Conductor. If used in scripts that are _not_ launched by Conductor,
these library functions will raise `RuntimeError` exceptions.

:::

## Path Utilities

### `get_deps_paths()`

```python
def get_deps_paths() -> List[pathlib.Path]
```

Returns a list of this task's dependencies' output paths. If the task has no
dependencies, the returned list will be empty.

### `get_output_path()`

```python
def get_output_path() -> pathlib.Path
```

Returns the path where this task should write its output files.

## Usage Example

The following code snippets provide an example of how you can use Conductor's
Python library to retrieve the location of dependent tasks' outputs as well as
the task's output path.

```python title="COND"
run_experiment(
  name="benchmark_1",
  run="./run_benchmark_1.sh",
)

run_experiment(
  name="benchmark_2",
  run="./run_benchmark_2.sh",
)

run_command(
  name="combine",
  run="python combine_results.py",
  deps=[
    ":benchmark_1",
    ":benchmark_2",
  ],
)
```

```python title="combine_results.py" {10,16}
import conductor.lib as cond
import pandas as pd


def main():
    """
    Combines the CSV files written by this task's dependencies.
    """
    results = []
    deps = cond.get_deps_paths()

    for dep_path in deps:
        results.append(pd.read_csv(dep_path / "measurements.csv"))
    combined = pd.concat(results, ignore_index=True)

    out_dir = cond.get_output_path()
    combined.to_csv(out_dir / "combined.csv", index=False)


if __name__ == "__main__":
    main()
```
