""" core.py
This module defines some core types in the Z# programming language.
"""
import typing
from dataclasses import dataclass
from enum import IntFlag
from typing import Optional

from zs.ctrt import get_runtime
from zs.ctrt.errors import MemberAlreadyDefinedError, UnknownMemberError, NoParentScopeError, NameNotFoundError, NameAlreadyExistsError, ReturnInstructionInvoked
from zs.ctrt.protocols import ClassProtocol, TypeProtocol, ObjectProtocol, SetterProtocol, GetterProtocol, BindProtocol, CallableTypeProtocol, MutableClassProtocol, ImmutableClassProtocol, \
    DynamicScopeProtocol, DisposableProtocol, ScopeProtocol, CallableProtocol
from zs.utils import SingletonMeta


__all__ = [
    "Type",
    "Void",
    "Unit",
    "Any",
    "Null",
    "Object"
]


_T = typing.TypeVar("_T")


# Special Types


class _TypeType(TypeProtocol, metaclass=SingletonMeta):
    """
    The `type` type. This type is the base class of all Z# types.
    """

    def __init__(self):
        self.runtime_type = self

    def assignable_from(self, source: "TypeProtocol") -> bool:
        return isinstance(source, TypeProtocol)

    def __repr__(self):
        return "type"


Type = _TypeType()
del _TypeType


class _VoidType(TypeProtocol, metaclass=SingletonMeta):
    """
    The `void` type. This type doesn't have any instances.
    """

    def __init__(self):
        self.runtime_type = Type

    def assignable_to(self, target: "TypeProtocol") -> bool:
        return False

    def assignable_from(self, _: "TypeProtocol") -> bool:
        return False

    def __repr__(self):
        return "void"


Void = _VoidType()
del _VoidType


class _UnitType(TypeProtocol, metaclass=SingletonMeta):
    """
    The `unit` type. This type only has 1 instance, the unit instance `()`.
    """

    class _Unit(ObjectProtocol, metaclass=SingletonMeta):
        def __init__(self, unit_type: "_UnitType"):
            self.runtime_type = unit_type

        def __str__(self):
            return "()"

    Instance = None

    def __init__(self):
        if self.Instance is None:
            _UnitType.Instance = self._Unit(self)
        self.runtime_type = Type

    def default(self) -> ObjectProtocol:
        return self.Instance

    def __repr__(self):
        return "unit"


Unit = _UnitType()
del _UnitType


class _BoolType(TypeProtocol, metaclass=SingletonMeta):
    """
    The `bool` type. This type has exactly 2 instances: `true` and `false`.
    """

    class _Boolean(ObjectProtocol):
        def __init__(self, bool_type: "_BoolType", value: bool):
            self.runtime_type = bool_type
            self.__value = value

        def __str__(self):
            return "true" if self is self.__value else "false"

    TRUE: _Boolean = None
    FALSE: _Boolean = None

    def __init__(self):
        if self.TRUE is None:
            _BoolType.TRUE = self._Boolean(self, True)
        if self.FALSE is None:
            _BoolType.FALSE = self._Boolean(self, False)
        self.runtime_type = Type

    def default(self) -> ObjectProtocol:
        return self.FALSE

    def __repr__(self):
        return "bool"


Bool = _BoolType()
del _BoolType


class _AnyType(TypeProtocol, metaclass=SingletonMeta):
    """
    The `any` type. This type is compatible with all Z# types (ObjectProtocol).
    """

    def __init__(self):
        self.runtime_type = Type

    def is_instance(self, instance: ObjectProtocol) -> bool:
        return isinstance(instance, ObjectProtocol)

    def assignable_to(self, target: "TypeProtocol") -> bool:
        return target is self

    def assignable_from(self, source: "TypeProtocol") -> bool:
        return isinstance(source, TypeProtocol)

    def __repr__(self):
        return "any"


Any = _AnyType()
del _AnyType


