from malloctrace.command import command, argparser
from malloctrace.exceptions import on_error_show_error_message
from malloctrace.common import get_malloctrace_objfile, has_process, assert_malloctrace_loaded, bt_line_for_address, has_malloctrace_objfile_loaded, warn_no_malloctrace_objfile_loaded_and_defered_change
from malloctrace.constants import ERR_CODES, LOG_LEVELS, REVERSE_LOG_LEVELS, DEFAULT_LOG_LEVEL
from malloctrace.environment import get_ld_preload, set_ld_preload, inferior_set_env, inferior_get_env
from malloctrace.ctypedefs import *
from malloctrace.logging import _address, _reset, _color_bool, _blue, malloctrace_warning, malloctrace_info, malloctrace_error
from malloctrace.params import MALLOCTRACE_OBJFILE_NAME_PARAM
from malloctrace.cbridge import c_heap_map_capacity, c_heap_map_clear, c_heap_map_for_each, c_heap_map_for_each_in_range


@command.GDBPrefixCommand("malloctrace", "Trace Heap", aliases=["mtrace", "mtr"])
def malloctrace(_):
    return


@command.GDBSubCommand("malloctrace on", "enable malloctrace", short_description="enable malloctrace")
@on_error_show_error_message(ValueError)
def malloctrace_on(_):
    ld_preload = get_ld_preload()
    if MALLOCTRACE_OBJFILE_NAME_PARAM.value not in ld_preload:
        ld_preload.add(MALLOCTRACE_OBJFILE_NAME_PARAM.value)
        set_ld_preload(ld_preload)

    if has_process():
        if has_malloctrace_objfile_loaded():
            MALLOCTRACE_ACTIVE.set(1)
            return
        warn_no_malloctrace_objfile_loaded_and_defered_change()


@command.GDBSubCommand("malloctrace off", "disable malloctrace", short_description="disable malloctrace")
@on_error_show_error_message(ValueError)
def malloctrace_off(_):
    ld_preload = get_ld_preload()
    if MALLOCTRACE_OBJFILE_NAME_PARAM.value  in ld_preload:
        ld_preload.remove(MALLOCTRACE_OBJFILE_NAME_PARAM.value)
        set_ld_preload(ld_preload)

    if has_process():
        if has_malloctrace_objfile_loaded():
            MALLOCTRACE_ACTIVE.set(0)
            return
        warn_no_malloctrace_objfile_loaded_and_defered_change()


parser = argparser.GDBArgumentParser(
    prog="malloctrace loglevel",
    description="get/set malloctrace log level", 
    short_description="get/set malloctrace log level",
    add_help=False,
)
parser.add_argument("log_level", help="Set current Log Level. Possibly values: 'none','debug','info','warning','error'.", nargs="?")
@command.GDBSubCommand("malloctrace loglevel", parser)
@on_error_show_error_message(ValueError)
def malloctrace_log_level(args):
    if args.log_level is None:
        # show
        if has_process() and has_malloctrace_objfile_loaded():
            log_level = LOG_LEVELS.get(MALLOCTRACE_LOG_LEVEL.get(), "Unknown")
        else:
            log_level = inferior_get_env("MALLOCTRACE_LOG_LEVEL") or DEFAULT_LOG_LEVEL
        print(f"{_reset}Log Level: {log_level!s}")
    else:
        # set
        if args.log_level not in REVERSE_LOG_LEVELS.keys():
            malloctrace_error(f"Unknown log level: '{args.log_level!s}'")
            return
        if has_process():
            if has_malloctrace_objfile_loaded():
                log_level = REVERSE_LOG_LEVELS.get(args.log_level)
                MALLOCTRACE_LOG_LEVEL.set(log_level)
                return
            warn_no_malloctrace_objfile_loaded_and_defered_change()
        else:
            inferior_set_env("MALLOCTRACE_LOG_LEVEL", args.log_level)


@command.GDBSubCommand("malloctrace clear", "clear the heap map", short_description="clear the heap map")
@on_error_show_error_message(ValueError)
def malloctrace_clear(_):
    c_heap_map_clear()


@command.GDBSubCommand("malloctrace status", "show status", short_description="show status")
@on_error_show_error_message(Exception)
def malloctrace_status(_):
    assert_malloctrace_loaded()
    is_active = _color_bool(bool(MALLOCTRACE_ACTIVE.get()))
    err_code = ERR_CODES.get(MALLOCTRACE_ERR_CODE.get(), "Unknown")
    log_level = LOG_LEVELS.get(MALLOCTRACE_LOG_LEVEL.get(), "Unknown")
    print(f"Active: {str(is_active)}")
    print(f"Error code: {err_code!s}")
    print(f"Log Level: {log_level!s}")


@command.GDBSubCommand("malloctrace capacity", "Show current heap map capacity", short_description="show current heap map capacity")
@on_error_show_error_message(Exception)
def malloctrace_capacity(args):
    capacity_desc = c_heap_map_capacity()
    print(f"total capacity: {_blue(hex(capacity_desc.total_bytes))} bytes / {_blue(hex(capacity_desc.total_entries))} backtrace entries")
    print(f"free capacity: {_blue(hex(capacity_desc.free_bytes))} bytes / {_blue(hex(capacity_desc.free_entries))} backtrace entries")


def print_allocation(allocation):
    chunk = allocation.chunk
    backtrace = allocation.backtrace

    chunk_addr = chunk.address
    chunk_size = chunk.size
    print(f"{_reset}------------------")
    print(f"{_reset}Chunk @ {_address(hex(chunk_addr))} - size: {hex(chunk_size)}")
    for index, frame_pc in enumerate(backtrace.frames):
        print(f"{_reset}#{index!s}  {bt_line_for_address(frame_pc)}")



# TODO: maybe make extra c function for this and call it
def heap_map_is_empty():
    capacity_desc = c_heap_map_capacity()
    return capacity_desc.free_bytes == capacity_desc.total_bytes

parser = argparser.GDBArgumentParser(
    prog="malloctrace show",
    description="This command shows the traced heap map", 
    short_description="show heap map",
    add_help=False
)
# TODO: allow hex value
parser.add_argument("start_addr", type=int, help="The address to begin with")
parser.add_argument("end_addr", type=int, help="The address to end with")
parser.add_argument("count", type=int, help="The number of chunks to print", nargs="?", default=10)
@command.GDBPrefixCommand("malloctrace show", parser)
@on_error_show_error_message(Exception)
def malloctrace_show(args):
    # TODO: make this command not reapeating, and instead paginating
    if heap_map_is_empty():
        malloctrace_info(f"No entries")
        return

    def f(allocation):
        print_allocation(allocation)
        args.count -= 1
        return args.count != 0

    c_heap_map_for_each_in_range(f, args.start_addr, args.end_addr)


@command.GDBSubCommand("malloctrace show all", "showall", short_description="showall")
@on_error_show_error_message(Exception)
def malloctrace_showall(_):
    if heap_map_is_empty():
        malloctrace_info(f"No entries")
        return

    def f(allocation):
        print_allocation(allocation)
        return True

    c_heap_map_for_each(f)

