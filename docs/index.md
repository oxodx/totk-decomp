<p class="project-kicker">An experimental hybrid decompilation</p>

# Tears of the Kingdom Decompilation

<p class="project-lede">Reconstructing the <em>Tears of the Kingdom</em> 1.0.0 executable as readable, testable C++—one function at a time.</p>

<div class="project-actions">
  <a class="md-button md-button--primary" href="getting-started/">Set up the project</a>
  <a class="md-button" href="contributing/">Make your first contribution</a>
</div>

## What is this?

This is an ongoing reverse-engineering project to understand and reimplement
parts of *The Legend of Zelda: Tears of the Kingdom* for Nintendo Switch.

The project combines readable C++ with exact AArch64 assembly. Reconstructed
functions are compiled back into their original slots, while code that has not
been decompiled remains untouched in your locally extracted executable.

!!! warning "Important note"
    This repository does **not** contain Nintendo executables, keys, game
    assets, saves, or generated pseudocode. It cannot be used without a legally
    dumped copy of your own game.

## How does it work?

<div class="project-flow">
  <div><strong>01 · Inspect</strong><span>Read the original AArch64 and Ghidra's C-like draft.</span></div>
  <div><strong>02 · Understand</strong><span>Work out what the function does and give it a useful name.</span></div>
  <div><strong>03 · Rebuild</strong><span>Write clean C++ or precise assembly for that function slot.</span></div>
  <div><strong>04 · Verify</strong><span>Compile, compare bytes, and test the hybrid executable.</span></div>
</div>

Every replacement is bounded to a declared address range. The validator checks
that every byte outside those ranges still matches the original executable.
That makes partial progress useful: the game can keep using its original code
everywhere the project has not supplied a replacement.

### Matching and reimplementation

A **matching** function compiles to the exact same machine code as the original.
A **replacement** is expected to behave the same but may produce different
instructions. A **research** function is understood or drafted but is not yet
inserted into the hybrid executable.

| Status | What it means |
| --- | --- |
| `research` | Notes or source exist, but the function is not inserted. |
| `replacement` | The behavior is understood; compiled bytes may differ. |
| `matching` | The compiled output is byte-for-byte identical. |

## Can I contribute?

Yes. If you know ordinary C++, you already know enough to start with a small
function. You do not need previous reverse-engineering or assembly experience;
the [beginner contribution guide](contributing.md) explains the unfamiliar
parts and keeps assembly beside readable pseudocode.

Start small, describe what you learned, and let exact matching come later.

[Read the beginner guide →](contributing.md){ .md-button .md-button--primary }

## Project scope

The executable and its code are in scope. Game assets, RomFS content, keys,
copyrighted binaries, and save data are not. The repository stores original
reimplementations, function metadata, build tooling, and documentation only.

This is a research and preservation effort—not a game download, PC port, or
substitute for owning *Tears of the Kingdom*.
