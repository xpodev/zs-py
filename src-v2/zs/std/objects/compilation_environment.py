from contextlib import contextmanager
from typing import Iterable, Optional, TypeVar, Generic, Any

from ... import EmptyObject, Object
from ...ast import node_lib
from ...ast.node import Node
from ...base import Null
from ...errors import UnnamedObjectError, DuplicateDefinitionError, UndefinedNameError
from ...text.file_info import DocumentInfo


_T = TypeVar("_T")


class IScope:
    @property
    def parent(self):
        return

    def add(self, value: Object, name: str = None, reference: bool = False):
        """
        Add a new item to the scope.
        If an item with the same name already exists it will be added to the existing item via the += operator.
        If it is not defined, an `DuplicateDefinitionError` is raised

        item: Object -
        """
        ...

    def get(self, name: str) -> Object:
        """
        Searches the scope for the given name and returns the object associated with it.
        if no such object exists, raise an `UndefinedNameError`

        This function should support the __get__ special method.
        """

    def set(self, name: str, value: Object):
        """
        Set a new value to associate with the given name.

        This function should support __set__ special method.
        """


class Scope(Object[_T], Generic[_T], IScope):
    _map: dict[str, Object]
    _parent: Optional["Scope"]

    def __init__(self, node: _T = None, parent: Optional["Scope"] = None, **items: Object):
        super().__init__(node)
        self._map = items
        self._parent = parent

    @property
    def parent(self):
        return self._parent

    @property
    def items(self):
        return self._map.items()

    @property
    def values(self):
        return self._map.values()

    def add(self, value: Object, name: str = None, reference: bool = False):
        name = name or getattr(value, "name")
        if name is None:
            raise UnnamedObjectError(value, f"Can't add an unnamed object to the context")
        if name in self._map:
            try:
                self._map[name] += value
            except TypeError:
                raise DuplicateDefinitionError(name, self)
        else:
            self._map[name] = value

    def get(self, name: str):
        try:
            return self._map[name]
        except KeyError:
            raise UndefinedNameError(name, self)

    def set(self, name: str, value: Object):
        if name not in self._map:
            raise UndefinedNameError(name, self)
        else:
            self._map[name] = value

    def __iter__(self):
        return iter(self._map)


class Document(Scope):
    _info: DocumentInfo
    _module: "Module"
    _nodes: list[Node]

    def __init__(self, info: DocumentInfo | None, nodes: Iterable[Node]):
        super().__init__()
        self._info = info
        self._nodes = list(nodes)

    @property
    def info(self):
        return self._info

    @property
    def module(self):
        return self._module

    @property
    def nodes(self):
        return self._nodes


class Module(Scope[node_lib.Module]):
    _name: str
    _documents: list[Document]
    _members: Scope
    _exported_items: dict[str, Object]
    _parent: Optional["Module"]
    _entry_point: Any  # type: Optional["Function"]  # why do I need to trick the IDE tho :/

    def __init__(self, name: str, node: node_lib.Module = None, parent: "Module" = None):
        if parent is None:
            super().__init__(node, this=self)
        else:
            super().__init__(node, this=self, base=parent)
        self._name = name
        self._parent = parent
        self._documents = []
        self._members = Scope()
        self._exported_items = {}
        self._entry_point = Null

    @property
    def name(self):
        return self._name

    @property
    def members(self):
        return self._members

    @property
    def parent(self):
        return self._parent

    @property
    def entry_point(self):
        return self._entry_point

    @entry_point.setter
    def entry_point(self, value):
        self._entry_point = value

    def add(self, item: Object, name: str = None, reference: bool = False, export: bool = False):
        if not reference:
            self._members.add(item, name, reference)

        name = name or getattr(item, "name", None)
        if name is None:
            raise UnnamedObjectError(item, f"Can't add an unnamed member to a module")

        super().add(item, name, reference)

        if export:
            # todo: make scope instead of regular dictionary
            self._exported_items[name] = item

    def add_document(self, document: Document):
        if document.module is not None:
            raise ValueError(f"Document is already inside a module")
        document._module = self
        self._documents.append(document)

    def set_entry_point(self, entry_point):
        self.entry_point = entry_point


class ModuleMember(Object[_T], Generic[_T]):
    _module: Module

    def __init__(self, node: _T, module: Module = None):
        super().__init__(node)
        self._module = module

    @property
    def module(self):
        return self._module


class ContextManager(EmptyObject):
    _document: Document | None
    _scopes: list[IScope]
    _module_stack: list[None | Module]
    _global_context: IScope
    _cache: dict[str, list[Node]]
    _modules: list[Module]

    def __init__(self, global_context: Scope = None):
        super().__init__()
        self._document = None
        self._global_context = global_context or Scope()
        self._scopes = [self._global_context]
        self._cache = {}
        self._module_stack = [None]
        self._modules = []

    @property
    def current_document(self):
        return self._document

    @property
    def current_module(self):
        return self._module_stack[-1]

    @property
    def current_scope(self):
        return self._scopes[-1]

    @property
    def global_context(self):
        return self._global_context

    @property
    def global_scope(self):
        return self._scopes[0]

    @property
    def module_stack(self):
        return self._module_stack

    @property
    def modules(self):
        """
        returns all top-level modules
        """
        return self._modules

    @property
    def srf(self):
        return self._global_context.get("__srf__")

    @srf.setter
    def srf(self, value):
        self._global_context.set("__srf__", value)

    @contextmanager
    def module(self, node: node_lib.Module | None, pop: bool = True):
        if node is not None:
            name = str(node.name)
            module = Module(name, node, self.current_module)

            if module.parent is None:
                self._modules.append(module)

            self.current_scope.add(module)

            try:
                with self.scope(module):
                    self._module_stack.append(module)
                    yield module
            finally:
                if pop:
                    self._module_stack.pop()
        else:
            try:
                self._module_stack.append(None)
                yield
            finally:
                self._module_stack.pop()

    @contextmanager
    def document(self, document: Document):
        # todo: does this really need to be so ugly?
        # probably not. we just need to get all the document scopes out of the scope stack
        last_stack = self._scopes
        self._scopes = [self._global_context]
        last_document = self._document
        self._document = document

        try:
            with self.scope(document):
                if self.current_module is not None:
                    self._scopes.append(self.current_module)
                yield document
        finally:
            self._scopes = last_stack
            self._document = last_document

    @contextmanager
    def scope(self, scope: IScope = None):
        if scope is None:
            scope = Scope()
        try:
            self._scopes.append(scope)
            yield scope
        finally:
            self._scopes.pop()

    def add(self, item: Object, name: str = None):
        self.current_scope.add(item, name)

    def get_nodes_from_cached(self, path: str) -> list[Node] | None:
        try:
            return self._cache[path]
        except KeyError:
            return None

    def __getitem__(self, name: str) -> Object:
        for scope in reversed(self._scopes):
            try:
                return scope.get(name)
            except UndefinedNameError:
                ...
        raise UndefinedNameError(name, self.current_scope)

    def __setitem__(self, name: str, value: Object):
        for scope in reversed(self._scopes):
            try:
                scope.set(name, value)
            except KeyError:
                ...
        raise UndefinedNameError(name, self.current_scope)
