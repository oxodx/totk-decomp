#include "ByteRange.h"

extern "C" bool isAsciiWhitespace(int character);

extern "C" ByteRange trimAsciiWhitespace(const ByteRange* range) {
  ByteRange result = *range;
  while (result.begin < result.end && isAsciiWhitespace(*result.begin))
    ++result.begin;
  while (result.begin < result.end && isAsciiWhitespace(result.end[-1]))
    --result.end;
  return result;
}
