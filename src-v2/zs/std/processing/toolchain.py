from pathlib import Path

from zs.ctrt.runtime import Interpreter
from zs.processing import StatefulProcessor, State
from zs.std.objects.compilation_environment import Document, ContextManager
from zs.text.file_info import SourceFile, DocumentInfo
from zs.text.parser import Parser
from zs.text.token_stream import TokenStream
from zs.text.tokenizer import Tokenizer


class Toolchain(StatefulProcessor):
    _context: ContextManager
    _tokenizer: Tokenizer
    _parser: Parser
    _interpreter: Interpreter
    _document: DocumentInfo

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
    def document(self):
        return self._document

    @property
    def gcs(self):
        return self._global

    def compile_document(self, path: Path) -> Document:
        super().run()

        path = path.resolve()
        self._document = info = DocumentInfo(path)

        if (nodes := self._context.get_nodes_from_cached(str(path))) is None:
            file = SourceFile.from_path(path)

            token_generator = self._tokenizer.tokenize(file)

            token_stream = TokenStream(token_generator, info.path_string)

            nodes = self._parser.parse(token_stream)

        document = Document(info, nodes)

        with self.interpreter.new_context():
            self.interpreter.x.push_frame()
            frame = self.interpreter.x.frame

            self.interpreter.run()

            try:
                for node in nodes:
                    self._interpreter.execute(node)
            except Exception as e:
                print(50 * '-')
                print(f"Caught exception '{type(e).__name__}' while processing node with token '{node}'.")
                print(f"The node is a '{type(node).__name__}' node.")
                print(f"File: {info.path}")
                print()
                print("Exception:", str(e))
                print(50 * '-')
                raise e

        for name, item in frame.items:
            document.add(item, name)

        return document
        # return self.interpreter.x.frame
