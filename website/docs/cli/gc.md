---
title: Garbage Collect (GC)
id: gc
---

```bash
$ cond gc [-h] [-n] [-v]
```

Removes failed experiment task output directories. This subcommand will traverse
the `cond-out` directory and will delete all experiment task outputs that are
associated with a failed task. A task is treated as "failed" if its exit code is
not 0.

## Optional Arguments

### `-n` or `--dry-run`

If this flag is set, Conductor will not actually remove anything. Instead, it
will print the output directories that it would have removed.

### `-v` or `--verbose`

Print all the experiment output directories that are being removed.

### `-h` or `--help`

Prints a help message that provides details about how to use the `cond clean`
subcommand.

## Usage Examples

```bash
# Removes all failed experiment task output directories.
$ cond gc
```
