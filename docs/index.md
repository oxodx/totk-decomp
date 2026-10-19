# TOTK decompilation

This project is gradually reconstructing the **Tears of the Kingdom 1.0.0**
executable as readable C++. You do not need reverse-engineering experience to
make a first contribution—ordinary C++ knowledge is enough for the small
starter functions.

## Pick a path

[:material-rocket-launch: Set up the project](getting-started.md){ .md-button .md-button--primary }
[:material-code-braces: Make your first contribution](contributing.md){ .md-button }

## The basic idea

```text
original AArch64 function
          ↓
Ghidra C-like draft + exact assembly
          ↓
clean reconstructed C++
          ↓
compile into the original function slot
          ↓
hybrid executable for testing
```

Only declared function slots are replaced. Every other executable byte remains
from your locally extracted game.

!!! warning "Bring your own game"
    This repository must not contain Nintendo executables, keys, game assets,
    saves, or generated pseudocode. Use only a legally dumped copy of your own
    game and keys.

## Current terminology

| Status | Meaning |
| --- | --- |
| `research` | Source or notes exist, but the function is not inserted. |
| `replacement` | Expected to behave equivalently, but compiled bytes differ. |
| `matching` | Compiled output is byte-for-byte identical to the original. |

New contributors should aim for a small, well-understood `research` function
first. Matching can come later.
