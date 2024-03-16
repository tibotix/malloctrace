from malloctrace.command import command, argparser
from malloctrace.exceptions import on_error_show_error_message
from malloctrace.common import get_malloctrace_objfile, has_process, assert_malloctrace_loaded, MALLOCTRACE_OBJFILE_NAME, ERR_CODES, get_symbol_for_address, bt_line_for_address
from malloctrace.environment import get_ld_preload, set_ld_preload
from malloctrace.ctypedefs import *
from malloctrace.logging import _address, _highlight, _function, _filename, _reset, _color_bool, _blue, malloctrace_warning, malloctrace_info


@command.GDBPrefixCommand("malloctrace", "Trace Heap", aliases=["mtrace", "mtr"])
def malloctrace(_):
    return


@command.GDBSubCommand("malloctrace on", "enable malloctrace", short_description="enable malloctrace")
@on_error_show_error_message(ValueError)
def malloctrace_on(_):
    ld_preload = get_ld_preload()
    if MALLOCTRACE_OBJFILE_NAME not in ld_preload:
        ld_preload.add(MALLOCTRACE_OBJFILE_NAME)
        set_ld_preload(ld_preload)

    if has_process():
        if get_malloctrace_objfile() is not None:
            MALLOCTRACE_ACTIVE.set(1)
            return
        malloctrace_warning("No Malloctrace objfile present. The change will take place only after you restart your program.")


@command.GDBSubCommand("malloctrace off", "disable malloctrace", short_description="disable malloctrace")
@on_error_show_error_message(ValueError)
def malloctrace_off(_):
    ld_preload = get_ld_preload()
    if MALLOCTRACE_OBJFILE_NAME  in ld_preload:
        ld_preload.remove(MALLOCTRACE_OBJFILE_NAME)
        set_ld_preload(ld_preload)

    if has_process():
        if get_malloctrace_objfile() is not None:
            MALLOCTRACE_ACTIVE.set(0)
            return
        malloctrace_warning("No Malloctrace objfile present. The change will take place only after you restart your program.")


@command.GDBSubCommand("malloctrace clear", "clear the heap map", short_description="clear the heap map")
@on_error_show_error_message(ValueError)
def malloctrace_clear(_):
    assert_malloctrace_loaded()
    heap_map = MALLOCTRACE_HEAP_MAP.get_dereferenced_cvar()
    base = heap_map.get_field("base")
    heap_map.set_field("head", base)


@command.GDBSubCommand("malloctrace status", "show status", short_description="show status")
@on_error_show_error_message(Exception)
def malloctrace_status(_):
    assert_malloctrace_loaded()
    is_active = _color_bool(bool(MALLOCTRACE_ACTIVE.get()))
    err_code = MALLOCTRACE_ERR_CODE.get()
    err_code = ERR_CODES.get(err_code, "Unknown")
    print(f"Active: {str(is_active)}")
    print(f"Error code: {err_code!s}")

@command.GDBSubCommand("malloctrace capacity", "show heap map capacity", short_description="show heap map capacity")
@on_error_show_error_message(Exception)
def malloctrace_capacity(_):
    assert_malloctrace_loaded()
    heap_map = MALLOCTRACE_HEAP_MAP.get_dereferenced_cvar()
    base = heap_map.get_field("base")
    head = heap_map.get_field("head")
    size = heap_map.get_field("size")
    total_capacity = size
    free_capacity = (base + size) - head
    total_entries_capacity = total_capacity // MALLOCTRACE_HEAP_MAP.value_size_in_bytes
    free_entries_capacity = free_capacity // MALLOCTRACE_HEAP_MAP.value_size_in_bytes
    print(f"total capacity: {_blue(hex(total_capacity))} bytes / {_blue(hex(total_entries_capacity))} backtrace entries")
    print(f"free capacity: {_blue(hex(free_capacity))} bytes / {_blue(hex(free_entries_capacity))} backtrace entries")

parser = argparser.GDBArgumentParser(
    prog="malloctrace show",
    description="This command shows the traced heap map", 
    short_description="show heap map",
    add_help=False
)
parser.add_argument("start_addr")
parser.add_argument("end_addr")
@command.GDBSubCommand("malloctrace show", parser)
@on_error_show_error_message(Exception)
def malloctrace_show(args):
    # TODO: make this command not reapeating, and instead paginating
    assert_malloctrace_loaded()
    heap_map = MALLOCTRACE_HEAP_MAP.get_dereferenced_cvar()
    base = heap_map.get_field("base")
    head = heap_map.get_field("head")

    addr = base
    while addr < head:
        allocation_desc = AllocationDescCStruct(address=addr)
        chunk = allocation_desc.get_field("chunk")
        backtrace = allocation_desc.get_field("backtrace")

        chunk_addr = chunk["address"]
        chunk_size = chunk["size"]
        print(f"{_reset}------------------")
        print(f"{_reset}Chunk @ {_address(hex(chunk_addr))} - size: {hex(chunk_size)}")
        for index, frame_pc in enumerate(backtrace):
            print(f"{_reset}#{index!s}  {bt_line_for_address(frame_pc)}")

        addr += allocation_desc.value_size_in_bytes
