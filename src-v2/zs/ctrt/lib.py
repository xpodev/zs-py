from zs import Object


class Parameter:
    def __init__(self, name: str, type_: Object, index: int, function: "Function"):
        self.name = name
        self.type = type_
        self.index = index
        self.owner = function


class Function:
    def __init__(self, name: str | None):
        self.name = name
        self.parameters = []
        self.body = []

    def add_parameter(self, name: str, type_: Object):
        parameter = Parameter(name, type_, len(self.parameters), self)
        self.parameters.append(parameter)
        return parameter


class ExObj(object):
    @staticmethod
    def none():
        return None
