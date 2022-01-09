---
title: Configuration
id: configuration
---

Every Conductor project contains a `cond_config.toml` file, which marks the
project root. As alluded to by its name, this file is also used to configure
Conductor and is written in [TOML](https://toml.io/).

## Options

### `disable_git`

**Type:** Boolean (default: `false`)

If your project is managed using Git, Conductor by default uses the repository's
state (e.g., the current commit) when recording task output versions. If this
option is set to `true`, Conductor will _not_ use Git.

#### Usage Example

```toml title="cond_config.toml"
# Disables Conductor's Git integration.
disable_git = true
```
