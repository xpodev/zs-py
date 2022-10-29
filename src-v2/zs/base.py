from abc import ABC, abstractmethod
from inspect import signature, Signature
from typing import TypeVar, Generic, TYPE_CHECKING, Any, Callable

_T = TypeVar("_T")


__all__ = [
    "EmptyObject",
    "Object",
]


class Object(Generic[_T]):
    _node: _T | None

    __zs_type__ = None

    def __init__(self, node: _T = None):
        self._node = node

    @property
    def node(self):
        return self._node

    @property
    def runtime_type(self):
        return Object_Type

    def __bool__(self):
        return self is not Null

    @staticmethod
    def null():
        return Null

    def __str__(self):
        if self is Null:
            return "null"
        return super().__str__()


Null = Object()


class EmptyObject(Object[None]):
    def __init__(self):
        super().__init__(None)

    if TYPE_CHECKING:
        @property
        def node(self):
            return None


class Type(EmptyObject):
    _members: dict[str, Object]
    _base: "Type"

    __base__ = None

    def __init__(self, base: "Type" = None, members: dict[str, Object] = None):
        super().__init__()
        self._members = members if members is not None else {}
        base = base or self.__base__
        if self.__base__ is None:
            self.__base__ = self
        self._base = base

    def get(self, name: str | Any):
        try:
            return self._members[str(name)]
        except KeyError:
            if self._base is not None:
                return self._base.get(name)

    @property
    def runtime_type(self):
        return Type_Type

    def cast_from(self, v: Object):
        return self._members[""](v)


class IFunction(ABC):
    @property
    @abstractmethod
    def name(self): ...

    @property
    @abstractmethod
    def return_type(self): ...

    @abstractmethod
    def get_match_score(self, *args: Object): ...


_om = {}
Object_Type = Type(None, _om)


class NativeFunction(EmptyObject, IFunction):
    _native: Callable

    def __init__(self, fn: Callable, name=None, sig: Signature = None):
        super().__init__()
        self._native = fn
        self._name = name or fn.__name__

        self._sig = sig or signature(fn)

        self._return_type = Object_Type if self._sig.return_annotation == Signature.empty else self._sig.return_annotation.__zs_type__

    @property
    def name(self):
        return self._name

    @property
    def return_type(self):
        return self._return_type

    def get_match_score(self, *args: Object):
        try:
            self._sig.bind(*args)
            return -1
        except TypeError:
            return 0

    def __call__(self, *args, **kwargs):
        return self._native(*args, **kwargs)

    def __get__(self, instance, owner):
        return NativeMethod(self._native, instance, self.name)


class NativeMethod(NativeFunction):
    def __init__(self, fn: Callable, bound=None, name=None):
        super().__init__(fn, name)
        self.__self__ = bound

    def __call__(self, *args, **kwargs):
        return super().__call__(self.__self__, *args, **kwargs)


_om.update({
    "_._": NativeFunction(lambda o, n: getattr(o, str(n)), "_._"),
    "": NativeFunction(lambda x: x)
})
Type_Type = Type(Object_Type, {

})
IFunction_Type = Type(Object_Type, {
    "_()": NativeFunction(IFunction.__call__, "_()")
})

Object.__zs_type__ = Object_Type
Type_Type.__zs_type__ = Type_Type
IFunction.__zs_type__ = IFunction_Type
