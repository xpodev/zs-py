import typing
from contextlib import contextmanager
from functools import singledispatchmethod
from pathlib import Path
from typing import Iterable, Callable

from .dependency_resolver import DependencyResolver
from .import_system import ImportSystem, ImportResult
from ..runtime import interpreter
from .. import String, List, Int32
from ..objects.compilation_environment import ContextManager, Module
from ..objects.expression import Call, IndirectCall, ExternalCall
from ..objects.function import Function
from ..objects.type import Class, Method, MethodGroup
from ... import Object
from ...ast.node import Node
from ...ast import node_lib
from ...base import NativeFunction
from ...errors import UndefinedNameError
from ...processing import StatefulProcessor, State
from ...text.token import TokenType
from ...utils import ResolveOnDemand


_T = typing.TypeVar("_T")


def _get_dict_from_import_result(node: node_lib.Import, result: ImportResult):
    res = {}

    match node.name:
        case node_lib.Identifier() as star:
            if star.name != '*':
                raise ValueError(f"Can't perform a default import since that is not a feature yet")
            for name, item in result.all():
                res[name] = item
        case node_lib.Alias() as alias:
            raise ValueError(f"Can't perform a default import since that is not a feature yet")
        case List() as names:
            for name in names:
                if isinstance(name, node_lib.Alias):
                    assert isinstance(name.expression, node_lib.Identifier)
                    res[name.name.name] = result.item(str(name.expression.name))
                else:
                    res[name.name] = result.item(name.name)
        case _:
            raise TypeError("???")

    return res


class CallFrame:
    _scope: dict[str, Object]

    def __init__(self, **args):
        self._scope = args

    def get(self, name: str):
        return self._scope[name]

    def set(self, name: str, value: Object):
        self._scope[name] = value


class Resolver(StatefulProcessor):
    _ctx: ContextManager
    _cache: set[Object | None]
    _dep: DependencyResolver

    def __init__(self, state: State, context: ContextManager):
        super().__init__(state)
        self._ctx = context
        self._cache = {None}
        self._dep = DependencyResolver(state, context, self._cache)

    def resolve(self, obj: Object, enable_caching: bool = True):
        if enable_caching:
            try:
                if obj in self._cache:
                    # 'obj' is already resolved
                    return obj
                self._cache.add(self._resolve(obj))
            except TypeError:
                ...
        return self._resolve(obj)

    def resolve_dependencies(self, items: Iterable[Object]):
        return self._dep.resolve(filter(lambda item: item not in self._cache, items))

    @singledispatchmethod
    def _resolve(self, obj: Object):
        return obj

    _do = _resolve.register

    @_do
    def _(self, obj: Function):
        for parameter in obj.parameters:
            self.resolve(parameter)

        return obj

    @_do
    def _(self, obj: Call):
        group = obj.callable

        if not isinstance(group, MethodGroup):
            raise TypeError

        num_arguments = len(obj.arguments)

        overloads = []

        for overload in group.overloads:
            overload = self.resolve(overload)

            if len(overload.parameters) != num_arguments:
                continue

            for argument, parameter in zip(obj.arguments, overload.parameters):
                ...

            overloads.append(overload)

        if not overloads:
            return self.state.error(f"Could not find a suitable overload", obj)

        if len(overloads) != 1:
            return self.state.error(f"Argument list matched more than 1 overload", obj)

        return Call(overloads[0], *obj.arguments, call_operator=obj.operator, node=obj.node)

    @_do
    def _(self, module: Module):
        order = self.resolve_dependencies(module.members.values)
        for items in order:
            for item in items:
                self.resolve(item)
        return module

    @_do
    def _(self, items: List):
        return List(map(self.resolve, items))

    # @_do
    # def _(self, call: Call):
    #     return Call(self.resolve(call.callable), *map(self.resolve, call.arguments), call_operator=call.operator, node=call.node)


