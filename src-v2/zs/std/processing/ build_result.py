from ..objects.variable import Variable
from ...ast.node import Node


class BuildResult:
    """
    Holds information about build results such as the declaration statement, initialization expressions and node.

    This class may not be used.
    """
    variable: Variable
    node: Node
