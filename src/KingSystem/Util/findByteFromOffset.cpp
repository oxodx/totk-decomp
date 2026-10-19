#include "ByteRange.h"

extern "C" const void* findByteInRange(const void* data, int value, unsigned long size);

extern "C" const unsigned char* findByteFromOffset(const ByteRange* range, int value,
                                                   unsigned long offset) {
  const unsigned long size = range->end - range->begin;
  if (offset >= size)
    return nullptr;
  return static_cast<const unsigned char*>(
    findByteInRange(range->begin + offset, value, size - offset));
}
