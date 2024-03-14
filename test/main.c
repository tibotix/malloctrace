#include <assert.h>
#include <limits.h>
#include <malloc.h>
#include <stdio.h>
#include <stdlib.h>

int main(int argc, char** argv) {
  if (argc != 3) {
    printf("Usage: %s <malloc-count> <chunk-size>\n", argv[0]);
    exit(0);
  }

  size_t malloc_count = strtoul(argv[1], NULL, 10);
  size_t malloc_size = strtoul(argv[2], NULL, 10);

  if (malloc_count == ULONG_MAX || malloc_size == ULONG_MAX) {
    printf("Failed converting arguments to integers.\n");
    exit(0);
  }

  void** array = malloc(malloc_count * 8);
  assert(array != NULL);
  for (int i = 0; i < malloc_count; ++i) {
    array[i] = malloc(malloc_size);
    printf("malloced %p\n", array[i]);
    assert(array[i] != NULL);
  }
  for (int i = 0; i < malloc_count; ++i) {
    printf("freeing %p\n", array[i]);
    free(array[i]);
  }
  free(array);
}