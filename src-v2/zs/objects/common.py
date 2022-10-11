from typing import TypeVar, Generic

from zs import Object
from zs.ast.node import Node
from zs.std.objects.wrappers import String

_T = TypeVar("_T", bound=Node)


class NamedObject(Object[_T], Generic[_T]):
    _name: String | None

    def __init__(self, node: _T | None, name: str | String | None):
        super().__init__(node)
        if name is not None and isinstance(name, str):
            name = String(name)
        self._name = name

    @property
    def name(self):
        return self._name


class EmptyNamedObject(NamedObject[None]):
    def __init__(self, name: str | String | None):
        super().__init__(None, name)


class TypedName(NamedObject[_T], Generic[_T]):
    _type: Object | None

    def __init__(self, node: _T | None, name: str | String | None, type_: Object):
        super().__init__(node, name)
        self._type = type_

    @property
    def type(self):
        return self._type


class EmptyTypedName(TypedName[None]):
    def __init__(self, name: str | String | None, type_: Object):
        super().__init__(None, name, type_)
