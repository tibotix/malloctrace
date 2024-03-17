from typing import Optional
import gdb
from malloctrace.logging import _address, _function, _filename, malloctrace_warning
from malloctrace.params import MALLOCTRACE_OBJFILE_NAME_PARAM


def get_malloctrace_objfile() -> Optional[gdb.Objfile]:
    try:
        return gdb.lookup_objfile(MALLOCTRACE_OBJFILE_NAME_PARAM.value)
    except ValueError:
        return None

def has_malloctrace_objfile_loaded() -> bool:
    return get_malloctrace_objfile() is not None

def warn_no_malloctrace_objfile_loaded_and_defered_change():
    malloctrace_warning("No Malloctrace objfile present. The change will take place only after you restart your program.")

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

def parse_number(number: str) -> int:
    if not isinstance(number, str):
        raise ValueError(f"{number!s} is not a string.")
    try:
        if number.startswith("0x"):
            return int(number[2:], 16)
        return int(number)
    except (ValueError, TypeError):
        raise ValueError(f"{number!s} is not a valid number")