#!/usr/bin/env nix-shell
#!nix-shell -i python3 -p python3 python3Packages.mkdocs-material
"""Preview or build the documentation website."""

import subprocess
import sys


def main() -> None:
  if len(sys.argv) == 1:
    command = ["mkdocs", "serve"]
  elif sys.argv[1:] == ["build"]:
    command = ["mkdocs", "build", "--strict"]
  else:
    raise SystemExit("usage: tools/docs.py [build]")
  subprocess.run(command, check=True)


if __name__ == "__main__":
  main()
