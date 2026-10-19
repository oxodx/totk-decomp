#include "ByteRange.h"

extern "C" int compareMemory(const void* left, const void* right, unsigned long size);

extern "C" __attribute__((minsize)) const unsigned char*
findByteSequence(const ByteRange* range, const unsigned char* needleBegin,
                 const unsigned char* needleEnd, unsigned long startOffset) {
  const unsigned long needleSize = needleEnd - needleBegin;
  if (needleSize == 0)
    return range->begin;

  const unsigned long size = range->end - range->begin;
  if (needleSize + startOffset > size)
    return nullptr;

  const unsigned char* candidate = range->begin + startOffset;
  const unsigned char* const last = range->end - needleSize;
  for (;;) {
    if (compareMemory(candidate, needleBegin, needleSize) == 0)
      return candidate;
    if (candidate == last)
      return nullptr;
    ++candidate;
  }
}
