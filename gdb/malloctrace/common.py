from typing import Optional
import gdb


# TODO: let the user change this
# MALLOCTRACE_OBJFILE_NAME = "libmalloctrace.so"
# NOTE: Only for development
MALLOCTRACE_OBJFILE_NAME = "/home/tibotix/Projects/malloctrace/build/libmalloctrace.so"
MAX_BACKTRACE_FRAMES = 0x4

ERR_CODES = {
    "-1": "ERR_UNITIIALIZED",
    "0": "ERR_OK",
    "1": "ERR_MAP_SIZE",
    "2": "ERR_MAP_ALLOC",
}


def get_malloctrace_objfile() -> Optional[gdb.Objfile]:
    try:
        return gdb.lookup_objfile(MALLOCTRACE_OBJFILE_NAME)
    except ValueError:
        return None

def has_process():
    inferior = gdb.selected_inferior()
    return inferior is not None and inferior.is_valid() and len(inferior.threads()) > 0

def assert_malloctrace_loaded():
    if not has_process():
        raise ValueError("No Program is running")
    if get_malloctrace_objfile() is None:
        raise ValueError("No Malloctrace objfile present")