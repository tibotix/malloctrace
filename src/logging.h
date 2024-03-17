#pragma once

#define LOG_LEVEL_DEBUG   0
#define LOG_LEVEL_INFO    1
#define LOG_LEVEL_WARNING 2
#define LOG_LEVEL_ERROR   3
#define LOG_LEVEL_NONE    0xff // because on uint8_t this is highest value

void malloctrace_error(char* fmt, ...);
void malloctrace_warning(char* fmt, ...);
void malloctrace_info(char* fmt, ...);
void malloctrace_debug(char* fmt, ...);
