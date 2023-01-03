import * from "env/libraries/std/lang/lang.zs";


var _node__while = create_type("_node__while")

var exec__node__while = fun(node) {
    fun(fn) {
        //Python.builtins.breakpoint();
        fn(__pexec__(node), fn)
    }(codegen(fun(node, self) {
        if (equals(__pexec__(node.condition), Python.True)) {
            print("condition=true");
            __pexec__(node.body)
            //self(node, self)
        }
    }))
}


var __parser_while = Object()
setattr(__parser_while, "nud", fun(parser) {
    fun(node) {
        parser.eat("while");
        parser.eat("(");
        setattr(node, "condition", parser.next("Expression"));
        parser.eat(Python.builtins.chr(41));
        parser.eat("{");
        setattr(node, "body", parser.next("Expression"));
        parser.eat(Python.builtins.chr(125));
        node
    }(_node__while())
})
setattr(__parser_while, "binding_power", 0)
setattr(__parser_while, "token", "while")
__srf__.toolchain.parser.get("Document").add_parser(__parser_while)
//__srf__.toolchain.parser.get("Expression").add_parser(__parser_while)
