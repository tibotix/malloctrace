#include "heap_map.h"

#include <assert.h>
#include <string.h>
#include <sys/mman.h>

#include "logging.h"

void* MALLOCTRACE_DEBUG_MAP_PAGE = 0x0;

HeapMap* heap_map_new(size_t size) {
  assert(size != 0x0);
  if (size <= sizeof(HeapMap)) return NULL;
  void* map_page = mmap(NULL, size, PROT_READ | PROT_WRITE,
                        MAP_PRIVATE | MAP_ANONYMOUS, -1, 0);
  MALLOCTRACE_DEBUG_MAP_PAGE = map_page;
  if (map_page == MAP_FAILED) {
    return NULL;
  }

  HeapMap* map = (HeapMap*)map_page;
  map->base = map_page + sizeof(HeapMap);
  map->size = size - sizeof(HeapMap);
  map->head = map->base;
  return map;
}

// TODO: Refactor and improve this algorithm/design. Right now i just want it to
// work.
int heap_map_insert(HeapMap* map, AllocationDesc* allocation) {
  // Just insert it at head.
  if (map->head + 1 > map->base + map->size) {
    // We don't have enough memory left...
    return -1;
  }
  *map->head = *allocation;
  map->head += 1;
  return 0;
}

int heap_map_remove(HeapMap* map, DeallocationDesc* deallocation) {
  AllocationDesc* allocation = heap_map_search(map, &deallocation->chunk);
  if (allocation == NULL) return -1;
  for (; allocation < map->head - 1; allocation += 1) {
    memcpy(allocation, allocation + 1, sizeof(AllocationDesc));
  }
  // theoretically we don't need this memset, so for performance we could delete
  // it. We only need the head update.
  memset(allocation, 0x0, sizeof(AllocationDesc));
  map->head = allocation;
  return 0;
}

AllocationDesc* heap_map_search(HeapMap* map, Chunk* chunk) {
  for (AllocationDesc* ptr = map->base; ptr < map->head; ptr += 1) {
    if (ptr->chunk.address == chunk->address) {
      return ptr;
    }
  }
  return NULL;
}

int heap_map_destroy(HeapMap* map) {
  int ret = munmap(map->base - sizeof(HeapMap), map->size + sizeof(HeapMap));
  if (ret == -1) {
    return -1;
  }
  map = NULL;
  return 0;
}

void heap_map_clear(HeapMap* map) {
  // []
}