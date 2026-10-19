# The Legend of Zelda: Tears of the Kingdom decompilation

Experimental matching decompilation of the Switch 1.0.0 executable.

This repository contains tooling and clean-room source only. It does not contain
game data, keys, extracted code, or assets. Use a copy of the game and keys
dumped from your own console.

## Setup

The configured input is:

```text
~/Games/roms/switch/TOTK [0100F2C0115B6000][v0].xci
```

Run once:

```sh
tools/setup.py
```

The setup script installs the local extractor if necessary, extracts `main`,
prepares its code/data segments, builds the hybrid executable, and checks it.

## Build

```sh
tools/build.py
```

Check an existing build without rebuilding:

```sh
tools/check
```

A successful check prints `MATCH` for `text`, `rodata`, and `data`.

The first reconstructed function is enabled already. A replacement build prints
`HYBRID text`: the configured function slot changed, while verification confirms
that every byte outside declared replacement slots remains original.

## Test in an emulator

After running `tools/build.py`, right-click TOTK in your emulator and open its
mods directory. Copy this whole generated folder into it:

```text
build/totk-decomp/
  exefs/
    main
```

Enable the `totk-decomp` mod and launch game version 1.0.0. Disable the mod to
return to the untouched executable. The Atmosphere-style copy is also generated
at `build/atmosphere/contents/0100F2C0115B6000/`.

For the sandboxed Eden installation configured on this machine, build and copy
the mod with:

```sh
tools/build.py
tools/install.py
```

## Decompiler reference

```sh
tools/decompile.py
```

This performs a local Ghidra analysis and creates paired references for every
discovered function:

```text
pseudocode/c/          readable, unverified C-like output
pseudocode/asm/        addresses, exact bytes, and AArch64 instructions
pseudocode/functions.csv   address index linking each pair
```

The directory is ignored by Git. Use C to understand the broad control flow and
assembly for precise behavior and matching. Ghidra's C output can guess types,
names, signatures, and expressions incorrectly. If Ghidra cannot decode an
instruction, the assembly file preserves its bytes as an `undecoded` `.word`.

Readable names in `config/functions.csv` and `config/symbols.csv` are applied to
Ghidra automatically on the next `tools/decompile.py` run. The same symbol CSV
also supplies linker bindings, so reconstructed C++ can call named original
game functions without hard-coded addresses in its source.

## Project structure

```text
config/       function and symbol metadata
include/      reconstructed declarations
src/          reconstructed C++
tools/        setup, build, checking, and analysis tools
baserom/      generated local executable data (ignored)
pseudocode/   generated Ghidra reference output (ignored)
build/        generated hybrid executable (ignored)
```

The build begins with every instruction supplied by the locally extracted
original executable. Each enabled C++ function replaces only its declared
original range; everything else remains original. A functional `replacement`
can be tested before it becomes byte-for-byte `matching`.

TOTK was developed from BOTW's technology, so the public
[zeldaret/botw](https://github.com/zeldaret/botw) project is an important
reference for subsystem names, library structure, types, and the established
Switch matching-decomp workflow. BOTW declarations must still be verified
against TOTK rather than copied blindly.

See [CONTRIBUTING.md](CONTRIBUTING.md) for the source workflow, or preview the
full searchable documentation site with `tools/docs.py`.

Published documentation: <https://oxodx.github.io/totk-decomp/>
