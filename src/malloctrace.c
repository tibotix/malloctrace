#define _GNU_SOURCE

#include "malloctrace.h"

#include <assert.h>
#include <dlfcn.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>

#include "backtrace.h"
#include "common.h"
#include "heap_map.h"
#include "logging.h"

HeapMap* MALLOCTRACE_HEAP_MAP;

#define ERR_UNINITIALIZED -1
#define ERR_OK 0
#define ERR_MAP_SIZE 1
#define ERR_MAP_ALLOC 2
int8_t MALLOCTRACE_ERR_CODE = ERR_UNINITIALIZED;

uint8_t MALLOCTRACE_ACTIVE = 0;
uint8_t MALLOCTRACE_DEPTH = 0;

uint8_t MALLOC_HOOK_ACTIVE = 1;
uint8_t REALLOC_HOOK_ACTIVE = 1;
uint8_t CALLOC_HOOK_ACTIVE = 1;
uint8_t FREE_HOOK_ACTIVE = 1;

#define DEFAULT_MAP_SIZE    0x4000
#define MAX_RECURSION_DEPTH 0x8

#define ENTER_HANDLER_SECTION(HOOK)       \
    assert(MALLOCTRACE_HEAP_MAP != NULL); \
    HOOK##_HOOK_ACTIVE = 0;               \
    MALLOCTRACE_DEPTH++;

#define LEAVE_HANDLER_SECTION(HOOK) \
    HOOK##_HOOK_ACTIVE = 1;         \
    MALLOCTRACE_DEPTH--;

//
// Initialization
//
static void malloctrace_init() {
    if (MALLOCTRACE_ERR_CODE == ERR_NONE)
        return;
    size_t heap_map_size = DEFAULT_MAP_SIZE;
    char* map_size;
    if ((map_size = getenv("MALLOCTRACE_MAP_SIZE")) != NULL) {
        heap_map_size = strtoul(map_size, NULL, 10);
    }
    MALLOCTRACE_HEAP_MAP = heap_map_new(heap_map_size);
    if (MALLOCTRACE_HEAP_MAP == NULL) {
        MALLOCTRACE_ERR_CODE = ERR_MAP_ALLOC;
        MALLOCTRACE_ACTIVE = 0;
        return;
    }
    MALLOCTRACE_ERR_CODE = ERR_NONE;
    MALLOCTRACE_ACTIVE = 1;
}

//
// Originals
//
static void* (*_original_malloc)(size_t);
static void (*_original_free)(void*);
static void* (*_original_calloc)(size_t, size_t);
static void* (*_original_realloc)(void*, size_t);
__attribute__((constructor)) void malloctrace_patch_functions() {
    _original_malloc = dlsym(RTLD_NEXT, "malloc");
    _original_free = dlsym(RTLD_NEXT, "free");
    _original_calloc = dlsym(RTLD_NEXT, "calloc");
    _original_realloc = dlsym(RTLD_NEXT, "realloc");

    malloctrace_init();
}

void* malloc(size_t size) {
    if (!_original_malloc)
        malloctrace_patch_functions();
    if (MALLOCTRACE_ERR_CODE != ERR_NONE)
        malloctrace_init();
    void* ptr = _original_malloc(size);
    handle_malloc(ptr, size);
    return ptr;
}

void free(void* ptr) {
    if (!_original_free)
        malloctrace_patch_functions();
    if (MALLOCTRACE_ERR_CODE != ERR_NONE)
        malloctrace_init();
    _original_free(ptr);
    handle_free(ptr);
}

void* calloc(size_t nmemb, size_t size) {
    if (!_original_calloc)
        malloctrace_patch_functions();
    if (MALLOCTRACE_ERR_CODE != ERR_NONE)
        malloctrace_init();
    void* ptr = _original_calloc(nmemb, size);
    handle_calloc(ptr, nmemb, size);
    return ptr;
}

void* realloc(void* ptr, size_t size) {
    if (!_original_realloc)
        malloctrace_patch_functions();
    if (MALLOCTRACE_ERR_CODE != ERR_NONE)
        malloctrace_init();
    void* new_ptr = _original_realloc(ptr, size);
    handle_realloc(new_ptr, ptr, size);
    return new_ptr;
}

//
// Handlers
//
// TODO: Add pthread mutex support for thread safety
ALWAYS_INLINE static void handle_malloc(void* ptr, size_t size) {
    if (!MALLOCTRACE_ACTIVE || !MALLOC_HOOK_ACTIVE || MALLOCTRACE_DEPTH > MAX_RECURSION_DEPTH) {
        return;
    }
    if (ptr == NULL || size == 0x0)
        return;
    ENTER_HANDLER_SECTION(MALLOC);
    AllocationDesc allocation = {.chunk = {.address = ptr, .size = size}, .backtrace = get_backtrace()};
    if (heap_map_insert(MALLOCTRACE_HEAP_MAP, &allocation) == -1) {
        malloctrace_error("Couldn't insert into heap map: OutOfMemory!\n");
    }
    LEAVE_HANDLER_SECTION(MALLOC);
}

ALWAYS_INLINE static void handle_free(void* ptr) {
    if (!MALLOCTRACE_ACTIVE || !FREE_HOOK_ACTIVE || MALLOCTRACE_DEPTH > MAX_RECURSION_DEPTH) {
        return;
    }
    if (ptr == NULL)
        return;
    ENTER_HANDLER_SECTION(FREE);
    DeallocationDesc deallocation = {.chunk = {.address = ptr}};
    heap_map_remove(MALLOCTRACE_HEAP_MAP, &deallocation);
    LEAVE_HANDLER_SECTION(FREE);
}

ALWAYS_INLINE static void handle_calloc(void* ptr, size_t nmemb, size_t size) {
    if (!MALLOCTRACE_ACTIVE || !CALLOC_HOOK_ACTIVE || MALLOCTRACE_DEPTH > MAX_RECURSION_DEPTH) {
        return;
    }
    if (ptr == NULL || nmemb * size == 0x0)
        return;
    ENTER_HANDLER_SECTION(CALLOC);
    AllocationDesc allocation = {.chunk = {.address = ptr, .size = nmemb * size}, .backtrace = get_backtrace()};
    if (heap_map_insert(MALLOCTRACE_HEAP_MAP, &allocation) == -1) {
        malloctrace_error("Couldn't insert into heap map: OutOfMemory!\n");
    }
    LEAVE_HANDLER_SECTION(CALLOC);
}

ALWAYS_INLINE static void handle_realloc(void* new_ptr, void* ptr, size_t size) {
    if (!MALLOCTRACE_ACTIVE || !REALLOC_HOOK_ACTIVE || MALLOCTRACE_DEPTH > MAX_RECURSION_DEPTH) {
        return;
    }
    if (ptr == NULL) {
        handle_malloc(new_ptr, size);
        return;
    }
    if (size == 0x0) {
        handle_free(ptr);
        return;
    }
    ENTER_HANDLER_SECTION(REALLOC);
    if (new_ptr == ptr) {
        // only size was changed
        Chunk chunk = {.address = ptr};
        AllocationDesc* allocation = heap_map_search(MALLOCTRACE_HEAP_MAP, &chunk);
        if (allocation != NULL) {
            allocation->chunk.size = size;
        }
    } else {
        handle_free(ptr);
        AllocationDesc allocation = {.chunk = {.address = new_ptr, .size = size}, .backtrace = get_backtrace()};
        heap_map_insert(MALLOCTRACE_HEAP_MAP, &allocation);
    }
    LEAVE_HANDLER_SECTION(REALLOC);
}