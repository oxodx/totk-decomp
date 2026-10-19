import hashlib
import importlib.util
import struct
import tempfile
import unittest
from pathlib import Path

SPEC = importlib.util.spec_from_file_location("decomp",
                                              Path(__file__).parents[1] / "tools/decomp.py")
decomp = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(decomp)

class NsoTests(unittest.TestCase):

  def test_lz4_literals_and_match(self):
    self.assertEqual(decomp.lz4_decompress_block(b"\x40abcd\x04\x00", 8), b"abcdabcd")

  def test_uncompressed_round_trip(self):
    header = bytearray(0x100)
    header[:4] = b"NSO0"
    struct.pack_into("<I", header, 0xC, 0x38)
    struct.pack_into("<III", header, 0x10, 0, 0, 4)
    struct.pack_into("<III", header, 0x20, 0, 0x1000, 3)
    struct.pack_into("<III", header, 0x30, 0, 0x2000, 2)
    segments = {"text": b"TEXT", "rodata": b"RO!", "data": b"DA"}
    blob = decomp.pack_uncompressed_nso(header, segments)
    path = Path(self.id().replace(".", "_") + ".nso")
    try:
      path.write_bytes(blob)
      parsed_header, metadata, parsed = decomp.parse_nso(path)
      self.assertEqual(parsed, segments)
      self.assertEqual(struct.unpack_from("<I", parsed_header, 0xC)[0] & 7, 0)
      self.assertEqual(metadata["segments"]["text"]["sha256"], hashlib.sha256(b"TEXT").hexdigest())
    finally:
      path.unlink(missing_ok=True)

  def test_analysis_elf_contains_aarch64_load_segments(self):
    segments = {"text": b"TEXT", "rodata": b"RO!", "data": b"DA"}
    metadata = {
      "bss_size": 0x20,
      "segments": {
        "text": {
          "memory_offset": 0
        },
        "rodata": {
          "memory_offset": 0x1000
        },
        "data": {
          "memory_offset": 0x2000
        },
      },
    }
    elf = decomp.pack_analysis_elf(metadata, segments)
    self.assertEqual(elf[:4], b"\x7fELF")
    self.assertEqual(struct.unpack_from("<H", elf, 18)[0], 183)
    self.assertEqual(struct.unpack_from("<H", elf, 56)[0], 3)
    self.assertEqual(elf[0x1000:0x1004], b"TEXT")

  def test_stale_ghidra_lock_is_recovered(self):
    with tempfile.TemporaryDirectory() as directory:
      project = Path(directory)
      (project / "totk.lock").write_text("stale")
      (project / "totk.lock~").touch()
      self.assertTrue(decomp.recover_stale_ghidra_lock(project))
      self.assertFalse((project / "totk.lock").exists())
      self.assertFalse((project / "totk.lock~").exists())

if __name__ == "__main__":
  unittest.main()
