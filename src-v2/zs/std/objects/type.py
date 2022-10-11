from typing import TypeVar, Generic

from zs.objects.common import TypedName
from .function import Function
from .wrappers import String, List, Bool
from zs import Object, EmptyObject
from zs.ast import node_lib as node


_T = TypeVar("_T")


__all__ = [
    "Field",
    "Member",
    "Method",
    "MethodGroup",
    "Property",
    "Type",
]


class Member:
    _declaring_type: "Type"
    _is_static: Bool

    def __init__(self, declaring_type: "Type"):
        self._declaring_type = declaring_type

    @property
    def declaring_type(self):
        return self._declaring_type

    @property
    def is_static(self):
        return self._is_static

    @is_static.setter
    def is_static(self, value):
        self._is_static = Bool(bool(value))


class Field(TypedName[node.Field], Member):
    ...


class Method(Function, Member):
    _declaring_type: "Type"


class MethodGroup(EmptyObject, Member):
    _methods: List[Method]


class Property(TypedName[node.Property], Member):
    _getter: Method | None
    _setter: Method | None


class Type(Object[node.Class]):
    _name: String | None

    _methods: List[MethodGroup]
    _fields: List[Field]
