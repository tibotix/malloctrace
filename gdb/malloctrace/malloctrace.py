import gdb
from malloctrace.command import command
from malloctrace.command import argparser

@command.GDBPrefixCommand("malloctrace", "Trace Heap", aliases=["mtrace"])
def malloctrace(args):
    return


@command.GDBSubCommand("malloctrace on", "enable malloctrace", short_description="enable malloctrace")
def malloctrace_on(args):
    print(str(args))


@command.GDBSubCommand("malloctrace off", "disable malloctrace", short_description="disable malloctrace")
def malloctrace_off(args):
    print(str(args))



parser = argparser.GDBArgumentParser(
    prog="malloctrace show",
    description="This command shows the traced heap map", 
    short_description="show heap map",
    add_help=False
)
parser.add_argument("start_addr")
parser.add_argument("end_addr")
@command.GDBSubCommand("malloctrace show", parser)
def malloctrace_off(args):
    print(str(args))