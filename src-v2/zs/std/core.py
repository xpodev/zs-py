from .objects.compilation_environment import Module, Document
from .objects.function import Function
from .objects.parameter import Parameter
from .objects.type import *
from .objects.wrappers import *
from ..utils import zs_type

__all__ = [
    "core",

    "Bool",
    "Dictionary",
    "Document",
    "Field",
    "Function",
    "Int32",
    "List",
    "Method",
    "Module",
    "Parameter",
    "Property",
    "String",
    "Class",
]


core = Module("core")

core.add(zs_type(Bool), export=True)
core.add(zs_type(Dictionary), export=True)
core.add(zs_type(Document), export=True)
core.add(zs_type(Field), export=True)
core.add(zs_type(Function), export=True)
core.add(zs_type(Int32), export=True)
core.add(zs_type(List), export=True)
core.add(zs_type(Method), export=True)
core.add(zs_type(Module), export=True)
core.add(zs_type(Parameter), export=True)
core.add(zs_type(Property), export=True)
core.add(zs_type(String), export=True)
core.add(zs_type(Class), export=True)
