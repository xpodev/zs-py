from pathlib import Path

from zs.ctrt.context import Scope
from zs.ctrt.interpreter import Interpreter
from zs.ctrt.pp import Preprocessor
from zs.processing import StatefulProcessor, State
from zs.std.objects.compilation_environment import Document, ContextManager
# from zs.std.processing.interpreter import Interpreter
from zs.text.file_info import SourceFile, DocumentInfo
from zs.text.parser import Parser
from zs.text.token_stream import TokenStream
from zs.text.tokenizer import Tokenizer


class Toolchain(StatefulProcessor):
    _context: ContextManager
    _tokenizer: Tokenizer
    _parser: Parser
    _interpreter: Interpreter

    def __init__(
            self,
            *,
            state: State = None,
            context: ContextManager = None,
            tokenizer: Tokenizer = None,
            parser: Parser = None,
            interpreter: Interpreter = None
    ):
        super().__init__(state or State())
        self._context = context or ContextManager()
        self._tokenizer = tokenizer or Tokenizer(state=self.state)
        self._parser = parser or Parser(state=self.state)
        # self._interpreter = interpreter or Interpreter(state=state, context=context)
        self._interpreter = interpreter or Interpreter(self.state)

    @property
    def tokenizer(self):
        return self._tokenizer

    @property
    def parser(self):
        return self._parser

    @property
    def interpreter(self):
        return self._interpreter

    @property
    def gcs(self):
        return self._global

    def compile_document(self, path: Path) -> Document:
        super().run()

        path = path.resolve()
        info = DocumentInfo(path)

        if (nodes := self._context.get_nodes_from_cached(str(path))) is None:
            file = SourceFile.from_path(path)

            token_generator = self._tokenizer.tokenize(file)

            token_stream = TokenStream(token_generator)

            nodes = self._parser.parse(token_stream)

        document = Document(info, nodes)

        with self._context.document(document), self._interpreter.x.scope():
            # self._interpreter.execute_document(document.nodes)

            preprocessor = Preprocessor(self.state)

            pp = list(map(preprocessor.preprocess, nodes))

            result = list(map(self._interpreter.execute, pp))

            return document
