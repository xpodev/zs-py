from .expression import ExpressionParser
from .function import *
from .module import get_module
from .type import *
from .document import DocumentParser


def get_standard_parser(state: State):
    document = DocumentParser(state)

    parser = Parser(document, state=state)

    parser.add(Expression, expression := ExpressionParser(state))
    parser.add(ClassBodyParser)
    parser.add(inlined := ContextualParser(state, "Inlined"))

    document.add_parsers(
        get_import,
        get_inlined,
        get_class,
        get_function,
        get_module,
        get_var
    )

    inlined.add_parsers(
        get_import
    )

    expression.add_parsers(
        copy_with(get_function, binding_power=0),
        copy_with(get_class, binding_power=0)
    )

    return parser

    # parser.add_parser(get_function)
    # parser.add_parser(get_class)
    # parser.add_parser(get_import)
