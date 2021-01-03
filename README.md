# 🎶 Conductor

Conductor is a simple and elegant tool that helps with orchestrating your
research computing. Conductor helps with automating your research computing
pipeline, all the way from experiments to figures in your paper.

**Note:** Conductor is still under active development. Its usage and system
requirements are subject to change between versions. Conductor uses semantic
versioning. Before the 1.0.0 release, backward compatibility between minor
versions will not be guaranteed.

------------------------------------------------------------------------------

## Installation
Conductor requires Python 3.8+ and is currently only supported on macOS and
Linux machines. It has been tested on macOS 10.14 and Ubuntu 20.04.

Conductor is available on PyPI and so it can be installed using `pip`.
```bash
pip install conductor-cli
```

After installation, the `cond` executable should be available in your shell.
```bash
cond --help
```

## Getting Started
A quick way to get started is to look at the example projects under the
`examples` directory.

### Project Root
When using Conductor with your project, you first need to add a
`cond_config.toml` file to your project's root directory. This file tells
Conductor where your project files are located and is important because all
task identifiers (defined below) are relative to your project root.

### Tasks
Conductor works with the concept of "tasks", which are jobs (arbitrary shell
commands or scripts) that it should run. You define tasks in `COND` files
using Python syntax, using either `run_experiment()` or `run_command()` (see
the example projects).

Conductor's tasks are very similar to (and inspired by)
[Bazel's](https://bazel.build) and [Buck's](https://buck.build) build rules.

#### Task Identifiers
A task is identified using the path to the `COND` file where it is defined
(relative to your project's root directory), followed by its name. For
example, a task named `run_benchmark` defined in a `COND` file located at
`experiments/COND` would have the task identifier `//experiments:run_benchmark`.
To have Conductor run the task, you run `cond run
//experiments:run_benchmark` in your shell.

#### Dependencies
Tasks can have dependencies on other tasks. To specify a dependency, you use
the `deps` keyword argument when defining a task (see the example projects).
When running a task with dependencies, Conductor will ensure all its
dependencies are executed first before the task is executed. This allows you
to build a dependency graph of tasks, which can be used to automate your
entire research computing pipeline.

#### Task Outputs
Tasks usually (but not always) will need to produce output file(s) (e.g.,
measurements, figures). When Conductor runs a task, it will set the
`COND_OUT` environment variable to a path where the task should write its
outputs. See the example projects for an example of how this is used. All
task outputs will be stored under the `cond-out` directory.

Similarly, Conductor will also set the `COND_DEPS` environment variable to a
colon (`:`) separated list of paths to the task's dependencies' outputs. If
the task has no dependencies, the `COND_DEPS` environment variable will be
set to an empty string.

It's **important** to write task outputs to the path specified by `COND_OUT`.
This ensures other tasks can find the current task's outputs, and also allows
Conductor to archive your tasks' outputs (discussed below).

#### Task Types
Conductor currently includes three task types:
1. `run_experiment()`
2. `run_command()`
3. `group()`

**`run_experiment()` and `run_command()`**
```python
run_experiment(
    name="task_name",
    run="<shell command to run>",
    deps=[
        # Any dependencies should be listed here.
        # The `deps` keyword argument is optional; omitting it implies having
        # no dependencies.
    ],
)
# The `run_command()` task type has the same arguments as `run_experiment()`.
```
The `run_experiment()` and `run_command()` task types are both used to
specify jobs to run. The difference is that `run_experiment()` task outputs
are *cached* and *archivable* (discussed below). Conductor will cache any
outputs from a `run_experiment()` task and will by default not run the task
again (similar to build tools like `make`).

To run an experiment task again, use the `--again` command line flag with
`cond run`. By default, Conductor will only use the latest version of a
`run_experiment()` task output.

**`group()`**
```python
group(
    name="<group_name>",
    deps=[
        # Tasks part of this group should be listed here.
    ],
)
```
The `group()` task is a convenience task used to group multiple other tasks
together under one name.

### Archiving and Restoring
Conductor can archive "archivable" task outputs for safekeeping (e.g., for
backup purposes). Currently, only `run_experiment()` task outputs are
archivable. The idea is that `run_command()` task outputs should be
inexpensive to recompute, relative to `run_experiment()` task outputs.

To archive task outputs, run `cond archive`. By default Conductor will
archive all versions of all archivable task outputs. The resulting archive
will be placed under `cond-out`.

To archive a specific task, just specify the task identifier when running
`cond archive`. Conductor will archive all versions of the archivable task
outputs in the specified task's transitive dependency closure. You can
additionally specify the `--latest` flag to ask Conductor to only archive the
most *recent* version of each archivable task output.

To restore previously archived task outputs, run `cond restore` and specify
the path to the archive.


## Acknowledgements
Conductor's interface was largely inspired by [Bazel](https://bazel.build)
and [Buck](https://buck.build).
