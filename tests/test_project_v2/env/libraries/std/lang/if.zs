import * from "env/libraries/std/lang/lang.zs";


var _node__if = create_type("_node__if")

var exec__node__if = fun(node) {
    __exec__(__impl_if(__exec__(node.condition), node.body, __impl_if(equals(__exec__(node.else), __exec__(Python.None)), empty(), node.else)))
}


var __parser_if = Object()
setattr(__parser_if, "nud", fun(parser) {
    fun(node) {
        parser.eat("if");
        parser.eat("(");
        setattr(node, "condition", parser.next("Expression"));
        parser.eat(Python.builtins.chr(41));
        parser.eat("{");
        setattr(node, "body", parser.next("Expression"));
        parser.eat(Python.builtins.chr(125));
        __srf__.toolchain.interpreter.execute(__impl_if(
            parser.token("else"),
            fun() {
                parser.eat("else");
                parser.eat("{");
                setattr(node, "else", parser.next("Expression"));
                parser.eat(Python.builtins.chr(125))
            }(),
            fun() {
                setattr(node, "else", Python.None)
            }()
        ));
        node
    }(_node__if())
})
setattr(__parser_if, "binding_power", 0)
setattr(__parser_if, "token", "if")
__srf__.toolchain.parser.get("Expression").add_parser(__parser_if)
__srf__.toolchain.parser.get("Document").add_parser(__parser_if)
