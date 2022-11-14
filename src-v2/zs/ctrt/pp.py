from functools import singledispatchmethod, reduce

from zs.ast import node_lib
from zs.ast.node import Node
from zs.processing import StatefulProcessor, State
from .instructions import SetLocal, Call, Name, Import, EnterScope, ExitScope, DeleteName, Do, Raw, RawCall
from ..text.token import TokenType


class Preprocessor(StatefulProcessor):
    def __init__(self, state: State):
        super().__init__(state)

    def preprocess(self, node: Node):
        self.run()
        return self._preprocess(node)

    @singledispatchmethod
    def _preprocess(self, node: Node):
        # self.state.warning(f"Preprocessing node {node}", node)
        if node is None:
            return node
        return Call(Name(f"pp_{type(node).__name__}"), [node])
        # return node

    _pp = _preprocess.register

    @_pp
    def _(self, node: node_lib.Binary):
        return Call(Name(f"_{str(node.token_info.operator.value)}_"), [self.preprocess(node.left), self.preprocess(node.right)], node)

    @_pp
    def _(self, node: node_lib.Function):
        name = str(node.name.name) if node.name is not None else None
        init = Call(Name("Function", node_lib.Identifier(node.token_info.keyword_fun)), [
            name,
            Call(Name("_._"), [Call(Name("_._"), [Call(Name("_._"), [Call(Name("_._"), [Name("__srf__"), "toolchain"]), "interpreter"]), "x"]), "local_scope"])
        ], node)

        delete = name is None
        if delete:
            name = "$"

        var = SetLocal(name, init, True, node)

        parameters = []
        for parameter in node.parameters:
            parameters.append(
                Call(
                    Call(
                        Name("_._"),
                        [Name(name), "add_parameter"]
                    ),
                    [parameter.name.name, self.preprocess(parameter.type) if parameter.type else None]
                )
            )

        body = []
        for inst in node.body:
            ir = self.preprocess(inst)
            if isinstance(ir, list):
                ir = list(map(Raw, ir))
                method = "extend"
            else:
                ir = Raw(ir)
                method = "append"
            body.append(
                Call(
                    Call(
                        Name("_._"),
                        [Call(Name("_._"), [Name(name), "body"]), method]
                    ),
                    [ir]
                )
            )

        return reduce(lambda x, y: RawCall(Name("_;_"), [x, y]), [
            var,
            EnterScope(None),
            *parameters,
            *body,
            ExitScope(),
            DeleteName(name) if delete else Name(name)
        ])
        # return Do(*[
        #     var,
        #     EnterScope(),
        #     *parameters,
        #     *body,
        #     ExitScope(),
        #     *([DeleteName(name)] if delete else [])
        # ], node)

    @_pp
    def _(self, node: node_lib.Var):
        return SetLocal(str(node.name.name.name), self.preprocess(node.initializer), True, node)

    @_pp
    def _(self, node: node_lib.FunctionCall):
        return Call(self.preprocess(node.callable), list(map(self.preprocess, node.arguments)), node)

    @_pp
    def _(self, node: node_lib.MemberAccess):
        return Call(Name("_._"), [self.preprocess(node.object), str(node.member.name)], node)

    @_pp
    def _(self, node: node_lib.Identifier):
        return Name(str(node.name))

    @_pp
    def _(self, node: node_lib.Import):
        if node.name is None:
            names = None
        elif isinstance(node.name, node_lib.Identifier):
            names = "*"
        else:
            names = []
            for name in node.name:
                if isinstance(name, node_lib.Identifier):
                    names.append(str(name.name))
                else:
                    names.append((name.name, name.expression.name))
        return Import(self.preprocess(node.source), names, node)

    @_pp
    def _(self, node: node_lib.Inlined):
        result = self.preprocess(node.item)

        match result:
            case Import():
                return result

    @_pp
    def _(self, node: node_lib.Literal):
        value = node.token_info.literal.value
        if value == "true":
            return True
        if value == "false":
            return False
        match node.token_info.literal.type:
            case TokenType.String:
                return str(value)
            case TokenType.Decimal:
                return int(str(node.token_info.literal.value))
            case _:
                raise TypeError(node.token_info.literal.type)
