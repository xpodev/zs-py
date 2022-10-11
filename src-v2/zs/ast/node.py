from typing import Generic, TypeVar, TYPE_CHECKING

from .. import Object
from ..text.token_info import TokenInfo


TokenInfoT = TypeVar("TokenInfoT", bound=TokenInfo)

_T = TypeVar("_T")  # for the Node[TokenInfoT].node return type


class Node(Object[None], Generic[TokenInfoT]):
    _token_info: TokenInfoT

    def __init__(self, token_info: TokenInfoT):
        super().__init__(self)
        self._token_info = token_info

    if TYPE_CHECKING:  # this is here for better typing
        @property
        def node(self: _T) -> _T:
            return self

    @property
    def token_info(self):
        return self._token_info
