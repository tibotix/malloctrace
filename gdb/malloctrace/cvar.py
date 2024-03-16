import gdb
import functools
import dataclasses
from typing import List, Optional, Type


def partialclass(cls, *args, **kwargs):
    class PartialClass(cls):
        __init__ = functools.partialmethod(cls.__init__, *args, **kwargs)
    return PartialClass


class TypeConverter:
    def __init__(self, value_size_in_bytes ,convert_to_bytes_func, convert_from_bytes_func):
        self.value_size_in_bytes = value_size_in_bytes
        self._convert_to_bytes_func = convert_to_bytes_func
        self._convert_from_bytes_func = convert_from_bytes_func

    def convert_to_bytes(self, value) -> bytes:
        return self._convert_to_bytes_func(value)

    def convert_from_bytes(self, bytes_: bytes):
        return self._convert_from_bytes_func(bytes_)


UInt8TypeConverter = TypeConverter(
    value_size_in_bytes=1,
    convert_to_bytes_func=lambda v:int.to_bytes(v, 1, "little", signed=False),
    convert_from_bytes_func=lambda b:int.from_bytes(b, "little", signed=False),
)
Int8TypeConverter = TypeConverter(
    value_size_in_bytes=1,
    convert_to_bytes_func=lambda v:int.to_bytes(v, 1, "little", signed=True),
    convert_from_bytes_func=lambda b:int.from_bytes(b, "little", signed=True),
)
UInt64TypeConverter = TypeConverter(
    value_size_in_bytes=8,
    convert_to_bytes_func=lambda v:int.to_bytes(v, 8, "little", signed=False),
    convert_from_bytes_func=lambda b:int.from_bytes(b, "little", signed=False),
)
Int64TypeConverter = TypeConverter(
    value_size_in_bytes=8,
    convert_to_bytes_func=lambda v:int.to_bytes(v, 8, "little", signed=True),
    convert_from_bytes_func=lambda b:int.from_bytes(b, "little", signed=True),
)
VoidPointerTypeConverter = TypeConverter(
    value_size_in_bytes=8,
    convert_to_bytes_func=lambda v:int.to_bytes(v, 8, "little"),
    convert_from_bytes_func=lambda b:int.from_bytes(b, "little"),
)
def _raise(e):
    raise e
VoidTypeConverter = TypeConverter(
    value_size_in_bytes=0,
    convert_to_bytes_func=lambda v: _raise(ValueError("I d not know how to convert the VOID.")),
    convert_from_bytes_func=lambda b: _raise(ValueError("I do not know how to convert the VOID."))
)




class CVar:
    @classmethod
    def bind_with_type_converter(cls, type_converter: TypeConverter):
        return partialclass(cls, *tuple(), **{"type_converter": type_converter})

    def __init__(self, type_converter: TypeConverter=None, address: int=None):
        assert type_converter is not None, "Please specifiy a type_converter."
        self.type_converter = type_converter
        self._address = address
    
    def _get_value_address(self) -> int:
        raise NotImplementedError("_get_value_address not implemented")

    @property
    def address(self) -> int:
        return self._address or self._get_value_address()
    
    @address.setter
    def address(self, addr: int):
        self._address = addr

    def _assert_has_address(self):
        if self.address is None:
            raise ValueError("This CVar has no address, but it needs one to get/set values.")
    
    @property
    def value_size_in_bytes(self):
        return self.type_converter.value_size_in_bytes
    
    def set(self, value):
        value_in_bytes = self.type_converter.convert_to_bytes(value)
        gdb.selected_inferior().write_memory(self.address, value_in_bytes, self.value_size_in_bytes)

    def get(self):
        value_in_bytes = gdb.selected_inferior().read_memory(self.address, self.value_size_in_bytes).tobytes()
        return self.type_converter.convert_from_bytes(value_in_bytes)


