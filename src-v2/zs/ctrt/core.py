from typing import Optional

from zs.ctrt.errors import FieldAlreadyDefinedError, MemberAlreadyDefinedError, UnknownMemberError, NameNotFoundError
from zs.ctrt.protocols import ClassProtocol, TypeProtocol, ObjectProtocol, SetterProtocol, GetterProtocol, BindProtocol, ParameterizedProtocol, ScopeProtocol
from zs.utils import SingletonMeta


class _TypeType(TypeProtocol, metaclass=SingletonMeta):
    """
    The `type` type. This type is the base class of all Z# types.
    """

    def get_type(self) -> TypeProtocol:
        return _TypeType()

    def is_instance(self, instance: ObjectProtocol) -> bool:
        return isinstance(instance, TypeProtocol)

    @classmethod
    def default(cls) -> ObjectProtocol:
        return cls()


class _VoidType(TypeProtocol):
    """
    The `void` type. This type doesn't have any instances.
    """

    def get_type(self) -> TypeProtocol:
        return _TypeType()

    def is_instance(self, _) -> bool:
        return False

    @classmethod
    def default(cls) -> ObjectProtocol:
        raise TypeError(f"`void` doesn't have a default value because it can't be instantiated")


class _UnitType(TypeProtocol, metaclass=SingletonMeta):
    """
    The `unit` type. This type only has 1 instance, the unit instance `()`.
    """

    class _Unit(ObjectProtocol):
        def get_type(self) -> TypeProtocol:
            return _UnitType()

    Instance = _Unit()

    def get_type(self) -> TypeProtocol:
        return _TypeType()

    def is_instance(self, instance: ObjectProtocol) -> bool:
        return instance is self.Instance

    @classmethod
    def default(cls) -> ObjectProtocol:
        return cls.Instance


class _AnyType(TypeProtocol, metaclass=SingletonMeta):
    """
    The `any` type. This type is compatible with all Z# types (ObjectProtocol).
    """

    def get_type(self) -> TypeProtocol:
        return _TypeType()

    def is_instance(self, instance: ObjectProtocol) -> bool:
        return isinstance(instance, ObjectProtocol)

    @classmethod
    def default(cls) -> ObjectProtocol:
        raise TypeError(f"`any` doesn't have a default value because it is an abstract type.")


class _FunctionType(TypeProtocol, ParameterizedProtocol):
    def __init__(self, parameters: list[TypeProtocol], returns: TypeProtocol):
        self.parameters = parameters
        self.returns = returns

    def get_type(self) -> "TypeProtocol":
        return _TypeType()

    def is_instance(self, instance: ObjectProtocol) -> bool:
        if not isinstance(instance, ParameterizedProtocol):
            raise TypeError(f"Only parameterized object may be checked for function compatibility")
        if instance.get_return_type() != self.returns:
            return False
        parameters = instance.get_parameter_types()
        if len(parameters) != len(self.parameters):
            return False
        for parameter1, parameter2 in zip(parameters, self.parameters):
            if parameter1 != parameter2:
                return False
        return True

    def get_parameter_types(self) -> list[TypeProtocol]:
        return self.parameters.copy()

    def get_return_type(self) -> TypeProtocol:
        return self.returns


class _Object(ObjectProtocol):
    """
    The base type for Z# objects. Not to be confused with `_ObjectType`, this class
    is the base structure for Z# OOP objects, not classes.

    You can inherit this class to create Z# OOP objects that behave differently.

    If what you want is to create a class, you can either inherit `_ObjectType` or
    instantiate a new `Class` object.
    """

    _type: "_ObjectType"
    _data: list[ObjectProtocol]

    def __init__(self, type: "_ObjectType"):
        if type and not isinstance(type, _ObjectType):
            raise TypeError(f"'type' must be a valid object type")
        self._type = type or self
        self._data = [field.type.default() for field in type.fields] if type is not None else []

    def get_type(self) -> "_ObjectType":
        return self._type

    @property
    def data(self):
        return self._data


