# Project layout

| Path                   | Purpose                                       | Commit it? |
| ---------------------- | --------------------------------------------- | ---------- |
| `src/`                 | Reconstructed C++, declarations, and types    | Yes        |
| `config/functions.csv` | Function boundaries, names, status, source    | Yes        |
| `config/symbols.csv`   | Named bindings to original functions and data | Yes        |
| `tools/`               | Setup, build, analysis, and install tooling   | Yes        |
| `docs/`                | Documentation site source                     | Yes        |
| `baserom/`             | Locally prepared original executable data     | No         |
| `extract/`             | Locally extracted game files                  | No         |
| `analysis/`            | Generated analysis inputs                     | No         |
| `ghidra-project/`      | Local Ghidra database                         | No         |
| `pseudocode/`          | Generated C-like and assembly references      | No         |
| `build/`               | Compiled hybrid executable and docs site      | No         |

## Important configuration files

### `config/functions.csv`

One row connects a raw text address and size to its readable name, status, and
C++ source file.

### `config/symbols.csv`

Names original game functions or data that reconstructed source needs to
reference. These names are supplied to both the linker and Ghidra.

### `config/project.toml`

Contains shared project identity, game version, default input location, and
output layout.

### `config/local.toml`

Optional machine-specific overrides. Do not commit local paths or key
locations.
