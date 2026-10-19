#include "OwnedString.h"

extern "C" char* cloneCString(const char* text);

extern "C" void copyOwnedString(OwnedString* destination, const OwnedString* source) {
  destination->taggedPointer = 0;
  const unsigned long sourcePointer = source->taggedPointer & cOwnedStringPointerMask;
  if (sourcePointer != 0) {
    destination->taggedPointer =
      reinterpret_cast<unsigned long>(cloneCString(reinterpret_cast<const char*>(sourcePointer))) |
      cOwnedStringFlag;
  }
}
