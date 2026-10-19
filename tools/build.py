#!/usr/bin/env nix-shell
#!nix-shell -i python3 -p python3 clang lld llvm
"""Build and verify the hybrid TOTK executable."""

import decomp

def main() -> None:
  config = decomp.load_config()
  decomp.cmd_build(config, None)
  decomp.cmd_verify(config, None)

if __name__ == "__main__":
  decomp.entrypoint(main)
