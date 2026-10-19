#include "ByteRange.h"

extern "C" int compareMemory(const void* left, const void* right, unsigned long size);

extern "C" bool rangesEqual(const ByteRange* left, const ByteRange* right) {
  const unsigned long leftSize = left->end - left->begin;
  const unsigned long rightSize = right->end - right->begin;
  return leftSize == rightSize && compareMemory(left->begin, right->begin, leftSize) == 0;
}
