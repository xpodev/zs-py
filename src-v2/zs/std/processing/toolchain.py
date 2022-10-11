from zs.processing import StatefulProcessor, State, Context
from zs.std.objects.compilation_environment import Document
from zs.std.processing.interpreter import Interpreter
from zs.text.file_info import SourceFile
from zs.text.parser import Parser
from zs.text.token_stream import TokenStream
from zs.text.tokenizer import Tokenizer


class Toolchain(StatefulProcessor):
    _context: Context
    _tokenizer: Tokenizer
    _parser: Parser
    _interpreter: Interpreter

    def __init__(
            self,
            *,
            state: State = None,
            context: Context = None,
            tokenizer: Tokenizer = None,
            parser: Parser = None,
            interpreter: Interpreter = None
    ):
        super().__init__(state or State())
        self._context = context or Context()
        self._tokenizer = tokenizer or Tokenizer(state=self.state)
        self._parser = parser or Parser(state=self.state)
        self._interpreter = interpreter or Interpreter(state=state, context=context)

    @property
    def tokenizer(self):
        return self._tokenizer

    @property
    def parser(self):
        return self._parser

    @property
    def interpreter(self):
        return self._interpreter

    def compile_document(self, file: SourceFile) -> Document:
        token_generator = self._tokenizer.tokenize(file)

        token_stream = TokenStream(token_generator)

        document = Document(self._parser.parse(token_stream))

        self._interpreter.execute_document(document.nodes)

        return document
