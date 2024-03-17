import gdb
import itertools


def inferior_set_env(key: str, value: str):
    gdb.execute(f"set environment {key!s}={value!s}", to_string=True)

def inferior_get_env(key: str):
    value = gdb.execute(f"show environment {key!s}", to_string=True)
    if not value.startswith(f"{key!s} ="):
        return None
    return value.removeprefix(f"{key!s} =")

def inferior_unset_env(key: str):
    gdb.execute(f"unset environment {key!s}")

def get_ld_preload() -> set:
    ld_preload = inferior_get_env("LD_PRELOAD")
    if ld_preload is None:
        return set()
    return set(filter(lambda x:x, map(lambda x:x.strip(), itertools.chain.from_iterable(map(lambda x:x.split(":"), ld_preload.split(" "))))))

def set_ld_preload(ld_preload: set):
    if len(ld_preload) == 0:
        inferior_unset_env("LD_PRELOAD")
        return
    ld_preload = ":".join(ld_preload)
    inferior_set_env("LD_PRELOAD", ld_preload)