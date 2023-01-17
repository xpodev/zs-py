""" protocols.py
This file contains different protocols for the Python backend of Z# objects.

"""
from typing import Optional, Any


class ObjectProtocol:
    """
    The base protocol for all Z# objects.

    Z# objects only hold data (i.e. other objects). How this data is stored is not part of the standard.

    The only thing an object has to have is the `get_type()` function, which should return an object that
    implements the `TypeProtocol` protocol.
    """

    def get_type(self) -> "TypeProtocol": ...


class TypeProtocol(ObjectProtocol):
    """
    Protocol for objects that can behave as types. All types are also objects.

    The minimal definition of a type is a group of values. Therefore, the minimal type API is to
    tell whether a value is part of the group (i.e. `is_instance`).
    """

    def is_instance(self, instance: ObjectProtocol) -> bool: ...

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
    def bind(self, instance: ObjectProtocol):
        """
        Return an object that wraps this one, but is bound to the given object.
        """


class ParameterizedProtocol:
    def get_parameter_types(self) -> list[TypeProtocol]:
        """
        Get the parameter types of this object.
        """

    def get_return_type(self) -> TypeProtocol:
        """
        Get the type of the result when parameters are applies.
        """


class CallableProtocol:
    def call(self, args: list[ObjectProtocol]):
        ...


class PartiallyCallableProtocol:
    def partial_call(self, args: list[ObjectProtocol]):
        ...


class DefaultCallableProtocol(CallableProtocol, PartiallyCallableProtocol):
    def partial_call(self, args: list[ObjectProtocol]):
        return _PartialCallImpl(self, args)


class _PartialCallImpl(DefaultCallableProtocol):
    callable: CallableProtocol
    args: list[ObjectProtocol]

    def __init__(self, callable_: CallableProtocol, args: list[ObjectProtocol]):
        self.callable = callable_
        self.args = args

    def call(self, args: list[ObjectProtocol]):
        return super().call(self.args + args)
