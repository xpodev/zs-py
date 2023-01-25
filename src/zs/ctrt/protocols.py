""" protocols.py
This file contains different protocols for the Python backend of Z# objects.

"""
from typing import Optional, Any


class ObjectProtocol:
    """
    The base protocol for all Z# objects.

    Z# objects only hold data (i.e. other objects). How this data is stored is not part of the standard.

    The only thing an object has to have is a `runtime_type` attribute, which should hold the exact type
    of the object.
    """
    runtime_type: "TypeProtocol"


class TypeProtocol(ObjectProtocol):
    """
    Protocol for objects that can behave as types. All types are also objects.

    The minimal definition of a type is a group of values. Therefore, the minimal type API is to
    tell whether a value is part of the group (i.e. `is_instance`).
    """

    def is_instance(self, instance: ObjectProtocol) -> bool:
        """
        Returns whether the given instance is an instance of this type
        """
        return instance.runtime_type.assignable_to(self)

    def assignable_to(self, target: "TypeProtocol") -> bool:
        """
        Returns whether instances of 'this' type are assignable to the given `target` type.
        """
        return target.assignable_from(self)

    def assignable_from(self, source: "TypeProtocol") -> bool:
        """
        Returns whether this type accepts values from the given source type
        """
        return source is self

    @classmethod
    def default(cls) -> ObjectProtocol:
        """
        The default value of the type, or raise `TypeError` if the type doesn't have a default value.
        """


class GetterProtocol:
    def get(self):
        """
        Get the value associated with this getter.
        """


class SetterProtocol:
    def set(self, value: ObjectProtocol):
        """
        Set the value associated with this setter to the given value.

        This method is responsible for typechecking as well.
        """


class ScopeProtocol:
    """
    A protocol for any type that creates its own scope.
    This is not used by the internal `_Scope` type.
    """

    def define(self, name: str, value: Any):
        """
        Define a new value in this scope.
        """

    def refer(self, name: str, value: Any):
        """
        Bind a name to a value from an external source in this scope.
        """


class ConstructibleTypeProtocol(TypeProtocol):
    def create_instance(self, args: list[ObjectProtocol]) -> ObjectProtocol: ...


class ImmutableTypeProtocol(TypeProtocol):
    def get_name(self, instance: ObjectProtocol | None, name: str) -> ObjectProtocol: ...


class MutableTypeProtocol(TypeProtocol):
    def get_name(self, instance: ObjectProtocol | None, name: str) -> ObjectProtocol: ...

    def set_name(self, instance: ObjectProtocol | None, name: str, value: ObjectProtocol): ...


class ClassProtocol(ConstructibleTypeProtocol):
    def get_base(self) -> Optional["ClassProtocol"]: ...

    def is_subclass(self, base: "ClassProtocol") -> bool:
        """
        Returns whether this type is a subtype of `base`
        """


class ImmutableClassProtocol(ClassProtocol, ImmutableTypeProtocol):
    ...


class MutableClassProtocol(ClassProtocol, MutableTypeProtocol):
    ...


class BindProtocol:
    def bind(self, args: list[ObjectProtocol]):
        """
        Bind this object to the given arguments and return it.
        This does not bind the original object.
        """


class CallableProtocol(ObjectProtocol):
    runtime_type: "CallableTypeProtocol"

    def call(self, args: list[ObjectProtocol]) -> ObjectProtocol:
        """
        Apply actual values to the object
        """


class CallableTypeProtocol(TypeProtocol):
    def assignable_from(self, source: "TypeProtocol") -> bool:
        if not isinstance(source, CallableTypeProtocol):
            raise TypeError

        return self.compare_type_signature(source)

    def compare_type_signature(self, other: "CallableTypeProtocol") -> bool:
        """
        Returns whether this callable has the same type signature as the given callable
        """

    def get_type_of_application(self, types: list[TypeProtocol]) -> TypeProtocol:
        """
        Returns the result type when applied with the given types.
        If the types given do not match this callable's types, raises a TypeError.
        """


class DefaultCallableProtocol(CallableProtocol, BindProtocol):
    def bind(self, args: list[ObjectProtocol]):
        return _PartialCallImpl(self, args)


class _PartialCallImpl(DefaultCallableProtocol):
    callable: CallableProtocol
    args: list[ObjectProtocol]

    class _PartialCallImplType(CallableTypeProtocol):
        def __init__(self, bound: list[TypeProtocol], origin: CallableTypeProtocol):
            self.bound = bound
            self.origin = origin

        def get_type_of_application(self, types: list[TypeProtocol]) -> TypeProtocol:
            return self.origin.get_type_of_application(self.bound + types)

        def compare_type_signature(self, other: "CallableProtocol") -> bool:
            return other.runtime_type.compare_type_signature(self.origin)

    def __init__(self, callable_: CallableProtocol, args: list[ObjectProtocol]):
        self.callable = callable_
        self.args = args
        self.runtime_type = self._PartialCallImplType(self.get_bound_argument_types(), self.callable.runtime_type)

    def get_bound_argument_types(self):
        return list(map(lambda arg: arg.runtime_type, self.args))

    def get_type_of_application(self, types: list[TypeProtocol]) -> TypeProtocol:
        return self.callable.runtime_type.get_type_of_application(self.get_bound_argument_types() + types)

    def compare_type_signature(self, other: "CallableTypeProtocol") -> bool:
        return other.compare_type_signature(self.runtime_type)

    def call(self, args: list[ObjectProtocol]):
        return super().call(self.args + args)
