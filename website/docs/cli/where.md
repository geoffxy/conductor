---
title: Where
id: where
---

```bash
$ cond where [-h] [-p] [-f] task_identifier
```

This command prints the path to where the specified task's outputs are stored.

If the task is versioned (i.e., it is an experiment task), this command will
print the output path associated with the [most relevant
version](task-types/run-experiment.md#versioning-and-caching-semantics). If no
relevant version exists, this command will return an error.

Sometimes, no output path will exist. This could be because the task was never
executed, or because the task never produces outputs (e.g.,
[`group()`](task-types/group.md)). In these cases, this command will also return
an error.

## Optional Arguments

### `-p` or `--project`

If set, the printed output path will be relative to the project root. By
default, Conductor prints an absolute path.

### `-f` or `--non-existent-ok`

If set, Conductor will print the output path even if it does not exist yet.
Usually, if the output path does not exist, `cond where` will return an error.

This flag only has an effect for tasks that have deterministic output paths
(e.g., [`run_command()`](task-types/run-command.md) or
[`combine()`](task-types/combine.md)).

### `-h` or `--help`

Prints a help message that provides details about how to use the `cond where`
subcommand.

## Usage Examples

```bash
# Prints the output path for the `//figures:main` task.
$ cond where //figures:main

# Move to the output directory for the `//figures:main` task.
$ cd $(cond where //figures:main)
```
