#pragma once

#include <execinfo.h>
#include <stddef.h>

#include "backtrace.h"

typedef struct {
    void* address;
    size_t size;
} Chunk;

typedef struct {
    Chunk chunk;
    bt backtrace;
} AllocationDesc;

typedef struct {
    Chunk chunk;
} DeallocationDesc;

typedef struct {
    void* base;
    size_t size;
    AllocationDesc* head;
} HeapMap;

typedef struct {
    size_t free_bytes;
    size_t free_entries;
    size_t total_bytes;
    size_t total_entries;
} CapacityDesc;

HeapMap* heap_map_new(size_t size);
int heap_map_destroy(HeapMap* map);

int heap_map_insert(HeapMap* map, AllocationDesc* allocation);
int heap_map_remove(HeapMap* map, DeallocationDesc* chunk);
void heap_map_clear(HeapMap* map);
CapacityDesc heap_map_capacity(HeapMap* map);

AllocationDesc* heap_map_search(HeapMap* map, Chunk* chunk);
void heap_map_for_each(HeapMap* map, int (*f)(AllocationDesc*, void*), void* data);
void heap_map_for_each_in_range(HeapMap* map, Chunk* start_chunk, Chunk* end_chunk, int (*f)(AllocationDesc*, void*), void* data);