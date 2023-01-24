""" native.py
This file contains utilities to create facade classes between the Python backend and the
Z# interpreter.
"""
# from inspect import get_annotations
from functools import partial
from typing import TypeVar, Generic, Callable, Any, Union

from .core import _Object, _ObjectType, _AnyType
from .errors import UnknownFieldError
from .protocols import *
from .protocols import CallableProtocol, ObjectProtocol
from ..ast.node_lib import While


class _TypeMeta(type, _ObjectType):
    _fields: dict[str, "NativeField"]
    _items: dict[str, Union["NativeField", "NativeFunction"]]
    _methods: dict[str, "NativeFunction"]

    def __init__(cls, name: str, bases: tuple, namespace: dict):
        super().__init__(name, bases, namespace)
        cls._fields = dict(namespace.get("_fields", ()))
        cls._methods = dict(namespace.get("_methods", ()))
        cls._items = dict(namespace.get("_items", ()))
        # _ObjectType.__init__(cls)
        # for name, item in namespace.items():
        #     if isinstance(item, NativeFunction):
        #         cls.add_method(name, item)
        #     elif isinstance(item, NativeField):
        #         cls.add_field(name, item.type, item.value)
        cls._fields.update({
            getattr(item, "name", name): item for name, item in namespace.items() if isinstance(item, ObjectProtocol) and isinstance(item, NativeField)
        })
        cls._methods.update({
            getattr(item, "name", name): item for name, item in namespace.items() if isinstance(item, ObjectProtocol) and isinstance(item, NativeFunction)
        })
        cls._items.update(cls._fields)
        cls._items.update(cls._methods)

    @property
    def fields(self):
        return list(self._fields.values())

    def get_name(self, instance: ObjectProtocol | None, name: str) -> ObjectProtocol | None:
        if not self.is_instance(instance):
            raise TypeError
        try:
            attr = self._items[name]
            if isinstance(attr, BindProtocol):
                attr = attr.bind([instance])
        except KeyError:
            if self is _TypeMeta:
                raise UnknownFieldError()
            return self.get_type().get_name(self, name)
        else:
            if isinstance(attr, GetterProtocol):
                attr = attr.get()
            return attr

    def set_name(self, instance: ObjectProtocol | None, name: str, value: ObjectProtocol):
        if not self.is_instance(instance):
            raise TypeError
        try:
            attr = self._items[name]
            if isinstance(attr, BindProtocol):
                attr = attr.bind([instance])
        except KeyError:
            if self is _TypeMeta:
                raise UnknownFieldError()
            return self.get_type().set_name(self, name, value)
        if isinstance(attr, SetterProtocol):
            attr.set(value)
        else:
            setattr(instance, name, value)

    def assignable_to(self, target: "TypeProtocol") -> bool:
        if isinstance(target, _TypeMeta):
            return target.is_subclass(self)
        return super().assignable_to(target)

    def is_subclass(self, base: TypeProtocol) -> bool:
        if base is self:
            return True
        for base_ in self.__bases__:
            if isinstance(base_, _TypeMeta) and base_ is base:
                return True
        for base_ in self.__bases__:
            if isinstance(base_, _TypeMeta) and base_.is_subclass(base):
                return True
        return False


# class NativeObject(ObjectProtocol, metaclass=_TypeMeta):
#     def get_type(self) -> "_TypeMeta":
#         typ = type(self)
#         if not isinstance(typ, _TypeMeta):
#             raise TypeError
#         return typ
#
#
# class NativeValue(NativeObject, Generic[_T]):
#     _native: _T
#
#     def __init__(self, native: _T):
#         self._native = native
#
#     @property
#     def native(self):
#         return self._native
#
#
# class NativeMethod(NativeValue[Callable]):
#     def __call__(self, *args, **kwargs):
#         return self._native(*args, **kwargs)
#
#
# def nativemethod(fn):
#     return NativeMethod(fn)


_T = TypeVar("_T")


class NativeField(GetterProtocol, SetterProtocol):
    class DefaultType(_AnyType):
        @classmethod
        def default(cls) -> ObjectProtocol:
            return None

    DefaultType = DefaultType()

    def __init__(self, name, value):
        self.name = name
        try:
            self.type = value.get_type()
        except (TypeError, AttributeError):
            self.type = self.DefaultType
        self.value = value

    def get(self):
        return self.value

    def set(self, value: ObjectProtocol):
        if not value.get_type().assignable_to(self.type):
            raise TypeError
        self.value = value


class NativeObject(_Object, metaclass=_TypeMeta):
    def __init__(self):
        super().__init__(type(self))

    def __setattr__(self, name, value):
        if name not in self._items:
            self._items[name] = value
        super().__setattr__(name, value)


class NativeFunction(NativeObject, CallableProtocol):
    name: str
    _native: Callable[..., Any]

    def __init__(self, native: Callable[..., Any], name: str = None):
        super().__init__()
        self._native = native
        try:
            self.name = name or native.__name__
        except AttributeError:
            self.name = ''

    def call(self, args: list[ObjectProtocol]):
        return self.invoke(*args)

    def invoke(self, *args, **kwargs):
        return self._native(*args, **kwargs)

    def __call__(self, *args, **kwargs):
        return self.invoke(*args, **kwargs)


class NativeValue(ObjectProtocol, Generic[_T]):
    Type: TypeProtocol  # implement on class level

    _native: _T

    def __init__(self, native: _T):
        self._native = native

    @property
    def native(self):
        return self._native

    def get_type(self) -> TypeProtocol:
        return self.Type

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


class _Type(metaclass=_TypeMeta):
    ...


# interop utility


def native_fn(name: str = None):
    def wrapper(fn):
        if not callable(fn):
            raise TypeError

        return NativeFunction(fn, name)

    return wrapper


# native types


class String(NativeValue[str]):
    class Type(_Type):
        @classmethod
        def default(cls):
            return String("")

        @native_fn("_+_")
        @staticmethod
        def add(left: "String", right: "String"):
            return String(left.native + right.native)


class Int64(NativeValue[int]):
    class Type(_Type):
        @classmethod
        def default(cls):
            return Int64(0)

        @native_fn("_+_")
        @staticmethod
        def add(left: "Int64", right: "Int64"):
            return Int64(left.native + right.native)


class Float64(NativeValue[float]):
    class Type(_Type):
        @classmethod
        def default(cls):
            return Float64(0.0)

        @native_fn("_+_")
        @staticmethod
        def add(left: "Float64", right: "Float64"):
            return Float64(left.native + right.native)


class Boolean(NativeValue[bool]):
    class Type(_Type):
        @classmethod
        def default(cls):
            return Boolean(False)


# Utility


class NodeWrapper(NativeObject, Generic[_T]):
    _node: _T

    def __init__(self, node: _T):
        super().__init__()
        self._node = node
        self.owner = None

    @property
    def node(self):
        return self._node


class WhileWrapper(NodeWrapper[While]):
    ...
