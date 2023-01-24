from typing import Optional, Any

from zs.ast.node import Node
from zs.ctrt import get_runtime
from zs.ctrt.core import _Object, _ObjectType, _TypeClass, _FunctionType, _TypeType
from zs.ctrt.errors import NameNotFoundError, NameAlreadyExistsError, NoParentScopeError, UnknownMemberError, ReturnInstructionInvoked
from zs.ctrt.native import NativeObject
from zs.ctrt.protocols import TypeProtocol, ObjectProtocol, ClassProtocol, MutableClassProtocol, SetterProtocol, GetterProtocol, ScopeProtocol, BindProtocol, \
    CallableProtocol, CallableTypeProtocol


class Parameter:
    _owner: "Function"
    name: str
    type: TypeProtocol

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


class Argument(NativeObject, GetterProtocol, SetterProtocol):
    parameter: Parameter
    value: ObjectProtocol

    def __init__(self, parameter: Parameter, value: ObjectProtocol):
        super().__init__()
        self.parameter = parameter
        self.value = value
        self.runtime_type = parameter.type

    def get(self):
        return self.value

    def set(self, value: ObjectProtocol):
        if not self.parameter.type.is_instance(value):
            raise TypeError()
        self.value = value


class Variable(NativeObject, GetterProtocol, SetterProtocol):
    name: str
    type: TypeProtocol
    value: ObjectProtocol

    def __init__(self, name: str, type: TypeProtocol, value: ObjectProtocol = None):
        super().__init__()
        self.name = name
        self.runtime_type = self.type = type
        self.set(value or type.default())

    def get(self):
        return self.value

    def set(self, value: ObjectProtocol):
        if not self.type.is_instance(value):
            raise TypeError(f"Can't assign value of type '{value.runtime_type}' to variable of type '{self.type}'")
        self.value = value


class Function(NativeObject, CallableProtocol):
    """
    Represents a Z# function that's used by the ct-runtime interpreter.
    """

    class Body:
        nodes: list[Node]

        def __init__(self):
            self.nodes = []

    class _BoundFunction(CallableProtocol):
        function: "Function"
        instance: ObjectProtocol

        def __init__(self, function: "Function", instance: ObjectProtocol):
            self.function = function
            self.instance = instance

        def call(self, args: list[ObjectProtocol]):
            return self.function.call([self.instance, args])

    name: str | None
    _lexical_scope: "Scope"
    _parameters: list[Parameter]
    _return_type: TypeProtocol
    _body: Body

    def __init__(self, return_type: TypeProtocol, lexical_scope: "Scope"):
        super().__init__()
        self._lexical_scope = lexical_scope
        self._parameters = []
        self._return_type = return_type
        self._body = self.Body()
        self.runtime_type = _FunctionType(self.get_parameter_types(), self._return_type)

    @property
    def lexical_scope(self):
        return self._lexical_scope

    @property
    def owner(self):
        return self.lexical_scope

    @property
    def parameters(self):
        return self._parameters.copy()

    @property
    def return_type(self):
        return self._return_type

    @property
    def body(self):
        return self._body

    def get_parameter_types(self):
        return list(map(lambda p: p.type, self._parameters))

    def call(self, args: list[ObjectProtocol]) -> ObjectProtocol:
        runtime = get_runtime()
        with runtime.x.frame(self):

            for argument, parameter in zip(args, self.parameters):
                # unpack the argument into the parameter. if an error has occurred, report it and do NOT call the function

                runtime.x.current_scope.refer(parameter.name, Argument(parameter, argument))

            last = None
            for instruction in self.body.nodes:
                try:
                    last = runtime.execute(instruction)
                except ReturnInstructionInvoked as e:
                    return e.value

            return last

    def add_parameter(self, name=None, typ=None, index: int = None):
        parameter = Parameter(name, typ, self)
        if index is None:
            self._parameters.append(parameter)
        else:
            self._parameters.insert(index, parameter)
        self.runtime_type = _FunctionType(self.get_parameter_types(), self._return_type)
        return parameter


# class Method(Function):
#     owner: "Class"
#     _static: bool
#
#     def __init__(self, owner: "Class", lexical_scope: "Scope", is_static: bool = False):
#         super().__init__(lexical_scope)
#         self.owner = owner
#         self._static = is_static
#
#     @property
#     def is_static(self):
#         return self._static
#
#     @is_static.setter
#     def is_static(self, value):
#         self._static = value


