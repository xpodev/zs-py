from typing import Callable

from zs import Object


class ResolveOnDemand:
    _resolver: Callable[[Object], Object]

    def __init__(self, original: property, name: str = None):
        self._original = original
        self._name = name

    def __get__(self, instance, owner):
        setattr(instance, self._name, self.resolve(getattr(instance, self._name)))
        setattr(owner, self._original_name, self._original)
        return self._original.__get__(instance, owner)

    def __set_name__(self, owner, name):
        self._original_name = name
        self._name = self._name or '_' + name

    @classmethod
    def resolve(cls, o: Object):
        return cls._resolver(o)

    @classmethod
    def resolver(cls, resolver: Callable[[Object], Object] = None):
        if resolver is None:
            return cls._resolver
        cls._resolver = resolver


def resolve_on_demand(name_or_property: str | property):
    name = name_or_property if isinstance(name_or_property, str) else None

    def wrapper(prop: property):
        return ResolveOnDemand(prop, name)

    if isinstance(name_or_property, property):
        return wrapper(name_or_property)
    return wrapper
