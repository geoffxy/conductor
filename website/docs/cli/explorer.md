---
title: Explorer
id: explorer
---

```bash
$ cond explorer [-h] [--host HOST] [--port PORT]
```

This command launches Conductor's results explorer user interface. This tool is
used to interactively examine the experiment result versions managed by
Conductor.

## Optional Arguments

### `--port`

The port that Conductor's explorer tool should bind to. If unspecified, this
will be port 8000.

### `--host`

The host that Conductor's explorer tool will bind to. If unspecified, this will
be `localhost`. Generally, you will not need to modify this value.

### `--no-browser`

If set, Conductor will not automatically launch a web browser. By default, this
explorer command will start a web browser pointed at the explorer's web
interface.

### `-h` or `--help`

Prints a help message that provides details about how to use the `cond explorer`
subcommand.

## Usage Examples

```bash
# Launch the Conductor explorer tool.
$ cond explorer

# Launch the Conductor explorer tool on port 8080 (e.g., if port 8000 is in use).
$ cond explorer --port 8080
```
