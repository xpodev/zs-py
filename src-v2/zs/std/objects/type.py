from typing import TypeVar, Generic

from zs.objects.common import TypedName
from .compilation_environment import ModuleMember, Module
from .function import Function
from .wrappers import String, List, Bool, Dictionary
from zs import Object, EmptyObject
from zs.ast import node_lib
from ...base import Type
from ...errors import UndefinedNameError

_T = TypeVar("_T")


__all__ = [
    "Field",
    "Member",
    "Method",
    "MethodGroup",
    "Property",
    "Class",
]


class Member(ModuleMember[_T], Generic[_T]):
    _declaring_type: "Class"
    _is_static: Bool

    def __init__(self, node: _T, declaring_type: "Class" = None, module: Module = None):
        super().__init__(node, module)
        self._declaring_type = declaring_type

    @property
    def name(self): yield

    @property
    def declaring_type(self):
        return self._declaring_type

    @property
    def is_static(self):
        return self._is_static

    @is_static.setter
    def is_static(self, value):
        self._is_static = Bool(bool(value))


class Field(TypedName[node_lib.Field], Member[node_lib.Field]):
    ...


class Method(Function, Member[node_lib.Function]):
    _declaring_type: "Class"


class MethodGroup(EmptyObject, Member):
    _name: String
    _methods: List[Method]

    def __init__(self, name: str | String, *overloads: Function | Method, module: Module = None):
        super().__init__()
        Member.__init__(self, None, module=module)
        self._name = name
        self._methods = List(overloads)

    @property
    def name(self):
        return self._name

    @property
    def overloads(self):
        return self._methods

    def add(self, overload: Function | Method):
        self._methods.add(overload)

    def __str__(self):
        return f"MethodGroup \"{self.name}\" with {len(self.overloads)} overloads"

    def __iadd__(self, other):
        if isinstance(other, MethodGroup):
            return MethodGroup(self.name, *self.overloads, *other.overloads, module=self.module)
        elif not isinstance(other, (Function, Method)):
            raise TypeError(f"Can only add functions and methods to a method group")
        else:
            self.add(other)
        return self

    def __call__(self, *args, **kwargs):
        return self.__zs_call__(*args, **kwargs)


class Property(TypedName[node_lib.Property], Member[node_lib.Property]):
    _getter: Method | None
    _setter: Method | None

    def __init__(self, node: node_lib.Property, name: str | String, type_: Object | None):
        super().__init__(node, name, type_)
        Member.__init__(self, node)
        self._getter = self._setter = None

    @property
    def getter(self):
        return self._getter

    @getter.setter
    def getter(self, value):
        self._getter = value

    @property
    def setter(self):
        return self._setter

    @setter.setter
    def setter(self, value):
        self._setter = value


Property_Type = Type()
Property_Type._members["_=_"] = lambda l, r: l.setter(r)


class Class(ModuleMember[node_lib.Class]):
    _name: String | None

    _methods: List[MethodGroup]
    _fields: List[Field]

    _members: Dictionary[String, Object]

    def __init__(self, node: node_lib.Class | None, module: Module = None):
        super().__init__(node, module)
        self._name = node.name.name
        self._methods = List()
        self._fields = List()
        self._members = Dictionary()

    @property
    def name(self):
        return self._name

    def add(self, member: Member, name: str | String = None):
        if member.declaring_type is not None:
            raise ValueError(f"Member \"{member}\" is already attached to another type \"{member.declaring_type}\"")
        member._declaring_type = self

        name = getattr(member, "name", String(name) if name is not None else None)
        if name is None:
            raise ValueError(f"Member must have a non-null name")

        if name in self._members:
            self._members[name] += member
        else:
            self._members[name] = member

        match member:
            case Field() as field:
                self._fields.add(field)
            case MethodGroup() as method:
                self._methods.add(method)

    def get(self, name: str | String):
        try:
            return self._members[String(name)]
        except KeyError:
            raise UndefinedNameError(name, self)
