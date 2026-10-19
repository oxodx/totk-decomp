# Beginner contribution guide

You only need ordinary C++ experience to start. You do **not** need to know
reverse engineering, ARM assembly, Ghidra, or Nintendo Switch internals first.
Start with a tiny function and learn one instruction at a time.

This project does not distribute Nintendo code or game data. Use your own
legally dumped TOTK 1.0.0 game and keys. Never commit anything under
`baserom/`, `extract/`, `analysis/`, `ghidra-project/`, `pseudocode/`, or
`build/`.

## What this project is doing

The original game executable contains AArch64 machine instructions but no
original C++ source. For each function we:

1. Read Ghidra's approximate C-like explanation.
2. Check that explanation against the real AArch64 instructions.
3. Write clean, readable C++ with the same behavior.
4. Compile it for AArch64.
5. Replace only that function's original byte range.
6. Keep Nintendo's original bytes everywhere else.

There are two useful goals:

- A **replacement** behaves like the original and is safe to test, but its
  compiled instructions differ.
- A **matching** function compiles to exactly the same bytes as the original.

Matching is the final goal, but a well-understood replacement is still useful.

## One-time setup

From the repository root, run:

```sh
tools/setup.py
tools/decompile.py
```

`tools/decompile.py` can take a long time on its first run because Ghidra must
analyze a very large executable. Later runs reuse the local project.

The generated reference files are:

```text
pseudocode/c/              readable but untrusted Ghidra pseudocode
pseudocode/asm/            exact AArch64 instructions and bytes
pseudocode/functions.csv   index of discovered functions
```

If setup or decompilation fails, do not edit generated files to hide the
problem. Ask for help and include the last error lines.

## Your first function

Choose something small. Good first functions are approximately 4–80 bytes and
contain simple comparisons, getters, setters, loops, or calls to already named
helpers.

Avoid these until you have more experience:

- constructors and destructors;
- virtual functions or unexplained indirect calls;
- exception-handling code;
- large functions;
- allocators and ownership-heavy code;
- functions with many unknown fields or global variables;
- Ghidra output containing lots of warnings or obviously broken types.

Open `pseudocode/functions.csv`, choose an address, and open its paired files in
`pseudocode/c/` and `pseudocode/asm/`.

The C-like file answers, “What might this function mean?” The assembly answers,
“What does it definitely do?” Never paste Ghidra output directly into `src/`.

## Tiny AArch64 cheat sheet

You do not need to memorize this. These are the instructions most beginner
functions use:

| Assembly           | Rough C++ meaning                       |
| ------------------ | --------------------------------------- |
| `mov x0, x1`       | `x0 = x1`                               |
| `ldr x0, [x1]`     | load a 64-bit value through a pointer   |
| `ldrb w0, [x1]`    | load one unsigned byte                  |
| `str w0, [x1, #8]` | store a 32-bit value at byte offset 8   |
| `add x0, x0, #1`   | `++x0`                                  |
| `sub w0, w1, w2`   | `w0 = w1 - w2`                          |
| `cmp w0, w1`       | compare values for the following branch |
| `cbz x0, address`  | branch if `x0 == 0`                     |
| `cbnz x0, address` | branch if `x0 != 0`                     |
| `b.eq address`     | branch if equal                         |
| `b.ne address`     | branch if not equal                     |
| `bl address`       | call a function                         |
| `b address`        | jump, sometimes a tail call             |
| `ret`              | return                                  |

Registers `x0` through `x7` normally hold function arguments. A return value is
normally placed in `x0` or `w0`. An `x` register is 64-bit; the corresponding
`w` register is its lower 32 bits.

Stack setup such as `stp x29, x30, [...]` is normally compiler bookkeeping. For
a first contribution, concentrate on loads, stores, comparisons, branches, and
calls in the middle of the function.

## Worked example

The original function at raw offset `0x000a4100` does this:

```text
if the pointer is null, return true
otherwise load its first byte
return whether that byte is zero
```

That becomes ordinary C++:

```cpp
extern "C" bool isNullOrEmpty(const char* text) {
  return text == nullptr || *text == '\0';
}
```

Its manifest entry is:

```csv
0x000a4100,0x1c,isNullOrEmpty,matching,src/KingSystem/Util/isNullOrEmpty.cpp
```

This one compiles to the exact original bytes, so its status is `matching`.

## Writing a new source file

