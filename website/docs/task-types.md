---
title: Task Types
id: task-types
---

The subpages in this section describe Conductor's task types in detail. This
page outlines the common concepts among all task types.

## Kinds of Task Types

At a high level, Conductor has two kinds of task types: experiment task types,
and non-experiment task types.

### Experiment Task Types

Experiment task types ([`run_experiment()`](task-types/run-experiment) and
[`run_experiment_group()`](task-types/run-experiment-group)) are used to launch
scripts or executables that produce results for your research. For example, a
benchmark script that you run to collect performance results for your project
should be encoded as a `run_experiment()` task.

**Special handling.**
Conductor distinguishes between experiment task types and non-experiment task
types because it does a few extra things for experiment tasks that are typically
not needed for non-experiment tasks. For experiment tasks, Conductor will
automatically

- Record the arguments and options passed to the task's executable
- Record the task executable's standard out and standard error streams

**Versioning.**
The outputs of an experiment task (e.g., the collected performance results) are
also versioned and [archivable](cli/archive). The reference page for
[`run_experiment()`](task-types/run-experiment) provides more details about what
this means.

### Non-Experiment Task Types

All other Conductor task types are non-experiment task types. The semantics of
each non-experiment task type are described in each task type's reference page.

Non-experiment task types are typically used to orchestrate the environment
setup and data transformation steps of your research computing pipeline. For
example, a script that takes raw experiment results and generates a graph should
be encoded as a [`run_command()`](task-types/run-command) task.

## Task Environment Variables

When running a task, Conductor will set a number of environment variables. These
environment variables are used to provide information to the task executable.

### `COND_OUT`

The `COND_OUT` environment variable is set to an absolute path where the task
executable should write its output file(s). This variable is always set (i.e.,
it is set for all tasks).

:::caution

When orchestrating your computing pipeline with Conductor, it is _very
important_ to make sure your executables write their outputs to the path given
by `COND_OUT`. Doing so ensures that any dependent tasks will be able to find
their dependencies' outputs. For experiment tasks, writing your outputs to
`COND_OUT` ensures that your experiment results can be versioned and archived
correctly.

:::

### `COND_DEPS`

The `COND_DEPS` environment variable is set to a string of colon (`:`) separated
absolute paths to the task's dependencies' outputs. If the task has no
dependencies, this variable will be set to an empty string.

The purpose of this environment variable is to enable a task to find the output
files of its dependencies. For example, suppose `task-1` lists `task-a` and
`task-b` as its dependencies. Suppose that `task-a`'s output path is `/task-a`
and `task-b`'s output path is `/task-b`. Then when `task-1` runs, `COND_DEPS`
will be set to `/task-a:/task-b`.

### `COND_NAME`

The `COND_NAME` environment variable is set to the task's name. This variable is
always set.

### `COND_SLOT`

The `COND_SLOT` environment variable is set when the task _may_ be executing in
parallel. When set, `COND_SLOT` will have a non-negative integer value that is
less than the maximum number of parallel tasks allowed (set using the `--jobs`
flag, see the reference for [`cond run`](cli/run)). For example, if `--jobs` was
set to 3, `COND_SLOT` will only be either 0, 1, or 2.

`COND_SLOT` will only be set if the task is parallelizable (specified by setting
the `parallelizable` argument when defining the task, see
[`run_experiment()`](task-type/run-experiment)). Conductor guarantees that all
tasks running in parallel will have distinct values of `COND_SLOT`.

One use case for `COND_SLOT` is to ensure tasks executing in parallel are
scheduled on different CPU cores. For example, a task executable may request to
be pinned on a specific core based on the value of `COND_SLOT`.
