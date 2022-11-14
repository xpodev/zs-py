from contextlib import contextmanager
from functools import singledispatchmethod
from pathlib import Path

from zs.processing import State, StatefulProcessor
from .context import Scope
from .instructions import Instruction, SetLocal, Call, Name, Import, EnterScope, ExitScope, DeleteName, Do, Raw, RawCall
from .lib import Function, CodeGenFunction
from .. import Object
from ..ast import node_lib
from ..std.processing.import_system import ImportSystem, ImportResult


def _get_dict_from_import_result(node: Import, result: ImportResult):
    res = {}
    errors = []

    match node.names:
        case str() as star:
            if star != '*':
                raise ValueError(f"Can't perform a default import since that is not a feature yet")
            for name, item in result.all():
                res[name] = item
        case node_lib.Alias() as alias:
            raise ValueError(f"Can't perform a default import since that is not a feature yet")
        case list() as names:
            for name in names:
                try:
                    if isinstance(name, tuple):
                        name, item = name
                        res[name] = result.item(item)
                    else:
                        res[name] = result.item(name)
                except KeyError:
                    errors.append(f"Could not import name \"{name}\" from \"{node.source}\"")
        case _:
            raise TypeError("???")

    return res, errors


SENTINEL = object()


class InterpreterState:
    _frames: list[dict[str, Object]]
    _scope: Scope | None
    _global: Scope

    def __init__(self, global_scope: Scope = None):
        self._frames = []
        self._global = global_scope or Scope()
        self._scope = self._global

    @property
    def global_scope(self):
        return self._global

    @property
    def local_scope(self):
        return self._scope

    @property
    def frame(self):
        def _(frame: dict[str, Object] = None):
            if frame is None:
                return self._frames[-1]

            @contextmanager
            def _():
                self._frames.append(frame)
                try:
                    yield
                finally:
                    self._frames.pop()

            return _

        return _

    def scope(self, scope_: Scope = None):
        @contextmanager
        def _(scope):
            if scope is None:
                scope = Scope(self._scope)

            scope, self._scope = self._scope, scope
            try:
                yield self._scope
            finally:
                self._scope = scope

        return _(scope_)

    def enter_scope(self, scope: Scope = None):
        if scope is None:
            scope = Scope(self._scope)

        self._scope = scope

    def exit_scope(self):
        self._scope = self._scope.parent

    def local(self, name: str, value: Object | None = SENTINEL, /, *, strict=False, new=False):
        if value is SENTINEL:
            return self._scope.name(name, strict=strict, new=new)
        return self._scope.name(name, value, strict=strict, new=new)


class Interpreter(StatefulProcessor):
    def __init__(self, state: State):
        super().__init__(state)
        self._x = InterpreterState()
        self._import_system = ImportSystem()

    def execute(self, inst: Object, *args, **kwargs):
        self.run()
        return self._execute(inst, *args, **kwargs)

    @singledispatchmethod
    def _execute(self, inst: Instruction):
        # self.state.warning(f"Executing instruction {inst} failed", inst)
        return inst

    @property
    def import_system(self):
        return self._import_system

    @property
    def x(self):
        return self._x

    _exec = _execute.register

    @_exec
    def _(self, inst: Do):
        return list(map(self.execute, inst.instructions))

    @_exec
    def _(self, inst: Raw):
        return inst.instruction

    @_exec
    def _(self, inst: SetLocal):
        if self._x.local(inst.name, self.execute(inst.value), new=True) is False:
            self.state.error(f"Variable {inst.name} already exists in scope", inst)
        return inst

    @_exec
    def _(self, inst: Call):
        callable_ = self.execute(inst.callable) if not isinstance(inst.callable, Function) else inst.callable

        if callable_ is None:
            return inst

        if callable(getter := getattr(callable_, "get", None)):
            try:
                callable_ = getter()
            except TypeError:
                ...

        if isinstance(callable_, CodeGenFunction):
            return self.execute(RawCall(callable_, inst.args, inst.node))
        if isinstance(callable_, Function):
            if len(inst.args) != len(callable_.parameters):
                self.state.error(f"Function \"{callable_.name}\" was called with an improper amount of arguments")
            else:
                with self._x.scope(Scope(callable_.scope)) as scope:
                    for argument, parameter in zip(inst.args, callable_.parameters):
                        self._x.local(str(parameter.name), self.execute(argument), new=True)

                    last = None
                    for inst in callable_.body:
                        last = self.execute(inst)
                    return last

        if not callable(callable_):
            self.state.error(f"The base interpreter may only execute native functions!", inst)
            return inst

        return self.execute(callable_(*map(self.execute, inst.args)))

    @_exec
    def _(self, inst: RawCall):
        callable_ = self.execute(inst.callable)

        if callable_ is None:
            return inst

        if isinstance(callable_, Function):
            if len(inst.args) != len(callable_.parameters):
                self.state.error(f"Function \"{callable_.name}\" was called with an improper amount of arguments")
            else:
                with self._x.scope() as scope:
                    for argument, parameter in zip(inst.args, callable_.parameters):
                        scope.name(str(parameter.name), argument)

                    last = None
                    for inst in callable_.body:
                        last = self.execute(inst)
                    return last

        if not callable(callable_):
            self.state.error(f"The base interpreter may only execute native functions!", inst)
            return inst

        return callable_(*inst.args)

    @_exec
    def _(self, fn: Function, *args, execute=False):
        if execute:
            return self.execute(Call(fn, list(args)))
        return fn

    @_exec
    def _(self, inst: Name):
        result = self._x.local(inst.name)
        if result is None:
            self.state.error(f"Could not resolve name \"{inst.name}\"", inst)
        return result

    @_exec
    def _(self, inst: Import):
        with self._x.scope():
            result = self.__get_import_result(inst)

        items, errors = _get_dict_from_import_result(inst, result)
        for name, item in items.items():
            self._x.local(name, item, new=True)

        for error in errors:
            self.state.error(error, inst)

        return result

    @_exec
    def _(self, _: EnterScope):
        self._x.enter_scope(Scope(_.parent or self._x.local_scope))
        return _

    @_exec
    def _(self, _: ExitScope):
        self._x.exit_scope()
        return _

    @_exec
    def _(self, _: DeleteName):
        result = self._x.local(_.name, strict=True)
        if not self._x.local(_.name, None):
            self.state.error(f"Could not delete name \"{_.name}\" because it doesn't exist in the current scope", _)
        return result

    def __get_import_result(self, inst: Import):
        source = self.execute(inst.source)
        if isinstance(source, str):
            # raise TypeError(f"Import statement source must evaluate to a string, not \"{type(source)}\"")

            path = Path(str(source))

            result = self._import_system.import_from(path)

            if result is None:
                return self.state.error(f"Could not import \"{path}\"", inst)

            result._node = inst.node

            return result

        return source  # todo: make sure is ImportResult

