namespace {
unsigned char toLowerAscii(unsigned char character) {
  if (character >= 'A' && character <= 'Z')
    return character + ('a' - 'A');
  return character;
}
}  // namespace

// Finds an ASCII case-insensitive substring and returns its byte index.
extern "C" __attribute__((minsize)) int findSubstringIgnoreCase(const char* const* text,
                                                                const char* needle) {
  const unsigned char* haystack = reinterpret_cast<const unsigned char*>(*text);
  if (*haystack == '\0')
    return -1;
  if (*needle == '\0')
    return 0;

  for (int index = 0; haystack[index] != '\0'; ++index) {
    const unsigned char* left = haystack + index;
    const unsigned char* right = reinterpret_cast<const unsigned char*>(needle);
    while (toLowerAscii(*left) == toLowerAscii(*right)) {
      ++left;
      ++right;
      if (*right == '\0')
        return index;
    }
  }
  return -1;
}
