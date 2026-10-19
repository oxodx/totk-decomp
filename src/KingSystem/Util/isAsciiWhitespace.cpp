extern "C" bool isAsciiWhitespace(int character) {
  switch (static_cast<unsigned char>(character)) {
  case '\t':
  case '\n':
  case '\r':
  case ' ':
    return true;
  default:
    return false;
  }
}
