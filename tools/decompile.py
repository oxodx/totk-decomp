#!/usr/bin/env nix-shell
#!nix-shell -i python3 -p python3 ghidra
"""Analyze the executable with Ghidra and export local C-like pseudocode."""

import decomp

def main() -> None:
  decomp.cmd_pseudocode(decomp.load_config(), None)

if __name__ == "__main__":
  decomp.entrypoint(main)