class FunctionGroup(NativeObject, BindProtocol):
    name: str
    _overloads: list[Function]

    class _BoundFunctionGroup(NativeObject, CallableProtocol):
        group: "FunctionGroup"
        args: list[ObjectProtocol]

        def __init__(self, group: "FunctionGroup", args: list[ObjectProtocol]):
            super().__init__()
            self.group = group
            self.args = args

        def get_matching_overloads(self, args: list[ObjectProtocol]):
            return [
                item.bind(self.args) if isinstance(item, BindProtocol) else item for item in self.group.get_matching_overloads(self.args + args)
            ]

        def call(self, args: list[ObjectProtocol]):
            overloads = self.get_matching_overloads(args)

            if not len(overloads):
                raise TypeError
            if len(overloads) > 1:
                raise TypeError
            return overloads[0].call(self.args + args)

    class _FunctionGroupType(CallableTypeProtocol):
        def __init__(self, group: "FunctionGroup"):
            self.group = group

        def compare_type_signature(self, other: "CallableTypeProtocol") -> bool:
            return any(overload.runtime_type.compare_type_signature(other) for overload in self.group.overloads)

        def get_type_of_application(self, types: list[TypeProtocol]) -> TypeProtocol:
            overloads = self.group.get_matching_overloads(types)

            if len(overloads) != 1:
                raise TypeError

            return overloads[0].return_type

    def __init__(self, name: str, *fns: Function):
        super().__init__()
        self.name = name
        self._overloads = list(fns)
        self.runtime_type = self._FunctionGroupType(self)

    @property
    def overloads(self):
        return self._overloads.copy()

    def bind(self, args: list[ObjectProtocol]):
        return self._BoundFunctionGroup(self, args)

    def add_overload(self, fn: Function):
        self._overloads.append(fn)

    def get_matching_overloads(self, args: list[ObjectProtocol]):
        return self.get_matching_overloads_for_types(list(map(lambda arg: arg.runtime_type, args)))

    def get_matching_overloads_for_types(self, arg_types: list[TypeProtocol]):
        result = []
        for overload in self._overloads:
            if len(overload.parameters) < len(arg_types):
                continue
            for parameter, arg_type in zip(overload.parameters, arg_types):
                if parameter.type is not None and not arg_type.assignable_to(parameter.type):
                    break
            else:
                result.append(overload)
        return result


class Scope(ScopeProtocol):
    _parent: Optional["Scope"]
    _items: dict[str, ObjectProtocol]
    _members: dict[str, ObjectProtocol]
    _types: dict[str, "Class"]

    def __init__(self, parent: Optional["Scope"] = None, **items: ObjectProtocol):
        self._parent = parent
        self._items = items
        self._types = {
            name: item.runtime_type for name, item in items.items()
        }
        self._members = {}

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

    @property
    def owner(self):
        return self.parent

    def add_local(self, name: str, value: ObjectProtocol = None, type_: "Class" = None):
        if value is None and type_ is None:
            raise ValueError(f"You must supply at least either the type or a value")
        if value is None:
            value = type_.default
        if type_ is None:
            type_ = value.runtime_type
        if name in self._items:
            raise NameAlreadyExistsError(name, self)
        self._items[name] = value
        self._types[name] = type_

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
        return self.parent.get_name(None, name)

    def set_nonlocal(self, name: str, value: Any):
        """
        Set a value bound to the given name in a parent scope.

        :raises: `NameNotFoundError` if the name doesn't exist in the current context.
        """
        if self.parent is None:
            raise NoParentScopeError(self)
        self.parent.set_name(name, value)

    def get_name(self, _, name: str):
        """
        Get a value bound to the given name in this or a parent scope.

        :raises: `NameNotFoundError` if the name doesn't exist in the current context.
        """
        if name in self._items:
            return self.get_local(name)
        if self.parent is None:
            raise NameNotFoundError(name, self)
        return self.parent.get_name(_, name)

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

    def define(self, name: str, value: ObjectProtocol = None, type_: "Class" = None):
        # if value is not None and value.owner is not None and value.owner is not self:
        #     raise NameAlreadyBoundError(f"'{name}' is already bound to scope {value.owner} and it can't be bound to {self}")
        # if value is not None and hasattr(value, "_owner"):
        #     value._owner = self
        self._members[name] = value
        self.add_local(name, value, type_)

    def refer(self, name: str, value: ObjectProtocol = None, type_: "Class" = None):
        self.add_local(name, value, type_)


