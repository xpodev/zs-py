from typing import Any

from zs import Object


class ZSError(Exception):
    """
    Base class for all Z# compiler related errors
    """


class ScopeError(ZSError):
    """
    Base class for errors relating a name with a scope
    """

    name: str
    scope: Any

    def __init__(self, name: str, scope, message: str):
        super().__init__(message)
        self.name = name
        self.scope = scope


class UndefinedNameError(ScopeError):
    """
    Raised when trying to access a name that doesn't exist within the scope
    """

    def __init__(self, name, scope):
        super().__init__(name, scope, f"scope {scope} does not contain a definition of \"{name}\"")


class DuplicateDefinitionError(ScopeError):
    """
    Raised when 2 definitions with same name exists in the same scope
    """

    def __init__(self, name, scope):
        super().__init__(name, scope, f"scope {scope} already has a definition of \"{name}\"")


class UnnamedObjectError(ZSError):
    """
    Raised when an unnamed object is passed to a function that must get a named object
    """

    object: Object

    def __init__(self, obj: Object, *args):
        super().__init__(args)
        self.object = obj
