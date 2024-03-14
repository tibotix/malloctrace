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

HeapMap* heap_map_new(size_t size);
int heap_map_insert(HeapMap* map, AllocationDesc* allocation);
int heap_map_remove(HeapMap* map, DeallocationDesc* chunk);
AllocationDesc* heap_map_search(HeapMap* map, Chunk* chunk);
int heap_map_destroy(HeapMap* map);
void heap_map_clear(HeapMap* map);