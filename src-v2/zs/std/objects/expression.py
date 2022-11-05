from zs import Object
from zs.ast import node_lib
from zs.std import List, String, Int32


class Call(Object[node_lib.FunctionCall]):
    _callable: Object
    _arguments: List[Object]
    _call_operator: String

    def __init__(self, callable_: Object, *args: Object, call_operator: str | String = "_()", node: node_lib.FunctionCall = None):
        super().__init__(node)
        self._callable = callable_
        self._arguments = List(args)
        self._call_operator = call_operator

    @property
    def callable(self):
        return self._callable

    @property
    def arguments(self):
        return self._arguments

    @property
    def operator(self):
        return self._call_operator


class IndirectCall(Call):
    ...


class ExternalCall(Call):
    ...


class PushLocal(Object[node_lib.Expression]):
    _name: String

    def __init__(self, name: str | String, node: node_lib.Expression = None):
        super().__init__(node)
        self._name = String(name)

    @property
    def name(self):
        return self._name


class PopLocal(Object[node_lib.Expression]):
    _name: String

    def __init__(self, name: str | String, node: node_lib.Expression = None):
        super().__init__(node)
        self._name = String(name)

    @property
    def name(self):
        return self._name


class Binary(Object[node_lib.Binary]):
    _left: Object
    _right: Object
    _operator: String

    def __init__(self, left: Object, right: Object, operator: str | String, node: node_lib.Binary = None):
        super().__init__(node)
        self._left = left
        self._right = right
        self._operator = String(operator)


# the interpreter should be implemented as a stack machine
