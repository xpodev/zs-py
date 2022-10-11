from functools import singledispatchmethod
from typing import Iterable

from zs import Object
from zs.dependency_graph import DependencyGraph
from zs.processing import StatefulProcessor, State


class DependencyResolver(StatefulProcessor):
    _graph: DependencyGraph[Object]

    def __init__(self, state: State):
        super().__init__(state)
        self._graph = DependencyGraph[Object]()

    def resolve(self, items: Iterable[Object]):
        self.run()

        for item in items:
            self._graph.add(item, *self.resolve_dependencies(item))

        return self._graph.get_dependency_order(self.state)

    @singledispatchmethod
    def resolve_dependencies(self, item: Object):
        return []

    _resolve = resolve_dependencies.register
