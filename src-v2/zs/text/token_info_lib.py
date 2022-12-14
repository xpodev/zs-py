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
class Assign(TokenInfo):
    """
    Token info for assignment

    EXPRESSION = EXPRESSION
    """

    assign: Token


@dataclass(**_cfg)
class Binary(TokenInfo):
    """
    Token info for binary expressions

    EXPRESSION OPERATOR EXPRESSION
    """

    operator: Token


@dataclass(**_cfg)
class Class(TokenInfo):
    """
    Token info for the 'class' node:

    'class' NAME? '{' BODY '}'
    """

    keyword_class: Token

    left_parenthesis: Token
    right_parenthesis: Token


@dataclass(**_cfg)
class Function(TokenInfo):
    """
    Token info for the 'fun' node:

    'fun' NAME? '(' ARGS ')' (':' EXPR)? CLAUSE* EXPRESSION
    """

    keyword_fun: Token

    left_parenthesis: Token
    right_parenthesis: Token

    colon: Token


@dataclass(**_cfg)
class FunctionCall(TokenInfo):
    """
    Token info for the function call expression:

    EXPRESSION '(' ARGUMENTS ')'
    """

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
class Inlined(TokenInfo):
    """
    Token info for the 'inline' node:

    'inline' INLINED
    """

    keyword_inline: Token


@dataclass(**_cfg)
class Literal(TokenInfo):
    """
    Token info for literals
    """

    literal: Token


@dataclass(**_cfg)
class MemberAccess(TokenInfo):
    """
    Token info for the member access syntax:

    EXPRESSION '.' IDENTIFIER
    """

    dot: Token


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


@dataclass(**_cfg)
class Tuple(TokenInfo):
    """
    Token info for the 'tuple' node:

    '(' EXPERSSIONS ')'
    """

    left_parenthesis: Token
    right_parenthesis: Token


@dataclass(**_cfg)
class TypedName(TokenInfo):
    """
    Token info for a typed name

    IDENTIFIER ':' TYPE
    """

    colon: Token | None


@dataclass(**_cfg)
class Var(TokenInfo):
    """
    Token info for a 'var' declaration

    var TYPED_NAME ('=' EXPRESSION)?
    """

    var: Token
    assign: Token | None

