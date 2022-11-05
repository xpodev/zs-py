from contextlib import contextmanager
from functools import singledispatchmethod, partial

from .. import List, String, Int32
from ..objects.compilation_environment import Module
from ..objects.function import Function
from ... import Object
from ..objects.expression import Call, PushLocal, PopLocal, IndirectCall, ExternalCall
from ...base import NativeFunction
from ...processing import StatefulProcessor, State


class Frame:
    _callable: Object
    _locals: dict[str, Object]
    _names: list[str]

    def __init__(self, callable_: Object, arguments: dict[str, Object]):
        self._callable = callable_
        self._locals = arguments
        self._names = list(arguments.keys())

    def local(self, name: str | String | int | Int32, value: Object = None):
        if isinstance(name, (int, Int32)):
            name = self._names[int(name)]
        name = str(name)
        if value is None:
            return self._locals[name]
        if name not in self._locals:
            self._names.append(name)
        self._locals[name] = value


class Interpreter(StatefulProcessor):
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
    def execute(self, obj: Object) -> Object | None:
        # self.state.warning(f"Object \"{obj}\" is not runtime executable", getattr(obj, "node", obj))
        return obj

    _exec = execute.register

    @_exec
    def _(self, call: Call):
        function = call.callable
        if not isinstance(function, Function):
            return self.state.error(f"Can only call a function, not a \"{type(call.callable)}\"", call.node)
        if len(function.parameters) != len(call.arguments):
            return self.state.error(f"Invalid number of arguments passed to function \"{function}\" (expected {len(function.parameters)}, got {len(call.arguments)}", function.node)
        arguments = {
            parameter.name: self.execute(argument) for parameter, argument in zip(function.parameters, call.arguments)
        }
        with self.frame(function, arguments):
            result = []
            for item in function.body:
                result.append(self.execute(item))
            result = function.return_type.cast_from(List(result))
            return result

    @_exec
    def _(self, call: IndirectCall):
        return self.execute((Call if isinstance(call.callable, Function) else ExternalCall)(
            self.execute(call.callable),
            *call.arguments,
            call_operator=call.operator,
            node=call.node
        ))

    @_exec
    def _(self, call: ExternalCall):
        if call.operator == "_<>":
            callable_ = NativeFunction(partial(partial, call.callable))
            call = ExternalCall(callable_, *call.arguments, call_operator=call.operator, node=call.node)
        return call.callable(*map(self.execute, call.arguments))

    @_exec
    def _(self, get: PushLocal):
        return self.frame().local(get.name)

    @_exec
    def _(self, set_: PopLocal):
        return self.frame().local(set_.name, set_.value)
