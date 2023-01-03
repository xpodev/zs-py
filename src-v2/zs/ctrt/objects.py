from typing import Optional, Any, Callable

from zs.ast.node import Node
from zs.ctrt.errors import NameNotFoundError, NameAlreadyExistsError, NoParentScopeError


class Parameter:
    _owner: "Function"
    name: str
    type: Any

    def __init__(self, name: str, typ: Any, owner: "Function"):
        self.name = name
        self.type = typ
        self._owner = owner

    @property
    def owner(self):
        return self._owner

    @property
    def index(self):
        return self._owner.parameters.index(self)


class FunctionType:
    def is_subclass(self, of):
        return of is self


class NativeFunction:
    _native: Callable[..., Any]
    _runtime: bool

    type = FunctionType

    def __init__(self, native: Callable[..., Any], include_runtime: bool = False):
        self._native = native
        self._runtime = include_runtime

    @property
    def include_runtime(self):
        return self._runtime

    def invoke(self, *args, **kwargs):
        return self._native(*args, **kwargs)


class Function:
    """
    Represents a Z# function that's used by the ct-runtime interpreter.
    """

    class Body:
        nodes: list[Node]

        def __init__(self):
            self.nodes = []

    name: str | None
    _lexical_scope: "Scope"
    _parameters: list[Parameter]
    _body: Body

    type = FunctionType

    def __init__(self, lexical_scope: "Scope"):
        self._lexical_scope = lexical_scope
        self._parameters = []
        self._body = self.Body()

    @property
    def lexical_scope(self):
        return self._lexical_scope

    @property
    def parameters(self):
        return self._parameters.copy()

    @property
    def body(self):
        return self._body

    def add_parameter(self, name=None, typ=None):
        parameter = Parameter(name, typ, self)
        self._parameters.append(parameter)
        return parameter


class Scope:
    _parent: Optional["Scope"]
    _items: dict[str, Any]

    def __init__(self, parent: Optional["Scope"] = None):
        self._parent = parent
        self._items = {}

    @property
    def is_toplevel_scope(self):
        return self._parent is None

    @property
    def parent(self):
        return self._parent

    @property
    def items(self):
        return self._items.items()

    def add_local(self, name: str, value: Any = None):
        """
        Adds a new storage unit to this scope.

        :raises: `NameAlreadyExistsError` if the name is already present in the context.
        """
        if name in self._items:
            raise NameAlreadyExistsError(name, self)
        self._items[name] = value

    def get_local(self, name: str) -> Any:
        """
        Get a value bound to the given name in this scope.

        :return: The value bound to the given name.

        :raises: `NameNotFoundError` if the name doesn't exist in the current context.
        """
        try:
            return self._items[name]
        except KeyError:
            raise NameNotFoundError(name, self)

    def set_local(self, name: str, value: Any):
        """
        Set a value bound to the given name in this scope.

        :raises: `NameNotFoundError` if the name doesn't exist in the current context.
        """
        if name not in self._items:
            raise NameNotFoundError(name, self)
        self._items[name] = value

    def get_nonlocal(self, name: str):
        """
        Get a value bound to the given name in a parent scope.

        :raises: `NameNotFoundError` if the name doesn't exist in the current context.
        """
        if self.parent is None:
            raise NoParentScopeError(self)
        return self.parent.get_name(name)

    def set_nonlocal(self, name: str, value: Any):
        """
        Set a value bound to the given name in a parent scope.

        :raises: `NameNotFoundError` if the name doesn't exist in the current context.
        """
        if self.parent is None:
            raise NoParentScopeError(self)
        self.parent.set_name(name, value)

    def get_name(self, name: str):
        """
        Get a value bound to the given name in this or a parent scope.

        :raises: `NameNotFoundError` if the name doesn't exist in the current context.
        """
        if name in self._items:
            return self.get_local(name)
        if self.parent is None:
            raise NameNotFoundError(name, self)
        return self.parent.get_name(name)

    def set_name(self, name: str, value: Any):
        """
        Set a value bound to the given name in this or a parent scope.

        :raises: `NameNotFoundError` if the name doesn't exist in the current context.
        """
        if name in self._items:
            self.set_local(name, value)
        elif self.parent is None:
            raise NameNotFoundError(name, self)
        self.parent.set_name(name, value)


class Instance:
    _type: "Class"
    _data: list[Any]

    def __init__(self, typ):
        self._type = typ
        self._data = [None for _ in range(len(typ.fields))]

    @property
    def type(self):
        return self._type

    def get_data(self, index):
        return self._data[index]

    def set_data(self, index, value):
        self._data[index] = value


class Class(Scope):
    """
    Represents a Z# class that's used by the ct-runtime interpreter.

    Z# classes define the behavior and fields of objects.
    Objects hold data.
    """

    class Field:
        name: str
        _index: int
        _type: "Class"
        _owner: "Class"

        def __init__(self, name, owner: "Class", typ: "Class", index=None):
            self.name = name
            self._index = len(owner.fields) if index is None else index
            self._type = typ
            self._owner = owner

        def get(self, instance: Instance):
            if not instance.type.is_subclass(self._owner):
                raise TypeError
            return instance.get_data(self._index)

        def set(self, instance: Instance, value: Instance):
            if not instance.type.is_subclass(self._owner):
                raise TypeError
            if not value.type.is_subclass(self._type):
                raise TypeError
            instance.set_data(self._index, value)

    name: str | None
    base: Optional["Class"]
    _lexical_scope: Scope
    _fields: list[Field]

    def __init__(self, name, base, lexical_scope):
        super().__init__(lexical_scope)
        self.name = name
        self.base = base
        self._lexical_scope = lexical_scope
        self._fields = base.fields if base is not None else []

    @property
    def fields(self):
        return self._fields.copy()

    def add_field(self, name, typ):
        field = self.Field(name, self, typ, len(self._fields))

    def is_subclass(self, of):
        cls = self
        while cls.base is not None:
            if cls.base == of:
                return True
            cls = cls.base
        return cls == of

    def __create_instance(self, runtime, constructor):
        instance = Instance(self)


class Frame(Scope):
    _function: Function

    def __init__(self, function: Function | None, parent: Optional[Scope] = None):
        super().__init__(parent)
        self._function = function

    @property
    def function(self):
        return self._function
