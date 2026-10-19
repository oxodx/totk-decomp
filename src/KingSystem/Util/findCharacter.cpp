extern "C" const char *findCharacterImpl(const char *text, int character);

extern "C" const char *findCharacter(const char *text, int character) {
  return findCharacterImpl(text, character);
}
