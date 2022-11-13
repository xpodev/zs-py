import * from "env/libraries/ntools.zs";
inline import * from "env/libraries/builtins.zs";

fun create_type(name) {
    type(name, tuple(), dict())
//    fun(type_) {
//        setattr(type_, "__class__", type);
//        setattr(type_, "__name__", name);
//        setattr(type_, "__call__", partial(fun(typ) {
//            fun(instance, typ_) {
//                setattr(instance,  "__class__", typ_);
//                getattr(typ_, "__init__", fun(_) { })(instance);
//                instance
//            }(Object(), typ)
//        }, type_));
//        type_
//    }(Object())
}

fun codegen(fn) {
    setattr(fn, "__class__", CodeGenFunction);
    fn
}

var if = codegen(fun(condition, true_, false_) {
    fun(cases) {
        cases.__setitem__(true, true_);
        cases.__setitem__(false, false_);
        __srf__.toolchain.interpreter.execute(
            cases.__getitem__(
                __srf__.toolchain.interpreter.execute(condition)
            )
        )
    }(dict())
})

fun pp_Call(node) { node }


var ASDNode = create_type("ASDNode")

var cls_parser = Object()
setattr(cls_parser, "nud", fun(parser) {
    parser.stream.read();
    print("asd");
    ASDNode()
})
setattr(cls_parser, "binding_power", 0)
setattr(cls_parser, "token", "ASD")
var doc_p = __srf__.toolchain.parser.get("Document")
print(doc_p)

doc_p.add_parser(cls_parser)

if(false,
    fun() {
        print("true!!!")
    }(),
    fun() {
        print("false!!!")
    }()
)
