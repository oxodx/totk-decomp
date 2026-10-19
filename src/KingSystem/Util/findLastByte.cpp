#include "ByteRange.h"

extern "C" __attribute__((minsize)) const unsigned char* findLastByte(const ByteRange* range,
                                                                      int value) {
  const unsigned char* cursor = range->end;
  while (cursor != range->begin) {
    --cursor;
    if (*cursor == value)
      return cursor;
  }
  return nullptr;
}
