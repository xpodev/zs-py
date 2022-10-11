from pathlib import Path
from typing import Callable

from zs.cli.options import Options, get_options
from zs.processing import State, Context, StatefulProcessor
from zs.std.importers import ZSImporter
from zs.std.objects.compilation_environment import Document, ContextManager
from zs.std.parsers.document import DocumentParser
from zs.std.processing.toolchain import Toolchain
from zs.text.file_info import SourceFile
from zs.text.parser import Parser


class Compiler(StatefulProcessor):
    _context: ContextManager
    _toolchain: Toolchain
    _toolchain_factory: Callable[["Compiler"], Toolchain]

    def __init__(self, *, state: State = None, context: ContextManager = None, toolchain_factory: Callable[["Compiler"], Toolchain] = None):
        super().__init__(state or State())
        self._context = context or ContextManager()
        self._toolchain_factory = toolchain_factory or (lambda _: Toolchain(self.state))
        self._toolchain = toolchain_factory(self)

    @property
    def context(self):
        return self._context
    
    @property
    def toolchain(self):
        return self._toolchain

    def compile(self, path: str | Path) -> Document:
        path = Path(path)
        if path.is_dir():
            toolchain = self._toolchain_factory(self)
            self._toolchain = toolchain
        else:
            toolchain = self._toolchain

        return toolchain.compile_document(SourceFile.from_path(path))


def main(options: Options):
    state = State()
    context = Context()

    parser = Parser(document_parser := DocumentParser(state))
    compiler = Compiler(state=state, context=context, toolchain_factory=lambda c: Toolchain(state=c.state, parser=parser))
    import_system = compiler.toolchain.interpreter.import_system

    import_system.add_directory("./tests/test_project_v2/")

    import_system.add_importer(ZSImporter(import_system, compiler), ".zs")

    document = compiler.compile(options.source)

    print(document)

    state.reset()

    for message in state.messages:
        print(f"[{message.type.value}] {message.origin} -> {message.content}")


if __name__ == '__main__':
    main(get_options())
