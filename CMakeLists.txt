cmake_minimum_required(VERSION 3.13)

project(malloctrace)

file(GLOB malloctrace_sources "src/*.c")
add_library(malloctrace SHARED ${malloctrace_sources})
# target_include_directories(malloctrace PUBLIC include)
target_link_options(malloctrace PUBLIC -Wl,-z,relro,-z,now)