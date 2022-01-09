---
title: Command Line Interface
id: cli
---

The primary way you interact with Conductor is through your terminal, using
Conductor's command line interface. After [installing Conductor](overview.md),
you will be able to access Conductor by running the `cond` program in your
shell.

Similar to other command line tools like Git, Conductor organizes its
functionality into subcommands. The pages in this section provide details about
each of Conductor's subcommands.

- [`cond run`](cli/run.md): Run a Conductor task
- [`cond archive`](cli/archive.md): Create archives of task outputs
- [`cond restore`](cli/restore.md): Restore results from an archive generated
  by `cond archive`
- [`cond clean`](cli/clean.md): Remove Conductor's output files

## `cond` Options

As described above, Conductor's functionality is meant to be accessed using
subcommands. However there are a few arguments you can pass to `cond` without a
subcommand. Running `cond` without any arguments is equivalent to running `cond
--help`.

#### Usage
```bash
$ cond [-h] [-v]
```

### `-v` or `--version`

Prints Conductor's version and exits. Conductor uses [semantic
versioning](https://semver.org).

### `-h` or `--help`

Prints a help message that provides details about how to use Conductor's command
line interface.
