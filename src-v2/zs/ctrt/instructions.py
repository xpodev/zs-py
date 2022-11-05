from zs import Object
from zs.ast.node import Node


class Instruction(Object):
    ...


class Name(Instruction):
    name: str

    def __init__(self, name: str, node: Node = None):
        super().__init__(node)
        self.name = name


class SetLocal(Instruction):
    name: str
    value: Object | None

    def __init__(self, name: str, value: Object | None, node: Node = None):
        super().__init__(node)
        self.name = name
        self.value = value


class Call(Instruction):
    callable: Object
    args: list[Object]

    def __init__(self, callable_: Object, args: list[Object], node: Node = None):
        super().__init__(node)
        self.callable = callable_
        self.args = args


class Import(Instruction):
    source: Object
    names: str | list[str | tuple[str, str]] | None

    def __init__(self, source: Object, names: str | list[str | tuple[str, str]] | None, node: Node = None):
        super().__init__(node)
        self.source = source
        self.names = names


class DeleteName(Instruction):
    name: str

    def __init__(self, name: str, node: Node = None):
        super().__init__(node)
        self.name = name


class EnterScope(Instruction):
    def __init__(self, node: Node = None):
        super().__init__(node)


class ExitScope(Instruction):
    def __init__(self, node: Node = None):
        super().__init__(node)
