from zs.ast.node import Node
from zs.ast.node_lib import Identifier, Import, Alias, Literal, Expression, Function, TypedName, Parameter, FunctionCall, Binary, MemberAccess, Assign
from zs.processing import State
from zs.std.parsers.misc import get_identifier, get_tuple, get_string, separated, copy_with
from zs.text.parser import ContextualParser, SubParser, Parser
from zs.text.token import TokenType, Token
from zs.text.token_stream import TokenStream


__all__ = [
    "ExpressionParser",
]


class ExpressionParser(ContextualParser[Expression]):
    """
    A parser that can parse Z# expressions
    """

    _stream: TokenStream

    def __init__(self, state: State):
        super().__init__(state, "Expression")

        self.add_parser(copy_with(get_identifier, binding_power=0))
        self.add_parser(copy_with(get_string, binding_power=0))
        self.add_parser(SubParser(0, TokenType.Decimal, nud=lambda p: Literal(p.eat(TokenType.Decimal))))
        self.add_parser(SubParser(0, "true", nud=lambda p: Literal(p.eat("true"))))
        self.add_parser(SubParser(0, "false", nud=lambda p: Literal(p.eat("false"))))
        self.add_parser(SubParser(100, TokenType.L_Curvy, led=self._next_function_call))

        self.add_parser(SubParser(80, ".", led=self._next_member_access))

        self.add_parser(SubParser.infix_r(20, "=", self.parse))

        # todo: fix semicolon operator
        # self.add_parser(SubParser.infix_l(5, TokenType.Semicolon, lambda parser, left: (parser.eat(":"), parser.next(5))[1]))

        self.add_parser(SubParser(20, TokenType.Comma, led=separated(",", 20, Expression)))
        self.add_parser(SubParser.infix_l(5, ";", self.parse))
        self.symbol(TokenType.R_Curvy)
        self.symbol(TokenType.R_Curly)

        self.symbol(TokenType.EOF)

    def parse(self, parser: Parser, binding_power: int) -> Expression:
        self._stream = parser.stream

        return super().parse(parser, binding_power)

    def _next_function_call(self, parser: Parser, left: Node):
        args = get_tuple(parser)

        if not isinstance(left, Expression):
            self.state.error(f"Only an expression may appear on the left side of a function call")
            return args

        return FunctionCall(left, args.token_info.left_parenthesis, args.items, args.token_info.right_parenthesis)

    def _next_member_access(self, parser: Parser, left: Node):
        _dot = parser.eat(".")

        right = get_identifier(parser)

        if not isinstance(left, Expression):
            self.state.error(f"Member access operator may only appear after an expression")
            return

        return MemberAccess(left, _dot, right)

    def _on_unknown_token(self, token: Token):
        if token == TokenType.Identifier:
            return Identifier(self._stream.read())
