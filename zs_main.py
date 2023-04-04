import sys

from pathlib import Path
from typing import Callable

from zs.cli.options import Options, get_options, InitOptions
from zs.ctrt.core import Scope
from zs.processing import State, StatefulProcessor
from zs.std.importers import ZSImporter, ModuleImporter
from zs.std.modules.module_core import core
from zs.std.modules.module_srf import srf
from zs.std.objects.compilation_environment import ContextManager
from zs.std.parsers import base as base_language
from zs.std.processing.toolchain import Toolchain


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

    def compile(self, path: str | Path) -> Scope:
        super().run()

        path = Path(path)
        if path.is_dir():
            toolchain = self._toolchain_factory(self)
            self._toolchain = toolchain
            path /= f"{path.name}.module.zs"
        else:
            toolchain = self._toolchain

        return toolchain.compile_document(path)


def main(options: Options):
    if isinstance(options, InitOptions):
        from zs import project
        return project.init(options)

    state = State()
    context = ContextManager()

    parser = base_language.get_parser(state)

    parser.setup()

    compiler = Compiler(state=state, context=context, toolchain_factory=lambda c: Toolchain(state=c.state, parser=parser, context=context))
    import_system = compiler.toolchain.interpreter.import_system

    import_system.add_directory(Path(options.source).parent.resolve())

    import_system.add_importer(ZSImporter(import_system, compiler), ".zs")
    import_system.add_importer(ModuleImporter(compiler), "module")

    compiler.context.add_module_to_cache("core", core)
    compiler.context.add_module_to_cache("srf", srf)

    try:
        compiler.compile(options.source)
    except Exception as e:
        raise e
    else:
        ...
        # for module in compiler.context.modules:
        #     if module.entry_point:
        #         print("Module:", module.name, " | Entry:", module.entry_point)
        #     else:
        #         print("Module:", module.name)
        #     for name, member in module.members.items:
        #         print('\t', name, " :: ", member)
    finally:
        state.reset()

        for message in state.messages:
            print(f"[{message.processor.__class__.__name__}] [{message.type.value}] {message.origin} -> {message.content}")


if __name__ == '__main__':
    sys.setrecursionlimit(10000)
    main(get_options())
