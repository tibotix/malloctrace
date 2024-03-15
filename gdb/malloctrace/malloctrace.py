from malloctrace.command import command, argparser
from malloctrace.exceptions import on_error_show_message, on_error_show_error_message
from malloctrace.common import get_malloctrace_objfile, has_process, assert_malloctrace_loaded, MALLOCTRACE_OBJFILE_NAME, ERR_CODES
from malloctrace.environment import get_ld_preload, set_ld_preload
from malloctrace.ctypedefs import *


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
        print("No Malloctrace objfile present. The change will take place only after you restart your program.")


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
        print("No Malloctrace objfile present. The change will take place only after you restart your program.")


@command.GDBSubCommand("malloctrace clear", "clear the heap map", short_description="clear the heap map")
def malloctrace_clear(_):
    heap_map = MALLOCTRACE_HEAP_MAP.get_dereferenced_cvar()
    base = heap_map.get_field("base")
    heap_map.set_field("head", base)


@command.GDBSubCommand("malloctrace status", "show status", short_description="show status")
@on_error_show_error_message(Exception)
def malloctrace_status(_):
    assert_malloctrace_loaded()
    is_active = bool(MALLOCTRACE_ACTIVE.get())
    err_code = MALLOCTRACE_ERR_CODE.get()
    err_code = ERR_CODES.get(err_code, "Unknown")
    print(f"Active: {str(is_active)}")
    print(f"Error code: {err_code!s}")


parser = argparser.GDBArgumentParser(
    prog="malloctrace show",
    description="This command shows the traced heap map", 
    short_description="show heap map",
    add_help=False
)
parser.add_argument("start_addr")
parser.add_argument("end_addr")
@command.GDBSubCommand("malloctrace show", parser)
def malloctrace_show(args):
    heap_map = MALLOCTRACE_HEAP_MAP.get_dereferenced_cvar()
    base = heap_map.get_field("base")
    head = heap_map.get_field("head")

    addr = base
    while addr < head:
        allocation_desc = AllocationDescCStruct(address=addr)
        chunk = allocation_desc.get_field("chunk")
        bt_0 = allocation_desc.get_field("bt_0")
        bt_1 = allocation_desc.get_field("bt_1")
        print(f"addr: {hex(addr)}")
        print(f"chunk: {chunk!s}")
        print(f"bt_0: {bt_0!s}")
        print(f"bt_1: {bt_1!s}")
        addr += allocation_desc.value_size_in_bytes