from contextlib import contextmanager
from functools import singledispatchmethod
from pathlib import Path

from zs.ast.node import Node
from zs.ast import node_lib as nodes
from zs.ctrt.errors import ReturnInstructionInvoked, NameNotFoundError, BreakInstructionInvoked, ContinueInstructionInvoked
from zs.ctrt.objects import Frame, Function, Scope, NativeFunction
from zs.processing import StatefulProcessor, State
from zs.std.processing.import_system import ImportSystem, ImportResult
from zs.text.token import TokenType


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
            for name in names:
                try:
                    name = name.name
                    if isinstance(name, nodes.Alias):
                        if not isinstance(name.expression, nodes.Identifier):
                            errors.append(f"Imported name must be an identifier")
                        item = name.expression.name
                        res[name] = result.item(item)
                    else:
                        res[name] = result.item(name)
                except KeyError:
                    errors.append(f"Could not import name \"{name}\" from \"{node.source}\"")
        case _:
            errors.append(f"Unknown error while importing \"{node.source}\"")

    return res, errors


class InterpreterState:
    _frame_stack: list[Frame]
    _global_scope: Scope

    def __init__(self, global_scope: Scope):
        self._frame_stack = [Frame(None, global_scope)]
        self._global_scope = global_scope

    @property
    def frame(self):
        return self._frame_stack[-1]

    @property
    def global_scope(self):
        return self._global_scope

    def push_frame_for(self, function: Function):
        self._frame_stack.append(Frame(function, function.lexical_scope))

    def push_frame(self, parent: Scope = _GLOBAL_SCOPE):
        if parent is _GLOBAL_SCOPE:
            parent = self._global_scope
        self._frame_stack.append(Frame(None, parent))

    def pop_last_frame(self):
        self._frame_stack.pop()


class Interpreter(StatefulProcessor):
    """
    This class is responsible for executing nodes.
    """

    _x: InterpreterState
    _import_system: ImportSystem

    def __init__(self, state: State, global_scope: Scope = None, import_system: ImportSystem = None):
        super().__init__(state)
        self._x = InterpreterState(global_scope or Scope())
        self._import_system = import_system or ImportSystem()

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

    def execute(self, node: Node):
        return self._execute(node)

    @singledispatchmethod
    def _execute(self, node: Node):
        return node

    _exec = _execute.register

    @_exec
    def _(self, assign: nodes.Assign):
        target = assign.left
        if isinstance(target, nodes.Identifier):
            self.x.frame.set_name(target.name, self.execute(assign.right))
        else:
            self.state.warning(f"Assignment for anything other than a variable is not yet supported.")

    @_exec
    def _(self, block: nodes.Block):
        self.x.push_frame(self.x.frame)

        for statement in block.statements:
            self.execute(statement)

        self.x.pop_last_frame()

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
        function = self.execute(call.callable)

        # is function really a function?

        arguments = list(map(self.execute, call.arguments))

        # native function support
        if isinstance(function, NativeFunction):
            return function.invoke(*((self,) if function.include_runtime else ()), *arguments)

        # did we successfully evaluate the arguments?

        # can we unpack the arguments into the function parameters without any errors? I guess we should try...

        self.x.push_frame_for(function)

        for argument, parameter in zip(arguments, function.parameters):
            # unpack the argument into the parameter. if an error has occurred, report it and do NOT call the function

            self.x.frame.add_local(parameter.name, argument)

        last = None
        for instruction in function.body.nodes:
            try:
                last = self.execute(instruction)
            except ReturnInstructionInvoked as e:
                return e.value

        return last

    @_exec
    def _(self, function: nodes.Function):
        func = Function(self.x.frame)

        func.name = function.name.name if function.name else None

        if func.name:
            self.x.frame.add_local(func.name, func)

        for parameter in function.parameters:
            parameter_type = self.execute(parameter.type) if parameter.type else None
            param = func.add_parameter(parameter.name.name, parameter_type)

        func.body.nodes.extend(function.body)

        return func

    @_exec
    def _(self, identifier: nodes.Identifier):
        try:
            return self.x.frame.get_name(identifier.name)
        except NameNotFoundError:
            return self.state.error(f"Could not resolve name '{identifier.name}'", identifier)

    @_exec
    def _(self, if_: nodes.If):
        condition = self.execute(if_.condition)

        if if_.name:
            self.x.push_frame(self.x.frame)
            self.x.frame.add_local(if_.name.name, if_)

        if condition:
            self.execute(if_.if_true)
        elif if_.if_false:
            self.execute(if_.if_false)

        if if_.name:
            self.x.pop_last_frame()

    @_exec
    def _(self, import_: nodes.Import):
        result = self.__get_import_result(import_)

        if isinstance(result, str):
            return self.state.error(result)

        items, errors = _get_dict_from_import_result(import_, result)
        for name, item in items.items():
            self.x.frame.add_local(name, item)

        for error in errors:
            self.state.error(error, import_)

        return result

    @_exec
    def _(self, literal: nodes.Literal):
        value = literal.token_info.literal.value
        if value == "true":
            return True
        if value == "false":
            return False
        match literal.token_info.literal.type:
            case TokenType.String:
                return value
            case TokenType.Decimal:
                return int(literal.token_info.literal.value)
            case TokenType.Real:
                return float(literal.token_info.literal.value)
            case _:
                raise TypeError(literal.token_info.literal.type)

    @_exec
    def _(self, member_access: nodes.MemberAccess):
        return getattr(self.execute(member_access.object), member_access.member.name)

    @_exec
    def _(self, module: nodes.Module):
        ...

    @_exec
    def _(self, cls: nodes.Class):
        ...

    @_exec
    def _(self, return_: nodes.Return):
        expression = self.execute(return_.expression) if return_.expression else None
        raise ReturnInstructionInvoked(expression)

    @_exec
    def _(self, when: nodes.When):
        if when.name:
            self.x.push_frame(self.x.frame)
            self.x.frame.add_local(when.name.name, when)

        value = self.execute(when.expression)

        self.x.push_frame(self.x.frame)
        self.x.frame.add_local("value", value)

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

        self.x.pop_last_frame()

        if when.name:
            self.x.pop_last_frame()

    @_exec
    def _(self, while_: nodes.While):
        if while_.name:
            self.x.push_frame(self.x.frame)
            self.x.frame.add_local(while_.name.name, while_)

        while self.execute(while_.condition):
            try:
                self.execute(while_.body)
            except BreakInstructionInvoked as e:
                if e.loop is None or e.loop is while_:
                    break
                raise
            except ContinueInstructionInvoked as e:
                if e.loop is None or e.loop is while_:
                    continue
                raise
        else:
            if while_.else_body:
                self.execute(while_.else_body)

        if while_.name:
            self.x.pop_last_frame()

    def __get_import_result(self, import_: nodes.Import):
        source = self.execute(import_.source)

        if isinstance(source, str):
            path = Path(str(source))
            if not path.suffixes:
                path /= f"{path.stem}.module.zs"

            result = self._import_system.import_from(path)

            if result is None:
                return f"Could not import \"{path}\""

            result._node = import_

            return result

        return source  # todo: make sure is ImportResult
