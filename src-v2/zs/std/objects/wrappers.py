from collections import UserString
from typing import TypeVar, Generic, Iterable, Union, overload

from zs import Object, EmptyObject

_T = TypeVar("_T", bound=Object)
_KT = TypeVar("_KT", bound=Object)
_VT = TypeVar("_VT", bound=Object)

_SINGULARITY = object()

__all__ = [
    "Bool",
    "Dictionary",
    "Int32",
    "List",
    "NativeValue",
    "String",
]


class NativeValue(EmptyObject):
    """
    A base class for all Z# values represented via native values.
    """


class String(NativeValue):
    _native: str

    def __init__(self, native: Union[str, "String"]):
        super().__init__()
        self._native = native if isinstance(native, str) else native._native

    @property
    def native(self):
        return self._native

    # todo: implement interface IString

    def startswith(self, prefix: Union[str, "String"]):
        return Bool(self._native.startswith(str(prefix)))

    def __str__(self):
        return self._native

    def __add__(self, other: Union[str, "String"]):
        return String(str(self) + str(other))

    def __radd__(self, other: Union[str, "String"]):
        return String(str(other) + str(self))

    def __hash__(self):
        return hash(self._native)

    def __eq__(self, other: Union[str, "String"]):
        return Bool(str(self) == str(other))


class Bool(NativeValue):
    _native: bool

    def __init__(self, native: Union[bool, "Bool"]):
        super().__init__()
        self._native = native if isinstance(native, bool) else native._native

    @property
    def native(self):
        return self._native

    # todo: implement interface IString

    def __bool__(self):
        return self._native


class Int32(NativeValue):
    _native: int

    def __init__(self, native: Union[int, "Int32"]):
        super().__init__()
        self._native = native if isinstance(native, int) else native._native

    @property
    def native(self):
        return self._native

    # todo: implement interface IInteger

    def __sub__(self, other: Union[int, "Int32"]):
        return Int32(int(self) - int(other))

    def __int__(self):
        return self._native

    def __index__(self):
        return int(self).__index__()

    def __lt__(self, other: Union[int, "Int32"]) -> Bool:
        return Bool(int(self) < int(other))

    def __eq__(self, other):
        return Bool(int(self) == int(other))


class List(NativeValue, Generic[_T]):
    _items: list[_T]

    @overload
    def __init__(self): ...
    @overload
    def __init__(self, iterable: Iterable[_T]): ...

    def __init__(self, iterable: Iterable[_T] | None = None):
        super().__init__()
        if iterable is not None:
            self._items = list(iterable)
        else:
            self._items = []

    # todo: implement interface IList<T>

    def add(self, item: _T):
        self._items.append(item)

    def extend(self, iterable: Iterable[_T]):
        self._items.extend(iterable)

    @overload
    def pop(self): ...
    @overload
    def pop(self, index: Int32): ...

    def pop(self, index: Int32 = _SINGULARITY):
        if index is _SINGULARITY:
            self._items.pop()
        else:
            self._items.pop(index)

    def __getitem__(self, index: Int32):
        return self._items[int(index)]


class Dictionary(NativeValue, Generic[_KT, _VT]):
    _items: dict[_KT, _VT]

    @overload
    def __init__(self, **kwargs: _VT): ...
    @overload
    def __init__(self, iterable: Iterable[tuple[_KT, _VT]], **kwargs: _VT): ...

    def __init__(self, *args, **kwargs):
        super().__init__()

        self._items = dict(*args, **kwargs)

    # todo: implement interface IMapping<KeyT, ValueT>

    @overload
    def get(self, key: _KT) -> _VT: ...
    @overload
    def get(self, key: _KT, default: _VT | None) -> _VT: ...

    def get(self, key: _KT, default: _VT = _SINGULARITY) -> _VT:
        if default is _SINGULARITY:
            return self._items.get(key)
        return self._items.get(key, default)

    def __contains__(self, key: _KT):
        return Bool(key in self._items)

    def __getitem__(self, key: _KT) -> _VT:
        return self._items[key]

    def __setitem__(self, key: _KT, value: _VT):
        self._items[key] = value
