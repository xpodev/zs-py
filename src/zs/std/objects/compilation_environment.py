from ...ctrt.core import Module, Scope


class ContextManager:
    _cache: dict[str, Scope]
    _module: dict[str, Module]

    def __init__(self):
        self._cache = {}
        self._module = {}

    def get_scope_from_cached(self, path: str) -> Scope | None:
        try:
            return self._cache[path]
        except KeyError:
            return None

    def add_scope_to_cache(self, path: str, scope: Scope):
        self._cache[path] = scope

    def add_module_to_cache(self, name: str, module: Module):
        self._module[name] = module

    def get_module_from_cache(self, name: str) -> Module | None:
        try:
            return self._module[name]
        except KeyError:
            return None
