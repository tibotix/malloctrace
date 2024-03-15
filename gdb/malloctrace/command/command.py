import gdb
import io

from .argparser import GDBArgumentParser


class _FunctionalCommand(gdb.Command):
    def __init__(self, function, command_name=None, command_class=gdb.COMMAND_USER, prefix: bool=False, aliases=None):
        if command_name is None:
            command_name = function.__name__
        super().__init__(command_name, command_class, prefix=prefix)
        self.function = function
        self.__name__ = command_name
    
    def parser_argument(self, argument: str):
        return gdb.string_to_argv(argument)
    
    def invoke(self, argument: str, from_tty: bool):
        try:
            args = self.parse_argument(argument)
            return self.function(args)
        except SystemExit:
            pass
        return None

class _Command(_FunctionalCommand):
    def __init__(self, parser: GDBArgumentParser, function, command_name: str, command_class=gdb.COMMAND_USER, prefix: bool=False) -> None:
        self.parser = parser
        if command_name is None:
            self.parser.prog = function.__name__
        else:
            self.parser.prog = command_name

        file = io.StringIO()
        self.parser.print_help(file)
        file.seek(0)
        self.__doc__ = file.read()

        super().__init__(function, command_name, command_class=command_class, prefix=prefix)
    
    def parse_argument(self, argument: str):
        argv = gdb.string_to_argv(argument)
        return self.parser.parse_args(argv)

class GDBCommand:
    def __init__(self, command_name, parser_or_desc: GDBArgumentParser|str, short_description=None, command_class=gdb.COMMAND_USER, prefix=False):
        if isinstance(parser_or_desc, str):
            self.parser = GDBArgumentParser(description=parser_or_desc, short_description=short_description)
        else:
            self.parser = parser_or_desc
        self._command_name = command_name
        self._command_class = command_class
        self._prefix = prefix

    def __call__(self, function):
        return _Command(self.parser, function, self._command_name, command_class=self._command_class, prefix=self._prefix)

class GDBPrefixCommand(GDBCommand):
    def __init__(self, command_name, parser_or_desc: GDBArgumentParser|str, short_description=None, command_class=gdb.COMMAND_USER, aliases=None):
        super().__init__(command_name, parser_or_desc, short_description, command_class, prefix=True)
        self._aliases = aliases or list()

    def __call__(self, function):
        main_command = super().__call__(function)
        for alias in self._aliases:
            gdb.execute(f"alias {alias}={self._command_name}")
        return main_command

class GDBSubCommand(GDBCommand):
    def __init__(self, command_name, parser_or_desc: GDBArgumentParser|str, short_description=None, command_class=gdb.COMMAND_USER, aliases=None):
        super().__init__(command_name, parser_or_desc, short_description, command_class, prefix=False)


