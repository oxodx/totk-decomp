extern "C" void *copyMemory(void *destination, const void *source,
                            unsigned long size);

extern "C" void copyBytesIfPresent(void *destination, void *,
                                   const void *source, int size) {
  if (size >= 1)
    copyMemory(destination, source, static_cast<unsigned int>(size));
}
