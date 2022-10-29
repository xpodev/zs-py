from zs.ast import node_lib as node_lib
from zs.objects.common import TypedName
from zs.std import Int32


class Parameter(TypedName[node_lib.Parameter]):
    def __init__(self, node, name, type, index):
        super().__init__(node, name, type)
        self.index = Int32(index)
