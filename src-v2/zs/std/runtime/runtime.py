from contextlib import contextmanager
from functools import singledispatchmethod

from .. import String
from ..objects.compilation_environment import Module
from ... import Object
from ...ast import node_lib
from ...processing import StatefulProcessor, State


class Scope:
    _items: dict[Object]


class Frame:
    _callable: Object
    _locals: dict[str, Object]

    def __init__(self, callable_: Object, arguments: dict[str, Object]):
        self._callable = callable_
        self._locals = arguments

    def local(self, name: str | String, value: Object = None):
        name = str(name)
        if value is None:
            return self._locals[name]
        self._locals[name] = value


def get_binary_operator_function(left: Object, right: Object, op: str | String):
    if op_fn := getattr(left, f"_{str(op)}_", None):
        op_fn = op_fn.bind()
    if op_fn := getattr(right, f"_{str(op)}_", op_fn):
        ...
    if op_fn is None:
        return None


class Runtime(StatefulProcessor):
    _module: Module | None
    _frames: list[Frame]

    def __init__(self, state: State):
        super().__init__(state)
        self._module = None
        self._frames = []

    @contextmanager
    def module(self, module: Module):
        self._module, module = module, self._module
        try:
            yield
        finally:
            self._module = module

    def frame(self, *args):
        if args:
            @contextmanager
            def wrapper():
                try:
                    frame = Frame(*args)
                    self._frames.append(frame)
                    yield frame
                finally:
                    self._frames.pop()
            return wrapper()
        return self._frames[-1]

    @singledispatchmethod
    def execute(self, node: node_lib.Node) -> Object | None:
        return self.state.warning(f"Can't process node {node}", node)
        # return node

    _exec = execute.register

    @_exec
    def _(self, node: node_lib.Binary):
        ...
