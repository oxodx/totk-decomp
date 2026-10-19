#include "OwnedString.h"

extern "C" void freeCString(char* text);

extern "C" void destroyOwnedString(OwnedString* string) {
  const unsigned long pointer = string->taggedPointer & cOwnedStringPointerMask;
  if (pointer != 0)
    freeCString(reinterpret_cast<char*>(pointer));
}
