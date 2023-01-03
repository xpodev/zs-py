from zs.ast.node import Node
from zs.ast.node_lib import Identifier, Import, Alias, Literal, Expression
from zs.processing import State
from zs.std.parsers.function import get_function
from zs.std.parsers.misc import get_inlined, get_import
from zs.std.parsers.module import get_module
from zs.std.parsers.type import get_class
from zs.text.parser import ContextualParser, SubParser, Parser
from zs.text.token import TokenType, Token
from zs.text.token_stream import TokenStream


__all__ = [
    "DocumentParser",
]


def _bind(fn):
    return lambda _, *args: fn(*args)


class DocumentParser(ContextualParser[list[Node]]):
    """
    A parser that can parse the body of a Z# document. It outputs a list of nodes representing the nodes in the document.
    """

    _stream: TokenStream
    _parser: Parser

    def __init__(self, state: State):
        super().__init__(state, "Document")

        self.symbol(TokenType.R_Curly)

        self.symbol(TokenType.EOF)

    def parse(self, parser: Parser, binding_power: int):
        self._parser = parser
        self._stream = parser.stream

        # todo: make coroutine
        result = []
        while not self._stream.end:
            node = super().parse(parser, binding_power)
            if node is None:
                self.state.warning(f"Unexpected None while parsing")
                break
            result.append(node)

        return result

    def setup(self, parser: "Parser"):
        # self.add_parser(get_function)
        # self.add_parser(get_class)
        ...

    def _on_unknown_token(self, token: Token):
        expr = self._parser.get(Expression)
        try:
            result = expr.get_parser(token.type)
        except KeyError:
            try:
                result = expr.get_parser(token.value)
            except KeyError:
                return None
        # self._parser.eat(";")
        return result