class _NullType(TypeProtocol, metaclass=SingletonMeta):
    """
    The type of the `null` value. This value is places in the bottom of the inheritance tree and can
    be case to all object types.
    """

    class _Null(ObjectProtocol, metaclass=SingletonMeta):
        def __init__(self, null_type: "_NullType"):
            super().__init__()
            self.runtime_type = null_type

        def __str__(self):
            return "null"

    Instance: _Null = None

    def __init__(self):
        super().__init__()
        if self.Instance is None:
            _NullType.Instance = self._Null(self)
        self.runtime_type = Type

    def __repr__(self):
        return "nulltype"


Null = _NullType()
del _NullType


class Union(TypeProtocol):
    """
    The `union` type. This type can be constructed by the or operator: `int | string`
    """

    types: tuple[TypeProtocol, ...]

    def __init__(self, *types: TypeProtocol):
        self.types = types
        self.runtime_type = Type

    def assignable_from(self, source: "TypeProtocol") -> bool:
        return any(map(source.assignable_to, self.types))


class Tuple(ObjectProtocol):
    items: tuple[ObjectProtocol, ...]
    runtime_type: "TupleType"

    def __init__(self, *args: ObjectProtocol):
        self.items = args
        self.runtime_type = TupleType(*map(lambda t: t.runtime_type, args))


class TupleType(Tuple, TypeProtocol):
    """
    The `tuple` type. This type can be constructed with a tuple literal: `(int, string)`
    """

    items: tuple[TypeProtocol, ...]

    def __init__(self, *args: TypeProtocol):
        if all(map(lambda t: t is Type, args)):
            self.items = args
            self.runtime_type = self
        else:
            super().__init__(*args)

    def assignable_from(self, source: "TypeProtocol") -> bool:
        # todo: packed protocol

        if not isinstance(source, TupleType):
            return False

        if len(self.items) != len(source.items):
            return False

        return all(map(lambda ts: ts[1].assignable_to(ts[0]), zip(self.items, source.items)))

    def default(self) -> ObjectProtocol:
        return Tuple(*map(lambda t: t.default(), self.items))


class FunctionType(CallableTypeProtocol):
    def __init__(self, parameters: list[TypeProtocol], returns: TypeProtocol):
        self.parameters = parameters
        self.returns = returns
        self.runtime_type = Type

    def assignable_from(self, source: "TypeProtocol") -> bool:
        if not isinstance(source, CallableTypeProtocol):
            return False

        return self.compare_type_signature(source)

    def get_type_of_call(self, types: list[TypeProtocol]) -> TypeProtocol:
        if len(types) != len(self.parameters):
            raise TypeError
        for type, parameter in zip(types, self.parameters):
            if not type.assignable_to(parameter):
                raise TypeError
        return self.returns

    def compare_type_signature(self, other: CallableTypeProtocol) -> bool:
        try:
            if not other.get_type_of_call(self.parameters).assignable_to(self.returns):
                return False
        except TypeError:
            return False

        return True


# End Special Types


# class OverloadGroupType(CallableTypeProtocol):
#     group: "OverloadGroup"
#
#     def __init__(self, group: "OverloadGroup"):
#         self.group = group
#         self.runtime_type = Type
#
#     def compare_type_signature(self, other: "CallableTypeProtocol") -> bool:
#         return any(overload.runtime_type.compare_type_signature(other) for overload in self.group.overloads)
#
#     def get_type_of_call(self, types: list[TypeProtocol]) -> TypeProtocol:
#         overloads = self.group.get_matching_overloads_for_types(types)
#
#         if not overloads:
#             raise TypeError
#         if len(overloads) > 1:
#             raise TypeError
#
#         return overloads[0].runtime_type.get_type_of_call(types)


class OverloadGroup(CallableProtocol):
    overloads: list[CallableProtocol]
    runtime_type: Union
    parent: "OverloadGroup"

    def __init__(self, parent: "OverloadGroup | None", *overloads: CallableProtocol):
        self.parent = parent
        self.overloads = list(overloads)
        self.build()

    def add_overload(self, fn: CallableProtocol):
        self.overloads.append(fn)

    def get_matching_overloads(self, args: list[ObjectProtocol]):
        return self.get_matching_overloads_for_types(list(map(lambda arg: arg.runtime_type, args)))

    def get_matching_overloads_for_types(self, types: list[TypeProtocol]):
        result = []
        for overload in self.overloads:
            try:
                if overload.runtime_type.get_type_of_call(types).assignable_to(overload.runtime_type):
                    result.append(overload)
            except TypeError:
                ...
            else:
                result.append(overload)
        if not result and self.parent:
            return self.parent.get_matching_overloads_for_types(types)
        return result

    def call(self, args: list[ObjectProtocol]) -> ObjectProtocol:
        overloads = self.get_matching_overloads(args)

        if not overloads:
            raise TypeError
        if len(overloads) > 1:
            raise TypeError

        return overloads[0].call(args)

    def build(self):
        self.runtime_type = Union(*map(lambda overload: overload.runtime_type, self.overloads))

