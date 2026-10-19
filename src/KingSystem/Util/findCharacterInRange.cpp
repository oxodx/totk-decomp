extern "C" int findCharacterInRange(const char* text, int character, int begin, int end) {
  if (begin >= 1) {
    for (int index = 0; index < begin; ++index) {
      if (text[index] == '\0')
        return -1;
    }
  }

  for (int index = begin; index < end; ++index) {
    if (text[index] == '\0')
      return -1;
    if (static_cast<unsigned char>(text[index]) == static_cast<unsigned char>(character))
      return index;
  }
  return -1;
}
