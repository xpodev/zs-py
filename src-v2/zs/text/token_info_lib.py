from dataclasses import dataclass

from .token import Token
from .token_info import TokenInfo


__all__ = [
    "Identifier",
    "If",
]


_cfg = {
    "init": True,
    "frozen": True,
    "slots": True,
}


@dataclass(**_cfg)
class Alias(TokenInfo):
    """
    Token info for the 'as' node:

    EXPRESSION 'as' NAME
    """

    keyword_as: Token


@dataclass(**_cfg)
class Function(TokenInfo):
    """
    Token info for the 'fun' node:

    'fun' NAME? '(' ARGS ')' CLAUSE* EXPRESSION
    """

    keyword_fun: Token

    left_parenthesis: Token
    right_parenthesis: Token


@dataclass(**_cfg)
class Identifier(TokenInfo):
    """
    Token info for the IDENTIFIER node
    """

    name: Token


@dataclass(**_cfg)
class If(TokenInfo):
    """
    Token info for the 'if' node:

    'if' IDENTIFIER '(' CONDITION ')' EXPRESSION
    'else' EXPRESSION
    """

    keyword_if: Token

    left_parenthesis: Token
    right_parenthesis: Token

    keyword_else: Token | None


@dataclass(**_cfg)
class Import(TokenInfo):
    """
    Token info for the 'import' node:

    'import' ((IDENTIFIER ('as' IDENTIFIER) | '*' | '{' NAMES '}') 'from')? STRING ';'
    """

    keyword_import: Token

    star: Token | None

    left_bracket: Token
    right_bracket: Token

    keyword_from: Token | None

    semicolon: Token


@dataclass(**_cfg)
class Literal(TokenInfo):
    """
    Token info for literals
    """

    literal: Token


@dataclass(**_cfg)
class Module(TokenInfo):
    """
    Token info for the 'module' node:

    'module' IDENTIFIER ('.' IDENTIFIER)* ('{' ITEMS '}') | ';'
    """

    keyword_module: Token

    left_bracket: Token
    right_bracket: Token

    semicolon: Token