# class FunctionGroup(NativeObject, BindProtocol):
#     name: str
#     _overloads: list[Function]
#
#     class _BoundFunctionGroup(NativeObject, CallableProtocol):
#         group: "FunctionGroup"
#         args: list[ObjectProtocol]
#
#         def __init__(self, group: "FunctionGroup", args: list[ObjectProtocol]):
#             super().__init__()
#             self.group = group
#             self.args = args
#
#         def get_matching_overloads(self, args: list[ObjectProtocol]):
#             return [
#                 item.bind(self.args) if isinstance(item, BindProtocol) else item for item in self.group.get_matching_overloads(self.args + args)
#             ]
#
#         def call(self, args: list[ObjectProtocol]):
#             overloads = self.get_matching_overloads(args)
#
#             if not len(overloads):
#                 raise TypeError
#             if len(overloads) > 1:
#                 raise TypeError
#             return overloads[0].call(self.args + args)
#
#     def __init__(self, name: str, *fns: Function):
#         super().__init__()
#         self.name = name
#         self._overloads = list(fns)
#         self.runtime_type = self._FunctionGroupType(self)
#
#     @property
#     def overloads(self):
#         return self._overloads.copy()
#
#     def bind(self, args: list[ObjectProtocol]):
#         return self._BoundFunctionGroup(self, args)


@dataclass(slots=True)
class Parameter:
    _owner: "FunctionSignature"
    name: str
    _type: TypeProtocol
    default_value: ObjectProtocol | None
    _index: int

    @property
    def owner(self):
        return self._owner

    @property
    def type(self):
        return self._type

    @type.setter
    def type(self, value):
        self.type = value
        self._owner.build()

    @property
    def index(self):
        return self._index


@dataclass(slots=True)
class Variable(GetterProtocol, SetterProtocol):
    name: str
    type: TypeProtocol
    value: ObjectProtocol

    def __init__(self, name: str, type: TypeProtocol, initializer: ObjectProtocol | None = None):
        self.name = name
        self.type = type
        self.value = initializer or type.default()

    def get(self):
        return self.value

    def set(self, value: ObjectProtocol):
        if not value.runtime_type.assignable_to(self.type):
            raise TypeError
        self.value = value


class FunctionSignature(ObjectProtocol):
    """
    Represents a function signature.
    Mainly used for stub functions.
    """

    runtime_type: FunctionType

    _return_type: TypeProtocol

    name: str | None
    parameters: list[Parameter]

    def __init__(self, name: str | None, return_type: TypeProtocol):
        self.name = name
        self.parameters = []
        self._return_type = return_type
        self.runtime_type = FunctionType([], return_type)

    @property
    def return_type(self):
        return self._return_type

    @return_type.setter
    def return_type(self, value):
        self._return_type = value
        self.runtime_type = FunctionType(self.runtime_type.parameters, value)

    def define_parameter(self, name: str, type: TypeProtocol, default_value: ObjectProtocol | None = None, index: int = -1):
        if index == -1:
            index = len(self.parameters) - 1
        parameter = Parameter(self, name, type, default_value, index)
        self.parameters.insert(index, parameter)

        return parameter

    def build(self):
        self.runtime_type = FunctionType(list(map(lambda p: p.type, self.parameters)), self.return_type)


