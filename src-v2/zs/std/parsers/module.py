from zs.ast.node_lib import Module
from zs.std.parsers.misc import subparser, get_identifier
from zs.text.parser import Parser


@subparser("module")
def get_module(parser: Parser) -> Module:
    _module = parser.eat("module")

    name = get_identifier(parser)

    items = _left_bracket = _right_bracket = _semicolon = None
    if parser.token("{"):
        _left_bracket = parser.eat("{")
        items = parser.next("Document")
        _right_bracket = parser.eat("}")
    else:
        _semicolon = parser.eat(";")

    return Module(_module, name, _left_bracket, items, _right_bracket, _semicolon)
