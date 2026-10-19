extern "C" int stringLength(const char *text);

extern "C" bool endsWith(const char *text, const char *suffix) {
  const int textLength = stringLength(text);
  const int suffixLength = stringLength(suffix);
  if (textLength < suffixLength)
    return false;

  const char *tail = text + textLength - suffixLength;
  for (int index = 0; index < suffixLength; ++index) {
    if (tail[index] != suffix[index])
      return false;
  }
  return true;
}
