from contextlib import contextmanager
from functools import singledispatchmethod
from pathlib import Path

from zs.ast.node import Node
from zs.ast import node_lib as nodes
from zs.ctrt.core import _NullType
from zs.ctrt.errors import ReturnInstructionInvoked, NameNotFoundError, BreakInstructionInvoked, ContinueInstructionInvoked
from zs.ctrt.objects import Frame, Function, Scope, NativeFunction, Class, FunctionGroup, Variable, TypeClass, Argument
from zs.processing import StatefulProcessor, State
from zs.std.processing.import_system import ImportSystem, ImportResult
from zs.text.token import TokenType

from zs.ctrt.native import *
from zs.utils import SingletonMeta

_GLOBAL_SCOPE = object()


def _get_dict_from_import_result(node: nodes.Import, result: ImportResult):
    res = {}
    errors = []

    match node.name:
        case nodes.Identifier() as star:
            if star.name != '*':
                errors.append(f"Can't perform a default import since that is not a feature yet")
            for name, item in result.all():
                res[name] = item
        case nodes.Alias() as alias:
            errors.append(f"Can't perform a default import since that is not a feature yet")
        case list() as names:
            for item in names:
                name = item.name
                try:
                    if isinstance(item, nodes.Alias):
                        if not isinstance(item.expression, nodes.Identifier):
                            errors.append(f"Imported name must be an identifier")
                        item_name = item.expression.name
                        res[name.name] = result.item(item_name)
                    else:
                        res[name] = result.item(name)
                except KeyError:
                    errors.append(f"Could not import name \"{name}\" from \"{node.source}\"")
        case _:
            errors.append(f"Unknown error while importing \"{node.source}\"")

    return res, errors


class InterpreterState:
    _frame_stack: list[Frame]
    _scope: Scope
    _global_scope: Scope
    _scope_protocol: ScopeProtocol | None

    def __init__(self, global_scope: Scope):
        self._frame_stack = [Frame(None, global_scope)]
        self._scope = self._global_scope = global_scope
        self._scope_protocol = None

    @property
    def current_frame(self):
        return self._frame_stack[-1]

    @property
    def current_scope(self):
        return self._scope

    @property
    def global_scope(self):
        return self._global_scope

    @contextmanager
    def scope_protocol(self, scope_protocol: ScopeProtocol):
        self._scope_protocol, old = scope_protocol, self._scope_protocol

        try:
            yield
        finally:
            self._scope_protocol = old

    @contextmanager
    def scope(self, scope: ScopeProtocol = None, /, parent: Scope = None, **items: ObjectProtocol):
        self._scope, old = scope or Scope(parent or self._scope, **items), self._scope
        try:
            yield self._scope
        finally:
            self._scope = old

    @contextmanager
    def frame(self, function: Function):
        self._frame_stack.append(Frame(function, function.lexical_scope))
        self._scope, scope = self.current_frame, self._scope
        try:
            yield
        finally:
            self._frame_stack.pop()
            self._scope = scope


# class Runtime(StatefulProcessor, metaclass=SingletonMeta):
#     _x: InterpreterState
#
#     def __init__(self, state: State, global_scope: Scope):
#         super().__init__(state)
#         self._x = InterpreterState(global_scope)
#
#     def do_function_call(self, function: Function | NativeFunction, args: list[ObjectProtocol]):
#         """
#         Executes a function call
#
#         :param function: The function to call. Must be a valid Z# function object or a native function object.
#         :param args: The arguments to call the function with.
#
#         :returns: The result of the function call, or None if an error has occurred.
#         """
#
#     def do_return(self, value: ObjectProtocol | None = None):
#         """
#         Execute a return command which will terminate the function.
#
#         :param value: The return value of the current executing function or `None`, if there's no return value (void).
#         """
#
#     def do_resolve_name(self, name: str) -> ObjectProtocol | None:
#         """
#         Resolves a name in the current scope.
#
#         :param name: The name of the object to look for.
#
#         :returns: The object bound to the name closest to the current scope or `None` if no such object was found.
#         """


