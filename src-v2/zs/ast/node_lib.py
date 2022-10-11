from typing import TypeVar, Generic, Optional, Union

from zs.std.objects.wrappers import List, String
from ..text import token_info_lib as token_info
from ..text.token import Token
from .node import Node


_T = TypeVar("_T")


class Expression(Node[_T], Generic[_T]):
    """
    Base AST node for expressions.
    """


class Alias(Node[token_info.Alias]):
    """
    AST node for the alias structure:

    EXPRESSION 'as' IDENTIFIER
    """

    name: "Identifier"

    expression: Expression

    def __init__(
            self,
            expression: Expression,
            _as: Token,
            name: "Identifier"
    ):
        super().__init__(token_info.Alias(_as))
        self.name = name
        self.expression = expression


class Class(Node[None]):  # todo
    """
    AST node for the 'class' construct

    'class' IDENTIFIER? ('<' PARAMETER*(,) '>')? ':' BASES '{' CLASS_ITEMS '}'
    """


class Field(Node[None]):  # todo
    """
    AST node for class fields (variable declaration)
    """

    def __init__(
            self,
    ):
        super().__init__(None)  # todo


class Function(Expression[token_info.Function]):
    """
    AST node for the function structure:

    'fun' NAME? '(' PARAMETER* ')' (WHERE_CLAUSE | WHEN_CLAUSE)* EXPRESSION
    """

    name: Optional["Identifier"]

    parameters: List["Parameter"]

    clauses: List[Union["WhenClause", "WhereClause"]]

    body: Expression

    def __init__(
            self,
            _fun: Token,
            name: Optional["Identifier"],
            _left_parenthesis: Token,
            parameters: list["Parameter"],
            _right_parenthesis: Token,
            clauses: list[Union["WhenClause", "WhereClause"]],
            body: Expression
    ):
        super().__init__(token_info.Function(_fun, _left_parenthesis, _right_parenthesis))
        self.name = name
        self.parameters = List(parameters)
        self.clauses = List(clauses)
        self.body = body


class Identifier(Expression[token_info.Identifier]):
    """
    AST node for identifiers.
    """

    name: String

    def __init__(self, name: Token):
        super().__init__(token_info.Identifier(name))
        self.name = String(name.value)


class If(Expression[token_info.If]):
    """
    AST node for the 'if' expression construct:

    'if' NAME '(' CONDITION ')' IF_TRUE
    'else' IF_FALSE
    """

    name: Identifier | None

    condition: Expression

    if_true: Expression
    if_false: Expression | None

    def __init__(
            self,
            _if: Token,
            name: Identifier | None,
            _left_parenthesis: Token,
            condition: Expression,
            _right_parenthesis: Token,
            if_true: Expression,
            _else: Token | None,
            if_false: Expression | None
    ):
        super().__init__(token_info.If(_if, _left_parenthesis, _right_parenthesis, _else))
        self.name = name
        self.condition = condition
        self.if_true = if_true
        self.if_false = if_false


class Import(Node[token_info.Import]):
    """
    AST node for the 'import' statement construct:

    'import' (('*' | NAME | ALIAS) 'from')? SOURCE ';'
    """

    name: List[Identifier | Alias] | Alias | Identifier | None
    source: Expression

    def __init__(
            self,
            _import: Token,
            _left_parenthesis: Token | None,
            name: List[Identifier | Alias] | Alias | Identifier | None,
            _right_parenthesis: Token | None,
            _from: Token | None,
            source: Expression,
            _semicolon: Token
    ):
        super().__init__(token_info.Import(_import, name if isinstance(name, Token) else None, _left_parenthesis, _right_parenthesis, _from, _semicolon))
        self.name = name
        self.source = source


class Literal(Expression[token_info.Literal]):
    """
    AST node for literals
    """

    def __init__(self, _literal: Token):
        super().__init__(token_info.Literal(_literal))


class Module(Node[token_info.Module]):
    """
    AST node for the 'module' statement construct:

    'module' IDENTIFIER ('.' IDENTIFIER)* ('{' ITEMS '}') | ';'
    """

    name: String
    items: List[Node] | None

    def __init__(
            self,
            _module: Token,
            name: str,
            _left_bracket: Token = None,
            items: list[Node] = None,
            _right_bracket: Token = None,
            _semicolon: Token = None
    ):
        super().__init__(token_info.Module(_module, _left_bracket, _right_bracket, _semicolon))
        self.name = String(name)
        self.items = List(items) if items is not None else items


class Parameter(Node[None]):  # todo
    """
    AST node for function parameter (just a typed name basically)
    """

    def __init__(
            self,
    ):
        super().__init__(None)  # todo


class Property(Node[None]):  # todo
    """
    AST node for class property
    """

    def __init__(
            self,
    ):
        super().__init__(None)  # todo