class Function(CallableProtocol):
    """
    Represents a Z# function.
    """

    class _Argument(GetterProtocol, SetterProtocol):
        parameter: Parameter
        value: ObjectProtocol

        def __init__(self, parameter: Parameter, value: ObjectProtocol):
            if not value.runtime_type.assignable_to(parameter.type):
                raise TypeError
            self.parameter = parameter
            self.value = value

        def get(self):
            return self.value

        def set(self, value: ObjectProtocol):
            if not value.runtime_type.assignable_to(self.parameter.type):
                raise TypeError
            self.value = value

    _signature: FunctionSignature
    lexical_scope: ScopeProtocol | None

    def __init__(self, name: str, return_type: TypeProtocol, lexical_scope: ScopeProtocol | None, body: list):
        self._signature = FunctionSignature(name, return_type)
        self.lexical_scope = lexical_scope
        self.body = body  # this is currently a list of nodes, but might as well be a list of instructions

    @property
    def signature(self):
        return self._signature

    @property
    def runtime_type(self):
        return self.signature.runtime_type

    def call(self, args: list[ObjectProtocol]) -> ObjectProtocol:
        if not self.runtime_type.get_type_of_call(list(map(lambda arg: arg.runtime_type, args))).assignable_to(self.signature.return_type):
            raise TypeError

        runtime = get_runtime()

        with runtime.x.frame(self):
            for parameter, argument in zip(self.signature.parameters, args):
                runtime.x.current_scope.define(parameter.name, self._Argument(parameter, argument))

            try:
                for item in self.body:
                    runtime.execute(item)
                if self.signature.return_type is not Void:
                    try:
                        return self.signature.return_type.default()
                    except TypeError:
                        raise TypeError(f"Function {self} marked as non-void did not return value")
            except ReturnInstructionInvoked as e:
                return e.value


class _ObjectType(ClassProtocol, metaclass=SingletonMeta):
    class Instance(ObjectProtocol):
        def __init__(self):
            self.runtime_type = Object

        def __repr__(self):
            return f"<Z# Object>"

    def get_base(self) -> "ClassProtocol | None":
        return None

    def is_subclass_of(self, base: "ClassProtocol") -> bool:
        return False

    def create_instance(self, args: list[ObjectProtocol]) -> ObjectProtocol:
        if len(args):
            raise TypeError(f"'object type' constructor may not be called with arguments.")

        return self.Instance()

    def assignable_from(self, source: "TypeProtocol") -> bool:
        if not isinstance(source, ClassProtocol):
            return False

        return self.is_superclass_of(source)

    def __repr__(self):
        return "object"


Object = _ObjectType()
del _ObjectType


class Scope(ScopeProtocol):
    _parent: Optional[ScopeProtocol]

    class _Scope(typing.Generic[_T]):
        """
        An internal type which wraps a dictionary to allow for function overloading.

        This does not handle any other protocol except the `CallableProtocol`
        """

        _items: dict[str, _T]

        def __init__(self, owner: "Scope", **items: _T):
            self._items = items
            self._owner = owner

        def items(self):
            return self._items.items()

        def __contains__(self, key: str):
            return key in self._items

        def __getitem__(self, key: str) -> _T:
            return self._items[key]

        def __setitem__(self, key: str, value: _T):
            def _get_overload_group_parent(scope: Scope | None = self._owner.parent):
                if scope is None:
                    return None
                try:
                    parent = self._owner.parent.get_name(key)
                except NameNotFoundError:
                    return None
                else:
                    if isinstance(parent, CallableProtocol):
                        parent = OverloadGroup(_get_overload_group_parent(scope.parent), parent)
                    if not isinstance(parent, OverloadGroup):
                        return None
                    return parent

            if isinstance(value, Function):
                value = OverloadGroup(_get_overload_group_parent(), value)

            if key in self._items:
                if not isinstance(value, CallableProtocol):
                    raise NameAlreadyExistsError(key, self._owner, self)
                original = self._items[key]
                if not isinstance(original, CallableProtocol):
                    raise NameAlreadyExistsError(key, self._owner, self)
                if isinstance(original, OverloadGroup):
                    if isinstance(value, OverloadGroup):
                        original.overloads.extend(value.overloads)
                    else:
                        original.add_overload(value)
                    return original.build()

                value = OverloadGroup(_get_overload_group_parent(), original, value)
            self._items[key] = value

    _items: _Scope[ObjectProtocol]
    _members: _Scope[ObjectProtocol]

    def __init__(self, parent: Optional[ScopeProtocol] = None, **items: ObjectProtocol):
        self._parent = parent
        self._items = self._Scope(self, **items)
        self._members = self._Scope(self)

    @property
    def is_toplevel_scope(self):
        return self._parent is None

    @property
    def parent(self):
        return self._parent

    @property
    def items(self):
        return self._items.items()

    @property
    def members(self):
        return self._members.items()

    def get_name(self, name: str):
        """
        Get a value bound to the given name in this or a parent scope.

        :raises: `NameNotFoundError` if the name doesn't exist in the current context.
        """
        if name in self._items:
            return self._items[name]
        if self.parent is None:
            raise NameNotFoundError(name, self)
        return self.parent.get_name(name)

    def define(self, name: str, value):
        self.refer(name, value)
        self._members[name] = value

    def refer(self, name: str, value):
        self._items[name] = value


