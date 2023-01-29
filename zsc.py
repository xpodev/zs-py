import sys

from functools import partial
from pathlib import Path
from typing import Callable

from zs.cli.options import Options, get_options, InitOptions
from zs.ctrt.core import Any, Void, Unit, Type, FunctionType, Class, ClassType
# from zs.ctrt.native import NativeObject, NativeFunction, Boolean, String, Int64, Float64
from zs.ctrt.native import NativeFunction, Boolean, String, Int64, Float64
from zs.ctrt.objects import Core, Scope
from zs.processing import State, StatefulProcessor
from zs.std.importers import ZSImporter, ModuleImporter
from zs.std.objects.compilation_environment import ContextManager
from zs.std.parsers import base as base_language
from zs.std.processing.toolchain import Toolchain


# class Builtins(NativeObject, ImportResult):
#     print = NativeFunction(print, "print")
#
#     def __init__(self):
#         super().__init__()
#
#     @property
#     def owner(self):
#         return Core
#
#     def all(self):
#         return {
#             "print": self.print
#         }.items()
#
#     def item(self, name: str):
#         return getattr(self, name)
#
#     def items(self, names: list[str]):
#         return list(map(partial(getattr, self), names))


class Compiler(StatefulProcessor):
    _context: ContextManager
    _toolchain: Toolchain
    _toolchain_factory: Callable[["Compiler"], Toolchain]
    # builtins: Builtins

    def __init__(self, *, state: State = None, context: ContextManager = None, toolchain_factory: Callable[["Compiler"], Toolchain] = None):
        super().__init__(state or State())
        self._context = context or ContextManager()
        self._toolchain_factory = toolchain_factory or (lambda _: Toolchain(state=self.state, context=self._context))
        self._toolchain = toolchain_factory(self)
        # self.builtins = Builtins()

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

    # builtins = compiler.builtins

    # for name in vars(__builtins__):
    #     item = getattr(__builtins__, name)
    #     if callable(item):
    #         setattr(builtins, name, NativeFunction(item))

    global_scope = compiler.toolchain.interpreter.x.global_scope

    # global_scope.refer("Python", builtins)

    global_scope.refer("print", NativeFunction(print, FunctionType([Any], Void), "print"))

    global_scope.refer("void", Void)
    global_scope.refer("unit", Unit)
    global_scope.refer("any", Any)
    global_scope.refer("type", Type)
    # global_scope.refer("Class", ClassType)
    global_scope.refer("Class", Class)

    global_scope.refer("bool", Boolean)
    global_scope.refer("string", String)
    global_scope.refer("i64", Int64)
    global_scope.refer("f64", Float64)

    # def _assign(left, right):
    #     if isinstance(left, Field):
    #         return left.set(right)
    #     if isinstance(left, str):
    #         compiler.toolchain.interpreter.x.local(left, right)
    #
    # def _set(obj, n, value):
    #     o = compiler.toolchain.interpreter.execute(obj, runtime=False)
    #     v = compiler.toolchain.interpreter.execute(value, runtime=False)
    #     setattr(o, str(n), v)
    #     return v
    #
    # def _get(obj, n):
    #     try:
    #         return getattr(obj, str(n))
    #     except AttributeError:
    #         ...

    # builtins.CodeGenFunction = CodeGenFunction
    # builtins.Function = Function
    # builtins.Object = ExObj
    # builtins.getattr = NativeFunction(lambda o, n: _get)
    # builtins.setattr = NativeFunction(lambda o, n, v: _set(o, n, v))
    # builtins.print = NativeFunction(lambda *args, **kwargs: print(*args, **{
    #     n: compiler.toolchain.interpreter.execute(value) for n, value in kwargs.items()
    # }))
    # builtins.partial = partial
    # builtins.partialmethod = partialmethod
    #
    # compiler.toolchain.interpreter.x.frame.add_local("__srf__", compiler)
    # compiler.toolchain.interpreter.x.frame.add_local("_._", _get)
    # compiler.toolchain.interpreter.x.frame.add_local("_=_", _assign)
    # compiler.toolchain.interpreter.x.frame.add_local("_;_", lambda l, r: (compiler.toolchain.interpreter.execute(l, runtime=False), compiler.toolchain.interpreter.execute(r, runtime=False))[1])

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
