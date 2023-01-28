""" native.py
This file contains utilities to create facade classes between the Python backend and the
Z# interpreter.
"""
import inspect
import typing
from functools import partial
from typing import Callable

from .core import Class, CallableAndBindProtocol, FunctionType, Any
from .protocols import *
from .protocols import ObjectProtocol


class _NativeClassMeta(type, Class):
    def __init__(cls, name: str, bases: tuple[type, ...], namespace: dict[str, object]):
        super().__init__(name, bases, namespace)
        base = None
        for b in bases:
            if isinstance(b, Class):
                if base is not None:
                    raise TypeError("May only inherit a single Z# class")
                base = b
        Class.__init__(cls, name, base, None, None)
        for name, item in namespace.items():
            if not isinstance(item, ObjectProtocol):
                continue
            if getattr(item, "__zs_native_function__", False):
                if not callable(item):
                    raise TypeError
                sig = inspect.signature(item)
                types = []
                for name, parameter in sig.parameters.items():
                    type = parameter.annotation
                    if type is _Self:
                        type = cls
                    if not isinstance(parameter, TypeProtocol):
                        raise TypeError(f"Native function must only have Z# types as parameters")
                    types.append(type)
                return_type = sig.return_annotation if sig.return_annotation is not sig.empty else Any
                fn_type = FunctionType(types, return_type)
                item = NativeFunction(item, fn_type, getattr(item, "__zs_native_name__", name))
            if isinstance(item, NativeFunction):
                cls.define_method(name, item)
            if isinstance(item, NativeField):
                cls.define_field(name, item.type, item.value)
            if isinstance(item, Class):
                cls.define_class(name, item)
            if isinstance(item, NativeConstructor):
                cls.define_constructor(item.function)


class NativeClass(ObjectProtocol, metaclass=_NativeClassMeta):
    ...


_T = typing.TypeVar("_T")
_U = typing.TypeVar("_U")
_Self = typing.TypeVar


class NativeField:
    def __init__(self, type: TypeProtocol, value=None, name: str = None):
        self.name = name
        self.type = type
        self.value = value or type.default()


class NativeFunction(CallableAndBindProtocol):
    name: str
    _native: Callable[..., typing.Any]
    runtime_type: FunctionType

    def __init__(self, native: Callable[..., typing.Any], type: FunctionType, name: str = None):
        self._native = native
        try:
            self.name = name or native.__name__
        except AttributeError:
            self.name = ''
        self.runtime_type = type

    def call(self, args: list[ObjectProtocol]):
        return self.invoke(*args)

    def invoke(self, *args, **kwargs):
        return self._native(*args, **kwargs)

    def bind(self, args: list[ObjectProtocol]):
        if isinstance(self._native, staticmethod):
            return self
        if len(args) > len(self.runtime_type.parameters):
            raise TypeError(f"Can't bind function {self.name} to more than {len(self.runtime_type.parameters)} arguments (got {len(args)})")
        for arg, parameter in zip(args, self.runtime_type.parameters):
            if not arg.is_instance_of(parameter):
                raise TypeError(f"Can't assign argument of type {arg.runtime_type} to parameter of type {parameter}")
        return NativeFunction(partial(self._native, *args), FunctionType(self.runtime_type.parameters[len(args):], self.runtime_type.returns))

    def __call__(self, *args, **kwargs):
        return self.invoke(*args, **kwargs)


class NativeConstructor:
    function: NativeFunction

    def __init__(self, function: NativeFunction):
        self.function = function


class NativeValue(NativeClass, typing.Generic[_T]):
    _native: _T

    def __init__(self, native: _T):
        super().__init__()
        self._native = native
        self.runtime_type = type(self)

    @property
    def native(self):
        return self._native

    # Python stuff

    def __str__(self):
        return str(self._native)

    def __int__(self):
        return int(self._native)

    def __bool__(self):
        return bool(self._native)

    def __float__(self):
        return float(self._native)

    def __eq__(self, other):
        return self._native == other


# interop utility


def native_fn(name_or_fn: str | Callable = None):
    def wrapper(fn):
        if not callable(fn):
            raise TypeError
        fn.__zs_native_function__ = True
        if name_or_fn:
            fn.__zs_native_name = name_or_fn
        return

    if callable(name_or_fn):
        fn_ = name_or_fn
        name_or_fn = None
        return wrapper(fn_)
    return wrapper


def native_constructor(fn: Callable[[_T], _U]):
    return native_fn()(fn)


# native types


class String(NativeValue[str]):
    @classmethod
    def default(cls):
        return cls("")

    @native_fn("_+_")
    def __add__(self: _Self, right: _Self):
        return String(self.native + right.native)

    @native_fn("length")
    def __len__(self):
        return Int64(len(self.native))


class Int64(NativeValue[int]):
    @native_fn("_+_")
    def __add__(self: _Self, right: _Self):
        if not isinstance(right, Int64):
            raise TypeError
        return Int64(self.native + right.native)

    @classmethod
    def default(cls):
        return cls(0)


class Float64(NativeValue[float]):
    @classmethod
    def default(cls):
        return cls(0.0)

    @native_fn("_+_")
    def __add__(self: _Self, right: _Self):
        return Float64(self.native + right.native)


class Boolean(NativeValue[bool]):
    @classmethod
    def default(cls):
        return cls.FALSE

    TRUE = FALSE = None


Boolean.TRUE = Boolean(True)
Boolean.FALSE = Boolean(False)

# Utility


# class NodeWrapper(NativeObject, Generic[_T]):
#     _node: _T
#
#     def __init__(self, node: _T):
#         super().__init__()
#         self._node = node
#         self.owner = None
#
#     @property
#     def node(self):
#         return self._node
#
#
# class WhileWrapper(NodeWrapper[While]):
#     ...
