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

Note that if you install Conductor locally on a Linux machine (e.g., using `pip
install --user conductor-cli`), you may need to add `$HOME/.local/bin` to your
`$PATH` to get access to the `cond` executable in your shell.

## Documentation and Getting Started
A quick way to get started is to look at the example projects under the
`examples` directory. For more details, please check out Conductor's reference
documentation [here](https://www.geoffreyyu.com/conductor/).

## Acknowledgements
Conductor's interface was largely inspired by [Bazel](https://bazel.build)
and [Buck](https://buck.build).
