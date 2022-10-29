from pathlib import Path
from typing import Callable

from zs.base import NativeFunction
from zs.cli.options import Options, get_options
from zs.processing import State, StatefulProcessor
from zs.std import Int32
from zs.std.importers import ZSImporter
from zs.std.objects.compilation_environment import Document, ContextManager
from zs.std.parsers.std import get_standard_parser
from zs.std.processing.toolchain import Toolchain
from zs.text.file_info import SourceFile


class Compiler(StatefulProcessor):
    _context: ContextManager
    _toolchain: Toolchain
    _toolchain_factory: Callable[["Compiler"], Toolchain]

    def __init__(self, *, state: State = None, context: ContextManager = None, toolchain_factory: Callable[["Compiler"], Toolchain] = None):
        super().__init__(state or State())
        self._context = context or ContextManager()
        self._toolchain_factory = toolchain_factory or (lambda _: Toolchain(state=self.state, context=self._context))
        self._toolchain = toolchain_factory(self)

    @property
    def context(self):
        return self._context
    
    @property
    def toolchain(self):
        return self._toolchain

    def compile(self, path: str | Path) -> Document:
        super().run()

        path = Path(path)
        if path.is_dir():
            toolchain = self._toolchain_factory(self)
            self._toolchain = toolchain
        else:
            toolchain = self._toolchain

        return toolchain.compile_document(path)


def main(options: Options):
    state = State()
    context = ContextManager()

    parser = get_standard_parser(state)

    parser.setup()

    compiler = Compiler(state=state, context=context, toolchain_factory=lambda c: Toolchain(state=c.state, parser=parser, context=context))
    import_system = compiler.toolchain.interpreter.import_system
    context.global_context.add(compiler, "__srf__")

    import_system.add_directory("./tests/test_project_v2/")

    import_system.add_importer(ZSImporter(import_system, compiler), ".zs")

    context.add(NativeFunction(lambda o, n, v: setattr(o, str(n), v)), "setattr")
    context.add(NativeFunction(lambda o, n: getattr(o, str(n))), "getattr")
    context.add(NativeFunction(lambda *args, **kwargs: print(*args, **kwargs)), "print")

    context.add(Int32, "i32")

    try:
        compiler.compile(options.source)
    except Exception as e:
        raise e
    else:

        for module in compiler.context.modules:
            if module.entry_point:
                print("Module:", module.name, " | Entry:", module.entry_point)
            else:
                print("Module:", module.name)
            for name, member in module.members.items:
                print('\t', name, " :: ", member)
    finally:
        state.reset()

        for message in state.messages:
            print(f"[{message.type.value}] {message.origin} -> {message.content}")


if __name__ == '__main__':
    main(get_options())
