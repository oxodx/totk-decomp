extern "C" int stringLength(const char* text);
extern "C" int compareMemory(const void* left, const void* right, unsigned long size);

extern "C" bool equalsBytes(const void* left, unsigned long size, const char* right) {
  if (right == nullptr)
    return size == 0;
  if (static_cast<unsigned long>(stringLength(right)) != size)
    return false;
  return compareMemory(left, right, size) == 0;
}
