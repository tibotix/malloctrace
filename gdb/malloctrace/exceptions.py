from typing import Type
import functools
from malloctrace.logging import malloctrace_error


def on_error_show_message(error_class: Type[Exception], msg: str):
    def _decorator(func):
        @functools.wraps(func)
        def _wrapper(*args, **kwargs):
            try:
                func(*args, **kwargs)
            except error_class as e:
                malloctrace_error(msg)
        return _wrapper
    return _decorator

def on_error_show_error_message(error_class: Type[Exception]):
    def _decorator(func):
        @functools.wraps(func)
        def _wrapper(*args, **kwargs):
            try:
                func(*args, **kwargs)
            except error_class as e:
                malloctrace_error(str(e))
        return _wrapper
    return _decorator
