// import * from "env/setup.zs";

// import * from "src/*.zs";

import * from "env/libraries/dot.zs";

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
