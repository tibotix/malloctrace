import gdb
import itertools


def get_ld_preload() -> set:
    ld_preload = gdb.execute("show environment LD_PRELOAD", to_string=True)
    if not ld_preload.startswith("LD_PRELOAD ="):
        return set()
    ld_preload = ld_preload.removeprefix("LD_PRELOAD =")
    return set(filter(lambda x:x, map(lambda x:x.strip(), itertools.chain.from_iterable(map(lambda x:x.split(":"), ld_preload.split(" "))))))

def set_ld_preload(ld_preload: set):
    if len(ld_preload) == 0:
        gdb.execute("unset environment LD_PRELOAD")
        return
    ld_preload = ":".join(ld_preload)
    gdb.execute(f"set environment LD_PRELOAD={ld_preload}")