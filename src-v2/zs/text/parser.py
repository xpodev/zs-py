from contextlib import contextmanager
from typing import Callable, overload, TypeVar, Generic, Type

from zs.std.objects.wrappers import String, Int32, Dictionary, List, Bool
from .token import TokenType, Token
from .token_stream import TokenStream
from .. import EmptyObject
from ..ast.node import Node
from ..ast.node_lib import Binary, Expression
from ..processing import StatefulProcessor, State

Unary = lambda *args: args  # todo: import


_T = TypeVar("_T")


__all__ = [
    "ContextualParser",
    "Parser",
    "SubParser",
]


class SubParser(EmptyObject):
    _binding_power: Int32
    _token: String | TokenType
    _nud: Callable[["Parser"], Node | None] | None
    _led: Callable[["Parser", Node], Node | None] | None

    def __init__(
            self,
            binding_power: int | Int32,
            token: str | String | TokenType,
            *,
            nud: Callable[["Parser"], Node | None] | None = None,
            led: Callable[["Parser", Node], Node | None] | None = None
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
    def _infix_func(binding_power: Int32, token: String, expr_fn: Callable[["Parser", Int32], Expression], factory=Binary):
        return lambda stream, left: factory(left, stream.eat(str(token)), expr_fn(stream, binding_power))

    @staticmethod
    def _prefix_func(binding_power: Int32, token: String, expr_fn: Callable[["Parser", Int32], Expression]):
        return lambda stream: Unary(token, expr_fn(stream, binding_power))

    @classmethod
    def infix_l(cls, binding_power: int | Int32, token: str | String | TokenType, expr_fn: Callable[["Parser", Int32], Expression]):
        return cls(binding_power, token, led=cls._infix_func(binding_power, token, expr_fn))

    @classmethod
    def infix_r(cls, binding_power: int | Int32, token: str | String | TokenType, expr_fn: Callable[["Parser", Int32], Expression], factory=Binary):
        return cls(binding_power, token, led=cls._infix_func(binding_power - 1, token, expr_fn, factory=factory))

    @classmethod
    def prefix(cls, binding_power: int | Int32, token: str | String | TokenType, expr_fn: Callable[["Parser", Int32], Expression]):
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

    def parse(self, parser: "Parser", binding_power: Int32) -> _T:
        stream = parser.stream
        sub = self._get_parser_for(stream.token)
        left = sub.nud(parser)

        if sub.binding_power == -1:
            return left

        while (sub := self._get_parser_for(stream.token)) is not None and binding_power < sub.binding_power:
            left = sub.led(parser, left)

        if sub is None:
            self.state.error(f"Could not parse token \"{stream.token}\"")

        return left

    def add_parser(self, parser: SubParser):
        self._parsers[parser.token] = parser

    def add_parsers(self, *parsers: SubParser):
        for parser in parsers:
            self.add_parser(parser)

    def get_parser(self, token: String | TokenType) -> SubParser:
        return self._parsers[token]

    def setup(self, parser: "Parser"):
        ...

    def symbol(self, symbol: str | String | TokenType) -> SubParser:
        self.add_parser(parser := SubParser(-1, symbol, nud=lambda _: None))
        return parser

    def _get_parser_for(self, token: Token):
        sub = self._parsers.get(token.value, None) or self._parsers.get(token.type, None)
        if sub is None:
            sub = self._on_unknown_token(token)
        if sub is None:
            self.state.error(f"Could not parse token: {token}")
        return sub

    def _on_unknown_token(self, token: Token):
        return self.state.error(f"Could not parse symbol '{token.value}'", token)


class Parser(StatefulProcessor):
    _context_parsers: Dictionary[String | type, ContextualParser]
    _parser_stack: List[ContextualParser]
    _stream: TokenStream

    def __init__(self, toplevel_parser: ContextualParser = None, *, state: State = None):
        super().__init__(state or State())
        self._context_parsers = Dictionary()
        if toplevel_parser is not None:
            self._parser_stack = List((toplevel_parser,))

            self.add(toplevel_parser)

    @property
    def parser(self):
        return self._parser_stack[Int32(-1)]

    @property
    def stream(self):
        return self._stream

    @property
    def parsers(self):
        return self._context_parsers.values()

    @contextmanager
    def context(self, name: str | String):
        self._parser_stack.add(parser := self._context_parsers[String(name)])
        try:
            yield parser
        finally:
            self._parser_stack.pop()

    @overload
    def add(self, type: Type[_T]): ...
    @overload
    def add(self, type: Type[_T], constructor: Type[ContextualParser[_T]]): ...
    @overload
    def add(self, type: Type[_T], parser: ContextualParser[_T]): ...
    @overload
    def add(self, name: str | String, parser: ContextualParser[_T]): ...
    @overload
    def add(self, parser: ContextualParser[_T]): ...

    def add(self, *args):
        try:
            type_or_name, parser = args
            if not isinstance(parser, ContextualParser):
                parser = parser(self.state)
            self._context_parsers[type_or_name] = parser
        except ValueError:
            parser, = args
            if isinstance(parser, ContextualParser):
                self.add(parser.name, parser)
            else:
                self.add(parser(self.state))

    @overload
    def eat(self, type_: TokenType) -> Token | None: ...
    @overload
    def eat(self, value: str | String) -> Token | None: ...

    def eat(self, type_or_value: TokenType | str | String) -> Token | None:
        if not self.token(type_or_value):
            self.state.error(f"Expected token: \"{type_or_value}\", got \"{self.stream.token}\" instead")
            return None
        return self.stream.read()

    @overload
    def get(self, name: str | String) -> ContextualParser: ...
    @overload
    def get(self, type_: type) -> ContextualParser: ...

    def get(self, name_or_type: str | String | type) -> ContextualParser:
        if isinstance(name_or_type, str):
            name_or_type = String(name_or_type)
        return self._context_parsers[name_or_type]

    @overload
    def next(self, binding_power: int | Int32 = 0) -> Node: ...
    @overload
    def next(self, name: str | String, binding_power: int | Int32 = 0) -> Node: ...
    @overload
    def next(self, type_: Type[_T], binding_power: int | Int32 = 0) -> _T: ...

    def next(self, name: str | String | Type[_T] | int | Int32 = None, binding_power=0) -> Node | _T:
        if isinstance(name, (int, Int32)):
            binding_power = Int32(name)
            name = None
        if name is None:
            return self.parser.parse(self, Int32(binding_power))
        try:
            return self.get(name).parse(self, Int32(binding_power))
        except KeyError:
            self.state.error(f"Unknown parser \"{name}\" was invoked")

    @overload
    def token(self) -> Token: ...
    @overload
    def token(self, type_: TokenType, *, eat: bool | Bool = False) -> Bool: ...
    @overload
    def token(self, value: str | String, *, eat: bool | Bool = False) -> Bool: ...

    def token(self, type_or_value: TokenType | str | String = None, eat: bool | Bool = False) -> Bool | Token:
        if type_or_value is None:
            return self.stream.token
        token = self._stream.peek()
        if not eat:
            return token == type_or_value
        if token == type_or_value:
            self.eat(type_or_value)
            return Bool(True)
        return Bool(False)

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
        self.run()
        self._stream = stream
        return self.next(binding_power)

    def setup(self):
        for parser in self.parsers:
            parser.setup(self)
