extern "C" int compareStrings(const char* left, const char* right) {
  while (*right != '\0') {
    if (*left != *right)
      return 0;
    ++left;
    ++right;
  }
  return 1;
}
