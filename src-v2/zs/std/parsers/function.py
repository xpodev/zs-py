from .misc import *
from ...ast.node_lib import Function


@subparser("fun")
def get_function(parser: Parser) -> Function:
    _fun = parser.eat("fun")

    name = None
    if parser.token(TokenType.Identifier):
        name = get_identifier(parser)
    elif parser.token(TokenType.String):
        name = Identifier(parser.eat(TokenType.String))

    parameters = []

    _l_paren = parser.eat(TokenType.L_Curvy)

    while not parser.token(TokenType.R_Curvy):
        parameters.append(get_typed_name(parser))

        if not parser.token(TokenType.Comma, eat=True):
            break

    _r_paren = parser.eat(TokenType.R_Curvy)

    _colon = return_type = None
    if parser.token(":"):
        _colon = parser.eat(":")

        return_type = parser.next(Expression)

    clauses = []
    # todo: parse clauses

    _left_bracket = parser.eat(TokenType.L_Curly)

    if parser.token(TokenType.R_Curly):
        body = []
    else:
        body = [parser.next(Expression)]

    _right_bracket = parser.eat(TokenType.R_Curly)

    return Function(
        _fun, name, _l_paren, parameters, _r_paren, _colon, return_type, clauses, body
    )