Create a sensibly named `.cpp` file under the closest subsystem in `src/`.
Prefer a readable behavioral name such as `findCharacterIndex`; do not keep a
name such as `FUN_001a01c0` in reconstructed source.

Use `extern "C"` for functions listed in the CSV so the compiler emits the
unmangled linker name expected by the patcher:

```cpp
extern "C" int exampleFunction(const char* text) {
  // Clean reconstruction supported by the assembly.
}
```

Do not use the C++ standard library yet. These replacements are freestanding
code inserted directly into the game executable.

## Adding it to the function manifest

Add one row to `config/functions.csv`:

```csv
raw_address,size,readableName,research,src/path/readableName.cpp
```

The statuses mean:

- `research`: source or notes exist, but it is not inserted into the game;
- `replacement`: compiled and inserted, with equivalent behavior expected;
- `matching`: compiled bytes have been checked against the original and are
  identical.

Start with `research`. Change it to `replacement` only after confirming the
address, size, signature, and behavior. Never label something `matching` just
because it boots.

### Important address difference

Manifest addresses are raw NSO text offsets. The current Ghidra project adds an
image base of `0x100000`.

```text
raw address = Ghidra address - 0x100000
```

For example:

```text
Ghidra: 0x001a01c0
raw:    0x000a01c0
```

The exported index and project tooling should handle this, but remember it when
manually comparing an address.

## Calling an original game function

If your C++ calls an original function that has not been reconstructed, give it
a readable binding in `config/symbols.csv`:

```csv
0x000a4360,findCharacter,function
```

Then declare and call it normally:

```cpp
extern "C" const char* findCharacter(const char* text, int character);
```

The build creates the linker binding. The Ghidra naming script also imports the
same readable name. Do not put numeric addresses directly in C++.

Names in these CSV files must be unique valid C/C++ identifiers.

## Build and safety checks

Run:

```sh
tools/build.py
```

The build refuses to continue if a function:

- compiles larger than its original slot;
- overlaps another replacement;
- lies outside the executable text;
- references an unknown symbol;
- has a missing source file.

A successful replacement build ends with output similar to:

```text
HYBRID text
MATCH  rodata
MATCH  data
verified: every other executable byte matches
```

`HYBRID text` is expected: declared functions changed. `rodata` and `data`
should remain `MATCH` unless the project deliberately gains support for those
types of replacements.

To check an existing build again without compiling:

```sh
tools/check
```

## Test in Eden

First close the running game. Build and install the mod:

```sh
tools/build.py
tools/install.py
```

Start TOTK 1.0.0 in Eden. The Eden log should contain:

```text
ExeFS: LayeredExeFS patches applied successfully
```

Loading successfully proves Eden used the hybrid executable. It does not prove
that every replacement ran, and it does not prove matching behavior. Exercise
the relevant game feature when you know what calls the function.

The local Eden save backup is outside this repository. Do not add saves to the
project. Disable the `totk-decomp` mod if the game becomes unstable.

## Common problems

### “Function is larger than its original slot”

Do not increase the size in the CSV unless the assembly proves the boundary was
wrong. Simplify the control flow, use early returns like the original, or leave
the function as `research`.

### The C++ looks right but the assembly differs

That is normal. Compilers can choose different registers, branches, stack
layouts, and instruction ordering. Keep the function as `replacement` until
the bytes are identical.

### Ghidra gives strange types

Treat them as guesses. Infer types from how values are used:

- `ldrb` usually indicates a byte or character;
- `ldr w...` indicates a 32-bit value;
- `ldr x...` indicates a pointer or 64-bit value;
- repeated accesses such as `[x0, #8]` suggest a structure member at offset 8.

Use an opaque `void*` when the surrounding class is not understood. Do not
invent a full class layout from one function.

### The game boots but I cannot see a difference

Correct replacements should usually produce no visible difference. Booting is
a useful smoke test, not proof of exact behavior. A targeted test, debugger
breakpoint, or carefully controlled canary build is needed to prove execution.

## Before submitting work

Check all of these:

- The function has a readable, evidence-based name.
- The address and size were verified from assembly.
- The source is clean C++, not pasted Ghidra output.
- Unknown assumptions are explained in comments or the contribution message.
- `tools/build.py` succeeds.
- `tools/check` succeeds.
- The game or relevant feature was tested when practical.
- Generated game data, pseudocode, binaries, keys, and saves are not included.

When uncertain, leave the status as `research` and ask for review. A cautious
partial reconstruction is much more valuable than a confident wrong one.
