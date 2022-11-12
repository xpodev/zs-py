import * from "env/setup.zs";

// import * from "src/*.zs";

fun foo(x) {
    print("in foo");
    print(x);
    print("exiting foo");
    x
}

print(str)
print(type)
print(dict)
print(list)

print("x:", foo(1))


var Type = Object()
Type.make_field("__name__") = "Type"
print(Type.__name__)

import * from "src/main.zs";
