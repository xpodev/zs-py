from zs import Object
from zs.processing import StatefulProcessor, State
from zs.std.objects.compilation_environment import Module
from zs.std.objects.expression import Call
from zs.std.runtime.interpreter import Interpreter


class ModuleProcessor(StatefulProcessor):
    _runtime: Interpreter

    def __init__(self, state: State):
        super().__init__(state)
        self._runtime = Interpreter(state)

    def process_module(self, module: Module, *args: Object):
        self.run()

        if module.entry_point is None:
            return self.state.error(f"Can't execute module \"{module.name}\" because it doesn't have an entry point", module)

        with self._runtime.module(module):
            return self._runtime.execute(Call(module.entry_point, *args))
