#!/usr/bin/env python3
"""Local-only extraction and hybrid NSO rebuild tooling."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import re
import shutil
import struct
import subprocess
import sys
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROJECT_FILE = ROOT / "config/project.toml"
LOCAL_FILE = ROOT / "config/local.toml"
EXTRACT = ROOT / "extract"
BASEROM = ROOT / "baserom"
BUILD = ROOT / "build"

class DecompError(RuntimeError):
  pass

def load_config() -> dict:
  with PROJECT_FILE.open("rb") as f:
    cfg = tomllib.load(f)
  if LOCAL_FILE.exists():
    with LOCAL_FILE.open("rb") as f:
      local = tomllib.load(f)
    for section, values in local.items():
      if isinstance(values, dict):
        cfg.setdefault(section, {}).update(values)
      else:
        cfg[section] = values
  return cfg

def expand(value: str) -> Path:
  return Path(os.path.expandvars(os.path.expanduser(value))).resolve()

def find_keys(cfg: dict) -> Path | None:
  candidates = []
  configured = cfg.get("input", {}).get("keys")
  if configured:
    candidates.append(expand(configured))
  candidates += [
    Path.home() / ".switch/prod.keys",
    Path.home() / ".local/share/eden/keys/prod.keys",
  ]
  return next((p for p in candidates if p.is_file()), None)

def find_hactool(cfg: dict) -> str | None:
  configured = cfg.get("input", {}).get("hactool")
  if configured:
    path = expand(configured)
    return str(path) if path.is_file() else None
  bundled = ROOT / ".tools/hactool/hactool"
  if bundled.is_file() and os.access(bundled, os.X_OK):
    return str(bundled)
  return shutil.which("hactool")

def run(args: list[str]) -> None:
  print("+", " ".join(args))
  subprocess.run(args, check=True)

def sha256(data: bytes) -> str:
  return hashlib.sha256(data).hexdigest()

def lz4_decompress_block(src: bytes, expected: int) -> bytes:
  """Decode the raw LZ4 block format used by NSO segments."""
  out = bytearray()
  i = 0
  while i < len(src):
    token = src[i]
    i += 1
    literal_len = token >> 4
    if literal_len == 15:
      while True:
        if i >= len(src):
          raise DecompError("truncated LZ4 literal length")
        value = src[i]
        i += 1
        literal_len += value
        if value != 255:
          break
    if i + literal_len > len(src):
      raise DecompError("truncated LZ4 literals")
    out += src[i:i + literal_len]
    i += literal_len
    if i == len(src):
      break
    if i + 2 > len(src):
      raise DecompError("truncated LZ4 match offset")
    offset = src[i] | (src[i + 1] << 8)
    i += 2
    if offset == 0 or offset > len(out):
      raise DecompError("invalid LZ4 match offset")
    match_len = token & 0x0F
    if match_len == 15:
      while True:
        if i >= len(src):
          raise DecompError("truncated LZ4 match length")
        value = src[i]
        i += 1
        match_len += value
        if value != 255:
          break
    match_len += 4
    for _ in range(match_len):
      out.append(out[-offset])
  if len(out) != expected:
    raise DecompError(f"LZ4 size mismatch: got {len(out):#x}, expected {expected:#x}")
  return bytes(out)

def parse_nso(path: Path) -> tuple[bytearray, dict, dict[str, bytes]]:
  blob = path.read_bytes()
  if len(blob) < 0x100 or blob[:4] != b"NSO0":
    raise DecompError(f"{path} is not an NSO0 executable")
  header = bytearray(blob[:0x100])
  flags = struct.unpack_from("<I", header, 0xC)[0]
  specs = {
    "text": (0x10, 0x60, 0),
    "rodata": (0x20, 0x64, 1),
    "data": (0x30, 0x68, 2),
  }
  segments: dict[str, bytes] = {}
  metadata: dict = {
    "source": str(path),
    "source_sha256": sha256(blob),
    "flags": flags,
    "build_id": bytes(header[0x40:0x60]).hex(),
    "bss_size": struct.unpack_from("<I", header, 0x3C)[0],
    "segments": {},
  }
  for name, (descriptor, compressed_at, flag_bit) in specs.items():
    file_offset, memory_offset, memory_size = struct.unpack_from("<III", header, descriptor)
    stored_size = struct.unpack_from("<I", header, compressed_at)[0]
    payload = blob[file_offset:file_offset + stored_size]
    if len(payload) != stored_size:
      raise DecompError(f"truncated {name} segment")
    data = lz4_decompress_block(payload, memory_size) if flags & (1 << flag_bit) else payload
    if len(data) != memory_size:
      raise DecompError(f"{name} size mismatch")
    segments[name] = data
    metadata["segments"][name] = {
      "file_offset": file_offset,
      "memory_offset": memory_offset,
      "size": memory_size,
      "stored_size": stored_size,
      "compressed": bool(flags & (1 << flag_bit)),
      "sha256": sha256(data),
    }
  return header, metadata, segments

def align(value: int, boundary: int = 0x10) -> int:
  return (value + boundary - 1) & -boundary

def pack_uncompressed_nso(header: bytearray, segments: dict[str, bytes]) -> bytes:
  header = bytearray(header)
  flags = struct.unpack_from("<I", header, 0xC)[0] & ~0x7
  struct.pack_into("<I", header, 0xC, flags)
  layout = (("text", 0x10, 0x60, 0xA0), ("rodata", 0x20, 0x64, 0xC0), ("data", 0x30, 0x68, 0xE0))
  cursor = 0x100
  chunks: list[tuple[int, bytes]] = []
  for name, descriptor, stored_at, hash_at in layout:
    data = segments[name]
    cursor = align(cursor)
    memory_offset = struct.unpack_from("<I", header, descriptor + 4)[0]
    struct.pack_into("<III", header, descriptor, cursor, memory_offset, len(data))
    struct.pack_into("<I", header, stored_at, len(data))
    header[hash_at:hash_at + 0x20] = hashlib.sha256(data).digest()
    chunks.append((cursor, data))
    cursor += len(data)
  out = bytearray(header)
  for offset, data in chunks:
    if len(out) < offset:
      out += bytes(offset - len(out))
    out += data
  return bytes(out)

def pack_analysis_elf(metadata: dict, segments: dict[str, bytes]) -> bytes:
  """Wrap decompressed NSO segments in a minimal AArch64 ELF for analyzers."""
  names = ("text", "rodata", "data")
  flags = {"text": 5, "rodata": 4, "data": 6}  # PF_R|PF_X, PF_R, PF_R|PF_W
  offsets = {}
  cursor = 0x1000
  for name in names:
    offsets[name] = cursor
    cursor = align(cursor + len(segments[name]), 0x1000)
  ident = b"\x7fELF" + bytes([2, 1, 1, 0]) + bytes(8)
  header = ident + struct.pack("<HHIQQQIHHHHHH", 3, 183, 1, 0, 64, 0, 0, 64, 56, 3, 0, 0, 0)
  program_headers = bytearray()
  for name in names:
    virtual = metadata["segments"][name]["memory_offset"]
    memory_size = len(segments[name])
    if name == "data":
      memory_size += metadata["bss_size"]
    program_headers += struct.pack("<IIQQQQQQ", 1, flags[name], offsets[name], virtual, virtual,
                                   len(segments[name]), memory_size, 0x1000)
  out = bytearray(header + program_headers)
  for name in names:
    if len(out) < offsets[name]:
      out += bytes(offsets[name] - len(out))
    out += segments[name]
  return bytes(out)

def recover_stale_ghidra_lock(project: Path, name: str = "totk") -> bool:
  """Remove only generated Ghidra locks when no analyzer owns the project."""
  lock_files = (project / f"{name}.lock", project / f"{name}.lock~")
  if not any(path.exists() for path in lock_files):
    return False
  process_list = subprocess.run(["ps", "-eo", "pid=,comm=,args="],
                                check=True,
                                capture_output=True,
                                text=True).stdout
  active = False
  for line in process_list.splitlines():
    fields = line.strip().split(None, 2)
    if len(fields) == 3 and fields[1] in {"java", "javaw"}:
      if "analyzeHeadless" in fields[2] and str(project) in fields[2]:
        active = True
        break
  if active:
    raise DecompError("this Ghidra project is already being analyzed; wait for it to finish")
  for path in lock_files:
    path.unlink(missing_ok=True)
  return True

def original_main() -> Path:
  candidates = [EXTRACT / "exefs/main", BASEROM / "main"]
  found = next((p for p in candidates if p.is_file()), None)
  if not found:
    raise DecompError("no ExeFS main found; run 'make extract' or import-exefs first")
  return found

def cmd_doctor(cfg: dict, _args: argparse.Namespace) -> None:
  xci = expand(cfg["input"]["xci"])
  keys = find_keys(cfg)
  hactool = find_hactool(cfg)
  checks = [
    ("XCI", xci.is_file(), str(xci)),
    ("prod.keys", keys is not None, str(keys) if keys else "not found"),
    ("hactool", hactool is not None, hactool or "not found"),
    ("Python >= 3.11", sys.version_info >= (3, 11), sys.version.split()[0]),
  ]
  for name, ok, detail in checks:
    print(f"{'ok' if ok else 'MISSING':7} {name:15} {detail}")
  if not all(ok for _, ok, _ in checks):
    raise DecompError("doctor found missing requirements")

def cmd_extract(cfg: dict, _args: argparse.Namespace) -> None:
  xci = expand(cfg["input"]["xci"])
  keys = find_keys(cfg)
  hactool = find_hactool(cfg)
  if not xci.is_file() or not keys or not hactool:
    cmd_doctor(cfg, _args)
  secure = EXTRACT / "secure"
  exefs = EXTRACT / "exefs"
  secure.mkdir(parents=True, exist_ok=True)
  exefs.mkdir(parents=True, exist_ok=True)
  common = [hactool, "--disablekeywarns", f"--keyset={keys}"]
  run(common + ["-t", "xci", f"--securedir={secure}", str(xci)])
  ncas = sorted(secure.glob("*.nca"), key=lambda p: p.stat().st_size, reverse=True)
  if not ncas:
    raise DecompError("XCI extraction produced no secure-partition NCAs")
  for nca in ncas:
    trial = EXTRACT / "exefs-trial"
    if trial.exists():
      shutil.rmtree(trial)
    trial.mkdir()
    result = subprocess.run(common + ["-t", "nca", f"--exefsdir={trial}", str(nca)])
    if result.returncode == 0 and (trial / "main").is_file():
      if exefs.exists():
        shutil.rmtree(exefs)
      trial.rename(exefs)
      print(f"found program ExeFS in {nca.name}")
      return
  raise DecompError("could not locate a program NCA containing ExeFS/main")

def cmd_import_exefs(_cfg: dict, args: argparse.Namespace) -> None:
  source = expand(args.path)
  if not (source / "main").is_file():
    raise DecompError(f"{source} does not contain an ExeFS main")
  EXTRACT.mkdir(parents=True, exist_ok=True)
  target = EXTRACT / "exefs"
  if target.exists():
    raise DecompError(f"{target} already exists; remove it explicitly before replacing it")
  shutil.copytree(source, target)
  print(f"imported {source} -> {target}")

def cmd_prepare(_cfg: dict, _args: argparse.Namespace) -> None:
  main = original_main()
  header, metadata, segments = parse_nso(main)
  BASEROM.mkdir(parents=True, exist_ok=True)
  (BASEROM / "main").write_bytes(main.read_bytes())
  (BASEROM / "main.header.bin").write_bytes(header)
  for name, data in segments.items():
    (BASEROM / f"main.{name}.bin").write_bytes(data)
  (BASEROM / "main.json").write_text(json.dumps(metadata, indent=2) + "\n")
  print(f"prepared NSO build ID {metadata['build_id']}")
  for name, info in metadata["segments"].items():
    print(f"  {name:7} {info['size']:#010x} bytes  sha256 {info['sha256']}")

def cmd_pseudocode(_cfg: dict, _args: argparse.Namespace) -> None:
  if not (BASEROM / "main.json").is_file():
    cmd_prepare(_cfg, _args)
  metadata = json.loads((BASEROM / "main.json").read_text())
  _header, segments = read_prepared()
  analysis = ROOT / "analysis"
  analysis.mkdir(parents=True, exist_ok=True)
  elf = analysis / "main.elf"
  elf.write_bytes(pack_analysis_elf(metadata, segments))
  analyzer = shutil.which("analyzeHeadless") or shutil.which("ghidra-analyzeHeadless")
  if not analyzer:
    ghidra_home = os.environ.get("GHIDRA_HOME")
    candidate = Path(ghidra_home) / "support/analyzeHeadless" if ghidra_home else None
    if candidate and candidate.is_file():
      analyzer = str(candidate)
  if not analyzer:
    raise DecompError("Ghidra analyzeHeadless was not found. Install Ghidra or set GHIDRA_HOME; "
                      "tools/decompile.py supplies it automatically on NixOS")
  project = ROOT / "ghidra-project"
  output = ROOT / "pseudocode"
  project.mkdir(parents=True, exist_ok=True)
  output.mkdir(parents=True, exist_ok=True)
  scripts = ROOT / "tools/ghidra_scripts"
  if recover_stale_ghidra_lock(project):
    print(">>> recovered an interrupted Ghidra project")
  ready = analysis / "ghidra-ready"
  command = [analyzer, str(project), "totk"]
  if ready.is_file():
    command += ["-process", "main.elf", "-noanalysis"]
    print(">>> reusing the existing Ghidra analysis")
  else:
    command += ["-import", str(elf), "-overwrite", "-analysisTimeoutPerFile", "3600"]
    print(">>> Ghidra is analyzing the executable; the first run can take a while")
  command += [
    "-scriptPath", str(scripts),
    "-preScript", "ApplySymbols.java", str(ROOT / "config/functions.csv"),
    str(ROOT / "config/symbols.csv"),
    "-postScript", "ExportPseudocode.java", str(output),
  ]
  run(command)
  ready.touch()
  index = output / "functions.csv"
  count = 0
  c_count = 0
  if index.is_file():
    with index.open(newline="") as f:
      rows = list(csv.DictReader(f))
      count = len(rows)
      c_count = sum(row.get("c_status") == "ok" for row in rows)
  print(f"exported assembly for {count} functions and C-like drafts for {c_count}")
  print(f">>> index: {index}")

def read_prepared() -> tuple[bytearray, dict[str, bytes]]:
  header_path = BASEROM / "main.header.bin"
  if not header_path.is_file():
    raise DecompError("prepared inputs missing; run 'make prepare'")
  segments = {}
  for name in ("text", "rodata", "data"):
    path = BASEROM / f"main.{name}.bin"
    if not path.is_file():
      raise DecompError(f"missing {path}")
    segments[name] = path.read_bytes()
  return bytearray(header_path.read_bytes()), segments

def replacement_rows() -> list[dict[str, str]]:
  """Read enabled source replacements from the small, reviewable manifest."""
  path = ROOT / "config/functions.csv"
  with path.open(newline="") as f:
    return [
      row for row in csv.DictReader(line for line in f if not line.lstrip().startswith("#"))
      if row.get("address") and row.get("status", "").strip().lower()
      in {"replacement", "matching"}
    ]

def symbol_rows() -> list[dict[str, str]]:
  """Return named original addresses that reconstructed source may call."""
  path = ROOT / "config/symbols.csv"
  with path.open(newline="") as f:
    return [
      row for row in csv.DictReader(line for line in f if not line.lstrip().startswith("#"))
      if row.get("address") and row.get("name")
    ]

def compile_replacement(row: dict[str, str]) -> bytes:
  """Compile one freestanding AArch64 function at its original text address."""
  address = int(row["address"], 0)
  size = int(row["size"], 0)
  name = row["name"].strip()
  source = ROOT / row["source"].strip()
  if not source.is_file():
    raise DecompError(f"replacement source does not exist: {source}")
  compiler = shutil.which("clang++")
  linker = shutil.which("ld.lld")
  objcopy = shutil.which("llvm-objcopy")
  if not compiler or not linker or not objcopy:
    raise DecompError("replacement builds require clang++, ld.lld, and llvm-objcopy")

  work = BUILD / "functions" / f"{address:08x}_{name}"
  work.mkdir(parents=True, exist_ok=True)
  object_file = work / "function.o"
  linked_file = work / "function.elf"
  binary_file = work / "function.bin"
  linker_script = work / "function.ld"
  bindings = []
  seen_names = set()
  for symbol in symbol_rows():
    symbol_name = symbol["name"].strip()
    if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", symbol_name):
      raise DecompError(f"symbol is not a C/C++ linker name: {symbol_name}")
    if symbol_name in seen_names:
      raise DecompError(f"duplicate symbol name: {symbol_name}")
    seen_names.add(symbol_name)
    bindings.append(f"PROVIDE({symbol_name} = {int(symbol['address'], 0):#x});\n")
  linker_script.write_text(
    f"ENTRY({name})\n"
    + "".join(bindings)
    +
    "SECTIONS {\n"
    f"  . = 0x{address:x};\n"
    "  .text : { *(.text*) }\n"
    "  /DISCARD/ : { *(.comment) *(.note*) *(.eh_frame*) }\n"
    "}\n")
  run([
    compiler, "--target=aarch64-none-elf", "-std=c++17", "-O2", "-ffreestanding",
    "-fno-exceptions", "-fno-rtti", "-fno-stack-protector", "-fno-unwind-tables",
    "-fno-asynchronous-unwind-tables", "-fno-ident", "-fomit-frame-pointer",
    "-fzero-call-used-regs=skip", "-ffunction-sections", "-nostdlib",
    "-c", str(source), "-o", str(object_file),
  ])
  run([linker, "-T", str(linker_script), "-o", str(linked_file), str(object_file)])
  run([objcopy, "-O", "binary", "--only-section=.text", str(linked_file), str(binary_file)])
  code = binary_file.read_bytes()
  if not code:
    raise DecompError(f"compiler emitted no code for {name}")
  if len(code) > size:
    raise DecompError(f"{name} is {len(code):#x} bytes but its original slot is only {size:#x}")
  if len(code) % 4 or size % 4:
    raise DecompError(f"{name} has a non-instruction-aligned size")
  # Any unreachable space left in the original function slot is filled with AArch64 NOPs.
  return code + b"\x1f\x20\x03\xd5" * ((size - len(code)) // 4)

def apply_replacements(segments: dict[str, bytes]) -> tuple[dict[str, bytes], list[dict[str, str]]]:
  rows = replacement_rows()
  if not rows:
    return segments, rows
  text = bytearray(segments["text"])
  occupied: list[tuple[int, int, str]] = []
  for row in rows:
    address = int(row["address"], 0)
    size = int(row["size"], 0)
    end = address + size
    if address < 0 or end > len(text):
      raise DecompError(f"replacement {row['name']} lies outside the text segment")
    for other_start, other_end, other_name in occupied:
      if address < other_end and other_start < end:
        raise DecompError(f"replacement {row['name']} overlaps {other_name}")
    code = compile_replacement(row)
    text[address:end] = code
    occupied.append((address, end, row["name"]))
    print(f"replaced {row['name']} at {address:#x} ({len(code):#x}-byte slot)")
  result = dict(segments)
  result["text"] = bytes(text)
  return result, rows

def cmd_build(cfg: dict, _args: argparse.Namespace) -> None:
  header, segments = read_prepared()
  segments, _rows = apply_replacements(segments)
  output_root = ROOT / cfg["output"]["atmosphere"]
  output = output_root / "contents" / cfg["project"]["title_id"] / "exefs/main"
  output.parent.mkdir(parents=True, exist_ok=True)
  built_nso = pack_uncompressed_nso(header, segments)
  output.write_bytes(built_nso)
  emulator_output = BUILD / "totk-decomp" / "exefs/main"
  emulator_output.parent.mkdir(parents=True, exist_ok=True)
  emulator_output.write_bytes(built_nso)
  print(f"built {output.relative_to(ROOT)} ({output.stat().st_size:#x} bytes)")
  print(f"emulator mod folder: {emulator_output.parent.parent.relative_to(ROOT)}")

def cmd_setup(cfg: dict, args: argparse.Namespace) -> None:
  """Idempotent first-time setup for the friendly launcher."""
  cmd_doctor(cfg, args)
  exefs_main = EXTRACT / "exefs/main"
  if exefs_main.is_file():
    print("using the already extracted ExeFS")
  else:
    cmd_extract(cfg, args)
  cmd_prepare(cfg, args)
  cmd_build(cfg, args)
  cmd_verify(cfg, args)
  cmd_paths(cfg, args)
  print("setup complete; use './decomp build' after making source changes")

def cmd_rebuild(cfg: dict, args: argparse.Namespace) -> None:
  cmd_build(cfg, args)
  cmd_verify(cfg, args)

def cmd_paths(cfg: dict, _args: argparse.Namespace) -> None:
  title_id = cfg["project"]["title_id"]
  atmosphere = ROOT / cfg["output"]["atmosphere"]
  print(f"project:       {ROOT}")
  print(f"original XCI:  {expand(cfg['input']['xci'])}")
  print(f"source code:   {ROOT / 'src'}")
  print(f"functions:     {ROOT / 'config/functions.csv'}")
  print(f"emulator mod:  {atmosphere / 'contents' / title_id}")
  print(f"simple mod:    {BUILD / 'totk-decomp'}")
  print(f"XCI output:    {ROOT / cfg['output']['xci']}")

def cmd_verify(cfg: dict, _args: argparse.Namespace) -> None:
  expected_header, expected = read_prepared()
  del expected_header
  output = ROOT / cfg["output"]["atmosphere"] / "contents" / cfg["project"][
    "title_id"] / "exefs/main"
  if not output.is_file():
    raise DecompError("build output missing; run 'make build'")
  _header, _metadata, actual = parse_nso(output)
  failed = False
  replacements = replacement_rows()
  expected_text = bytearray(expected["text"])
  for row in replacements:
    address = int(row["address"], 0)
    size = int(row["size"], 0)
    expected_text[address:address + size] = actual["text"][address:address + size]
  text_ok = bytes(expected_text) == actual["text"]
  label = "HYBRID" if replacements and text_ok else ("MATCH" if text_ok else "DIFF")
  print(f"{label:6} text    {sha256(actual['text'])}")
  failed |= not text_ok
  for name in ("rodata", "data"):
    ok = actual[name] == expected[name]
    print(f"{'MATCH' if ok else 'DIFF':6} {name:7} {sha256(actual[name])}")
    failed |= not ok
  if failed:
    raise DecompError("build changed bytes outside declared replacement slots")
  if replacements:
    print(f"verified: {len(replacements)} replacement(s); every other executable byte matches")
  else:
    print("verified: every decompressed executable segment matches")

def cmd_progress(_cfg: dict, _args: argparse.Namespace) -> None:
  rows = []
  with (ROOT / "config/functions.csv").open(newline="") as f:
    rows = [
      r for r in csv.DictReader(line for line in f if not line.lstrip().startswith("#"))
      if r.get("address")
    ]
  total = sum(int(r["size"], 0) for r in rows)
  matched = sum(int(r["size"], 0) for r in rows if r["status"].strip().lower() == "matching")
  percent = (100.0 * matched / total) if total else 0.0
  print(f"catalogued functions: {len(rows)}")
  print(f"matching bytes:       {matched:#x} / {total:#x} ({percent:.2f}%)")

def cmd_xci(cfg: dict, args: argparse.Namespace) -> None:
  # Never package an unverified executable.
  cmd_verify(cfg, args)
  packer_value = cfg.get("output", {}).get("xci_packer")
  if not packer_value:
    raise DecompError("XCI packer is not configured; see README 'Optional XCI output'. "
                      "The verified emulator ExeFS build is ready under build/atmosphere")
  packer = expand(packer_value)
  if not packer.is_file() or not os.access(packer, os.X_OK):
    raise DecompError(f"configured XCI packer is not executable: {packer}")
  original = expand(cfg["input"]["xci"])
  replacement = ROOT / cfg["output"]["atmosphere"] / "contents" / cfg["project"][
    "title_id"] / "exefs"
  output = ROOT / cfg["output"]["xci"]
  output.parent.mkdir(parents=True, exist_ok=True)
  run([str(packer), str(original), str(replacement), str(output)])
  if not output.is_file():
    raise DecompError("XCI packer exited successfully but produced no output")
  print(f"built emulator image {output}")

def cmd_clean(_cfg: dict, _args: argparse.Namespace) -> None:
  if BUILD.exists():
    shutil.rmtree(BUILD)
    print(f"removed {BUILD}")

def entrypoint(action) -> None:
  """Run a public tool with a short error instead of a Python traceback."""
  try:
    action()
  except (DecompError, subprocess.CalledProcessError, OSError) as exc:
    print(f"error: {exc}", file=sys.stderr)
    raise SystemExit(1) from None
