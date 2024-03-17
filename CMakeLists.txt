cmake_minimum_required(VERSION 3.13)

project(malloctrace)

file(GLOB malloctrace_sources "src/*.c")
add_library(malloctrace SHARED ${malloctrace_sources})

# Note: you may need to run ldconfig first to make
# libmalloctrace.so visible to the dynamic linker
install(TARGETS malloctrace)

# Somehow gdb does not find our symbols in the symtab section.
# So we need to add debug_info, otherwise we have no easy way of looking up symbols from gdb python api,
# as the current gdb python api does not expose the `lookup_minimal_symbol` functionality...
target_compile_options(malloctrace PRIVATE -g)

target_link_options(malloctrace PUBLIC -Wl,-z,relro,-z,now)