class CPointerVar(CVar):
    @classmethod
    def bind_with_wrapped_cvar_type(cls, wrapped_cvar_type: Type[CVar]):
        return partialclass(cls, *tuple(), **{"wrapped_cvar_type": wrapped_cvar_type})

    def __init__(self, wrapped_cvar_type: Type[CVar]=None, address: int=None):
        assert wrapped_cvar_type is not None, "Plesae specify a wrapped_cvar_type"
        self.wrapped_cvar = wrapped_cvar_type()
        super().__init__(VoidPointerTypeConverter, address=address)

    def get_dereferenced_cvar(self):
        dereferenced_address = self.get()
        self.wrapped_cvar.address = dereferenced_address
        return self.wrapped_cvar


@dataclasses.dataclass
class CStructField:
    name: str
    cvar_type: Type[CVar]
    offset: Optional[int] = None

class CStructVar(CVar):
    @classmethod
    def bind_with_fields(cls, fields: List[CStructField]):
        return partialclass(cls, *tuple(), **{"fields": fields})

    @dataclasses.dataclass
    class _CStructField:
        name: str
        cvar: CVar
        offset: Optional[int] = None

    def __init__(self, fields: List[CStructField]=None, address: int=None):
        assert fields is not None, "Please specify fields"
        assert len(set(map(lambda f:f.name, fields))) == len(fields), "struct field names must be unique"
        # Copy fields cvar instances over, so they don't get modified by two CVars using the same CStruct blueprint
        self.fields = list(map(lambda f:self._CStructField(f.name, f.cvar_type(), f.offset), fields))
        self._total_size = None
        super().__init__(VoidTypeConverter, address=address)
        if address is not None:
            self._update_field_addresses()
    
    @CVar.address.setter
    def address(self, value):
        CVar.address.fset(self, value)
        if value is not None:
            self._update_field_addresses()
    
    def _update_field_addresses(self):
        next_address = self.address
        for field in self.fields:
            if field.offset is not None:
                field.cvar.address = self.address + field.offset
            else:
                field.cvar.address = next_address
            next_address = field.cvar.address + field.cvar.value_size_in_bytes
        self._total_size = next_address - self.address
    
    @property
    def value_size_in_bytes(self):
        self._assert_has_address()
        return self._total_size

    def set_field(self, field_name, value):
        self._assert_has_address()
        for field in self.fields:
            if field.name == field_name:
                field.cvar.set(value)
                return
    
    def get_field(self, field_name):
        self._assert_has_address()
        for field in self.fields:
            if field.name == field_name:
                return field.cvar.get()
    
    def set(self, value):
        self._assert_has_address()
        for field_name, field_value in value.items():
            self.set_field(field_name, field_value)

    def get(self):
        self._assert_has_address()
        # TODO: maybe don't use dict, but namedtuple or some other dataclass where i can use .value instead of ['value']
        value = dict()
        for field in self.fields:
            value[field.name] = field.cvar.get()
        return value


class CArrayVar(CVar):
    @classmethod
    def bind_with_contained_cvar_type(cls, contained_cvar_type: Type[CVar]):
        return partialclass(cls, *tuple(), **{"contained_cvar_type": contained_cvar_type})

    @classmethod
    def bind_with_size(cls, size:int=None):
        return partialclass(cls, *tuple(), **{"size": size})

    def __init__(self, contained_cvar_type: Type[CVar]=None, size:int=None, address:int = None):
        assert contained_cvar_type is not None, "Please specify contained_cvar_type"
        assert size is not None, "Please specify size"
        self.contained_cvar = contained_cvar_type()
        self.size = size
        super().__init__(VoidTypeConverter, address=address)

    @property
    def value_size_in_bytes(self):
        return self.contained_cvar.value_size_in_bytes * self.size

    def set_index(self, index: int, value):
        self._assert_has_address()
        element_address = self.address + (self.contained_cvar.value_size_in_bytes * index)
        self.contained_cvar.address = element_address
        self.contained_cvar.set(value)

    def get_index(self, index: int):
        self._assert_has_address()
        element_address = self.address + (self.contained_cvar.value_size_in_bytes * index)
        self.contained_cvar.address = element_address
        return self.contained_cvar.get()

    def set(self, value: list):
        assert len(value) == self.size, "Please use an array that has the same size as specified"
        for index, element in value:
            self.set_index(index, element)

    def get(self) -> list:
        value = list()
        for index in range(self.size):
            value.append(self.get_index(index))
        return value
    

