

# TODO: let the user change this
MAX_BACKTRACE_FRAMES = 0x4

DEFAULT_MAP_SIZE = 0x4000
DEFAULT_LOG_LEVEL = "error"

LOG_LEVELS = {
    0: "debug",
    1: "info",
    2: "warning",
    3: "error",
    0xff: "none",
}
REVERSE_LOG_LEVELS = {v:k for k,v in LOG_LEVELS.items()}

ERR_CODES = {
    -1: "ERR_UNITIIALIZED",
    0: "ERR_NONE",
    1: "ERR_MAP_SIZE",
    2: "ERR_MAP_ALLOC",
}