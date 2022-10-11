from zs.std import Type


__all__ = [
    "zs_type",
]


def zs_type(cls_or_none=None, *, name: str = None):
    def _internal(cls):
        if not isinstance(cls, type):
            raise TypeError(f"The 'zs_type' decorator can only be applied to types, not '{type(cls)}'")

        result = Type()

        result.name = name or cls.__name__

        return result

    if cls_or_none is not None:
        return _internal(cls_or_none)
    return _internal