class Builder(StatefulProcessor):
    _ctx: ContextManager

    def __init__(self, state: State, ctx: ContextManager):
        super().__init__(state)
        self._ctx = ctx

    def context_is(self, t: typing.Type[_T]) -> _T:
        if not self._special_context:
            return None
        if isinstance(self._special_context[-1], t):
            return self._special_context[-1]

    @singledispatchmethod
    def build(self, node: Node) -> Object:
        raise TypeError(f"Can't execute node: \"{node}\"")

    _build = build.register


class Interpreter(StatefulProcessor):
    _call_stack: list[CallFrame]
    _ctx: ContextManager
    _import_system: ImportSystem
    _special_context: list[Object]
    _resolver: Resolver
    _resolve: bool
    _runtime: interpreter.Interpreter
    _builder: Builder

    def __init__(self, *, state: State = None, context: ContextManager = None, import_system: ImportSystem = None):
        super().__init__(state or State())
        self._call_stack = []
        self._ctx = context or ContextManager()
        self._import_system = import_system or ImportSystem()
        self._on_document_end: list[Callable] | None = None
        self._special_context = []
        self._resolver = Resolver(state, self._ctx)
        self._resolve = True
        self._runtime = interpreter.Interpreter(self.state)
        self._builder = Builder(self.state, self._ctx)

        ResolveOnDemand.resolver(self._resolver.resolve)

    @property
    def context(self):
        return self._ctx

    @property
    def import_system(self):
        return self._import_system

    @property
    def runtime(self):
        return self._runtime

    def execute_document(self, nodes: Iterable[Node]):
        super().run()

        self._on_document_end = []

        for node in nodes:
            self.runtime.execute(self.resolve(self.exec(node)))

        list(map(object.__call__, self._on_document_end))

    def context_is(self, t: typing.Type[_T]) -> _T:
        if not self._special_context:
            return None
        if isinstance(self._special_context[-1], t):
            return self._special_context[-1]

    @contextmanager
    def special_context(self, ctx):
        self._special_context.append(ctx)
        try:
            yield
        finally:
            self._special_context.pop()

    @typing.overload
    def resolve(self, resolve: bool) -> typing.ContextManager[Resolver]: ...
    @typing.overload
    def resolve(self, item: _T, force: bool = False) -> _T: ...
    @typing.overload
    def resolve(self, item: Object, force: bool = False) -> Object: ...

    def resolve(self, arg: _T | bool | Object, force: bool = False) -> Object | _T | typing.ContextManager[Resolver]:
        if isinstance(arg, bool):
            def wrapper(resolve):
                self._resolve, resolve = resolve, self._resolve
                try:
                    yield self._resolver
                finally:
                    self._resolve = resolve
            return contextmanager(wrapper)(arg)
        if self._resolve or force:
            return self._resolver.resolve(arg)
        return arg

    @singledispatchmethod
    def exec(self, node: Node):
        return self._builder.build(node)

    _do = exec.register

    # @_do
    # def _(self, node: node_lib.Assign):
    #     left = self.exec(node.left)
    #     right = self.exec(node.right)

    @_do
    def _(self, node: node_lib.Binary):
        left = self.runtime.execute(self.resolve(self.exec(node.left)))
        right = self.runtime.execute(self.resolve(self.exec(node.right)))

        try:
            getter = left.runtime_type.get(f"_{node.token_info.operator.value}_")
            cls = Call
            if not isinstance(getter, Function):
                cls = ExternalCall
            return self.runtime.execute(cls(getter, left, right))
        except KeyError:
            self.state.error(f"Type \"{left.runtime_type}\" does not define the a member access function", node)

        # self.state.warning(f"Binary operators are not implemented yet", node)

    @_do
    def _(self, node: node_lib.Import):
        with self.context.module(None):
            result = self.__get_import_result(node)

        for name, item in _get_dict_from_import_result(node, result).items():
            self._ctx.current_scope.add(item, name, reference=True)

        return result

    @_do
    def _(self, node: node_lib.Inlined):
        if isinstance(node.item, node_lib.Import):
            result = self.__get_import_result(node.item)
        else:
            result = self.exec(node.item)

        match result:
            case ImportResult() as import_result:
                if self.context.current_module is None:
                    return self.state.error(f"Can't inline import outside a module", node)
                assert isinstance(node.item, node_lib.Import)
                for name, item in _get_dict_from_import_result(node.item, import_result).items():
                    self.context.current_scope.add(item, name)

                return import_result

    @_do
    def _(self, node: node_lib.Function):
        if self.context_is(Class):
            func = Method(node.name.name, node)
        else:
            func = Function(node.name.name, node)
        if func.name is not None:
            try:
                group = self.context.current_scope.get(func.name)
            except UndefinedNameError:
                group = MethodGroup(func.name, module=self.context.current_module)
                self.context.add(group)
            group.add(func)

            def _call_function(*args: Object):
                call = Call(group, *args)
                call = self.resolve(call, force=True)
                return self.runtime.execute(call)

            group.__zs_call__ = _call_function

        for parameter in node.parameters:
            func.add_parameter(parameter.name.name, parameter.type)

        func.body.extend(map(self.exec, node.body))

        func = self.resolve(func)

        return func

    @_do
    def _(self, node: node_lib.FunctionCall):
        callable_ = self.resolve(self.exec(node.callable))

        if isinstance(callable_, NativeFunction):
            cls = ExternalCall
        elif isinstance(callable_, Function):
            cls = Call
        else:
            cls = IndirectCall
        return cls(callable_, *node.arguments, node=node)
        # self.state.warning(f"Compile-time function calls are not implemented yet. Please avoid relying on those", node)

    @_do
    def _(self, node: node_lib.Class):
        cls = Class(node, self.context.current_module)
        if cls.name is not None:
            self._ctx.add(cls)

        with self.context.scope(cls), self.special_context(cls):
            for node in node.items:
                self.exec(node)

        return cls

    @_do
    def _(self, node: node_lib.Literal):
        value = node.token_info.literal.value
        match node.token_info.literal.type:
            case TokenType.String:
                return String(value)
            case TokenType.Decimal:
                return Int32(int(str(node.token_info.literal.value)))
            case _:
                raise TypeError(node.token_info.literal.type)

    @_do
    def _(self, node: node_lib.MemberAccess):
        left = self.exec(node.object)
        try:
            getter = left.runtime_type.get("_._")
            cls = Call
            if not isinstance(getter, Function):
                cls = ExternalCall
            return cls(getter, left, node.member.name)
        except KeyError:
            self.state.error(f"Type \"{left.runtime_type}\" does not define the a member access function", node)

    @_do
    def _(self, node: node_lib.Module):
        with self.context.module(node, node.items is not None) as module, self.resolve(False) as resolver:
            body = []
            for item in node.items:
                result = self.exec(item)
                if result is not None:
                    body.append(result)
            if not node.items:
                def reset():
                    self.context.module_stack.pop()

                self._on_document_end.append(reset)

            resolver.resolve(module)

            with self.runtime.module(module):
                for item in body:
                    self.runtime.execute(item)

    @_do
    def _(self, node: node_lib.Identifier):
        try:
            item = self.context[node.name]
        except UndefinedNameError:
            self.state.error(f"Could not resolve name \"{node.name}\"", node)
        else:
            return self.resolve(item, True)

    def __get_import_result(self, node: node_lib.Import):
        source = self.exec(node.source)
        if not isinstance(source, String):
            raise TypeError(f"Import statement source must evaluate to a string, not \"{type(source)}\"")

        path = Path(str(source))

        result = self._import_system.import_from(path)

        if result is None:
            return self.state.error(f"Could not import \"{path}\"", node)

        result._node = node

        return result
