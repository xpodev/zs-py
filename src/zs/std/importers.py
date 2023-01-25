from pathlib import Path
from typing import Iterable

from zs.ctrt.objects import Scope
from zs.ctrt.protocols import ObjectProtocol
from zs.std.processing.import_system import Importer, ImportResult, ImportSystem


class ZSImportResult(ImportResult):
    _scope: Scope
    _items: dict[str, ObjectProtocol]

    def __init__(self, scope: Scope):
        super().__init__()
        self._scope = scope
        self._items = dict(scope.members)

    def all_items(self) -> Iterable[tuple[str, ObjectProtocol]]:
        for name, item in self._items.items():
            yield name, item

    def items(self, names: list[str]) -> Iterable[ObjectProtocol]:
        for name in names:
            yield self._items[name]

    def item(self, name: str) -> ObjectProtocol:
        return self._items[name]


class ZSImporter(Importer):
    _import_system: ImportSystem

    def __init__(self, import_system: ImportSystem, compiler):
        super().__init__()
        self._import_system = import_system
        self._compiler = compiler

    def import_file(self, path: Path) -> ImportResult | None:
        path = self._import_system.resolve(path)

        if path is None:
            return None

        document: Scope = self._compiler.compile(path)

        return ZSImportResult(document)
