extern "C" int compareStrings(const char *left, const char *right);

extern "C" int stringEquals(const char *const *left, const char *right) {
  return compareStrings(*left, right);
}