class Class(MutableClassProtocol, DynamicScopeProtocol, DisposableProtocol):
    class _Instance(ObjectProtocol):
        data: list[ObjectProtocol]
        runtime_type: "Class"

        def __init__(self, runtime_type: "Class"):
            self.runtime_type = runtime_type
            self.data = []

        def __repr__(self):
            return f"<Z# Object of type {self.runtime_type.name}>"

    class _Member:
        _dynamic: bool
        _instance: bool

        name: str
        owner: "Class"
        original: ObjectProtocol | None

        def __init__(self, name: str, owner: "Class", original: ObjectProtocol | None = None):
            self.name = name
            self.owner = owner
            self.original = original
            self._instance = False
            self._dynamic = False

        @property
        def is_instance(self) -> bool:
            return self._instance

        @is_instance.setter
        def is_instance(self, value):
            self._instance = value

        @property
        def is_dynamic_binding(self):
            return self._dynamic

        @is_dynamic_binding.setter
        def is_dynamic_binding(self, value):
            self._dynamic = value

        @property
        def is_virtual(self):
            return self.is_dynamic_binding and self.is_instance

        @is_virtual.setter
        def is_virtual(self, value):
            if value:
                self.is_dynamic_binding = self.is_instance = True
            else:
                raise ValueError

        @property
        def is_static(self):
            return not self.is_dynamic_binding and not self.is_instance

        @is_static.setter
        def is_static(self, value):
            if value:
                self.is_dynamic_binding = self.is_instance = False
            else:
                raise ValueError

        @property
        def is_class(self):
            return self.is_dynamic_binding and not self.is_instance

        @is_class.setter
        def is_class(self, value):
            if value:
                self.is_dynamic_binding = True
                self.is_instance = False
            else:
                raise ValueError

    class _Field(_Member):
        ...

    class _Method(_Member):
        ...

    name: str | None
    base: ClassProtocol | None
    constructor: OverloadGroup

    _fields: list[_Field]
    _methods: list[_Method]

    _items: dict[str, typing.Union[_Field,  _Method, "Class"]]
    _scope: Scope

    def __init__(self, name: str | None = None, base: ClassProtocol | None = None, lexical_scope: ScopeProtocol | None = None):
        self.name = name
        self.base = base or Object

        self._fields = []
        self._methods = []

        self._items = {}
        self._scope = Scope(lexical_scope)

        self.constructor = OverloadGroup(None)

    @property
    def runtime_type(self):
        return self.constructor.runtime_type

    def create_instance(self, args: list[ObjectProtocol]) -> ObjectProtocol:
        instance = self._Instance(self)
        result = self.constructor.call([instance, *args])
        return result if result != Unit.Instance else instance

    def get_base(self) -> "ClassProtocol":
        return self.base

    def get_name(self, name: str) -> ObjectProtocol:
        result = self._scope.get_name(name)

        return result

    def all(self) -> list[tuple[str, ObjectProtocol]]:
        return [(name, item) for name, item in self._items.items()]

    def define(self, name: str, value: ObjectProtocol):
        match value:
            case Function() as function:
                ...
            case Variable() as variable:
                ...
            case Class() as class_:
                ...
        self._scope.define(name, value)

    def refer(self, name: str, value: ObjectProtocol):
        self._scope.refer(name, value)

    def delete(self, name: str):
        raise TypeError(f"You may not delete values from a class")

    def dispose(self):
        if not self.constructor.overloads:
            constructor = Function(self.name, Unit, None, [])
            constructor.signature.define_parameter("this", self)
            constructor.signature.build()
            self.define_constructor(constructor)

    # OOP Class Stuff

    def define_constructor(self, function: Function):
        self.constructor.add_overload(function)

    def define_field(self, name: str, type: TypeProtocol, initializer: ObjectProtocol = None):
        ...

    def define_method(self, name: str, function: Function):
        ...

    def define_class(self, name: str, class_: ClassProtocol):
        ...

    # End OOP Class Stuff

    def __repr__(self):
        return f"<Z# Class {self.name}>"


