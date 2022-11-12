from enum import Enum
from typing import Optional

from . import EmptyObject, Object
from .std import List, String


class MessageType(String, Enum):
    Info = "Info"
    Warning = "Warning"
    Error = "Error"


class Message(EmptyObject):
    _type: MessageType
    _origin: Object | None
    _content: String
    _processor: "StatefulProcessor"

    def __init__(self, message_type: MessageType, message: str | String, origin: Object = None, proc: "StatefulProcessor" = None):
        super().__init__()
        self._type = message_type
        self._origin = origin
        self._content = String(message)
        self._processor = proc

    @property
    def content(self):
        return self._content

    @property
    def origin(self):
        return self._origin

    @property
    def type(self):
        return self._type

    @property
    def processor(self):
        return self._processor


class State(EmptyObject):
    _messages: List[Message]
    _processor: Optional["StatefulProcessor"]
    _cache: List[Message] | None

    def __init__(self):
        super().__init__()
        self._messages = List()
        self._processor = None
        self._cache = None

    @property
    def is_running(self):
        return self._processor is not None

    @property
    def messages(self):
        return self._messages

    @property
    def processor(self):
        return self._processor

    def error(self, message: str | String, origin: Object = None):
        self.message(MessageType.Error, message, origin)

    def info(self, message: str | String, origin: Object = None):
        self.message(MessageType.Info, message, origin)

    def message(self, message_type: MessageType, message: str | String, origin: Object = None):
        self._messages.add(Message(message_type, String(message), origin, self._processor))

    def reset(self):
        self._processor = None
        if self._cache:
            self._messages.extend(self._cache)
        self._cache = List()

    def run(self, processor: "StatefulProcessor"):
        self._processor = processor

    def warning(self, message: str | String, origin: Object = None):
        self.message(MessageType.Warning, message, origin)


class StatefulProcessor(EmptyObject):
    _state: State

    def __init__(self, state: State):
        super().__init__()
        self._state = state

    @property
    def state(self):
        return self._state

    def run(self):
        self._state.reset()
        self._state.run(self)


# class Context(EmptyObject):
#     _items: dict[str, Object]
#     _parent: Optional["Context"]
#
#     def __init__(self, parent: Optional["Context"] = None, **items: Object):
#         super().__init__()
#         self._items = items
#         self._parent = parent
#
#     @property
#     def items(self):
#         return self._items.items()
#
#     def add(self, value: Object, name: str | String = None):
#         name = name or getattr(value, "name")
#         if name is None:
#             raise TypeError(f"Can't add an unnamed object to the context")
#         name = str(name)
#         if name in self._items:
#             self._items[name] += value
#         else:
#             self._items[name] = value
#
#     def get(self, name: str | String):
#         try:
#             return self._items[str(name)]
#         except KeyError:
#             if self._parent is not None:
#                 return self._parent.get(name)
#             raise
#
#     def set(self, name: str | String, value: Object):
#         name = str(name)
#         if name not in self._items:
#             if self._parent is None:
#                 raise KeyError(f"Could not find name \"{name}\"")
#             self._parent.set(name, value)
#         else:
#             self._items[name] = value
