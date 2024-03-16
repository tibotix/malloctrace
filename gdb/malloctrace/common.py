from typing import Optional
import gdb
from malloctrace.logging import _address, _function, _filename


# TODO: let the user change this
# MALLOCTRACE_OBJFILE_NAME = "libmalloctrace.so"
# NOTE: Only for development
MALLOCTRACE_OBJFILE_NAME = "/home/tibotix/Projects/malloctrace/build/libmalloctrace.so"
MAX_BACKTRACE_FRAMES = 0x4

ERR_CODES = {
    -1: "ERR_UNITIIALIZED",
    0: "ERR_NONE",
    1: "ERR_MAP_SIZE",
    2: "ERR_MAP_ALLOC",
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

def get_symbol_for_address(address):
    symbol = gdb.execute(f"info symbol {hex(address)}", to_string=True)
    if symbol.startswith("No symbol"):
      return "<Unknwon>"
    symbol = symbol.split(" ", 3)
    offset = '+' + hex(int(symbol[2])) if symbol[1] == '+' else ""
    return f"{symbol[0]}{offset}"

def bt_line_for_address(address):
    sal = gdb.current_progspace().find_pc_line(address)
    symbol = _function(get_symbol_for_address(address))
    address = _address(hex(address))
    if sal.symtab is None:
        return f"{address} in {symbol} ()"
    source_line = sal.line
    source_file = sal.symtab.filename
    return f"{address} in {symbol} () at {_filename(source_file)}:{source_line}"