class Class(_ObjectType, MutableClassProtocol, ScopeProtocol, CallableProtocol):
    """
    Represents a Z# class that's used by the ct-runtime interpreter.

    Z# classes define the behavior and fields of objects.
    Objects hold data.
    """

    name: str | None
    base: Optional["Class"]
    default: Any | None
    _lexical_scope: Scope
    _methods: dict[str, FunctionGroup]
    _constructor: FunctionGroup

    def __init__(self, name, base: ClassProtocol | None, lexical_scope: Scope | None):
        super().__init__()
        self.name = name
        self.base = base or _ObjectType.Instance
        self._lexical_scope = lexical_scope
        self._constructor = FunctionGroup(name)

    @property
    def constructor(self):
        return self._constructor

    def add_method(self, name: str, method: Function):
        method.add_parameter("this", self, 0)
        if name not in self._methods:
            group = FunctionGroup(name, method)
            super().add_method(name, group)
        else:
            self._methods[name].add_overload(method)

    def add_constructor(self, constructor: Function):
        constructor.add_parameter("this", self, 0)
        self._constructor.add_overload(constructor)

    def define(self, name: str, value: Function | Variable = None):
        if isinstance(value, Class):
            raise NotImplementedError
        if isinstance(value, Function):
            if name == self.name:
                self.add_constructor(value)
            else:
                self.add_method(name, value)
        if isinstance(value, Variable):
            self.add_field(name, value.type, value.value)

    def get_base(self) -> ClassProtocol | None:
        return self.base

    def get_name(self, instance: ObjectProtocol | None, name: str):
        try:
            return super().get_name(instance, name)
        except UnknownMemberError as e:
            try:
                return self._lexical_scope.get_name(instance, name)
            except NameNotFoundError:
                raise e

    def is_subclass(self, base):
        cls = self
        while cls.base is not None:
            if cls.base == base:
                return True
            cls = cls.base
        return cls == base

    def create_instance(self, args: list[ObjectProtocol]):
        instance = _Object(self)

        runtime = get_runtime()
        overloads = self.constructor.get_matching_overloads([instance, *args])

        if not len(overloads):
            raise TypeError(f"Could not find a suitable overload")
        if len(overloads) != 1:
            raise TypeError(f"Too many overloads match the given arguments")

        constructor = overloads[0]

        runtime.do_function_call(constructor, [instance, *args])

        return instance

    def call(self, args: list[ObjectProtocol]):
        return self.create_instance(args)

    def __str__(self):
        return f"<Z# Class '{self.name if self.name else '{Anonymous}'}'>"


class TypeClassImplementation(Class):
    implemented_type: TypeProtocol

    def __init__(self, name: str, lexical_scope: Scope, implemented_type: TypeProtocol):
        super().__init__(name, None, lexical_scope)
        self.implemented_type = implemented_type

    def add_method(self, name: str, method: Function):
        method.add_parameter("this", self.implemented_type, 0)
        if name not in self._methods:
            group = FunctionGroup(name, method)
            _ObjectType.add_method(self, name, group)
        else:
            self._methods[name].add_overload(method)


class TypeClass(_TypeClass, Class, CallableProtocol):
    name: str

    def __init__(self, name: str, lexical_scope: Scope):
        _TypeClass.__init__(self)
        Class.__init__(self, name, None, lexical_scope)
        self.name = name
        self.runtime_type = _FunctionType([_TypeType()], _TypeType())

    def call(self, args: list[ObjectProtocol]):
        if len(args) != 1:
            raise TypeError
        type = args[0]
        if not isinstance(type, TypeProtocol):
            raise TypeError
        return self.get_implementation(type)


Core = Scope()


class Frame(Scope):
    _function: Function

    def __init__(self, function: Function | None, parent: Optional[Scope] = None):
        super().__init__(parent)
        self._function = function

    @property
    def function(self):
        return self._function
