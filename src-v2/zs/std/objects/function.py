from .parameter import Parameter
from .wrappers import String, List
from ... import Object
from ...ast import node_lib as node_lib
from ...utils import resolve_on_demand


class Function(Object[node_lib.Function]):
    _name: String | None
    _parameters: List[Parameter]
    _return_type: Object

    def __init__(self, name: str | String, node: node_lib.Function = None):
        super().__init__(node)
        self._name = String(name)
        self._parameters = List()
        self._return_type = Object.__zs_type__
        self._body = List()

    @property
    def name(self):
        return self._name

    @resolve_on_demand
    @property
    def body(self):
        return self._body

    @property
    def parameters(self):
        return self._parameters

    @property
    def return_type(self):
        return self._return_type

    @return_type.setter
    def return_type(self, value):
        self._return_type = value

    def add_parameter(self, name: str | String, type_: Object):
        self._parameters.add(Parameter(None, name, type_, len(self._parameters)))
