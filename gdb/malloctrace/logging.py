import gdb

_reset = "\033[0m"
_color_names_to_ansi_codes = {
    "black": "\033[30m",
    "red": "\033[31m",
    "green": "\033[32m",
    "yellow": "\033[33m",
    "blue": "\033[34m",
    "magenta": "\033[35m",
    "cyan": "\033[36m",
    "white": "\033[37m",
}

def get_gdb_style_color_for_categroy(category: str):
    output = gdb.execute(f"show style {category} foreground", to_string=True)
    parts = output.split(":")
    if len(parts) != 2:
        return _reset
    return _color_names_to_ansi_codes.get(parts[1].strip(), _reset)

def _color_code_wrapper(color_code):
    def wrapper(msg: str):
        return _reset + color_code + msg + _reset
    return wrapper


_highlight = _color_code_wrapper(get_gdb_style_color_for_categroy("highlight"))
_address = _color_code_wrapper(get_gdb_style_color_for_categroy("address"))
_function = _color_code_wrapper(get_gdb_style_color_for_categroy("function"))
_filename = _color_code_wrapper(get_gdb_style_color_for_categroy("filename"))

_black = _color_code_wrapper(_color_names_to_ansi_codes["black"])
_red = _color_code_wrapper(_color_names_to_ansi_codes["red"])
_green = _color_code_wrapper(_color_names_to_ansi_codes["green"])
_yellow = _color_code_wrapper(_color_names_to_ansi_codes["yellow"])
_blue = _color_code_wrapper(_color_names_to_ansi_codes["blue"])
_magenta = _color_code_wrapper(_color_names_to_ansi_codes["magenta"])
_cyan = _color_code_wrapper(_color_names_to_ansi_codes["cyan"])
_white = _color_code_wrapper(_color_names_to_ansi_codes["white"])

def _color_bool(value: bool):
    if value:
        return _green("True")
    return _red("False")


def malloctrace_info(msg: str):
    print(f"{_blue('[*]')}: {msg}")

def malloctrace_warning(msg: str):
    print(f"{_yellow('[!]')}: {msg}")

def malloctrace_error(msg: str):
    print(f"{_red('[-]')}: {msg}")