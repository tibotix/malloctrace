#pragma once

#include <stddef.h>

static void malloctrace_init();
static void handle_malloc(void *ptr, size_t size);
static void handle_free(void *ptr);
static void handle_calloc(void *ptr, size_t nmemb, size_t size);
static void handle_realloc(void *new_ptr, void *ptr, size_t size);