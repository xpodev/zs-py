from ...ctrt.objects import Scope


class ContextManager:
    _cache: dict[str, Scope]

    def __init__(self):
        self._cache = {}

    def get_scope_from_cached(self, path: str) -> Scope | None:
        try:
            return self._cache[path]
        except KeyError:
            return None

    def add_scope_to_cache(self, path: str, scope: Scope):
        self._cache[path] = scope
