from zs import Object
from zs.ctrt.context import Scope

_SINGULARITY = object()


class Parameter:
    def __init__(self, name: str, type_: Object, index: int, function: "Function"):
        self.name = name
        self.type = type_
        self.index = index
        self.owner = function


class Function(Object):
    parameters: list[Parameter]

    def __init__(self, name: str | None, scope: Scope = None, node=None):
        super().__init__(node)
        self.name = name
        self.parameters = []
        self.body = []
        self.scope = scope

    def add_parameter(self, name: str, type_: Object):
        parameter = Parameter(name, type_, len(self.parameters), self)
        self.parameters.append(parameter)
        return parameter


class CodeGenFunction(Function):
    ...


class Field:
    ref: "ExObj"

    def __init__(self, ref: "ExObj", name: str):
        self.ref = ref
        self.name = name

    def __str__(self):
        return f"field {self.name} of {self.ref}"

    def get(self):
        return super(ExObj, self.ref).__getattribute__(self.name)

    def set(self, value):
        setattr(self.ref, self.name, value)
        return self


class ExObj(object):
    def make_field(self, name: str, value=_SINGULARITY):
        if value is _SINGULARITY:
            return Field(self, name)
        return self.make_field(name).set(value)

    @staticmethod
    def none():
        return None
