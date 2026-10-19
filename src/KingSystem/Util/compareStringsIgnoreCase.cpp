namespace {
unsigned char lowerAscii(unsigned char character) {
  if (character >= 'A' && character <= 'Z')
    return character + ('a' - 'A');
  return character;
}
}  // namespace

extern "C" __attribute__((minsize)) int compareStringsIgnoreCase(const char* left,
                                                                 const char* right) {
  for (;;) {
    const unsigned char rawLeft = *left;
    const unsigned char rawRight = *right;
    if (rawLeft == '\0')
      return rawRight == '\0' ? 0 : -1;
    if (rawRight == '\0')
      return 1;

    const unsigned char leftCharacter = lowerAscii(rawLeft);
    const unsigned char rightCharacter = lowerAscii(rawRight);
    if (leftCharacter < rightCharacter)
      return -1;
    if (leftCharacter > rightCharacter)
      return 1;
    ++left;
    ++right;
  }
}
