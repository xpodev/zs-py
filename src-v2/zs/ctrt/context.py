from typing import Optional

from zs import Object, EmptyObject


SENTINEL = object()


class Scope(EmptyObject):
    _parent: Optional["Scope"]
    _items: dict[str, Object]

    def __init__(self, parent: Optional["Scope"] = None, **items: Object):
        super().__init__()
        self._items = items
        self._parent = parent

    @property
    def parent(self):
        return self._parent

    def name(self, name: str, value: Object | None = SENTINEL, /, *, strict=False, new=False, srf=False):
        if value is SENTINEL:
            if name not in self._items:
                if strict:
                    return None
                if self._parent is None:
                    return None
                return self._parent.name(name, strict=strict)
            return self._items[name]
        if value is None:
            return self._items.pop(name, None)
        if new:
            if strict and name in self._items:
                return False
            self._items[name] = value
            return True
        else:
            if name not in self._items:
                if strict:
                    return False
                if self._parent is not None and self._parent.name(name, value, strict=strict):
                    return True
            self._items[name] = value
            return True
