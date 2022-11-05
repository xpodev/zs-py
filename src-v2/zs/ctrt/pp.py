from functools import singledispatchmethod

from zs.ast import node_lib
from zs.ast.node import Node
from zs.processing import StatefulProcessor, State
from .instructions import SetLocal, Call, Name, Import, EnterScope, ExitScope, DeleteName
from ..text.token import TokenType


class Preprocessor(StatefulProcessor):
    def __init__(self, state: State):
        super().__init__(state)

    @singledispatchmethod
    def preprocess(self, node: Node):
        self.state.warning(f"Preprocessing node {node}", node)
        return node

    _pp = preprocess.register

    @_pp
    def _(self, node: node_lib.Function):
        name = str(node.name.name) if node.name is not None else None
        init = Call(Name("Function", node_lib.Identifier(node.token_info.keyword_fun)), [name], node)

        delete = name is None
        if delete:
            name = f"$"

        var = SetLocal(name, init, node)

        parameters = []
        for parameter in node.parameters:
            parameters.append(
                Call(
                    Call(
                        Name("_._"),
                        [Call(Name("_._"), [Name(name), "body"]), "append"]
                    ),
                    [
                        SetLocal(
                            parameter.name,
                            Call(
                                Call(
                                    Name("_._"),
                                    [Name(name), "add_parameter"]),
                                [parameter.name, self.preprocess(parameter.type)]),
                            parameter.node
                        )
                    ]
                )
            )

        body = []
        for inst in node.body:
            ir = self.preprocess(inst)
            if isinstance(ir, list):
                method = "extend"
            else:
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

        return [
            var,
            EnterScope(),
            *parameters,
            *body,
            ExitScope(),
            *([DeleteName(name)] if delete else [])
        ]

    @_pp
    def _(self, node: node_lib.Var):
        return SetLocal(str(node.name.name.name), self.preprocess(node.initializer), node)

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
    def _(self, node: node_lib.Literal):
        value = node.token_info.literal.value
        match node.token_info.literal.type:
            case TokenType.String:
                return str(value)
            case TokenType.Decimal:
                return int(str(node.token_info.literal.value))
            case _:
                raise TypeError(node.token_info.literal.type)