# class _Object(ObjectProtocol):
#     """
#     The base type for Z# objects. Not to be confused with `ObjectType`, this class
#     is the base structure for Z# OOP objects, not classes.
#
#     You can inherit this class to create Z# OOP objects that behave differently.
#
#     If what you want is to create a class, you can either inherit `_ObjectType` or
#     instantiate a new `Class` object.
#     """
#
#     _data: list[ObjectProtocol]
#
#     def __init__(self, type: "_ObjectType"):
#         self._data = [field.type.default() for field in type.fields] if type is not None else []
#         self.runtime_type = type
#
#     @property
#     def data(self):
#         return self._data
#
#     def __repr__(self):
#         return f"<Z# object of type {self.runtime_type}>"
#
#
# class _ObjectType(_Object, ClassProtocol):
#     """
#     The `object` type. This is the base type of all OOP classes.
#
#     Do not instantiate this class, since it is only the base structure of a class.
#
#     You can inherit this type to create a type that is considered an OOP class but
#     behaves differently, with the new behavior defined in native Python.
#     """
#
#     class _Field(BindProtocol):
#         name: str
#         type: TypeProtocol
#         initializer: ObjectProtocol
#
#         is_static: bool
#
#         _index: int
#         _owner: "_ObjectType"
#
#         def __init__(self, name: str, type: TypeProtocol, index: int, initializer: ObjectProtocol | None, owner: "_ObjectType"):
#             self.name = name
#             self.type = type
#             self.initializer = initializer or self.type.default()
#             self._index = index
#             self._owner = owner
#
#             self.is_static = False
#
#         def get(self, instance: "_Object"):
#             if not isinstance(instance, _Object):
#                 raise TypeError(f"'instance' must be a valid Z# OOP object.")
#             if self.is_static:
#                 return self._owner.data[self.index]
#
#             return instance.data[self.index]
#
#         def set(self, instance: "_Object", value: ObjectProtocol):
#             if not isinstance(instance, _Object):
#                 raise TypeError(f"'instance' must be a valid Z# OOP object.")
#
#             if not self.type.is_instance(value):
#                 raise TypeError(f"'value' must be an instance of type '{self.type}'")
#             if self.is_static:
#                 self._owner.data[self.index] = value
#             else:
#                 instance.data[self.index] = value
#
#         def bind(self, args: [ObjectProtocol]) -> "_ObjectType._BoundField":
#             if len(args) != 1:
#                 raise TypeError(f"May only bind a field to a single instance")
#             instance = args[0]
#             if not isinstance(instance, _Object):
#                 raise TypeError("A field may only be bound to OOP objects.")
#             if not self.is_static:
#                 if not self._owner.is_instance(instance):
#                     raise TypeError(f"'instance' must be an instance of '{self._owner}'")
#             else:
#                 if isinstance(instance, _ObjectType) and not instance.is_subclass_of(self._owner):
#                     raise TypeError(f"'instance' must be a subclass of 'owner' in order to bind to a static field")
#                 instance = self._owner
#             return _ObjectType._BoundField(self, instance)
#
#         @property
#         def index(self):
#             return self._index
#
#         @property
#         def owner(self):
#             return self._owner
#
#     class _BoundField(GetterProtocol, SetterProtocol):
#         _field: "_ObjectType._Field"
#         _instance: "_Object"
#
#         def __init__(self, field: "_ObjectType._Field", instance: "_Object"):
#             self._field = field
#             self._instance = instance
#
#         def get(self):
#             return self._field.get(self._instance)
#
#         def set(self, value: ObjectProtocol):
#             self._field.set(self._instance, value)
#
#     class _Method:
#         ...
#
#     Instance = None
#
#     _fields: list[_Field]
#     _methods: list[_Method]
#     _items: dict[str, _Field | _Method]
#
#     def __init__(self, metaclass: Optional["_ObjectType"] = None):
#         if self.Instance is None:
#             self.Instance = self
#         self._fields = []
#         super().__init__(metaclass or self.Instance)
#         self._methods = []
#         self._items = {}
#
#     def add_field(self, name: str, type: TypeProtocol, initializer: ObjectProtocol | None):
#         if name in self._items:
#             raise MemberAlreadyDefinedError(f"Type '{self}' already defines a member '{name}'")
#         self._items[name] = field = self._Field(name, type, len(self._fields), initializer, self)
#         self._fields.append(field)
#
#     def add_method(self, name: str, method):
#         self._items[name] = method
#         self._methods.extend(getattr(method, "overloads", [method]))
#
#     def get_base(self) -> ClassProtocol | None:
#         return None
#
#     def get_name(self, instance: ObjectProtocol | None, name: str):
#         if instance is not None and not isinstance(instance, _Object):
#             raise TypeError("'instance' must be a valid OOP object.")
#         try:
#             member = self._items[name]
#             if isinstance(member, BindProtocol):
#                 return member.bind([instance if instance is not None else self])
#             return member
#         except KeyError:
#             raise UnknownMemberError(f"Type '{self}' does not define member '{name}'")
#
#     def set_name(self, instance: ObjectProtocol | None, name: str, value: ObjectProtocol):
#         ...
#
#     def assignable_to(self, target: "TypeProtocol") -> bool:
#         if not isinstance(target, _ObjectType):
#             return super().assignable_to(target)
#
#         return self.is_subclass_of(target)
#
#     def is_subclass_of(self, base: "_ObjectType"):
#         if not isinstance(base, ClassProtocol):
#             raise TypeError(f"Subclass check must be done on a class protocol type")
#
#         cls = self
#         while cls is not None:
#             if base == cls:
#                 return True
#             cls = cls.get_base()
#
#         return False
#
#     @classmethod
#     def default(cls) -> ObjectProtocol:
#         raise TypeError(f"Type '{cls}' does not define a default value")
#
#     @property
#     def fields(self):
#         return self._fields.copy()
#
#     @property
#     def methods(self):
#         return self._methods.copy()


