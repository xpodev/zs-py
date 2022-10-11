from pathlib import Path
from typing import Iterable

from zs import Object
from zs.std.objects.compilation_environment import Document
from zs.std.processing.import_system import Importer, ImportResult, ImportSystem


class ZSImportResult(ImportResult):
    _document: Document
    _items: dict[str, Object]

    def __init__(self, document: Document):
        super().__init__()
        self._document = document
        self._items = dict(document.items)

    def all(self) -> Iterable[tuple[str, Object]]:
        for name, item in self._items.items():
            yield name, item

    def items(self, names: list[str]) -> Iterable[Object]:
        for name in names:
            yield self._items[name]

    def item(self, name: str) -> Object:
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

        document: Document = self._compiler.compile(path)

        return ZSImportResult(document)
