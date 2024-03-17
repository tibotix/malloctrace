import gdb
from malloctrace.environment import inferior_get_env, inferior_set_env, get_ld_preload, set_ld_preload
from malloctrace.logging import _blue
from malloctrace.constants import DEFAULT_MAP_SIZE, DEFAULT_LOG_LEVEL


class HeapMapSizeParam(gdb.Parameter):
    """The Heap Map size of malloctrace in bytes.\nNote that for the changes to take place you have to restart your program."""

    def __init__(self):
        super().__init__("malloctrace-heap-size", gdb.COMMAND_DATA, gdb.PARAM_UINTEGER)
        # TODO: maybe persist these settings across gdb starts
        self.value = int(inferior_get_env("MALLOCTRACE_MAP_SIZE") or DEFAULT_MAP_SIZE)

    def get_set_string(self):
        inferior_set_env("MALLOCTRACE_MAP_SIZE", str(self.value))
        return ""
    
    def get_show_string(self, svalue):
        return f"total capacity: {_blue(hex(self.value))} bytes"

MALLOCTRACE_HEAP_SIZE_PARAM = HeapMapSizeParam()


class LibraryPathParam(gdb.Parameter):
    """This is the library path to libmalloctrace.so.\nIt is used to inject libmalloctrace.so in a new process using LD_PRELOAD."""

    def __init__(self):
        super().__init__("malloctrace-library-path", gdb.COMMAND_DATA, gdb.PARAM_STRING)
        self.value = "libmalloctrace.so"
        self.old_value = self.value
    
    def get_set_string(self):
        ld_preload = get_ld_preload()
        if self.old_value in ld_preload:
            ld_preload.remove(self.old_value)
        if self.value not in ld_preload:
            ld_preload.add(self.value)
        set_ld_preload(ld_preload)
        self.old_value = self.value
        return ""

    def get_show_string(self, svalue):
        return f"current library-path: '{svalue}'"

MALLOCTRACE_OBJFILE_NAME_PARAM = LibraryPathParam()
