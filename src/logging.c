#include <stdarg.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
#include "logging.h"


uint8_t MALLOCTRACE_LOG_LEVEL = LOG_LEVEL_INFO;


void malloctrace_debug(char* fmt, ...) {
    if (MALLOCTRACE_LOG_LEVEL > LOG_LEVEL_DEBUG)
        return;
    fprintf(stdout, "[mtr_debug] ");
    va_list args;
    va_start(args, fmt);
    vfprintf(stdout, fmt, args);
    va_end(args);

    fflush(stdout);
}

void malloctrace_info(char* fmt, ...) {
    if (MALLOCTRACE_LOG_LEVEL > LOG_LEVEL_INFO)
        return;
    fprintf(stdout, "[mtr_info] ");
    va_list args;
    va_start(args, fmt);
    vfprintf(stdout, fmt, args);
    va_end(args);

    fflush(stdout);
}

void malloctrace_warning(char* fmt, ...) {
    if (MALLOCTRACE_LOG_LEVEL > LOG_LEVEL_WARNING)
        return;
    fprintf(stdout, "[mtr_warning] ");
    va_list args;
    va_start(args, fmt);
    vfprintf(stdout, fmt, args);
    va_end(args);

    fflush(stdout);
}

void malloctrace_error(char* fmt, ...) {
    if (MALLOCTRACE_LOG_LEVEL > LOG_LEVEL_ERROR)
        return;
    fprintf(stderr, "[mtr_error] ");
    va_list args;
    va_start(args, fmt);
    vfprintf(stderr, fmt, args);
    va_end(args);

    fflush(stderr);
}


__attribute__((constructor)) void malloctrace_logging_init() {
    char* log_level = getenv("MALLOCTRACE_LOG_LEVEL");
    if (log_level == NULL) {
        log_level = "error";
    }
    if (strcmp(log_level, "debug") == 0) {
        MALLOCTRACE_LOG_LEVEL = LOG_LEVEL_DEBUG;
    } else if (strcmp(log_level, "info") == 0) {
        MALLOCTRACE_LOG_LEVEL = LOG_LEVEL_INFO;
    } else if (strcmp(log_level, "warning") == 0) {
        MALLOCTRACE_LOG_LEVEL = LOG_LEVEL_WARNING;
    } else if (strcmp(log_level, "error") == 0) {
        MALLOCTRACE_LOG_LEVEL = LOG_LEVEL_ERROR;
    } else if (strcmp(log_level, "none") == 0) {
        MALLOCTRACE_LOG_LEVEL = LOG_LEVEL_NONE;
    }
}