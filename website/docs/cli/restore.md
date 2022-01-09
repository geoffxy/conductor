---
title: Restore
id: restore
---

```bash
$ cond restore [-h] archive_file
```

Restore the task outputs from an archive file that was generated using `cond
archive`. See the reference documentation for [`cond archive`](cli/archive.md)
for more details about Conductor's archive and restore features.

## Positional Arguments

### `archive_file`

**Type:** String (required)

The path to the archive file to restore.

## Optional Arguments

### `-h` or `--help`

Prints a help message that provides details about how to use the `cond restore`
subcommand.

## Usage Examples

```bash
# Restores from my_archive.tar.gz
$ cond restore my_archive.tar.gz
```
