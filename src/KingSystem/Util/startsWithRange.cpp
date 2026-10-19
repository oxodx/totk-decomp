#include "ByteRange.h"

extern "C" int compareMemory(const void* left, const void* right, unsigned long size);

extern "C" bool startsWithRange(const ByteRange* range, const ByteRange* prefix) {
  const unsigned long rangeSize = range->end - range->begin;
  const unsigned long prefixSize = prefix->end - prefix->begin;
  return rangeSize >= prefixSize && compareMemory(range->begin, prefix->begin, prefixSize) == 0;
}
