from inspect import get_annotations
from typing import TypeVar, Generic, Any

from zs.ast import node_lib
from zs.base import Type, EmptyObject, Object, NativeFunction
from zs.objects.common import TypedName
from zs.std import Bool, String, List, Int32
# from zs.std.objects.compilation_environment import ModuleMember, Module
from zs.std.objects.function import Function

_T = TypeVar("_T")


class Member(Object[_T], Generic[_T]):
    _declaring_type: Type
    _is_static: Bool

    def __init__(self, node: _T, declaring_type: Type = None, *args, **kwargs):
        super().__init__(node)
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
    _declaring_type: Type


class MethodGroup(EmptyObject, Member):
    _name: String
    _methods: List[Method]

    def __init__(self, name: str | String, *overloads: Function | Method, **kwargs):
        super().__init__()
        Member.__init__(self, None, **kwargs)
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


def zs_data(**config):
    def wrapper(o):
        o.__zs_data__ = config

        return o

    return wrapper


def zs_function(name: str = None, *, constructor=None):
    constructor = constructor or NativeFunction

    def construct_function(func):
        fn = constructor(func, name=name)

        # typing = get_annotations(func)
        #
        # fn.return_type = typing.pop("return", Object).__zs_type__
        #
        # for parameter_name, parameter_type in typing.items():
        #     fn.add_parameter(String(parameter_name), parameter_type.__zs_type__ if parameter_type != Any else Object.__zs_type__)

        return zs_data()(fn)

    return construct_function


def zs_type(name: str = None, *, metaclass=None):
    metaclass = metaclass or Type

    def construct_type(cls: type):
        typ = metaclass(None)

        cls.__zs_type__ = typ

        typ.name = name or cls.__name__

        for item_name, item in vars(cls).items():
            if (data := getattr(item, "__zs_data__", None)) is None:
                continue

            if item_name in typ._members:
                typ._members[name] += item
            else:
                typ._members[name] = item

        return cls

    return construct_type
