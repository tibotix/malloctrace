

#include <stdarg.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

void malloctrace_error(char* fmt, ...) {
    fprintf(stderr, "!!! ERROR: ");
    va_list args;
    va_start(args, fmt);
    vfprintf(stderr, fmt, args);
    va_end(args);

    fflush(stderr);
}

void malloctrace_info(char* fmt, ...) {
    fprintf(stdout, "--- ");
    va_list args;
    va_start(args, fmt);
    vfprintf(stdout, fmt, args);
    va_end(args);

    fflush(stdout);
}


// TODO: conditionally activate/deactivate