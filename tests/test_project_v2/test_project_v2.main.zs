// import * from "env/setup.zs";

// import * from "src/*.zs";

var x = 2
import * from "env/libraries/dot.zs";

fun foo(x, y: i32) { 1 }

var str = Object.__name__.__class__
print(str)
var type = str.__class__
print(type)
var dict = __srf__.context._cache.__class__
print(dict)
var list = __srf__.context._scopes.__class__
print(list)

var equalitySP = Object()
setattr(equalitySP, "token", "==")
setattr(equalitySP, "binding_power", 30)
setattr(equalitySP, "nud", fun(parser) {
    print(parser)
})
setattr(equalitySP, "led", fun(parser, left) {
    print(left)
})

__srf__.toolchain.parser.get("Expression").add_parser(equalitySP)
print(__srf__.toolchain.parser.get("Expression").get_parser("=="))

module TestProjectV2 {

// var x = "Hello"
fun foo() {}
fun foo(x: i32) {
    print(x)
}

foo(12)

inline import * from "src/main.zs";
inline import * from "src/functions.zs";
inline import * from "src/classes.zs";

}
