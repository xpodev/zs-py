from typing import Generic, TypeVar


T = TypeVar('T')
U = TypeVar('U')
V = TypeVar('V')
NodeT = TypeVar("NodeT", bound=Node)


class Object(Generic[NodeT]):
    """
    Base class of all compiler objects.
    """

    @property
    def node(self) -> T | None:
        """
        The original node of this object, or None if this object is dynamically generated.
        """


class Node(Object[Node]):
    """
    Represents a construct in a Z# code file.
    """

    @property
    def node(self) -> T | None:
        return self

    @property
    def token_info(self):
        """
        The token info of this node.
        """


class TokenInfo(Object):
    """
    A superclass of node-specific classes that hold information about the tokens that make up the node.
    """


class Context(Object):
    """
    A wrapper class over a dict[str, Object] used for resolving objects from names.
    This class also supports scoping of names.
    """

    @property
    def parent(self) -> Context:
        """
        The parent context of the context or None if this is the global context.
        """

    def get(self, name: String) -> Object:
        """
        Find and return an object by name in the nearest scope. Parent contexts are also looked up if an object was not found in this context.
        """


class BuildState(Object):
    """
    Holds a state for the whole compilation context. Mostly responsible for holding messages emitted while compiling.
    """


class ZSCompiler(Object):
    """
    The main Z# compiler class. This class is a singleton.
    """

    @property
    def global_context(self) -> Context:
        """
        global interpreter context. modifying this context may influence the compilation of external modules.
        """

    @property
    def toolchain(self) -> Toolchain:
        """
        The toolchain used by the compiler. Each module compilation process uses a different toolchain.
        """

    @property
    def modules(self) -> List[Module]:
        """
        List of module objects that were collected as part of the compilation process.
        """


class Dictionary(Object, Generic[T, U]):
    """
    A wrapper over a dict[T, U] used by the Z# compiler.
    """


class List(Object, Generic[T]):
    """
    A wrapper over a list[T] used by the Z# compiler.
    """


class String(Object):
    """
    A wrapper over a Python string used by the Z# compiler.
    """


class Boolean(Object):
    """
    A wrapper over a Python bool used by the Z# compiler.
    """


class Tokenizer(Object):
    """
    The tokenizer is responsible for converting source code into a stream of tokens
    """


class Parser(Object):
    """
    The parser takes a stream of tokens and returns a stream of nodes.
    """


class ASTProcessor(Object):
    """
    The ast processor takes a stream of nodes and converts them to objects. It also adds them to the document context.
    Import statements, operator definitions and modifiers are executed at this stage.
    Objects are recursively partially created at this point.

    While this processor is running, it will change the context so order matters.
    """


class DependencyResolver(Object):
    """
    The dependency resolver is responsible for gathering all dependencies of the objects and ordering them in an order
    such that when an object is built, it knows for sure that all the objects can be resolved.
    """


class Resolver(Object):
    """
    The resolver is responsible for finishing the object graph such that all objects are connected.
    This is where all the objects are executed.

    Name resolution is done on module basis, meaning that 2 objects defined in separate files but imported into the same module may collide.
    """


class Toolchain(Object):
    """
    A toolchain for converting text to Z# objects.
    """

    @property
    def tokenizer(self) -> Tokenizer:
        """
        The tokenizer of the toolchain.
        """

    @property
    def parser(self) -> Parser:
        """
        The parser of the toolchain.
        """

    @property
    def ast_processor(self) -> ASTProcessor:
        """
        The ast processor of the toolchain.
        """

    @property
    def dependency_resolver(self) -> DependencyResolver:
        """
        The dependency resolver of the toolchain.
        """

    @property
    def resolver(self) -> Resolver:
        """
        The resolver of the toolchain.
        """

    def compile(self, path: String, full: Boolean) -> Module | Document:
        """
        Compile a file from path. If full is true, returns a module object. Otherwise, returns a document object.
        """


class Module(Object):
    """
    Represents a Z# module.
    A Z# module is a directory with a module file.

    Module objects cannot be modified after they are created.
    """

    @property
    def name(self) -> String:
        """
        The name of the module.
        """

    @property
    def exported_items(self) -> Dictionary[String, Object]:
        """
        A mapping of [String -> Object] of the items exported from the module.
        """

    @property
    def documents(self) -> List[Document]:
        """
        A list of all document object that were created while compiling the module.
        """

    @property
    def imported_modules(self) -> List[Module]:
        """
        A list of all imported modules that were compiled while compiling this module.
        """


class Document(Object):
    """
    Represents a Z# document.

    A Z# document is the result of compiling a Z# file.
    """

    @property
    def name(self) -> String:
        """
        The name of the document.
        """

    @property
    def objects(self) -> Dictionary[String, Object]:
        """
        A mapping [String -> Object] of all top-level objects in the document.
        """
