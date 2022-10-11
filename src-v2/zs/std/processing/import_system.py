from pathlib import Path
from typing import Iterable

from zs import EmptyObject, Object
from zs.ast.node_lib import Import
from zs.std import String, List, Dictionary


class ImportResult(Object[Import]):
    def __init__(self):
        super().__init__(None)

    def all(self) -> Iterable[tuple[str, Object]]:
        ...

    def item(self, name: str) -> Object:
        ...

    def items(self, names: list[str]) -> Iterable[Object]:
        ...


class Importer(EmptyObject):
    def import_file(self, path: Path) -> ImportResult | None:
        ...

    @lambda _: None
    def import_directory(self, path: Path) -> ImportResult | None:
        ...


class ImportSystem(Importer):
    _path: List[String]
    _importers: Dictionary[String, Importer]
    _directory_importers: List[Importer]

    def __init__(self):
        super().__init__()
        self._path = List()
        self._importers = Dictionary()
        self._directory_importers = List()

    def add_directory(self, path: str | String | Path):
        path = Path(str(path))
        if not path.is_dir():
            raise ValueError(f"Can only add directories to search path")
        if not path.is_absolute():
            path = self.resolve(path)
        if path is None:
            raise ValueError(f"Could not find path")
        self._path.add(String(str(path)))

    def add_importer(self, importer: Importer, ext: str | String):
        ext = String(ext)
        if ext in self._importers:
            raise ValueError(f"Importer for \"{ext}\" already exists")

        if not ext.startswith('.'):
            ext = '.' + ext

        self._importers[ext] = importer
        if importer.import_directory is not None:
            self._directory_importers.add(importer)

    def import_directory(self, path: Path) -> ImportResult | None:
        for importer in self._directory_importers:
            if result := importer.import_directory(path):
                return result
        return None

    def import_file(self, path: Path) -> ImportResult | None:
        try:
            return self._importers[String(path.suffix)].import_file(path)
        except KeyError:
            return None

    def import_from(self, path: Path) -> ImportResult | None:
        if path.is_dir():
            return self.import_directory(path)
        return self.import_file(path)

    def resolve(self, path: str | Path) -> Path | None:
        path = Path(path)
        if path.is_absolute():
            return path if path.exists() else None
        for directory in self._path:
            if (result := (str(directory) / path)).exists():
                return result
        if (result := (Path.cwd() / path)).exists():
            return result
        return None
