// import {} from "env/setup.zs";
// import {} from "src/main.zs";
// import {} from "src/test_typeclass.zs";
// import {} from "src/test_export.zs";


fun foo() {
    print("blah");
}

fun foo(x: type) {
    print(x);
}

fun foo(_: unit) {
    print("()");
}

{
    fun foo(x: type) {
        print("Nested", x);
    }

    foo(unit);

    //foo();
}

foo();
foo(type);

var x = type;
print(x);

class FooCls {
    var x = type;
}

fun Foo(x: type) {
    print("Foo function");
    return "asd";
}

var f = FooCls();
print(f);
