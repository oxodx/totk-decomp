// Returns the byte index of the last matching character, or -1 when absent.

extern "C" const char *findCharacter(const char *text, int character);

extern "C" int findLastCharacterIndex(const char *const *text, int character) {
  const char *const start = *text;
  const char *found = findCharacter(start, character);
  if (found == nullptr)
    return -1;

  const char *last;
  do {
    last = found;
    found = findCharacter(last + 1, character);
  } while (found != nullptr);

  return static_cast<int>(last - start);
}
