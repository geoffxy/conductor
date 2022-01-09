---
title: Clean
id: clean
---

```bash
$ cond clean [-h] [-f]
```

Removes Conductor's generated files, including task outputs. In practice, this
subcommand deletes the `cond-out` directory. Be careful when using this
subcommand because it cannot be undone.

## Optional Arguments

### `-f` or `--force`

If set, Conductor will not prompt for confirmation before performing the clean
operation.

:::caution

Be careful when using this flag! The clean operation cannot be undone.

:::

### `-h` or `--help`

Prints a help message that provides details about how to use the `cond clean`
subcommand.

## Usage Examples

```bash
# Removes the `cond-out` directory.
$ cond clean
```
