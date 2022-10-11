from functools import singledispatchmethod
from pathlib import Path
from typing import Iterable

from .import_system import ImportSystem
from .. import String, List
from ... import Object
from ...ast.node import Node
from ...ast.node_lib import Import, Literal, Identifier, Alias
from ...processing import StatefulProcessor, State, Context
from ...text.token import TokenType


class CallFrame:
    _scope: dict[str, Object]

    def __init__(self, **args):
        self._scope = args

    def get(self, name: str):
        return self._scope[name]

    def set(self, name: str, value: Object):
        self._scope[name] = value


class Interpreter(StatefulProcessor):
    _call_stack: list[CallFrame]
    _ctx: Context
    _import_system: ImportSystem

    def __init__(self, *, state: State = None, context: Context = None, import_system: ImportSystem = None):
        super().__init__(state or State())
        self._call_stack = []
        self._ctx = context or Context()
        self._import_system = import_system or ImportSystem()

    @property
    def context(self):
        return self._ctx

    @property
    def import_system(self):
        return self._import_system

    def execute_document(self, nodes: Iterable[Node]):
        super().run()

        for node in nodes:
            self.exec(node)

    @singledispatchmethod
    def exec(self, node: Node):
        raise TypeError(f"Can't execute node of type: \"{type(node)}\"")

    _do = exec.register

    @_do
    def _(self, node: Import):
        source = self.exec(node.source)
        if not isinstance(source, String):
            raise TypeError(f"Import statement source must evaluate to a string, not \"{type(source)}\"")

        path = Path(str(source))

        result = self._import_system.import_from(path)

        if result is None:
            return self.state.error(f"Could not import \"{path}\"", node)

        result._node = node

        match node.name:
            case Identifier() as star:
                if star.name != '*':
                    raise ValueError(f"Can't perform a default import since that is not a feature yet")
                for name, item in result.all():
                    self._ctx.add(item, name)
            case Alias() as alias:
                raise ValueError(f"Can't perform a default import since that is not a feature yet")
            case List() as names:
                for name in names:
                    if isinstance(name, Alias):
                        assert isinstance(name.expression, Identifier)
                        self._ctx.add(result.item(str(name.expression.name)), name.name.name)
                    else:
                        self._ctx.add(result.item(name.name))
            case _:
                raise TypeError("???")

        return result

    @_do
    def _(self, node: Literal):
        value = node.token_info.literal.value
        match node.token_info.literal.type:
            case TokenType.String:
                return String(value)
            case _:
                raise TypeError(node.token_info.literal.type)
