from typing import Generic, TypeVar, TYPE_CHECKING

from ..text.token_info import TokenInfo


TokenInfoT = TypeVar("TokenInfoT", bound=TokenInfo)

_T = TypeVar("_T")  # for the Node[TokenInfoT].node return type


class Node(Generic[TokenInfoT]):
    _token_info: TokenInfoT

    def __init__(self, token_info: TokenInfoT):
        self._token_info = token_info

    if TYPE_CHECKING:  # this is here for better typing
        @property
        def node(self: _T) -> _T:
            return self

    @property
    def token_info(self):
        return self._token_info

    def __str__(self):
        return str(self._token_info)
