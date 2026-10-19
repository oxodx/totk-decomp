# Contributing

## Working on a function

1. Run `tools/decompile.py` once to create the local Ghidra project and
   pseudocode export.
2. Find the function address in `pseudocode/functions.csv`.
3. Read its paired `pseudocode/c/*.c` and `pseudocode/asm/*.s` files. Use the C
   for readability and assembly for exact instruction-level behavior.
4. Add confirmed function and data names to `config/functions.csv` and
   `config/symbols.csv`. Use raw NSO addresses; the tooling handles Ghidra's
   `0x100000` image base automatically.
5. Write clean C++ under the appropriate subsystem directory in `src/`.
6. Add it to `config/functions.csv` with status `replacement` only after its
   address and size have been checked against the assembly.
7. Run `tools/build.py`; run `tools/check` again before submitting changes.

Do not paste Ghidra output directly into `src/`. It is useful because it makes
control flow readable, but it guesses types, parameters, names, and expressions.
Reconstructed source should describe the code clearly and be supported by the
actual instructions and surrounding data.

## BOTW as a reference

TOTK shares substantial engine ancestry with BOTW. Search the public BOTW
decompilation for equivalent classes, functions, middleware interfaces, and
subsystem layout before inventing names. Useful high-level areas include
`KingSystem`, game actors, physics, resources, events, AI, and engine libraries.

A BOTW match is evidence, not proof. Confirm offsets, members, signatures,
behavior, and instruction output against TOTK. The games use different SDK and
engine revisions and TOTK contains extensive new and changed systems.

## Matching standard

A function is matching only when the configured compiler produces the expected
AArch64 instructions byte-for-byte. Code that merely behaves similarly or looks
like Ghidra's output remains work in progress.

A `replacement` only promises equivalent behavior and is suitable for emulator
testing. Use `matching` only when the generated instructions match the original
byte-for-byte. The build rejects replacements that overflow their original
function slot, overlap another slot, or lie outside the executable text.

## Repository hygiene

Never commit the game, keys, NCAs, NSOs, assets, Ghidra projects, pseudocode
exports, or instruction dumps. Commit clean-room source, headers, symbol/function
metadata, documentation, and tooling only.
