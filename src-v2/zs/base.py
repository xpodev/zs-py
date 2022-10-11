from typing import TypeVar, Generic, TYPE_CHECKING

_T = TypeVar("_T")


__all__ = [
    "EmptyObject",
    "Object",
]


class Object(Generic[_T]):
    _node: _T | None

    def __init__(self, node: _T | None = None):
        self._node = node

    @property
    def node(self):
        return self._node


class EmptyObject(Object[None]):
    def __init__(self):
        super().__init__(None)

    if TYPE_CHECKING:
        @property
        def node(self):
            return None
