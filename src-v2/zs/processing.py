from enum import Enum
from typing import Optional

from . import EmptyObject, Object


class MessageType(str, Enum):
    Info = "Info"
    Warning = "Warning"
    Error = "Error"


class Message(EmptyObject):
    _type: MessageType
    _origin: Object | None
    _content: str
    _processor: "StatefulProcessor"

    def __init__(self, message_type: MessageType, message: str, origin: Object = None, proc: "StatefulProcessor" = None):
        super().__init__()
        self._type = message_type
        self._origin = origin
        self._content = message
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
    _messages: list[Message]
    _processor: Optional["StatefulProcessor"]
    _cache: list[Message] | None

    def __init__(self):
        super().__init__()
        self._messages = []
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

    def error(self, message: str, origin: Object = None):
        self.message(MessageType.Error, message, origin)

    def info(self, message: str, origin: Object = None):
        self.message(MessageType.Info, message, origin)

    def message(self, message_type: MessageType, message: str, origin: Object = None):
        self._messages.append(Message(message_type, message, origin, self._processor))

    def reset(self):
        self._processor = None
        if self._cache:
            self._messages.extend(self._cache)
        self._cache = []

    def run(self, processor: "StatefulProcessor"):
        self._processor = processor

    def warning(self, message: str, origin: Object = None):
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
