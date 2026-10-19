#include "ParticleSort.h"

namespace {
[[gnu::always_inline]] bool comesBefore(const ParticleSortEntry& left,
                                        const ParticleSortEntry& right) {
  if (left.key != right.key)
    return left.key < right.key;
  return left.particleIndex < right.particleIndex;
}

[[gnu::always_inline]] void siftDown(ParticleSortEntry* entries, unsigned long count,
                                     unsigned long root) {
  const ParticleSortEntry value = entries[root];
  for (;;) {
    unsigned long child = root * 2 + 1;
    if (child >= count)
      break;
    if (child + 1 < count && comesBefore(entries[child], entries[child + 1]))
      ++child;
    if (!comesBefore(value, entries[child]))
      break;
    entries[root] = entries[child];
    root = child;
  }
  entries[root] = value;
}
}  // namespace

extern "C" void sortParticleEntriesAscending(ParticleSortEntry* begin, ParticleSortEntry* end,
                                             const void*) {
  const unsigned long count = end - begin;
  if (count < 2)
    return;

  for (unsigned long root = count / 2; root != 0;)
    siftDown(begin, count, --root);

  for (unsigned long remaining = count - 1; remaining != 0; --remaining) {
    const ParticleSortEntry first = begin[0];
    begin[0] = begin[remaining];
    begin[remaining] = first;
    siftDown(begin, remaining, 0);
  }
}
