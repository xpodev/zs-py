from contextlib import contextmanager
from typing import Callable, overload, TypeVar, Generic

from .token import TokenType
from .token_stream import TokenStream
from .. import EmptyObject
from ..ast.node import Node
from zs.std.objects.wrappers import String, Int32, Dictionary, List
from ..processing import StatefulProcessor, State

Binary = Unary = None  # todo: import


_T = TypeVar("_T")


__all__ = [
    "ContextualParser",
    "Parser",
    "SubParser",
]


class SubParser(EmptyObject):
    _binding_power: Int32
    _token: String | TokenType
    _nud: Callable[[TokenStream], Node | None] | None
    _led: Callable[[TokenStream, Node], Node | None] | None

    def __init__(
            self,
            binding_power: int | Int32,
            token: str | String | TokenType,
            *,
            nud: Callable[[TokenStream], Node | None] | None = None,
            led: Callable[[TokenStream, Node], Node | None] | None = None
    ):
        super().__init__()
        self.binding_power = binding_power
        self._token = String(token) if not isinstance(token, TokenType) else token
        self._nud = nud
        self._led = led

    @property
    def binding_power(self):
        return self._binding_power

    @binding_power.setter
    def binding_power(self, value: int | Int32):
        self._binding_power = Int32(value)

    @property
    def token(self):
        return self._token

    @property
    def nud(self):
        return self._nud

    @nud.setter
    def nud(self, value: Callable[[TokenStream], Node | None] | None):
        self.nud = value

    @nud.deleter
    def nud(self):
        self.nud = None

    @property
    def led(self):
        return self._led

    @led.setter
    def led(self, value: Callable[[TokenStream, Node], Node | None] | None):
        self._led = value

    @led.deleter
    def led(self):
        self.led = None

    @staticmethod
    def _infix_func(binding_power: Int32, token: String, expr_fn: Callable[[TokenStream, Int32], Node]):
        return lambda stream, left: Binary(left, token, expr_fn(stream, binding_power))

    @staticmethod
    def _prefix_func(binding_power: Int32, token: String, expr_fn: Callable[[TokenStream, Int32], Node]):
        return lambda stream: Unary(token, expr_fn(stream, binding_power))

    @classmethod
    def infix_l(cls, binding_power: int | Int32, token: str | String | TokenType, expr_fn: Callable[[TokenStream, Int32], Node]):
        return cls(binding_power, token, led=cls._infix_func(binding_power, token, expr_fn))

    @classmethod
    def infix_r(cls, binding_power: int | Int32, token: str | String | TokenType, expr_fn: Callable[[TokenStream, Int32], Node]):
        return cls(binding_power, token, led=cls._infix_func(binding_power - 1, token, expr_fn))

    @classmethod
    def prefix(cls, binding_power: int | Int32, token: str | String | TokenType, expr_fn: Callable[[TokenStream, Int32], Node]):
        return cls(binding_power, token, nud=cls._prefix_func(binding_power, token, expr_fn))


class ContextualParser(StatefulProcessor, Generic[_T]):
    _name: String
    _parsers: Dictionary[String | TokenType, SubParser]

    def __init__(self, state: State, name: str | String):
        super().__init__(state)
        self._name = String(name)
        self._parsers = Dictionary()

    @property
    def name(self):
        return self._name

    def parse(self, stream: TokenStream, binding_power: Int32) -> _T:
        token = stream.token
        left = None
        if token == TokenType.Identifier:
            left = self._parsers.get(token.value, None)
        if left is None:
            parser = self._parsers.get(token.type, None)
            if parser is None:
                # todo: parse error: unknown symbol: token.type
                return self.state.error(f"Could not parse symbol '{token.value}'", token)
                # raise ValueError("Could not parse symbol " + token.value)
        else:
            parser = left
        left = parser.nud(stream)

        if parser.binding_power == -1:
            return left

        token = stream.read()
        while binding_power < (parser := self._parsers.get(token.value if token.is_term else token.type, None)).binding_power:
            token = stream.read()
            left = parser.led(stream, left)

        return left

    def add_parser(self, parser: SubParser):
        self._parsers[parser.token] = parser

    def get_parser(self, token: String | TokenType) -> SubParser:
        return self._parsers[token]


class Parser(StatefulProcessor):
    _context_parsers: Dictionary[String, ContextualParser]
    _parser_stack: List[ContextualParser]

    def __init__(self, toplevel_parser: ContextualParser = None, *, state: State = None):
        super().__init__(state or State())
        self._context_parsers = Dictionary()
        if toplevel_parser is not None:
            self._parser_stack = List((toplevel_parser,))

            self.add(toplevel_parser)

    @property
    def parser(self):
        return self._parser_stack[Int32(-1)]

    @contextmanager
    def context(self, name: str | String):
        self._parser_stack.add(parser := self._context_parsers[String(name)])
        try:
            yield parser
        finally:
            self._parser_stack.pop()

    def add(self, parser: ContextualParser):
        self._context_parsers[parser.name] = parser

    def register(self, token: str | String | TokenType, binding_power: int | Int32 = 0) -> SubParser:
        token = token if isinstance(token, TokenType) else String(token)
        try:
            s = self.parser.get_parser(token)
            if binding_power >= s.binding_power:
                s.binding_power = binding_power
        except KeyError:
            self.parser.add_parser(s := SubParser(binding_power, token))
        return s

    @overload
    def parse(self, stream: TokenStream): ...
    @overload
    def parse(self, stream: TokenStream, binding_power: int): ...
    @overload
    def parse(self, stream: TokenStream, binding_power: Int32): ...

    def parse(self, stream: TokenStream, binding_power: int | Int32 = 0):
        return self.parser.parse(stream, Int32(binding_power))
