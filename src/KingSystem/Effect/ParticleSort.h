#pragma once

struct ParticleSortEntry {
  float key;
  int particleIndex;
};

static_assert(sizeof(ParticleSortEntry) == 8);