class CSymbolVar(CVar):
    def __init__(self, name: str, type_converter: TypeConverter=None, objfile_getter=None):
        self.name = name
        self.objfile_getter = objfile_getter
        CVar.__init__(self, type_converter)
        self.symbol = self._load_symbol()
    
    def _load_symbol(self):
        if self.objfile_getter is not None:
            objfile = self.objfile_getter()
            if objfile is not None:
                return objfile.lookup_global_symbol(self.name, gdb.SYMBOL_VAR_DOMAIN)
        else:
            return gdb.lookup_global_symbol(self.name, gdb.SYMBOL_VAR_DOMAIN)
    
    def _load_symbol_if_needed(self):
        if self.symbol is None or not self.symbol.is_valid():
            self.symbol = self._load_symbol()
        if self.symbol is None or not self.symbol.is_valid():
            raise ValueError(f"Could not load symbol {self.name}")
    
    def _get_value(self) -> gdb.Value:
        return self.symbol.value()
    
    def _get_value_address(self) -> int:
        self._load_symbol_if_needed()
        return int(self._get_value().address)


class CPointerSymbolVar(CSymbolVar, CPointerVar):
    def __init__(self, name: str, wrapped_cvar_type: Type[CVar]=None, objfile_getter=None):
        CSymbolVar.__init__(self, name, type_converter=VoidPointerTypeConverter, objfile_getter=objfile_getter)
        CPointerVar.__init__(self, wrapped_cvar_type=wrapped_cvar_type)

class CStructSymbolVar(CSymbolVar, CStructVar):
    def __init__(self, name: str, fields: List[CStructField]=None, objfile_getter=None):
        CSymbolVar.__init__(self, name, type_converter=VoidTypeConverter, objfile_getter=objfile_getter)
        CStructVar.__init__(self, fields=fields)

class CArraySymbolVar(CSymbolVar, CArrayVar):
    def __init__(self, name: str, contained_cvar_type: Type[CVar]=None, size:int=None, objfile_getter=None):
        CSymbolVar.__init__(self, name, type_converter=VoidTypeConverter, objfile_getter=objfile_getter)
        CArrayVar.__init__(self, contained_cvar_type=contained_cvar_type, size=size)


CUInt8 = CVar.bind_with_type_converter(UInt8TypeConverter)
CInt8 = CVar.bind_with_type_converter(Int8TypeConverter)
CUInt64 = CVar.bind_with_type_converter(UInt64TypeConverter)
CInt64 = CVar.bind_with_type_converter(Int64TypeConverter)
CVoid = CVar.bind_with_type_converter(VoidTypeConverter)
CVoidPointer = CPointerVar.bind_with_wrapped_cvar_type(CVoid)
CUInt64Pointer = CPointerVar.bind_with_wrapped_cvar_type(CUInt64)
CVoidPointerArray = CArrayVar.bind_with_contained_cvar_type(CVoidPointer)
CUInt64Array = CArrayVar.bind_with_contained_cvar_type(CUInt64)

CUInt8Symbol = CSymbolVar.bind_with_type_converter(UInt8TypeConverter)
CInt8Symbol = CSymbolVar.bind_with_type_converter(Int8TypeConverter)
CUInt64Symbol = CSymbolVar.bind_with_type_converter(UInt64TypeConverter)
CInt64Symbol = CSymbolVar.bind_with_type_converter(Int64TypeConverter)
CVoidPointerSymbol = CPointerSymbolVar.bind_with_wrapped_cvar_type(CVoid)
CUInt64PointerSymbol = CPointerSymbolVar.bind_with_type_converter(CUInt64)
CVoidPointerArraySymbol = CArraySymbolVar.bind_with_contained_cvar_type(CVoidPointer)
CUInt64ArraySymbol = CArraySymbolVar.bind_with_contained_cvar_type(CUInt64)