class Nullable(TypeProtocol):
    type: TypeProtocol

    def __init__(self, type: TypeProtocol):
        if not isinstance(type, _ObjectType):
            raise TypeError("Nullables may only be used with class types")
        self.type = type
        self.runtime_type = Type

    def assignable_from(self, source: "TypeProtocol") -> bool:
        if source is Null:
            return True

        return source.assignable_to(self.type)

    def default(self) -> ObjectProtocol:
        return Null.Instance


class TypeClass(ImmutableClassProtocol, DynamicScopeProtocol):
    class _TypeClassImplementationInfo:
        type: TypeProtocol
        implementation: Class
        type_class: "TypeClass"

        def __init__(self, type: TypeProtocol, implementation: Class, type_class: "TypeClass"):
            self.type = type
            self.implementation = implementation
            self.type_class = type_class

    _implementations: dict[TypeProtocol, _TypeClassImplementationInfo]

    def __init__(self):
        super().__init__()
        self._implementations = {}

    def assignable_from(self, source: "TypeProtocol") -> bool:
        return source in self._implementations

    def get_name(self, instance: ObjectProtocol | None, name: str):
        try:
            return self._implementations[instance.runtime_type].implementation.get_name(instance, name)
        except KeyError:
            raise TypeError(f"type {instance.runtime_type} does not implement type class '{self}'")

    def add_implementation(self, type: TypeProtocol, implementation: Class):
        if type in self._implementations:
            raise TypeError(f"type '{type}' already implements '{self}'")
        self._implementations[type] = self._TypeClassImplementationInfo(type, implementation, self)

    def get_implementation(self, type: TypeProtocol) -> Class:
        return self._implementations[type].implementation
