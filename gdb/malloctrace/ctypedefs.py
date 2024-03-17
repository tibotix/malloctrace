from malloctrace.cvar import *
from malloctrace.common import get_malloctrace_objfile
from malloctrace.constants import MAX_BACKTRACE_FRAMES


# typedef struct {
#   void* address;
#   size_t size;
# } Chunk;
ChunkCStruct = CStructVar.bind_with_fields([
    CStructField(name="address", cvar_type=CVoidPointer),
    CStructField(name="size", cvar_type=CUInt64),
])

# typedef struct {
#   Chunk chunk;
#   bt backtrace;
# } AllocationDesc;
# typedef struct {
#   void* frames[MAX_BACKTRACE_FRAMES];
# } bt;
AllocationDescCStruct = CStructVar.bind_with_fields([
    CStructField(name="chunk", cvar_type=ChunkCStruct),
    CStructField(name="backtrace", cvar_type=CUInt64Array.bind_with_size(MAX_BACKTRACE_FRAMES)),
])

# typedef struct {
#   void* base;
#   size_t size;
#   AllocationDesc* head;
# } HeapMap;
HeapMapCStruct = CStructVar.bind_with_fields([
    CStructField(name="base", cvar_type=CVoidPointer),
    CStructField(name="size", cvar_type=CUInt64),
    CStructField(name="head", cvar_type=CVoidPointer)
])


MALLOCTRACE_ACTIVE = CUInt8Symbol("MALLOCTRACE_ACTIVE", objfile_getter=get_malloctrace_objfile)
MALLOCTRACE_ERR_CODE = CInt8Symbol("MALLOCTRACE_ERR_CODE", objfile_getter=get_malloctrace_objfile)
MALLOCTRACE_LOG_LEVEL = CUInt8Symbol("MALLOCTRACE_LOG_LEVEL", objfile_getter=get_malloctrace_objfile)
MALLOCTRACE_HEAP_MAP = CPointerSymbolVar("MALLOCTRACE_HEAP_MAP", wrapped_cvar_type=HeapMapCStruct, objfile_getter=get_malloctrace_objfile)