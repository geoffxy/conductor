---
title: Overview
slug: /
---

Conductor is a simple and elegant tool that helps orchestrate your research
computing. Conductor automates your research computing pipeline, all the way
from experiments to figures in your paper.

## Installing
Conductor requires Python 3.8+ and is currently only supported on macOS and
Linux machines. It has been tested on macOS 10.14 and Ubuntu 20.04.

Conductor is [available on PyPI](https://pypi.org/project/conductor-cli/) and so
it can be installed using `pip`.
```bash
pip install conductor-cli
```

After installation, the `cond` executable should be available in your shell.
```bash
cond --help
```

## Getting Started
A quick way to get started is to look at Conductor's [example
projects](https://github.com/geoffxy/conductor/tree/master/examples). Below is a
quick overview of a few important Conductor concepts.

### Project Root
When using Conductor with your project, you first need to add a
`cond_config.toml` file to your project's root directory. This file tells
Conductor where your project files are located and is important because all
task identifiers (defined below) are relative to your project root.

### Tasks
Conductor works with "tasks", which are jobs (arbitrary shell commands or
scripts) that it should run. You define tasks in `COND` files using Python
syntax. All tasks are of a predefined "type" (e.g., `run_experiment()`), which
are listed in the [task types reference documentation](task-types).

Conductor's tasks are very similar to (and inspired by)
[Bazel's](https://bazel.build) and [Buck's](https://buck.build) build rules.

#### Task Identifiers
A task is identified using the path to the `COND` file where it is defined
(relative to your project's root directory), followed by its name. For example,
a task named `run_benchmark` defined in a `COND` file located in
`experiments/COND` would have the task identifier `//experiments:run_benchmark`.
To have Conductor run the task, you run `cond run
//experiments:run_benchmark` in your shell.

#### Dependencies
Tasks can be dependent on other tasks. To specify a dependency, you use the
`deps` keyword argument when defining a task.  When running a task that has
dependencies, Conductor will ensure that all of its dependencies are executed
first before the task is executed. This allows you to build a dependency graph
of tasks, which can be used to automate your entire research computing pipeline.

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

It's *important* to write task outputs to the path specified by `COND_OUT`.
This ensures other tasks can find the current task's outputs, and also allows
Conductor to archive your tasks' outputs.
