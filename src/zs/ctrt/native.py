""" native.py
This file contains utilities to create facade classes between the Python backend and the
Z# interpreter.
"""
# from inspect import get_annotations
from functools import partial
from typing import TypeVar, Generic, Callable, Any, Union

from .core import _Object, _ObjectType, _AnyType, _TypeType
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

    def default(cls):
        return cls.default()

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
            return self.runtime_type.get_name(self, name)
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
            return self.runtime_type.set_name(self, name, value)
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


class _NativeTypeMeta(type, TypeProtocol):
    def __init__(cls, *args, **kwargs):
        super().__init__(*args, **kwargs)
        cls.runtime_type = _TypeType()

    def assignable_from(self, source: "TypeProtocol") -> bool:
        return isinstance(source, TypeProtocol)

    def default(cls) -> ObjectProtocol:
        return cls.default()

    def __str__(self):
        return type.__str__(self)


class NativeType(metaclass=_NativeTypeMeta):
    ...


class _NativeClassMeta(_NativeTypeMeta, _ObjectType):
    def __init__(cls, name: str, bases: tuple, namespace: dict):
        super().__init__(name, bases, namespace)
        _ObjectType.__init__(cls)

        for name, item in namespace.items():
            if not isinstance(item, ObjectProtocol):
                continue
            elif isinstance(item, NativeFunction):
                cls.add_method(item.name or name, item)
            elif isinstance(item, NativeField):
                cls.add_field(item.name or name, item.type, item.value)


class NativeClass(_Object, metaclass=_NativeClassMeta):
    def __init__(self):
        super().__init__(type(self))


class _Type(metaclass=_TypeMeta):
    ...


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


class NativeField:
    def __init__(self, type: TypeProtocol, value=None, name: str = None):
        self.name = name
        self.type = type
        self.value = value or type.default()


class NativeObject(_Object, metaclass=_NativeClassMeta):
    def __init__(self):
        super().__init__(type(self))

    def __setattr__(self, name, value):
        if name not in self._items:
            self._items[name] = value
        super().__setattr__(name, value)

    def __getattr__(self, item):
        try:
            result = self.__getattribute__(item)
        except AttributeError:
            try:
                result = self._items[item]
            except KeyError:
                raise AttributeError
        if isinstance(result, BindProtocol):
            result = result.bind([self])
        if isinstance(result, GetterProtocol):
            return result.get()
        return result


class NativeFunction(NativeObject, CallableProtocol, BindProtocol):
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

    def bind(self, args: list[ObjectProtocol]):
        if isinstance(self._native, staticmethod):
            return self
        return NativeFunction(partial(self._native, *args))

    def __call__(self, *args, **kwargs):
        return self.invoke(*args, **kwargs)


class NativeValue(NativeClass, Generic[_T]):
    Type: TypeProtocol  # implement on class level

    _native: _T

    def __init__(self, native: _T):
        super().__init__()
        self._native = native
        self.runtime_type = type(self)

    @property
    def native(self):
        return self._native

    @classmethod
    def default(cls):
        return cls.Type.default()

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


def native_fn(name: str = None):
    def wrapper(fn):
        if not callable(fn):
            raise TypeError
        return NativeFunction(fn, name)

    return wrapper


# native types


class String(NativeValue[str]):
    @classmethod
    def default(cls):
        return cls("")

    @native_fn("_+_")
    def __add__(self: "String", right: "String"):
        return String(self.native + right.native)

    @native_fn("length")
    def __len__(self):
        return Int64(len(self.native))


class Int64(NativeValue[int]):
    @native_fn("_+_")
    def __add__(self: "Int64", right: "Int64"):
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
    def __add__(self: "Float64", right: "Float64"):
        return Float64(self.native + right.native)


class Boolean(NativeValue[bool]):
    @classmethod
    def default(cls):
        return cls.FALSE

    TRUE = FALSE = None


Boolean.TRUE = Boolean(True)
Boolean.FALSE = Boolean(False)


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
