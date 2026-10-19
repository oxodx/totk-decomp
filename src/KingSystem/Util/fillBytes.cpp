extern "C" void fillBytesImpl(void* destination, int value, unsigned long count);

extern "C" void fillBytes(void* destination, int value, unsigned int count) {
  fillBytesImpl(destination, value, count);
}
