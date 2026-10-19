# Getting started

## Requirements

- Nix or NixOS
- A legally dumped TOTK 1.0.0 XCI
- Keys dumped from your own Switch
- Basic C++ knowledge

The default local XCI path is configured in `config/project.toml`. Machine-only
overrides belong in `config/local.toml`, which should not be committed.

## Prepare the project

From the repository root:

```sh
tools/setup.py
```

This extracts the executable, prepares its segments, produces an initial hybrid
build, and checks it.

## Generate reference material

```sh
tools/decompile.py
```

The first Ghidra analysis can take a long time. It generates:

```text
pseudocode/c/              readable, unverified C-like drafts
pseudocode/asm/            exact AArch64 instructions and bytes
pseudocode/functions.csv   index connecting both versions
```

The generated directories are local reference material and must not be
committed.

## Confirm the baseline

```sh
tools/build.py
tools/check
```

A healthy hybrid build reports `MATCH` for read-only data and verifies that no
bytes outside declared replacement ranges changed.

## Next step

Continue with the [beginner contribution guide](contributing.md).
