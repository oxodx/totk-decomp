#!/usr/bin/env nix-shell
#!nix-shell -i python3 -p python3
"""Install the current hybrid executable as an Eden per-game mod."""

import shutil
from pathlib import Path

import decomp

def main() -> None:
  source = decomp.BUILD / "totk-decomp/exefs/main"
  if not source.is_file():
    raise decomp.DecompError("build missing; run tools/build.py first")
  title_id = decomp.load_config()["project"]["title_id"]
  eden_data = Path.home() / ".local/share/eden-sandbox/data/eden"
  destination = eden_data / "load" / title_id / "totk-decomp/exefs/main"
  destination.parent.mkdir(parents=True, exist_ok=True)
  shutil.copy2(source, destination)
  print(f"installed Eden mod: {destination.parent.parent}")

if __name__ == "__main__":
  decomp.entrypoint(main)
