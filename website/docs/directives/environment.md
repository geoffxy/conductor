---
title: environment()
id: environment
---

```python
environment(name, connect_config, start=None, stop=None)
```

The `environment()` directive lets you define a remote environment where tasks
can run (e.g., a remote server, a VM in the cloud, etc.).

For Conductor, an environment is a machine that it can connect to using SSH. You
use the `environment()` directive to tell Conductor how to connect to the
machine. You can then specify an environment for a `run_command()` or
`run_experiment()` using the `env` argument and Conductor will transparently
execute the task in the environment on your behalf. See
[`run_experiment()`](task-types/run-experiment.md#env) for more details.

Conductor environments work best with Linux-based machines. Your machine must
have `git` and other standard utilities (e.g., `bash`) installed.

:::note

To use environments, you need to have installed Conductor with the `[envs]`
extra.

```bash
pip3 install conductor-cli[envs]
```

or

```bash
pip3 install conductor-cli[all]
```

:::

## Arguments

### `name`

**Type:** String (required)

The name of the environment. This name must be unique within your Conductor
project. An environment name can only contain letters, numbers, hyphens (`-`),
and underscores (`_`). `run_experiment()` and `run_command()` tasks refer to an
environment by this name.

### `connect_config`

**Type:** String (required)

An executable to run, which generates a configuration string (described below)
used to connect to the remote environment using SSH. Conductor runs this
executable after `start` has run, which allows you to dynamically set the SSH
host (e.g., a dynamic IP that is assigned after a cloud VM starts).

This executable must generate a TOML string with the following format

```toml title="Example generated configuration"
host = 192.168.0.1
user = geoffxy
```

Here `host` must refer to a SSH-able host (e.g., IP address, domain name, SSH
hostname) and `user` is the username to log in as. Note that you must have SSH
authentication set up for the remote machine. You can use hosts that are defined
in your local `~/.ssh/config` file.

### `start`

**Type:** String (default: `None`)

An optional executable to run to "start" the remote environment. For example, if
your remote environment is a cloud VM, this script can be used to start the VM.

### `stop`

**Type:** String (default: `None`)

An optional executable to run to "stop" (i.e., shutdown) the remote environment.
For example, if your remote environment is a cloud VM, this script can be used
to shutdown the VM.

## Usage Example

In this example, we define an environment called `my_remote_machine`. We include
a `config.sh` script that generates the config values we want Conductor to use
to SSH into our remote machine. Conductor will use SSH keys to connect (you need
to set up your keys beforehand).

```python
environment(
  name="my_remote_machine",
  connect_config="./config.sh",
)
```

```bash title="config.sh"
echo "host = 192.168.0.1"
echo "user = geoffxy"
```
