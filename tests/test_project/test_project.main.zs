import {} from "env/setup.zs";
//import {} from "src/main.zs";
import {} from "src/test_typeclass.zs";
// import {} from "src/test_export.zs";

print("Hello, World!");

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
    var x: any;

    fun FooCls(this: FooCls, x) {
        this.x = x;
    }

    fun print_x(this) {
        print("FooCls.print_x:");
        print(this.x);
    }
}

fun Foo(x: type) {
    print("Foo function");
    return "asd";
}

var f = FooCls("hello");
f.print_x();
print(f);

foo(FooCls);

typeclass TCls {
    fun bar(x);
}

typeclass TCls(FooCls) {
    fun bar(this, x) {
        print("TCls.FooCls");
        print(this.x);
    }
}

typeclass TCls(type) {
    fun bar(this, x) {
        print("TCls.type");
        print(x);
    }
}

fun test_tcls(inst: TCls, value: any) {
    inst.bar(value);
}

test_tcls(FooCls("asd"), "hello");
test_tcls(void, "VOID!");
