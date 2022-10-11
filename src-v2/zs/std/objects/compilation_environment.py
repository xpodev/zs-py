from contextlib import contextmanager
from typing import Iterable, Optional

from ... import EmptyObject, Object
from ...ast import node_lib
from .wrappers import List, String, Dictionary, Bool
from ...ast.node import Node
from ...processing import Context


class Document(Context):
    _module: "Module"
    _nodes: List[Node]

    def __init__(self, nodes: Iterable[Node]):
        super().__init__()
        self._nodes = List(nodes)

    @property
    def module(self):
        return self._module

    @property
    def nodes(self):
        return self._nodes


class Module(Object[node_lib.Module]):
    _name: String
    _documents: List[Document]
    _items: List[Object]
    _exported_items: Dictionary[String, Object]
    _parent: Optional["Module"]

    def __init__(self, name: str | String, parent: "Module" = None):
        super().__init__()
        self._name = String(name)
        self._parent = parent
        self._documents = List()
        self._items = List()
        self._exported_items = Dictionary()

    @property
    def name(self):
        return self._name

    @property
    def parent(self):
        return self._parent

    def add(self, item: Object, name: str | String = None, export: bool | Bool = False):
        self._items.add(item)
        name = name or getattr(item, "name", None)
        if name is None:
            raise TypeError(f"Can't export an unnamed item")
        if export:
            self._exported_items[String(name)] = item

    def add_document(self, document: Document):
        if document.module is not None:
            raise ValueError(f"Document is already inside a module")
        self._documents.add(document)


class ContextManager(EmptyObject):
    _scopes: list[Context]
    _documents: list[Document]
    _module: Module | None
    _module_cache: dict[str, Module]
    _global_context: Context

    def __init__(self, global_context: Context = None):
        super().__init__()
        self._global_context = global_context or Context()
        self._scopes = [self._global_context]
        self._module_cache = {}
        self._module = None
        self._documents = []

    @property
    def current_document(self):
        return self._documents[-1]

    @property
    def current_module(self):
        return self._module

    @property
    def current_scope(self):
        return self._scopes[-1]

    @property
    def global_context(self):
        return self._global_context

    @property
    def global_scope(self):
        return self._scopes[0]

    @contextmanager
    def module(self, module: Module, name: str | String = None):
        name = str(name or module.name)
        if name in self._module_cache:
            raise ValueError(f"Module \"{module.name}\" was already closed")
        if module.parent is None:
            self._module_cache[name] = module

        last_module = self._module
        try:
            self._module = module
            yield module
        finally:
            self._module = last_module

    @contextmanager
    def document(self, document: Document):
        try:
            self._documents.append(document)
            yield document
        finally:
            self._documents.pop()

    @contextmanager
    def scope(self, scope: Context):
        try:
            self._scopes.append(scope)
            yield scope
        finally:
            self._scopes.pop()

    def __getitem__(self, name: str | String) -> Object:
        return self.current_scope.get(name)

    def __setitem__(self, name: str | String, value: Object):
        self.current_scope.set(name, value)
