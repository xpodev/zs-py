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


class Assign(Node[token_info.Assign]):
    """
    AST node for assignment syntax

    EXPRESSION = EXPRESSION
    """

    left: Expression
    right: Expression

    def __init__(
            self,
            left: Expression,
            _assign: Token,
            right: Expression
    ):
        super().__init__(token_info.Assign(_assign))
        self.left = left
        self.right = right


class Binary(Expression[token_info.Binary]):
    left: Expression
    right: Expression

    def __init__(self, left: Expression, _operator: Token, right: Expression):
        super().__init__(token_info.Binary(_operator))
        self.left = left
        self.right = right


class Class(Node[token_info.Class]):  # todo
    """
    AST node for the 'class' construct

    'class' IDENTIFIER? ('<' PARAMETER*(,) '>')? ':' BASES '{' CLASS_ITEMS '}'
    """

    name: Optional["Identifier"]

    items: List[Node]

    def __init__(
            self,
            _class: Token,
            name: Optional["Identifier"],
            _left_parenthesis: Token,
            items: list[Node],
            _right_parenthesis: Token
    ):
        super().__init__(token_info.Class(_class, _left_parenthesis, _right_parenthesis))
        self.name = name
        self.items = List(items)


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

    parameters: List["TypedName"]

    return_type: Expression

    clauses: List[Union["WhenClause", "WhereClause"]]

    body: list  # Expression | None

    def __init__(
            self,
            _fun: Token,
            name: Optional["Identifier"],
            _left_parenthesis: Token,
            parameters: list["TypedName"],
            _right_parenthesis: Token,
            _colon: Token,
            return_type: Expression | None,
            clauses: list[Union["WhenClause", "WhereClause"]],
            body: Expression | None
    ):
        super().__init__(token_info.Function(_fun, _left_parenthesis, _right_parenthesis, _colon))
        self.name = name
        self.parameters = List(parameters)
        self.return_type = return_type
        self.clauses = List(clauses)
        self.body = body


class FunctionCall(Expression[token_info.FunctionCall]):
    """
    AST node for the function call expression

    EXPRESSION '(' ARGUMENTS ')'
    """

    callable: Expression
    arguments: List[Expression]

    def __init__(
            self,
            callable_: Expression,
            _left_parenthesis: Token,
            arguments: list[Expression],
            _right_parenthesis: Token
    ):
        super().__init__(token_info.FunctionCall(_left_parenthesis, _right_parenthesis))
        self.callable = callable_
        self.arguments = List(arguments)


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


class Inlined(Node[token_info.Inlined]):
    """
    AST node for the 'inline' modifier

    'import' (('*' | NAME | ALIAS) 'from')? SOURCE ';'
    """

    item: Node

    def __init__(
            self,
            _inline: Token,
            item: Node
    ):
        super().__init__(token_info.Inlined(_inline))
        self.item = item


class Literal(Expression[token_info.Literal]):
    """
    AST node for literals
    """

    def __init__(self, _literal: Token):
        super().__init__(token_info.Literal(_literal))


class MemberAccess(Expression[token_info.MemberAccess]):
    """
    AST node for the member access syntax

    EXPRESSION '.' IDENTIFIER
    """

    object: Expression
    member: Identifier

    def __init__(self, expr: Expression, _dot: Token, member: Identifier):
        super().__init__(token_info.MemberAccess(_dot))
        self.object = expr
        self.member = member


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
            name: Identifier,
            _left_bracket: Token = None,
            items: list[Node] = None,
            _right_bracket: Token = None,
            _semicolon: Token = None
    ):
        super().__init__(token_info.Module(_module, _left_bracket, _right_bracket, _semicolon))
        self.name = name.name
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


class Tuple(Expression[token_info.Tuple]):
    """
    AST node for a tuple

    '(' EXPRESSIONS ')'
    """

    items: List[Expression]

    def __init__(self, _left_parenthesis: Token, items: list[Expression], _right_parenthesis: Token):
        super().__init__(token_info.Tuple(_left_parenthesis, _right_parenthesis))
        self.items = List(items)


class TypedName(Node[token_info.TypedName]):
    """
    AST node for a typed name

    IDENTIFIER ':' EXPRESSION
    """

    name: Identifier
    type: Expression | None

    def __init__(self, name: Identifier, _colon: Token | None, type: Expression | None):
        super().__init__(token_info.TypedName(_colon))
        self.name = name
        self.type = type


class Var(Node[token_info.Var]):
    name: TypedName
    initializer: Expression | None

    def __init__(self, _var: Token, name: TypedName, _assign: Token | None, initializer: Expression | None):
        super().__init__(token_info.Var(_var, _assign))
        self.name = name
        self.initializer = initializer
