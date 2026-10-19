extern "C" bool isNullOrEmpty(const char *text) {
  return text == nullptr || *text == '\0';
}
