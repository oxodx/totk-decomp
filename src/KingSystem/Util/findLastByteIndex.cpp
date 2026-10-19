#include "ByteRange.h"

extern "C" __attribute__((minsize)) int findLastByteIndex(const ByteRange* range, int value) {
  const unsigned char* cursor = range->end;
  while (cursor != range->begin) {
    --cursor;
    if (*cursor == value)
      return static_cast<int>(cursor - range->begin);
  }
  return -1;
}
