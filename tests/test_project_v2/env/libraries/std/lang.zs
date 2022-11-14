import * from "env/libraries/builtins.zs";


fun codegen(fn) {
    setattr(fn, "__class__", CodeGenFunction);
    fn
}


var Call = codegen(id)(fun(){}()).__class__
var Name = codegen(id)(id).__class__


fun create_type(name) {
    Python.type(name, Python.tuple(), Python.dict())
}


var __impl_if = codegen(fun(condition, true_, false_) {
    fun(cases) {
        cases.__setitem__(true, true_);
        cases.__setitem__(false, false_);
        __srf__.toolchain.interpreter.execute(
            cases.__getitem__(
                Python.bool(__srf__.toolchain.interpreter.execute(condition))
            )
        )
    }(Python.dict())
})


var __impl_while = codegen(fun(condition, body) {
    fun rec(body_, condition_) {
       if(condition_, fun() { __srf__.toolchain.interpreter.execute(body_); rec(body_, condition_) }(), fun() {}())
    }(body, condition)
})


fun closure(fn) {
    setattr(fn, "refer", codegen(fun(name) {
        fn.body.append(Call(__srf__.toolchain.interpreter.x.local(name.name, __srf__.toolchain.interpreter.execute(name))));
        fn.closure.__setitem__(name.name, __srf__.toolchain.interpreter.execute(name))
    }));
    setattr(fn, "closure", Python.dict());
    fn
}

fun get(fn, x) {
    closure(fn).refer(x)
}

get(fun() { print(x) }, 2)()


Python.builtins.exit()


fun equals(x, y) {
    fun(res, y) {
        __impl_if(res.__eq__(Python.builtins.NotImplemented), y.__eq__(x), res)
    }(x.__eq__(y), y)
}


var _node__if = create_type("_node__if")

fun pp__node__if(node) {
    fun(args) {
        args.append(node.condition);
        args.append(node.body);
        args.append(__impl_if(equals(node.else, Python.None), fun(){}, node.else));
        Call(__impl_if, args)
    }(Python.list())
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
__srf__.toolchain.parser.get("Document").add_parser(__parser_if)
