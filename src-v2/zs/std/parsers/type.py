from zs.ast.node_lib import Class
from zs.processing import State
from zs.std.parsers.function import get_function
from zs.std.parsers.misc import *
from zs.text.parser import Parser, ContextualParser


@subparser("class")
def get_class(parser: Parser) -> Class:
    _class = parser.eat("class")

    name = None
    if parser.token(TokenType.Identifier):
        name = get_identifier(parser)
    elif parser.token(TokenType.String):
        name = Identifier(parser.eat(TokenType.String))

    _left_bracket = parser.eat('{')

    body = []
    while not parser.token('}'):
        body.append(parser.next("ClassBody"))

    _right_bracket = parser.eat('}')

    return Class(_class, name, _left_bracket, body, _right_bracket)


class ClassBodyParser(ContextualParser[list[Node]]):
    def __init__(self, state: State):
        super().__init__(state, "ClassBody")

        self.add_parser(get_function)