class _ObjectType(_Object, ClassProtocol):
    """
    The `object` type. This is the base type of all OOP classes.

    Do not instantiate this class, since it is only the base structure of a class.

    You can inherit this type to create a type that is considered an OOP class but
    behaves differently, with the new behavior defined in native Python.
    """

    class _Field(BindProtocol):
        name: str
        type: TypeProtocol
        initializer: ObjectProtocol

        is_static: bool

        _index: int
        _owner: "_ObjectType"

        def __init__(self, name: str, type: TypeProtocol, index: int, initializer: ObjectProtocol | None, owner: "_ObjectType"):
            self.name = name
            self.type = type
            self.initializer = initializer or self.type.default()
            self._index = index
            self._owner = owner

            self.is_static = False

        def get(self, instance: "_Object"):
            if not isinstance(instance, _Object):
                raise TypeError(f"'instance' must be a valid Z# OOP object.")
            if self.is_static:
                return self._owner.data[self.index]

            return instance.data[self.index]

        def set(self, instance: "_Object", value: ObjectProtocol):
            if not isinstance(instance, _Object):
                raise TypeError(f"'instance' must be a valid Z# OOP object.")

            if not self.type.is_instance(value):
                raise TypeError(f"'value' must be an instance of type '{self.type}'")
            if self.is_static:
                self._owner.data[self.index] = value
            else:
                instance.data[self.index] = value

        def bind(self, instance: "_Object") -> "_ObjectType._BoundField":
            if not isinstance(instance, _Object):
                raise TypeError("A field may only be bound to OOP objects.")
            if not self.is_static:
                if not self._owner.is_instance(instance):
                    raise TypeError(f"'instance' must be an instance of '{self._owner}'")
            else:
                if isinstance(instance, _ObjectType) and not instance.is_subclass(self._owner):
                    raise TypeError(f"'instance' must be a subclass of 'owner' in order to bind to a static field")
                instance = self._owner
            return _ObjectType._BoundField(self, instance)

        @property
        def index(self):
            return self._index

        @property
        def owner(self):
            return self._owner

    class _BoundField(GetterProtocol, SetterProtocol):
        _field: "_ObjectType._Field"
        _instance: "_Object"

        def __init__(self, field: "_ObjectType._Field", instance: "_Object"):
            self._field = field
            self._instance = instance

        def get(self):
            return self._field.get(self._instance)

        def set(self, value: ObjectProtocol):
            self._field.set(self._instance, value)

    class _Method:
        ...

    Instance = None

    _fields: dict[str, _Field]
    _methods: dict[str, _Method]
    _items: dict[str, _Field | _Method]

    def __init__(self, metaclass: Optional["_ObjectType"] = None):
        super().__init__(metaclass or self.Instance)
        if self.Instance is None:
            self.Instance = self
        self._fields = {}
        self._methods = {}
        self._items = {}

    def add_field(self, name: str, type: TypeProtocol, initializer: ObjectProtocol | None):
        if name in self._fields:
            raise FieldAlreadyDefinedError(f"Field '{name}' is already defined in type '{self}'")
        if name in self._items:
            raise MemberAlreadyDefinedError(f"Type '{self}' already defines a member '{name}'")
        self._items[name] = self._fields[name] = self._Field(name, type, len(self._fields), initializer, self)

    def add_method(self, name: str, method):
        self._items[name] = self._methods[name] = method

    def get_base(self) -> ClassProtocol | None:
        return None

    def get_name(self, instance: ObjectProtocol | None, name: str):
        if instance is not None and not isinstance(instance, _Object):
            raise TypeError("'instance' must be a valid OOP object.")
        try:
            member = self._items[name]
            if isinstance(member, BindProtocol):
                return member.bind(instance or self)
            return member
        except KeyError:
            raise UnknownMemberError(f"Type '{self}' does not define member '{name}'")

    def is_instance(self, instance: ObjectProtocol) -> bool:
        type = instance.get_type()

        if not isinstance(type, ClassProtocol):
            return False

        return type.is_subclass(self)

    def is_subclass(self, base: "_ObjectType"):
        if not isinstance(base, ClassProtocol):
            raise TypeError(f"Subclass check must be done on a class protocol type")

        cls = self
        while cls is not None:
            if base == cls:
                return True
            cls = cls.get_base()

        return False

    @classmethod
    def default(cls) -> ObjectProtocol:
        raise TypeError(f"Type '{cls}' does not define a default value")

    @property
    def fields(self):
        return list(self._fields.values())

    @property
    def methods(self):
        return list(self._methods.values())


class _NullableType(_ObjectType):
    def is_instance(self, instance: ObjectProtocol) -> bool:
        if instance is _NullType.Instance:
            return True

        return super().is_instance(instance)

    @classmethod
    def default(cls) -> ObjectProtocol:
        return _NullType.Instance


_ObjectType()  # the 'object' type


class _NullType(_ObjectType, metaclass=SingletonMeta):
    """
    The type of the `null` value. This value is places in the bottom of the inheritance tree and can
    be case to all object types.
    """

    class _Null(ObjectProtocol):
        def __init__(self):
            super().__init__()

        def get_type(self) -> "TypeProtocol":
            return _NullType()

    Instance = _Null()

    def get_type(self) -> "TypeProtocol":
        return _TypeType()

    def is_instance(self, instance: ObjectProtocol) -> bool:
        return instance is self.Instance

    @classmethod
    def default(cls) -> ObjectProtocol:
        raise TypeError(f"`null` type doesn't have a default value because it may not be instantiated.")


class _TypeClass(_ObjectType):
    class _TypeClassImplementation:
        type: TypeProtocol
        implementation: _ObjectType
        type_class: "_TypeClass"

        def __init__(self, type: TypeProtocol, implementation: _ObjectType, type_class: "_TypeClass"):
            self.type = type
            self.implementation = implementation
            self.type_class = type_class

    _implementations: dict[TypeProtocol, _TypeClassImplementation]

    def __init__(self):
        super().__init__()
        self._implementations = {}

    def is_instance(self, instance: ObjectProtocol) -> bool:
        return instance.get_type() in self._implementations

    def get_name(self, instance: ObjectProtocol | None, name: str):
        try:
            return self._implementations[instance.get_type()].implementation.get_name(instance, name)
        except KeyError:
            raise TypeError(f"type {instance.get_type()} does not implement type class '{self}'")

    def add_implementation(self, type: TypeProtocol, implementation: _ObjectType):
        if type in self._implementations:
            raise TypeError(f"type '{type}' already implements '{self}'")
        self._implementations[type] = self._TypeClassImplementation(type, implementation, self)
