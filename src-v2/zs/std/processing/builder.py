from functools import singledispatchmethod

from .build_result import BuildResult
from ...ast.node import Node


class Builder:
    @singledispatchmethod
    def build(node: Node) -> BuildResult:
        ...

    _build = build.register
