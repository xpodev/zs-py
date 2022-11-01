from functools import singledispatchmethod


class Definer:
    @singledispatchmethod
    def definition(obj: BuildResult):
        ...

    _def = definition.register
