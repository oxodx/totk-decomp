#pragma once

struct OwnedString {
  unsigned long taggedPointer;
};

static constexpr unsigned long cOwnedStringFlag = 1;
static constexpr unsigned long cOwnedStringPointerMask = ~cOwnedStringFlag;
