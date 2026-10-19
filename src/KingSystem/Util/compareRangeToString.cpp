#include "ByteRange.h"

extern "C" int stringLength(const char* text);
extern "C" int compareMemory(const void* left, const void* right, unsigned long size);

extern "C" __attribute__((minsize)) int compareRangeToString(const ByteRange* range,
                                                             const char* text) {
  const unsigned char* const textBytes = reinterpret_cast<const unsigned char*>(text);
  const unsigned long textSize = text == nullptr ? 0 : stringLength(text);
  const unsigned char* const textEnd = text == nullptr ? nullptr : textBytes + textSize;

  if (range->begin == textBytes) {
    if (range->end == textEnd)
      return 0;
    return range->end < textEnd ? -1 : 1;
  }

  const unsigned long rangeSize = range->end - range->begin;
  const unsigned long commonSize = rangeSize < textSize ? rangeSize : textSize;
  const int comparison = compareMemory(range->begin, textBytes, commonSize);
  if (comparison != 0)
    return comparison < 0 ? -1 : 1;
  if (rangeSize == textSize)
    return 0;
  return rangeSize < textSize ? -1 : 1;
}
