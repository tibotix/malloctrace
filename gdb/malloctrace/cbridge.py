import gdb
import ctypes
from malloctrace.constants import MAX_BACKTRACE_FRAMES
from malloctrace.ctypedefs import MALLOCTRACE_HEAP_MAP
from malloctrace.common import get_malloctrace_objfile, assert_malloctrace_loaded


class bt(ctypes.Structure):
    _fields_ = [("frames", ctypes.c_void_p * MAX_BACKTRACE_FRAMES)]

class Chunk(ctypes.Structure):
    _fields_ = [("address", ctypes.c_void_p),
                ("size", ctypes.c_size_t)]

class AllocationDesc(ctypes.Structure):
    _fields_ = [("chunk", Chunk),
                ("backtrace", bt)]

class DeallocationDesc(ctypes.Structure):
    _fields_ = [("chunk", Chunk)]

class HeapMap(ctypes.Structure):
    _fields_ = [("base", ctypes.c_void_p),
                ("size", ctypes.c_size_t),
                ("head", ctypes.POINTER(AllocationDesc))]

class CapacityDesc(ctypes.Structure):
    _fields_ = [("free_bytes", ctypes.c_size_t),
                  ("free_entries", ctypes.c_size_t),
                  ("total_bytes", ctypes.c_size_t),
                  ("total_entries", ctypes.c_size_t)]


file = "/home/tibotix/Projects/malloctrace/build/libmalloctrace.so"

libmalloctrace = None
FOR_EACH_CALLBACK_TYPE = None

def initialize_cfunctions():
    global libmalloctrace, FOR_EACH_CALLBACK_TYPE

    if libmalloctrace is not None:
        return

    assert_malloctrace_loaded()
    filepath = get_malloctrace_objfile().filename
    libmalloctrace = ctypes.CDLL(filepath)

    FOR_EACH_CALLBACK_TYPE = ctypes.CFUNCTYPE(ctypes.c_int, ctypes.POINTER(AllocationDesc), ctypes.c_void_p)
    libmalloctrace.heap_map_for_each.restype = None
    libmalloctrace.heap_map_for_each.argtypes = [ctypes.POINTER(HeapMap), FOR_EACH_CALLBACK_TYPE, ctypes.c_void_p]

    libmalloctrace.heap_map_for_each_in_range.restype = None
    libmalloctrace.heap_map_for_each_in_range.argtypes = [ctypes.POINTER(HeapMap), ctypes.POINTER(Chunk), ctypes.POINTER(Chunk), FOR_EACH_CALLBACK_TYPE, ctypes.c_void_p]

    libmalloctrace.heap_map_capacity.restype = CapacityDesc
    libmalloctrace.heap_map_capacity.argtypes = [ctypes.POINTER(HeapMap)]

    libmalloctrace.heap_map_clear.restype = None
    libmalloctrace.heap_map_clear.argtypes = [ctypes.POINTER(HeapMap)]

# ------

def assert_cbridge_loaded():
    initialize_cfunctions()
    if libmalloctrace is None:
        raise ValueError("cbridge could not be loaded")


def ptrdiff(p1, p2) -> int:
    return ctypes.cast(p1, ctypes.c_void_p).value - ctypes.cast(p2, ctypes.c_void_p).value

    
def c_heap_map_for_each(f):
    assert_cbridge_loaded()
    def ff(allocation, data):
        return 0 if f(allocation.contents) else -1

    heap_map = MALLOCTRACE_HEAP_MAP.get_dereferenced_cvar()
    buffer = heap_map.get_tobytes(writeable=True)
    heap_map = HeapMap.from_buffer(buffer)

    base_head_distance = ptrdiff(heap_map.head, heap_map.base)

    heap_map_buffer = gdb.selected_inferior().read_memory(heap_map.base, heap_map.size).tobytes()
    heap_map.base = ctypes.cast(heap_map_buffer, ctypes.c_void_p)
    heap_map.head = ctypes.cast(heap_map.base + base_head_distance, ctypes.POINTER(AllocationDesc))

    libmalloctrace.heap_map_for_each(ctypes.byref(heap_map), FOR_EACH_CALLBACK_TYPE(ff), None)

def c_heap_map_for_each_in_range(f, start_address: int, end_address: int):
    assert_cbridge_loaded()
    def ff(allocation, data):
        return 0 if f(allocation.contents) else -1

    heap_map = MALLOCTRACE_HEAP_MAP.get_dereferenced_cvar()
    buffer = heap_map.get_tobytes(writeable=True)
    heap_map = HeapMap.from_buffer(buffer)

    base_head_distance = ptrdiff(heap_map.head, heap_map.base)

    heap_map_buffer = gdb.selected_inferior().read_memory(heap_map.base, heap_map.size).tobytes()
    heap_map.base = ctypes.cast(heap_map_buffer, ctypes.c_void_p)
    heap_map.head = ctypes.cast(heap_map.base + base_head_distance, ctypes.POINTER(AllocationDesc))

    start_chunk = Chunk(address=start_address, size=0)
    end_chunk = Chunk(address=end_address, size=0)
    libmalloctrace.heap_map_for_each_in_range(ctypes.byref(heap_map), ctypes.byref(start_chunk), ctypes.byref(end_chunk), FOR_EACH_CALLBACK_TYPE(ff), None)
    

def c_heap_map_capacity():
    assert_cbridge_loaded()
    heap_map = MALLOCTRACE_HEAP_MAP.get_dereferenced_cvar()
    buffer = heap_map.get_tobytes(writeable=True)
    heap_map = HeapMap.from_buffer(buffer)
    result = libmalloctrace.heap_map_capacity(ctypes.byref(heap_map))
    return result

def c_heap_map_clear():
    assert_cbridge_loaded()
    heap_map = MALLOCTRACE_HEAP_MAP.get_dereferenced_cvar()
    buffer = heap_map.get_tobytes(writeable=True)
    c_heap_map = HeapMap.from_buffer(buffer)
    libmalloctrace.heap_map_clear(ctypes.byref(c_heap_map))
    heap_map.set_frombytes(buffer)
