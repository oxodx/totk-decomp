extern "C" const char* locateCharacter(const char* text, int character);

extern "C" int findCharacterIndex(const char* text, int character) {
  const char* result = locateCharacter(text, static_cast<unsigned char>(character));
  return result != nullptr ? static_cast<int>(result - text) : -1;
}
