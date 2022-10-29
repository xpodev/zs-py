from contextlib import contextmanager
from enum import Enum
from typing import Iterable

from .token import Token, TokenType
from .. import EmptyObject


__all__ = [
    "SeekMode",
    "TokenStream",
]

from zs.std.objects.wrappers import Int32


class SeekMode(Int32, Enum):
    Start = 0
    Current = 1
    End = 2


class TokenStream(EmptyObject):
    _tokens: list[Token]
    _current: int

    def __init__(self, tokens: Iterable[Token]):
        super().__init__()
        self._tokens = list(filter(lambda t: not t.is_whitespace, tokens))
        self._current = 0

    @property
    def end(self):
        return self._current == len(self._tokens) or self.token.type == TokenType.EOF

    @property
    def token(self) -> Token:
        return self._tokens[self._current]

    def peek(self, next_: int = 0) -> Token:
        return self._tokens[self._current + next_]

    def seek(self, pos: int, mode: SeekMode = SeekMode.Current):
        if mode == SeekMode.Start:
            self._current = pos
        elif mode == SeekMode.Current:
            self._current += pos
        elif mode == SeekMode.End:
            self._current = len(self._tokens) - pos
        else:
            raise ValueError(mode)

    def read(self) -> Token:
        if self.end:
            return self.token
        token = self.token
        self._current += 1
        return token

    def __iter__(self):
        return self._tokens[self._current:]

    @contextmanager
    def save_position(self):
        position = self._current
        state = type("", (object,), {"__restore__": True, "restore": None})()
        state.commit = lambda: setattr(state, "__restore__", False)

        def restore():
            state.__restore__ = False
            self._current = position

        state.restore = restore
        try:
            yield state
        finally:
            if state.__restore__:
                self._current = position
