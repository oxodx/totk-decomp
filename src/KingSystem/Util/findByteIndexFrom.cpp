#include "ByteRange.h"

extern "C" const void* findByteInRange(const void* data, int value, unsigned long size);

extern "C" __attribute__((minsize)) int findByteIndexFrom(const ByteRange* range, int value,
                                                          int startIndex) {
  const unsigned char* const start = range->begin + startIndex;
  const void* const found = findByteInRange(start, value, range->end - start);
  if (found == nullptr)
    return -1;
  return static_cast<int>(static_cast<const unsigned char*>(found) - range->begin);
}
