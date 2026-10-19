# Build and test

## Build the hybrid executable

```sh
tools/build.py
```

The build compiles every function marked `replacement` or `matching`, checks
that it fits its original slot, patches a local copy of the executable, and
verifies the result.

Expected summary:

```text
HYBRID text
MATCH  rodata
MATCH  data
verified: every other executable byte matches
```

`HYBRID text` is normal because reconstructed functions changed. A failure
about bytes outside declared slots is not normal and must be fixed before
testing.

## Recheck without compiling

```sh
tools/check
```

## Install in the sandboxed Eden setup

Close the running game, then run:

```sh
tools/install.py
```

This copies the generated mod to:

```text
~/.local/share/eden-sandbox/data/eden/load/
  0100F2C0115B6000/totk-decomp/exefs/main
```

Start TOTK 1.0.0. Eden's log should report:

```text
ExeFS: LayeredExeFS patches applied successfully
```

That proves the hybrid executable loaded. It does not prove every replacement
was executed or behaved correctly.

## If the game fails

1. Close Eden.
2. Disable or remove the `totk-decomp` mod directory.
3. Confirm the unmodified game still boots.
4. Change new functions back to `research` one at a time.
5. Rebuild and retest to isolate the failing replacement.

Never solve a slot overflow by blindly increasing its CSV size: that may
overwrite the neighboring original function.
