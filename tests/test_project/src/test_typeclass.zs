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


fun do_print(x: IPrint)
{
    x.print();
}

do_print(Foo());
