import { print } from Python;
import { Foo } from "src/main.zs";


typeclass IPrint {
    fun print();
}


typeclass IPrint(Foo) {
    fun print() {
        Foo.baz();
        Python.print(IPrint(Foo).print);
        Python.print(print);
        Python.print(this);
    }
}


typeclass IPrint(i64) {
    fun print() {
        Python.print("Number", this);
    }
}


typeclass IPrint(f64) {
    fun print() {
        Python.print("Float!,", this);
    }
}


fun do_print(x: IPrint)
{
    x.print();
}

do_print(Foo());
do_print(45);
do_print(3.14);
