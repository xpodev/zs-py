import * from "env/libraries/ntools.zs";
inline import * from "env/libraries/builtins.zs";

var cls_parser = Object()
setattr(cls_parser, "nud", fun(parser) {
    parser.stream.read();
    print("asd")
})
setattr(cls_parser, "binding_power", 0)
setattr(cls_parser, "token", "ASD")
var doc_p = __srf__.toolchain.parser.get("Document")
print(doc_p)

doc_p.add_parser(cls_parser)
