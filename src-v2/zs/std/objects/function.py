from .parameter import Parameter
from zs import Object
from .wrappers import String, List
from zs.ast import node_lib as node


class Function(Object[node.Function]):
    _name: String | None
    _parameters: List[Parameter]
