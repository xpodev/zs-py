from functools import singledispatchmethod
from typing import Iterable

from zs import Object
from zs.ast import node_lib
from zs.dependency_graph import DependencyGraph
from zs.errors import UndefinedNameError
from zs.processing import StatefulProcessor, State
from zs.std.objects.compilation_environment import ContextManager
from zs.std.objects.function import Function
from zs.std.objects.type import MethodGroup


class DependencyResolver(StatefulProcessor):
    _context: ContextManager
    _graph: DependencyGraph[Object]
    _cache: set[Object]
    _temp: list[Object]

    def __init__(self, state: State, context: ContextManager, cache: set[Object] = None):
        super().__init__(state)
        self._context = context
        self._graph = DependencyGraph[Object]()
        self._cache = cache or {None}

    def resolve(self, items: Iterable[Object]):
        self.run()

        for item in items:
            self._temp = []
            self._resolve(item)
            if self._temp is not None:
                self._graph.add(item, *self._temp)

        return self._graph.get_dependency_order(self.state)

    def _resolve(self, item: Object):
        if item not in self._cache:
            self._dispatch(item)

    @singledispatchmethod
    def _dispatch(self, _: Object):
        return []

    _do = _dispatch.register

    @_do
    def _(self, name: node_lib.Identifier):
        try:
            self._resolve(self._context[name.name])
        except UndefinedNameError:
            self.state.error(f"Could not resolve name \"{name.name}\"")

    @_do
    def _(self, ms: MethodGroup):
        for method in ms.overloads:
            self._resolve(method)

    @_do
    def _(self, fn: Function):
        for parameter in fn.parameters:
            self._resolve(parameter.type)

        self._resolve(fn.return_type)