class Interpreter(StatefulProcessor, metaclass=SingletonMeta):
    """
    This class is responsible for executing nodes.
    """

    _x: InterpreterState
    _import_system: ImportSystem

    def __init__(self, state: State, global_scope: Scope = None, import_system: ImportSystem = None):
        super().__init__(state)
        self._x = InterpreterState(global_scope or Scope())
        self._import_system = import_system or ImportSystem()

        self._srf_access = False

    @property
    def x(self):
        return self._x

    @property
    def import_system(self):
        return self._import_system

    @contextmanager
    def new_context(self):
        context = self.x
        try:
            self._x = InterpreterState(self.x.global_scope)
            yield
        finally:
            self._x = context

    @contextmanager
    def srf_access(self):
        self._srf_access = True
        try:
            yield
        finally:
            self._srf_access = False

    def execute(self, node: Node):
        return self._execute(node)

    @singledispatchmethod
    def _execute(self, node: Node):
        return node

    _exec = _execute.register

    @_exec
    def _(self, assign: nodes.Assign):
        # target = assign.left
        # if isinstance(target, nodes.Identifier):
        #     self.x.frame.set_name(target.name, self.execute(assign.right))
        # else:
        #     self.state.warning(f"Assignment for anything other than a variable is not yet supported.")
        with self.srf_access():
            target = self.execute(assign.left)

            if not isinstance(target, SetterProtocol):
                self.state.error(f"Could not assign to '{assign.left}' because it does not implement the setter protocol", assign)

            target.set(self.execute(assign.right))

    @_exec
    def _(self, block: nodes.Block):
        with self.x.scope():

            for statement in block.statements:
                self.execute(statement)

    @_exec
    def _(self, break_: nodes.Break):
        loop = self.execute(break_.loop) if break_.loop else None

        raise BreakInstructionInvoked(loop)

    @_exec
    def _(self, continue_: nodes.Continue):
        loop = self.execute(continue_.loop) if continue_.loop else None

        raise ContinueInstructionInvoked(loop)

    @_exec
    def _(self, expression_statement: nodes.ExpressionStatement):
        self.execute(expression_statement.expression)

    @_exec
    def _(self, call: nodes.FunctionCall):
        group_or_function = self.execute(call.callable)

        # is function really a function?

        arguments = list(map(self.execute, call.arguments))

        # native function support
        if isinstance(group_or_function, NativeFunction):
            return self.do_function_call(group_or_function, arguments)

        # did we successfully evaluate the arguments?

        # can we unpack the arguments into the function parameters without any errors? I guess we should try...

        if isinstance(group_or_function, FunctionGroup):
            overloads = group_or_function.get_matching_overloads(arguments)

            if len(overloads) > 1:
                raise TypeError(f"Too many overloads were found")
            if not len(overloads):
                raise TypeError(f"Could not find a suitable overload")

            function = overloads[0]
        else:
            function: Function = group_or_function

        return self.do_function_call(function, arguments)

    @_exec
    def _(self, function: nodes.Function):
        func = Function(self.x.current_scope)

        func.name = function.name.name if function.name else None

        if func.name:
            self.x.current_scope.define(func.name, func)

        for parameter in function.parameters:
            parameter_type = self.execute(parameter.type) if parameter.type else None
            param = func.add_parameter(parameter.name.name, parameter_type)

        if function.body:
            func.body.nodes.extend(function.body)

        return func

    @_exec
    def _(self, identifier: nodes.Identifier):
        try:
            item = self.x.current_scope.get_name(None, identifier.name)
            if self._srf_access:
                return item
            if isinstance(item, GetterProtocol):
                return item.get()
            return item
        except NameNotFoundError:
            return self.state.error(f"Could not resolve name '{identifier.name}'", identifier)

    @_exec
    def _(self, if_: nodes.If):

        with self.x.scope():
            condition = self.execute(if_.condition)

            if if_.name:
                if_.owner = if_.type = None
                self.x.current_scope.define(if_.name.name, if_)

            if condition:
                self.execute(if_.if_true)
            elif if_.if_false:
                self.execute(if_.if_false)

    @_exec
    def _(self, import_: nodes.Import):
        result = self.__get_import_result(import_)

        if isinstance(result, str):
            return self.state.error(result)

        items, errors = _get_dict_from_import_result(import_, result)
        for name, item in items.items():
            self.x.current_scope.refer(name, item)

        for error in errors:
            self.state.error(error, import_)

        return result

    @_exec
    def _(self, literal: nodes.Literal):
        value = literal.token_info.literal.value
        if value == "true":
            return Boolean(True)
        if value == "false":
            return Boolean(False)
        if value == "null":
            return _NullType.Instance
        match literal.token_info.literal.type:
            case TokenType.String:
                return String(value)
            case TokenType.Decimal:
                return Int64(int(literal.token_info.literal.value))
            case TokenType.Real:
                return Float64(float(literal.token_info.literal.value))
            case _:
                raise TypeError(literal.token_info.literal.type)

    @_exec
    def _(self, member_access: nodes.MemberAccess):
        with self.srf_access():
            obj_srf = self.execute(member_access.object)
        obj = self.execute(member_access.object)
        member = obj_srf.get_type().get_name(obj, member_access.member.name)
        if self._srf_access:
            return member
        if isinstance(member, GetterProtocol):
            return member.get()
        return member

    @_exec
    def _(self, module: nodes.Module):
        ...

    @_exec
    def _(self, cls: nodes.Class):
        name = cls.name.name if cls.name else None
        class_ = Class(name, self.execute(cls.base), self.x.current_scope)

        if class_.name is not None:
            self.x.current_scope.define(class_.name, class_)

        with self.x.scope(class_):
            for item in cls.items:
                self.execute(item)

            return class_

    @_exec
    def _(self, tc: nodes.TypeClass):
        type_class = TypeClass(tc.name.name)

        self.x.current_scope.define(type_class.name, type_class)

        with self.x.scope(type_class), self.x.scope_protocol(type_class):
            for item in tc.items:
                self.execute(item)

        return type_class

    @_exec
    def _(self, impl: nodes.TypeClassImplementation):
        type_class: TypeClass = self.execute(impl.name)
        impl_type: TypeProtocol = self.execute(impl.implemented_type)

        if not isinstance(type_class, TypeClass):
            raise TypeError(f"'{impl.name}' is not a valid type class")

        if not isinstance(impl_type, TypeProtocol):
            raise TypeError(f"implementation for typeclass '{type_class.name}' must be a class")

        implementation: Class = Class(f"{type_class.name}.{impl_type}", None, self.x.current_scope)
        with self.x.scope(implementation, value=implementation), self.x.scope_protocol(implementation):
            for item in impl.items:
                self.execute(item)

        # validate that all items are implemented

        type_class.add_implementation(impl_type, implementation)

        return implementation

    @_exec
    def _(self, return_: nodes.Return):
        expression = self.execute(return_.expression) if return_.expression else None
        raise ReturnInstructionInvoked(expression)

    @_exec
    def _(self, var: nodes.Var):
        var_type = self.execute(var.name.type) if var.name.type is not None else None
        initializer = self.execute(var.initializer) if var.initializer is not None else None

        if var_type is None and initializer is None:
            return self.state.error(f"You must either specify a type or a value in a `var` statement", var)

        if var_type is None:
            var_type = initializer.get_type()
        elif not isinstance(var_type, TypeProtocol):
            return self.state.error(f"'var' statement type must be a valid Z# type")
        elif initializer is None:
            initializer = var_type.default()

        if var_type is not None and not var_type.is_instance(initializer):
            return self.state.error(f"Initializer expression does not match the variable type", var)

        name = var.name.name.name
        self.x.current_scope.define(name, Variable(name, var_type, initializer))

    @_exec
    def _(self, when: nodes.When):
        when.owner = when.type = None

        with self.x.scope():
            if when.name:
                self.x.current_scope.define(when.name.name, when)

            value = self.execute(when.expression)

            self.x.current_scope.refer("value", value)

            skip_validation = False
            for case in when.cases:
                case_value = self.execute(case.expression)

                if skip_validation or case_value == value:
                    try:
                        self.execute(case.body)
                    except BreakInstructionInvoked:
                        ...
                    except ContinueInstructionInvoked:
                        skip_validation = True
                        continue
                    break
            else:
                if when.else_body:
                    self.execute(when.else_body)

    @_exec
    def _(self, while_: nodes.While):
        with self.x.scope():
            if while_.name:
                while_wrapper = WhileWrapper(while_)
                self.x.current_scope.define(while_.name.name, while_wrapper)

            while self.execute(while_.condition):
                try:
                    self.execute(while_.body)
                except BreakInstructionInvoked as e:
                    if e.loop is None or e.loop.node is while_:
                        break
                    raise
                except ContinueInstructionInvoked as e:
                    if e.loop is None or e.loop.node is while_:
                        continue
                    raise
            else:
                if while_.else_body:
                    self.execute(while_.else_body)

    def __get_import_result(self, import_: nodes.Import):
        source = self.execute(import_.source)

        if isinstance(source, String):
            source = source.native
            path = Path(str(source))
            if not path.suffixes:
                path /= f"{path.stem}.module.zs"

            result = self._import_system.import_from(path)

            if result is None:
                return f"Could not import \"{path}\""

            result._node = import_

            return result

        return source  # todo: make sure is ImportResult

    # runtime implementation functions

    def do_function_call(self, function: Function | NativeFunction, arguments: list[ObjectProtocol]) -> ObjectProtocol:
        if isinstance(function, NativeFunction):
            return function.invoke(*arguments)

        with self.x.frame(function):

            for argument, parameter in zip(arguments, function.parameters):
                # unpack the argument into the parameter. if an error has occurred, report it and do NOT call the function

                self.x.current_scope.refer(parameter.name, Argument(parameter, argument))

            last = None
            for instruction in function.body.nodes:
                try:
                    last = self.execute(instruction)
                except ReturnInstructionInvoked as e:
                    return e.value

            return last
