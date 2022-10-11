from zs.ast.node import Node
from zs.ast.node_lib import Identifier, Import, Alias, Literal
from zs.processing import State
from zs.std.objects.wrappers import Int32, List
from zs.text.parser import ContextualParser, SubParser
from zs.text.token import TokenType
from zs.text.token_stream import TokenStream


__all__ = [
    "DocumentParser",
]


def _bind(fn):
    return lambda _, *args: fn(*args)


class DocumentParser(ContextualParser[List[Node]]):
    """
    A parser that can parse the body of a Z# document. It outputs a list of nodes representing the nodes in the document.
    """

    _stream: TokenStream

    def __init__(self, state: State):
        super().__init__(state, "Document")

        self.add_parser(SubParser(-1, "import", nud=_bind(self._next_import)))

    def parse(self, stream: TokenStream, binding_power: Int32):
        self._stream = stream
        result = []
        while not self._stream.end:
            while (node := super().parse(stream, binding_power)) is None and not stream.end:
                while stream.read() != ";" and not stream.end:
                    stream.read()
            if node is not None:
                result.append(node)

        return List(result)

    def _eat(self, typ: TokenType | str):
        token = self._stream.read()
        if (token.type if isinstance(typ, TokenType) else token.value) != typ:
            self.state.error(f"Expected token {typ} but got {(token.type if isinstance(typ, TokenType) else token.value)} instead at ({token.span})", token)
            return token
            # raise ValueError(f"Expected token {typ} but got {(token.type if isinstance(typ, TokenType) else token.value)} instead at ({token.span})")
        return token

    def _is(self, typ: TokenType | str, eat: bool = False):
        token = self._stream.peek()
        if not eat:
            return token == typ
        if self._is(typ):
            self._eat(typ)
            return True
        return False

    def _next_identifier(self):
        return Identifier(self._eat(TokenType.Identifier))

    def _next_import(self):
        _import = self._eat("import")

        if self._is("*"):
            imported_names = Identifier(self._eat("*"))
            if self._is("as"):
                imported_names = Alias(imported_names, self._eat("as"), self._next_identifier())
        elif self._is(TokenType.String):
            return Import(
                _import, None, None, None, None, Literal(self._eat(TokenType.String)), self._eat(TokenType.Semicolon)
            )
        else:
            imported_names = List()

        _l_curly = _r_curly = None
        if self._is(TokenType.L_Curly):
            _l_curly = self._eat(TokenType.L_Curly)
            while True:
                name = self._next_identifier()

                if self._is("as"):
                    name = Alias(name, self._eat("as"), self._next_identifier())

                imported_names.add(name)

                if not self._is(TokenType.R_Curly):
                    self._eat(TokenType.Comma)
                else:
                    break
            _r_curly = self._eat(TokenType.R_Curly)

        _from = self._eat("from")
        source = Literal(self._eat(TokenType.String))

        return Import(
            _import, _l_curly, imported_names, _r_curly, _from, source, self._eat(TokenType.Semicolon)
        )
