#!/usr/bin/env nix-shell
#!nix-shell -i python3 -p python3 git gnumake gcc
"""Set up the local TOTK executable and create the initial hybrid build."""

import shutil
import subprocess
from pathlib import Path

import decomp

def install_hactool() -> None:
  if decomp.find_hactool(decomp.load_config()):
    return
  root = decomp.ROOT / ".tools/hactool"
  root.parent.mkdir(parents=True, exist_ok=True)
  subprocess.run(
    ["git", "clone", "--filter=blob:none", "https://github.com/SciresM/hactool.git",
     str(root)],
    check=True)
  subprocess.run(["git", "-C", str(root), "checkout", "1.4.0"], check=True)
  shutil.copy2(root / "config.mk.template", root / "config.mk")
  subprocess.run(["make", "-C", str(root)], check=True)

def main() -> None:
  cfg = decomp.load_config()
  install_hactool()
  decomp.cmd_doctor(cfg, None)
  if not (decomp.EXTRACT / "exefs/main").is_file():
    decomp.cmd_extract(cfg, None)
  else:
    print(">>> using existing ExeFS extraction")
  decomp.cmd_prepare(cfg, None)
  decomp.cmd_build(cfg, None)
  decomp.cmd_verify(cfg, None)
  print(">>> setup complete")

if __name__ == "__main__":
  decomp.entrypoint(main)
