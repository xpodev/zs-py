import sys

from functools import partial, partialmethod
from pathlib import Path
from typing import Callable

from zs.base import NativeFunction
from zs.cli.options import Options, get_options
from zs.ctrt.lib import Function, ExObj, Field, CodeGenFunction
from zs.processing import State, StatefulProcessor
from zs.std.importers import ZSImporter
from zs.std.objects.compilation_environment import Document, ContextManager
from zs.std.parsers.std import get_standard_parser
from zs.std.processing.import_system import ImportResult
from zs.std.processing.toolchain import Toolchain


class Builtins(ImportResult, ExObj):
    def __init__(self):
        super().__init__()

    def all(self):
        return vars(self)

    def item(self, name: str):
        return getattr(self, name)

    def items(self, names: list[str]):
        return list(map(partial(getattr, self), names))


class Compiler(StatefulProcessor):
    _context: ContextManager
    _toolchain: Toolchain
    _toolchain_factory: Callable[["Compiler"], Toolchain]
    builtins: Builtins

    def __init__(self, *, state: State = None, context: ContextManager = None, toolchain_factory: Callable[["Compiler"], Toolchain] = None):
        super().__init__(state or State())
        self._context = context or ContextManager()
        self._toolchain_factory = toolchain_factory or (lambda _: Toolchain(state=self.state, context=self._context))
        self._toolchain = toolchain_factory(self)
        self.builtins = Builtins()

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

    builtins = compiler.builtins

    def _assign(left, right):
        if isinstance(left, Field):
            return left.set(right)
        if isinstance(left, str):
            compiler.toolchain.interpreter.x.local(left, right)

    def _set(obj, n, value):
        o = compiler.toolchain.interpreter.execute(obj, runtime=False)
        v = compiler.toolchain.interpreter.execute(value, runtime=False)
        setattr(o, str(n), v)
        return v

    def _get(obj, n):
        try:
            return getattr(obj, str(n))
        except AttributeError:
            ...

    builtins.CodeGenFunction = CodeGenFunction
    builtins.Function = Function
    builtins.Object = ExObj
    builtins.getattr = NativeFunction(lambda o, n: _get)
    builtins.setattr = NativeFunction(lambda o, n, v: _set(o, n, v))
    builtins.print = NativeFunction(lambda *args, **kwargs: print(*args, **{
        n: compiler.toolchain.interpreter.execute(value) for n, value in kwargs.items()
    }))
    builtins.partial = partial
    builtins.partialmethod = partialmethod

    compiler.toolchain.interpreter.x.local("__srf__", compiler)
    compiler.toolchain.interpreter.x.local("_._", _get)
    compiler.toolchain.interpreter.x.local("_=_", _assign)
    compiler.toolchain.interpreter.x.local("_;_", lambda l, r: (compiler.toolchain.interpreter.execute(l, runtime=False), compiler.toolchain.interpreter.execute(r, runtime=False))[1])

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
            print(f"[{message.processor.__class__.__name__}] [{message.type.value}] {message.origin} -> {message.content}")


if __name__ == '__main__':
    sys.setrecursionlimit(10000)
    main(get_options())
