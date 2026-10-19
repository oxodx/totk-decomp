extern "C" unsigned int hashStringFnv1a(const unsigned char* text) {
  unsigned int hash = 0x811c9dc5;
  unsigned int character = *text;
  if (character == 0)
    return hash;

  do {
    ++text;
    hash = (hash ^ (character & 0xff)) * 0x01000193;
    character = *text;
  } while (character != 0);
  return hash;
}
