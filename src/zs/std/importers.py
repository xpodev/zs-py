from pathlib import Path
from typing import Iterable

from zs.ctrt.objects import Scope
from zs.ctrt.protocols import ObjectProtocol, ImmutableScopeProtocol
from zs.std.processing.import_system import Importer, ImportSystem


class ZSImportResult(ImmutableScopeProtocol):
    _scope: Scope
    _items: dict[str, ObjectProtocol]

    def __init__(self, scope: Scope):
        super().__init__()
        self._scope = scope
        self._items = dict(scope.members)

    def all(self) -> Iterable[tuple[str, ObjectProtocol]]:
        for name, item in self._items.items():
            yield name, item

    def get_name(self, name: str, **_) -> ObjectProtocol:
        return self._items[name]


class ZSImporter(Importer):
    _import_system: ImportSystem

    def __init__(self, import_system: ImportSystem, compiler):
        super().__init__()
        self._import_system = import_system
        self._compiler = compiler

    def import_from(self, source: str) -> ImmutableScopeProtocol | None:
        return self.import_file(Path(source))

    def import_file(self, path: Path) -> ImmutableScopeProtocol | None:
        path = self._import_system.resolve(path)

        if path is None:
            return None

        document: Scope = self._compiler.compile(path)

        return ZSImportResult(document)


class ModuleImporter(Importer):
    def __init__(self, compiler):
        self._compiler = compiler

    def import_from(self, source: str) -> ImmutableScopeProtocol | None:
        return self._compiler.context.get_module_from_cache(source)
