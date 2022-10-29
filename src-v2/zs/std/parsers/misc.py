from typing import overload, Generic, TypeVar, Callable

from zs.ast.node import Node
from zs.ast.node_lib import Identifier, TypedName, Tuple, Expression, Inlined, Alias, Import, Literal, Var
from zs.std import String, Bool, List, Int32
from zs.text.parser import SubParser, Parser
from zs.text.token import TokenType, Token

_T = TypeVar("_T")
_U = TypeVar("_U")


class _SubParserWrapper(SubParser, Generic[_T]):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    @overload
    def __call__(self, parser: Parser) -> _T | None: ...
    @overload
    def __call__(self, parser: Parser, left: Node) -> _T | None: ...

    def __call__(self, parser: Parser, left: None = None) -> _T | None:
        if left is None:
            return self.nud(parser)
        return self.led(parser, left)


def _is_not(a, b, v=None):
    return a if a is not v else b


def subparser(token: TokenType | str | String) -> Callable[[Callable[[Parser], _T]], _SubParserWrapper[_T]]:
    def wrapper(fn: Callable[[Parser], _T]):
        return _SubParserWrapper(-1, token, nud=fn)
    return wrapper


def modifier(name: str | String):
    def wrapper(fn: Callable[[Token, _T], _U]):
        @subparser
        def parse(parser: Parser) -> _U:
            _modifier = parser.eat(name)

            node = parser.next()

            return fn(_modifier, node)
        return parse
    return wrapper


def literal(token: TokenType) -> _SubParserWrapper[Literal]:
    @subparser(token)
    def wrapper(parser: Parser) -> Literal:
        return Literal(parser.eat(token))

    return wrapper


def separated(token: str | String | TokenType, binding_power: int | Int32, context: type | str = None):
    def wrapper(parser: Parser, left):
        if not parser.token(token):
            return [left] if not isinstance(left, list) else left

        if not isinstance(left, list):
            left = [left]

        parser.eat(token)
        right = parser.next(context, binding_power)
        return [*left, right]

    return wrapper


def copy_with(
        original: SubParser,
        *,
        binding_power: int | Int32 = None,
        token: str | String | TokenType = None,
        nud: Callable[[Parser], Node] = None,
        led: Callable[[Parser, Node], Node] = None
) -> SubParser:
    return SubParser(
        _is_not(binding_power, original.binding_power),
        _is_not(token, original.token),
        nud=_is_not(nud, original.nud),
        led=_is_not(led, original.led)
    )


get_string = literal(TokenType.String)


@subparser(TokenType.Identifier)
def get_identifier(parser: Parser):
    return Identifier(parser.eat(TokenType.Identifier))


def get_typed_name(parser: Parser, must_be_typed: bool | Bool = False):
    name = get_identifier(parser)

    if not must_be_typed and not parser.token(':'):
        return TypedName(name, None, None)

    _colon = parser.eat(':')
    type_ = parser.next(Expression)

    return TypedName(name, _colon, type_)


@subparser(TokenType.L_Curvy)
def get_tuple(parser: Parser):
    _left = parser.eat('(')

    if not parser.token(')'):
        expressions = separated(",", 20, Expression)(parser, parser.next(Expression))
    else:
        expressions = []

    _right = parser.eat(')')

    return Tuple(_left, expressions, _right)


@subparser("inline")
def get_inlined(parser: Parser):
    _inline = parser.eat("inline")

    item = parser.next("Inlined")

    return Inlined(_inline, item)


@subparser("import")
def get_import(parser: Parser):
    _import = parser.eat("import")

    if parser.token("*"):
        imported_names = Identifier(parser.eat("*"))
        if parser.token("as"):
            imported_names = Alias(imported_names, parser.eat("as"), get_identifier(parser))
    elif parser.token(TokenType.String):
        return Import(
            _import, None, None, None, None, Literal(parser.eat(TokenType.String)), parser.eat(";")
        )
    else:
        imported_names: List[Identifier | Alias] | Identifier | Alias = List()

    _l_curly = _r_curly = None
    if parser.token("{"):
        _l_curly = parser.eat("{")
        while True:
            name = get_identifier(parser)

            if parser.token("as"):
                name = Alias(name, parser.eat("as"), get_identifier(parser))

            imported_names.add(name)

            if not parser.token("}"):
                parser.eat(",")
            else:
                break
        _r_curly = parser.eat("}")

    _from = parser.eat("from")

    source = Literal(parser.eat(TokenType.String))  # todo: expression

    return Import(
        _import, _l_curly, imported_names, _r_curly, _from, source, parser.eat(";")
    )


@subparser("var")
def get_var(parser: Parser):
    _var = parser.eat("var")

    name = get_typed_name(parser)

    _assign = initializer = None
    if parser.token("="):
        _assign = parser.eat("=")

        initializer = parser.next(Expression)

    return Var(_var, name, _assign, initializer)

