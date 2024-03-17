#include "heap_map.h"

#include <assert.h>
#include <string.h>
#include <sys/mman.h>

#include "logging.h"

HeapMap* heap_map_new(size_t size) {
    assert(size != 0x0);
    if (size <= sizeof(HeapMap))
        return NULL;
    void* map_page = mmap(NULL, size, PROT_READ | PROT_WRITE, MAP_PRIVATE | MAP_ANONYMOUS, -1, 0);
    if (map_page == MAP_FAILED) {
        return NULL;
    }

    HeapMap* map = (HeapMap*)map_page;
    map->base = map_page + sizeof(HeapMap);
    map->size = size - sizeof(HeapMap);
    map->head = map->base;
    return map;
}

int heap_map_destroy(HeapMap* map) {
    int ret = munmap(map->base - sizeof(HeapMap), map->size + sizeof(HeapMap));
    if (ret == -1) {
        return -1;
    }
    map = NULL;
    return 0;
}

// TODO: Refactor and improve this algorithm/design. Right now i just want it to
// work.
int heap_map_insert(HeapMap* map, AllocationDesc* allocation) {
    // Just insert it at head.
    if ((void*)(map->head + 1) > (void*)(map->base + map->size)) {
        // We don't have enough memory left...
        return -1;
    }
    *map->head = *allocation;
    map->head += 1;
    return 0;
}

int heap_map_remove(HeapMap* map, DeallocationDesc* deallocation) {
    AllocationDesc* allocation = heap_map_search(map, &deallocation->chunk);
    if (allocation == NULL)
        return -1;
    for (; allocation < map->head - 1; allocation += 1) {
        memcpy(allocation, allocation + 1, sizeof(AllocationDesc));
    }
    // theoretically we don't need this memset, so for performance we could delete
    // it. We only need the head update.
    memset(allocation, 0x0, sizeof(AllocationDesc));
    map->head = allocation;
    return 0;
}

void heap_map_clear(HeapMap* map) {
    map->head = map->base;
}

CapacityDesc heap_map_capacity(HeapMap* map) {
    size_t total_bytes = map->size;
    size_t free_bytes = (map->base - (void*)map->head) + map->size;
    size_t total_entries = total_bytes / sizeof(HeapMap);
    size_t free_entries = free_bytes / sizeof(HeapMap);
    CapacityDesc capacity_desc = {.total_bytes = total_bytes, .free_bytes = free_bytes, .total_entries = total_entries, .free_entries = free_entries};
    return capacity_desc;
}

typedef struct {
    Chunk* chunk;
    AllocationDesc* found;
} SearchData;
int search(AllocationDesc* allocation, void* data) {
    SearchData* comparison_data = (SearchData*)data;
    if (allocation->chunk.address == comparison_data->chunk->address) {
        comparison_data->found = allocation;
        return -1;
    }
}
AllocationDesc* heap_map_search(HeapMap* map, Chunk* chunk) {
    SearchData search_data = {.chunk = chunk, .found = NULL};
    heap_map_for_each(map, search, &search_data);
    return search_data.found;
}

void heap_map_for_each(HeapMap* map, int (*f)(AllocationDesc*, void*), void* data) {
    for (AllocationDesc* ptr = map->base; ptr < map->head; ptr += 1) {
        if (f(ptr, data) == -1) {
            return;
        }
    }
}

void heap_map_for_each_in_range(HeapMap* map, Chunk* start_chunk, Chunk* end_chunk, int (*f)(AllocationDesc*, void*), void* data) {
    for (AllocationDesc* ptr = map->base; ptr < map->head; ptr += 1) {
        if (start_chunk->address <= ptr->chunk.address && ptr->chunk.address <= end_chunk->address) {
            if (f(ptr, data) == -1) {
                return;
            }
        }
    }
}