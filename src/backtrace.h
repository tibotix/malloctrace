#pragma once
#include <execinfo.h>
#include <stdint.h>

#include "common.h"

#define MAX_BACKTRACE_FRAMES 0x4

typedef struct {
  void* frames[MAX_BACKTRACE_FRAMES];
} bt;

ALWAYS_INLINE bt get_backtrace() {
  bt bt;
  int nptrs = backtrace(bt.frames, MAX_BACKTRACE_FRAMES);
  return bt;
}