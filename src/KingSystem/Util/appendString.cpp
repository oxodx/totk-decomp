extern "C" void insertStringRange(void* string, int position, const char* source, int sourceLength);

extern "C" void appendString(void* string, const char* source) {
  if (source == nullptr)
    return;

  const int size = *reinterpret_cast<const int*>(static_cast<const unsigned char*>(string) + 8);
  insertStringRange(string, size - 1, source, -1);
}
